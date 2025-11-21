from core.json_reader import Reader
from core.parser import Parser
from core.azure_writer import AzureWriter
from support.types import GenerateCSVProps, ManualCSVProps, APISettings, Formatting, TemplateMap, Response
from base64 import b64decode
from io import BytesIO
from logger import Log
from pathlib import Path
from typing import Any, Literal, TypedDict
from support.vars import DEFAULT_HEADER_MAP, DEFAULT_OPCO_MAP, DEFAULT_SETTINGS_MAP
import support.utils as utils
import pandas as pd

ReaderType = Literal["excel", "opco", "settings"]
AzureFileState = TypedDict(
    "AzureFileState", 
    {
        "upload_id": str,
        "csv_file_name": str,
        "skip_version_row": bool,
    }
)

class API:
    def __init__(self, *, 
            excel_reader: Reader, settings_reader: Reader,
            opco_reader: Reader, logger: Log = None
        ):
        '''API class.
        
        Parameters
        ----------
            excel_reader: Reader
                The Reader used for the Excel columns for reading and parsing files.
            
            settings_reader: Reader
                The Reader used for handling program settings.

            opco_reader: Reader
                The Reader used for handling operating company-domain name key-value mapping.
            
            logger: Log, default None
                The logger, if None is given then it will be a default logger.
        '''
        self.excel: Reader = excel_reader
        self.settings: Reader = settings_reader
        self.opco: Reader = opco_reader
        self.logger: Log = logger or Log()

        self.readers: dict[ReaderType, Reader] = {
            "settings": self.settings,
            "opco": self.opco,
            "excel": self.excel,
        }

        # state tracking for generate_azure_csv
        self._auto_azure_state: AzureFileState = {
            "upload_id": "", 
            "csv_file_name": "",
            "skip_version_row": False,
        }

    def generate_azure_csv(self, content: GenerateCSVProps | pd.DataFrame, upload_id: str = None) -> Response: 
        '''Generates the Azure CSV file for bulk accounts.
        
        Parameters
        ----------
            content: GenerateCSVProps
                A dictionary containing the content to read and parse the Excel file. For testing purposes,
                a DataFrame can also be passed. 
            
            upload_id: str, default None
                The upload ID for each file. It is used to keep track of each file and write to the
                correct file. This is only relevant if flatten CSV is enabled.
        '''
        res: Response = utils.generate_response(message="Generated CSV")
        df: pd.DataFrame = None

        if isinstance(content, dict):
            delimited: list[str] = content['b64'].split(',')
            file_name: str = content['fileName']

            # could add csv support here, for now it will be excel.
            # NOTE: this could be useless because my front end already has this check.
            if 'spreadsheet' not in delimited[0].lower():
                return utils.generate_response(status="error", 
                    message='Incorrect file entered, got file TYPE_HERE'
                )

            b64_string: str = delimited[-1]
            decoded_data: bytes = b64decode(b64_string)
            in_mem_bytes: BytesIO = BytesIO(decoded_data)

            df = pd.read_excel(in_mem_bytes)
        else:
            df = content

        parser: Parser = Parser(df)
        
        # the user defined headers (values).
        # the key is the internal name, the value is the user defined columns.
        # however there is only three required keys: name, opco, and country.
        default_excel_columns: dict[str, str] = self.excel.get_content()

        validate_dict: dict[str, str] = parser.validate_headers(
            default_headers=default_excel_columns
        )

        if validate_dict.get('status', 'error') == 'error':
            return utils.generate_response(status='error', message=f'Invalid file \
                {file_name} uploaded.')

        # maybe read this back? for now i want to keep the full name.
        #parser.apply(default_excel_columns["name"], func=utils.format_name)
        parser.apply(default_excel_columns["opco"], func=lambda x: x.lower())
        excel_names: list[str] = parser.get_rows(default_excel_columns["name"])

        names: list[str] = [utils.format_name(name) for name in excel_names]
        full_names: list[str] = [utils.format_name(name, keep_full=True) for name in excel_names]
        opcos: list[str] = parser.get_rows(default_excel_columns["opco"])

        self.logger.debug(f"Opcos: {opcos}") 
        dupe_names: list[str] = utils.check_duplicate_names(names)

        # the mapping of the operating company to their domain name.
        opco_mappings: dict[str, str] = self.opco.get_content()

        formatters: Formatting = self.settings.get("format")
        usernames: list[str] = utils.generate_usernames(
            dupe_names, opcos, opco_mappings,
            format_type=formatters["format_type"],
            format_case=formatters["format_case"], 
            format_style=formatters["format_style"],
        )

        writer: AzureWriter = AzureWriter(logger=self.logger)

        writer.set_full_names(full_names)
        writer.set_names(names)
        writer.set_block_sign_in(len(names), []) 
        writer.set_usernames(usernames)
        writer.set_passwords([utils.generate_password(20) for _ in range(len(names))])

        curr_date: str = utils.get_date()
        csv_name: str = f"{curr_date}-az-bulk-{utils.get_id()}.csv"

        if upload_id != self._auto_azure_state["upload_id"]:
            self._auto_azure_state["upload_id"] = upload_id
            self._auto_azure_state["csv_file_name"] = csv_name
            self._auto_azure_state["skip_version_row"] = False
        else:
            csv_name = self._auto_azure_state["csv_file_name"]
            
        writer.write(Path(self.get_reader_value("settings", "output_dir")) 
            / csv_name, skip_version=self._auto_azure_state["skip_version_row"])

        # only applicable if flatten_csv is true. multi-file operations are not affected by this.
        # NOTE: flatten csv condition is only used in the front end. it is not used in the backend
        self._auto_azure_state["skip_version_row"] = True

        self.logger.info(f"Generated {csv_name} at {self.get_reader_value('settings', 'output_dir')}")

        templates: TemplateMap = self.settings.get("template")
        if templates["enabled"]:
            temp_res: Response = self._generate_template(templates["text"], writer, curr_date)

            res["status"] = temp_res["status"]
            res["message"] += temp_res["message"]

            # NOTE: the only error here is if the text is too long.
            if temp_res["status"] == "error":
                self.logger.warning(f"{res['message']}, text trimmed to 1250 characters from {len(templates['text'])}")

                # max char is 1250, and only triggers if the text is > 1250.
                self.update_setting("text", templates["text"][:1250], "template")

        # NOTE: any failures will require an update to the context in the frontend. 
        return res
    
    def generate_manual_csv(self, content: list[ManualCSVProps]) -> dict[str, str]:
        '''Generates the Azure CSV file for bulk accounts through the manual input.
        
        Parameters
        ----------
            content: list[ManualCSVProps]
                A list of dictionaries to convert into a DataFrame for a CSV.
                Each dictionary represents a row to be added.
        '''
        res: Response = utils.generate_response(message="")

        self.logger.debug(f"Manual generation data: {content}")
        names: list[str] = []
        opcos: list[str] = []
        full_names: list[str] = []

        opco_mappings: dict[str, str] = self.opco.get_content()

        # contains name, opco, and id. id is not relevant to this however.
        # i could also possibly add in the block sign in values in the content...
        for obj in content:
            name: str = utils.format_name(obj["name"])
            full_name: str = utils.format_name(obj["name"], keep_full=True)
            opco: str = obj["opco"].lower()

            names.append(name)
            full_names.append(full_name)
            opcos.append(opco)

        self.logger.debug(f"Opcos: {opcos}") 
        dupe_names: list[str] = utils.check_duplicate_names(names)

        formatters: Formatting = self.settings.get("format")
        usernames: list[str] = utils.generate_usernames(
            dupe_names, 
            opcos, 
            opco_mappings,
            format_type=formatters["format_type"],
            format_case=formatters["format_case"],
            format_style=formatters["format_style"],
        )
        passwords: list[str] = [utils.generate_password() for _ in range(len(names))]

        writer: AzureWriter = AzureWriter(logger=self.logger)

        writer.set_full_names(full_names)
        writer.set_usernames(usernames)
        writer.set_passwords(passwords)
        writer.set_block_sign_in(len(names), [])
        writer.set_names(names)

        curr_date: str = utils.get_date()
        csv_name: str = f"{curr_date}-az-bulk.csv"
        writer.write(Path(self.get_reader_value("settings", "output_dir")) / csv_name)

        self.logger.info(f"Manual generated {csv_name} at {self.get_reader_value('settings', 'output_dir')}")

        if res["message"] == "":
            res["message"] = "Generated manual CSV"

        templates: TemplateMap = self.settings.get("template")
        if templates["enabled"]:
            temp_res: Response = self._generate_template(templates["text"], writer, curr_date)

            res["status"] = temp_res["status"]
            res["message"] += temp_res["message"]

            # NOTE: the only error here is if the text is too long.
            if temp_res["status"] == "error":
                self.logger.warning(f"{res['message']}, text trimmed to 1250 characters from {len(templates['text'])}")

                # max char is 1250, and only triggers if the text is > 1250.
                self.update_setting("text", templates["text"][:1250], "template")
        
        self.logger.debug(f"Response: {res}")

        return res

    def _generate_template(self, text: str, writer: AzureWriter, date: str) -> Response:
        res: Response = utils.generate_response(message="")
        template_res: Response = writer.write_template(
            self.settings.get("output_dir"), 
            text=text, 
            start_date=date,
        )

        if template_res["status"] == "error":
            res["status"] = "error"
            res["message"] = ", failed to generate template files"
        elif template_res["status"] == "success":
            # NOTE: this is appended to the final successful message
            res["message"] = " and template files"
        
        return res
    
    def get_reader_value(self, reader: Literal["settings", "opco", "excel"], key: str) -> Any:
        '''Gets the values from any Reader keys. If the key does not exist,
        then an empty string is returned.'''
        val: Any = self.readers[reader].get(key)

        if val is None:
            self.logger.error(f"Key {key} does not exist in {reader}")
            return ""
        
        return val
    
    def get_reader_content(self, reader: Literal["settings", "opco", "excel"]) -> dict[str, Any]:
        '''Gets the data of the Reader.'''
        return self.readers[reader].get_content()

    def update_key(self, reader_type: Literal["settings", "opco", "excel"], key: str, value: Any) -> dict[str, Any]:
        '''Updates a key from the given value.'''
        reader: Reader = self.readers[reader_type]

        self.logger.info(f"Starting key update with key {key} and value {value}")
        prev_val: Any = reader.get(key)

        self.logger.debug(f"Key: {key} | Previous value: {prev_val} | New value: {value}")
        res: dict[str, Any] = reader.update(key, value)

        if res["status"] != "error":
            self.logger.info(f"Updated key {key} with value {value}")

        return res
    
    def delete_opco_key(self, key: str) -> dict[str, Any]:
        '''Deletes a key from the operating company Reader.'''
        res: dict[str, Any] = self.opco.delete(key.lower())

        return res
    
    def insert_update_rm_many(self, reader: ReaderType, content: dict[str, Any]) -> dict[str, Any]:
        '''Insert, update, and remove content to the Reader from a given dictionary.'''
        self.readers[reader].clear()
        res: dict[str, Any] = self.readers[reader].insert_update_many(content)

        return res
    
    def add_opco(self, content: dict[str, Any]) -> dict[str, Any]:
        '''Adds a key-value pair to the Reader's content.'''
        # defined in the front end
        KEY: str = "opcoKey"
        VALUE: str = "value"

        self.logger.info(f"Operating company data received: {content}")

        res: dict[str, Any] = self.opco.insert(key=content[KEY], value=content[VALUE])

        return res
    
    def set_output_dir(self, dir_: Path | str = None) -> dict[str, Any]:
        '''Update the output directory.'''
        from tkinter.filedialog import askdirectory

        curr_dir: str = self.settings.get("output_dir")
        
        new_dir: str = ""
        if dir_ is None:
            new_dir = askdirectory()
        else:
            new_dir = str(dir_)
        
        # tuple is a linux only problem with askdirectory lol
        if new_dir == "" or isinstance(new_dir, tuple) or new_dir == curr_dir:
            return utils.generate_response(status="error", message="No changes done")

        self.logger.info(f"New directory: {new_dir}")
        res: dict[str, Any] = self.settings.update("output_dir", new_dir)
        res["content"] = new_dir

        return res
    
    def update_setting(self, key: str, value: Any, parent_key: str = None) -> dict[str, Any]:
        '''Updates a setting key.
        
        Parameters
        ----------
            key: str
                The target key being updated.
            
            value: Any
                Any value for the key replacement.
            
            parent_key: str, default None
                The parent key of the given key argument. This is only necessary if multiple keys
                of the same name exists in different nest levels. By default it is None.
        '''
        self.logger.info("Settings update requested")
        debug_val: Any = utils.format_value(value)

        self.logger.debug(f"Key: {key} | Value: {debug_val} | Parent Key: {parent_key}")

        res: dict[str, Any] = self.settings.update_search(key, value, main_key=parent_key)

        if res["status"] == "success":
            self.settings.write(self.settings.get_content())

        return res