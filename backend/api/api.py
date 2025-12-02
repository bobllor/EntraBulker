from core.json_reader import Reader
from core.parser import Parser
from core.azure_writer import AzureWriter
from support.types import GenerateCSVProps, ManualCSVProps, APISettings, Formatting, TemplateMap, Response, HeaderMap
from support.types import Password
from base64 import b64decode
from io import BytesIO
from logger import Log
from pathlib import Path
from typing import Any, Literal, TypedDict
from support.vars import DEFAULT_SETTINGS_MAP
import support.utils as utils
import pandas as pd

ReaderType = Literal["excel", "opco", "settings"]
AzureFileState = TypedDict(
    "AzureFileState", 
    {
        "upload_id": str,
        "csv_file_name": str,
        "skip_version_row": bool,
        "uid": str,
        "template_name": str,
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
            "uid": "",
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
        res: Response = utils.generate_response(message="CSV generated")
        df: pd.DataFrame = None

        if isinstance(content, dict):
            delimited: list[str] = content['b64'].split(',')
            file_name: str = content['fileName']

            meta_info: str = delimited[0]

            self.logger.info(f"Received file {file_name}: {meta_info}")
            if all(file_type not in meta_info.lower() for file_type in ["spreadsheet", "csv"]):
                return utils.generate_response(status="error", 
                    message='Invalid file entered, only .csv and .xlsx are allowed'
                )
            
            is_excel: bool = "spreadsheet" in meta_info

            b64_string: str = delimited[-1]
            decoded_data: bytes = b64decode(b64_string)
            in_mem_bytes: BytesIO = BytesIO(decoded_data)

            try:
                if is_excel:
                    df = pd.read_excel(in_mem_bytes)
                else:
                    df = pd.read_csv(in_mem_bytes)
            except Exception as e:
                self.logger.critical(f"Failed to parse file: {file_name} | {meta_info}")
                self.logger.critical(f"Exception: {e}")

                return utils.generate_response("error", message=f"An unknown error occurred while parsing {file_name}")

            self.logger.info(f"File column names: {df.columns.to_list()}")
        else:
            df = content

        if upload_id is None:
            upload_id = utils.get_id(divisor=2)

        parser: Parser = Parser(df)
        base_len: int = parser.length

        if base_len == 0:
            res["status"] = "error"
            res["message"] = "File is empty"
            
            return res
        
        # the user defined headers (values).
        # the key is the internal name, the value is the user defined columns.
        # however there are only two required keys: name and opco.
        excel_columns: HeaderMap = self.excel.get_content()

        self.logger.debug(f"Headers: {self.get_reader_content('excel')}")
        validate_dict: Response = parser.validate(
            default_headers=self.get_reader_content("excel")
        )

        if validate_dict["status"] == "error":
            self.logger.error(f"Error validating DataFrame, message: {validate_dict['message']}")
            return validate_dict

        # maybe read this back? for now i want to keep the full name.
        #parser.apply(default_excel_columns["name"], func=utils.format_name)

        # converting all values to a string to ensure no errors occur.
        parser.apply(excel_columns["opco"], func=lambda x: x.lower())
        
        dropped_name_rows: int = parser.drop_empty_rows(excel_columns["name"])
        dropped_opco_rows: int = parser.drop_empty_rows(excel_columns["opco"])

        dropped_rows: int = dropped_name_rows + dropped_opco_rows

        new_len: int = parser.length

        self.logger.debug(f"Dropped names: {dropped_name_rows}/{base_len}")
        self.logger.debug(f"Dropped opcos: {dropped_opco_rows}/{base_len}")
        self.logger.debug(f"Total dropped rows: {dropped_rows}/{base_len}")

        if new_len == 0:
            res["status"] = "error"
            res["message"] = f"File is empty after validation ({dropped_rows}/{base_len} dropped rows), please correct the data"

            return res

        if dropped_rows > 0:
            rows_str: str = "rows" if dropped_rows > 1 else "row"
            res["message"] += f", dropped {dropped_rows}/{base_len} {rows_str} from file due to missing values"

        # ensure only strings are being worked with here. 
        parser.apply(excel_columns["name"], func=lambda x: str(x))
        parser.apply(excel_columns["opco"], func=lambda x: str(x))

        excel_names: list[str] = parser.get_rows(excel_columns["name"])
        opcos: list[str] = parser.get_rows(excel_columns["opco"])

        self.logger.debug(f"Name DF columns: {excel_names}")
        self.logger.debug(f"Opco DF columns: {opcos}")

        names: list[str] = [utils.format_name(name) for name in excel_names]
        full_names: list[str] = [utils.format_name(name, keep_full=True) for name in excel_names]

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

        passwords: list[str] = []
        for _ in range(len(names)):
            password_res: Response = self.generate_password()

            passwords.append(password_res["content"])
        
        writer.set_passwords(passwords)

        curr_date: str = utils.get_date()

        # determines whether or not to create a new file or append to an existing file
        if upload_id != self._auto_azure_state["upload_id"]:
            # this is always reset on every run (assuming no flatten csv).
            self._auto_azure_state["upload_id"] = upload_id
            self._auto_azure_state["skip_version_row"] = False

            self._auto_azure_state["uid"] = utils.get_id()
            csv_name: str = f"{curr_date}-az-bulk-{self._auto_azure_state['uid']}.csv"

            self._auto_azure_state["csv_file_name"] = csv_name
            self._auto_azure_state["template_name"] = f"{curr_date}-{self._auto_azure_state['uid']}"
        else:
            csv_name: str = self._auto_azure_state["csv_file_name"]
            
        writer.write(Path(self.get_reader_value("settings", "output_dir")) 
            / csv_name, skip_version=self._auto_azure_state["skip_version_row"])

        # only applicable if flatten_csv is true. multi-file operations are not affected by this.
        # NOTE: flatten csv condition is only used in the front end. it is not used in the backend
        self._auto_azure_state["skip_version_row"] = True

        self.logger.info(f"Generated {csv_name} at {self.get_reader_value('settings', 'output_dir')}")

        templates: TemplateMap = self.settings.get("template")
        if templates["enabled"]:
            temp_res: Response = self._generate_template(templates["text"], writer, self._auto_azure_state["template_name"])

            res["status"] = temp_res["status"]
            res["message"] += temp_res["message"]

            # NOTE: the only error here is if the text is too long.
            if temp_res["status"] == "error":
                self.logger.warning(f"{res['message']}, text trimmed to 1250 characters from {len(templates['text'])}")

                # max char is 1250, and only triggers if the text is > 1250.
                self.update_setting("text", templates["text"][:1250], "template")

        # NOTE: any failures will require an update to the context in the frontend. 
        self.logger.debug(f"Azure CSV generated: {res}")

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
        passwords: list[str] = []
        for _ in range(len(names)):
            password_res: Response = self.generate_password()

            passwords.append(password_res["content"])

        writer: AzureWriter = AzureWriter(logger=self.logger)

        writer.set_full_names(full_names)
        writer.set_usernames(usernames)
        writer.set_passwords(passwords)
        writer.set_block_sign_in(len(names), [])
        writer.set_names(names)

        curr_date: str = utils.get_date()
        uid: str = utils.get_id()

        csv_name: str = f"{curr_date}-az-bulk-{uid}.csv"
        writer.write(Path(self.get_reader_value("settings", "output_dir")) / csv_name)

        self.logger.info(f"Manual generated {csv_name} at {self.get_reader_value('settings', 'output_dir')}")

        if res["message"] == "":
            res["message"] = "Generated manual CSV"

        templates: TemplateMap = self.settings.get("template")
        if templates["enabled"]:
            temp_res: Response = self._generate_template(templates["text"], writer, f"{curr_date}-{uid}")

            res["status"] = temp_res["status"]
            res["message"] += temp_res["message"]

            # NOTE: the only error here is if the text is too long.
            if temp_res["status"] == "error":
                self.logger.warning(f"{res['message']}, text trimmed to 1250 characters from {len(templates['text'])}")

                # max char is 1250, and only triggers if the text is > 1250.
                self.update_setting("text", templates["text"][:1250], "template")
        
        self.logger.debug(f"Response: {res}")

        return res

    def _generate_template(self, text: str, writer: AzureWriter, file_name: str) -> Response:
        res: Response = utils.generate_response(message="")
        template_res: Response = writer.write_template(
            self.settings.get("output_dir"), 
            text=text, 
            file_name=file_name,
        )

        if template_res["status"] == "error":
            res["status"] = "error"
            res["message"] = ", failed to generate template files"
        elif template_res["status"] == "success":
            # NOTE: this is appended to the final successful message
            res["message"] = " and generated template files"
        
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
        
        self.logger.debug(f"Update setting response: {res}")

        return res
    
    def generate_password(self) -> Response:
        '''Generates a random password based off of the settings and returns a response. A password
        will always be returned regardless of an error or not.

        The password is always guaranteed to have one lowercase letter, one uppercase letter,
        and one special character.
        
        The password is part of the `content` key of the Response.
        '''
        res: Response = utils.generate_response(message="Generated password", content="")

        # if all else fails then grab the default values.
        password_settings: Password = self.settings.get("password")

        if password_settings is None:
            self.logger.warning(f"Failed to get Password settings from the Settings Reader, it has been reset to its default values")

            password_settings = DEFAULT_SETTINGS_MAP["password"]
            self.settings.update("password", password_settings)

            res["message"] += ", an error occurred while generating the password and has been reset to its default values"

            update_res: Response = self.update_setting("password", DEFAULT_SETTINGS_MAP["password"])

            if update_res["status"] == "error":
                self.logger.error(f"Failed to update settings: {update_res}")

                # catastrophic fail, will default back to default settings but still generate a password.
                return utils.generate_response("error", message="Unknown failure has occurred, the issue has been logged", 
                    content=utils.generate_password(DEFAULT_SETTINGS_MAP["password"]["length"]))
        
        password: str = utils.generate_password(
            password_settings["length"], 
            use_punctuations=password_settings["use_punctuations"],
            use_uppercase_letters=password_settings["use_uppercase"]
        )

        res["content"] = password

        return res