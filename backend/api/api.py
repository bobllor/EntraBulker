from core.json_reader import Reader
from core.parser import Parser
from core.azure_writer import AzureWriter
from support.types import GenerateCSVProps, ManualCSVProps, APISettings, Response, HeaderMap
from support.types import Password, Formatting, TemplateMap, Metadata
from base64 import b64decode
from io import BytesIO
from logger import Log
from pathlib import Path
from typing import Any, Literal, TypedDict, Callable
from support.vars import DEFAULT_SETTINGS_MAP, PROJECT_ROOT, META, UPDATER
from copy import deepcopy
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
            excel_reader: Reader, 
            settings_reader: Reader,
            opco_reader: Reader, 
            logger: Log = None,
            project_root: Path = PROJECT_ROOT,
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
            
            project_root: Path, default `PROJECT_ROOT`
                The project root folder. This is only used for writing to files,
                it ensures that the files are working in the same file system. 
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

        self._project_root: Path = project_root

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
        settings: APISettings = self.settings.get_content()

        self.logger.debug(f"Headers: {excel_columns}")
        validate_dict: Response = self._validate_df(
            df,
            excel_columns,
            two_name_column_support=settings["two_name_column_support"],
        )

        if validate_dict["status"] == "error":
            self.logger.error(f"Error validating DataFrame, message: {validate_dict['message']}")
            return validate_dict
        
        # creating the name series and adding it into the DataFrame for normalization
        # only if using two name columns
        if settings["two_name_column_support"]:
            full_name_series: pd.Series = parser.create_series(
                func=self._concat_full_name,
                args=(parser.df[excel_columns["first_name"]], parser.df[excel_columns["last_name"]])
            )

            parser.add(excel_columns["name"], full_name_series)

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

        writer: AzureWriter = self._get_azure_writer(full_names=full_names, usernames=usernames, names=names)

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
    
    def _validate_df(self, df: pd.DataFrame, headers: HeaderMap, *, two_name_column_support: bool = False):
        '''Validate the DataFrame and its headers. It will return a Response indicating an
        error/success and a message with the error if applicable.
        
        Parameters
        ----------
            df: DataFrame
                The DataFrame.

            headers: dict[str, str]
                Dictionary that maps internal variable names to user-defined names. The keys
                are the internal names, the values are user-defined names. Used to validate
                column headers.
            
            two_name_column_support: bool, default `False`
                A boolean used to handle the column for the client name being split
                into *two columns* (`First name`/`Last name`) instead of a single `Full name` column.
                By default it is `False`. If true, then it will create a new column `Full name` and remove
                the two columns for normalization.
        '''
        headers_copy: HeaderMap = deepcopy(headers)

        # must remove otherwise column check will fail
        if not two_name_column_support:
            del headers_copy["first_name"]
            del headers_copy["last_name"]
        else:
            # this will be added back in the check_df_columns step
            # after combining the first_name and last_name columns.
            del headers_copy["name"]

        # check_df_columns must be the last number in the dict
        # any other functions can be in any order
        func_dict: dict[int, dict[str, Any]] = {
            0: {"func": self._check_duplicate_headers, "args": [headers_copy]},
            1: {"func": self._check_duplicate_columns, "args": [df]},
            2: {"func": self._check_df_columns, "args": [df, headers_copy]},
        }

        res: Response = utils.generate_response(message="")

        for i in range(len(func_dict)):
            func: Callable[[Any], Response] = func_dict[i]["func"]
            args: tuple[Any] = func_dict[i]["args"]

            if args is not None:
                res = func(*args)
            else:
                res = func()

            if res["status"] == "error":
                return res

        res["message"] = "Successful validation"

        return res
    
    def _concat_full_name(self, first_series: pd.Series, last_series: pd.Series) -> pd.Series:
        '''Concatenates two name Series into a full name Series. This is used for two column support.
        
        If there are empty values in either series or if a non-string is read, then the row will be empty. 
        This is intended to be used to drop the row.

        Parameters
        ----------
            first_series: pd.Series[str]
                The Series representing the first name column.

            last_series: pd.Series[str]
                The Series representing the last name column.
        '''
        name_func = lambda x: "" if not isinstance(x, str) else x.strip()

        first_series = first_series.fillna("").apply(name_func)
        last_series = last_series.fillna("").apply(name_func)

        first_list: list[str] = first_series.to_list()
        last_list: list[str] = last_series.to_list()

        self.logger.debug(f"Concatenating to full name, first name data: {first_list} | last name data: {last_list}")

        full_names: list[str] = []

        for i, f_name in enumerate(first_list):
            l_name: str = last_list[i]

            if f_name == "" or l_name == "":
                full_names.append("")
            else:
                full_names.append(f_name + " " + l_name)
        
        full_series: pd.Series = pd.Series(full_names)

        self.logger.debug(f"Concatenated names: {full_names}")

        return full_series
    
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

        writer: AzureWriter = self._get_azure_writer(
            full_names=full_names,
            usernames=usernames,
            names=names
        )

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
    
    def _get_azure_writer(self, *,
        full_names: list[str],
        usernames: list[str],
        names: list[str]) -> AzureWriter:
        '''Creates an AzureWriter with the data set for writing.'''
        writer: AzureWriter = AzureWriter(logger=self.logger, project_root=self._project_root)

        passwords: list[str] = []
        for _ in range(len(names)):
            password_res: Response = self.generate_password()

            passwords.append(password_res["content"])

        writer.set_full_names(full_names)
        writer.set_names(names)
        writer.set_usernames(usernames)
        writer.set_block_sign_in(len(full_names), [])
        writer.set_passwords(passwords)

        return writer

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
            use_uppercase_letters=password_settings["use_uppercase"],
            use_numbers=password_settings["use_numbers"],
        )

        res["content"] = password

        return res

    def _check_duplicate_headers(self, headers: HeaderMap) -> Response:
        '''Checks the given HeaderMap for duplicate values. The HeaderMap will be reversed to
        value-key in order to validate and get the correct data from the DataFrame.
        
        If duplicate values are found, then an error Response will be returned.
        '''
        res: Response = utils.generate_response(message="Successful Headers validation")
        seen: set[str] = set()

        for val in headers.values():
            seen.add(val)

        if len(seen) != len(headers):
            value_str: str = "value" if len(seen) == 1 else "values"
            res["message"] = f'Duplicate {value_str} "{", ".join([val for val in seen])}" found' \
                ', cannot have duplicate values: header values must be updated'
            res["status"] = "error"
        
        return res
    
    def _check_duplicate_columns(self, df: pd.DataFrame) -> Response:
        '''Checks the DataFrame of the file for duplicate column names. This ensures that there will not be multiple
        same valued columns in a given file.

        It returns an Response with an error if found.
        '''
        seen_values: set[str] = set()
        duplicates: list[str] = []

        for val in df.columns:
            if val in seen_values:
                duplicates.append(val)

            seen_values.add(val)
        
        if len(duplicates) != 0:
            col_str: str = "columns found in the file" if len(duplicates) != 1 else "column found in the file"
            return utils.generate_response("error", message=f"Duplicate {col_str}: {', '.join(duplicates)}")
        
        return utils.generate_response(message="No duplicates found in the excel")

    def _check_df_columns(self, df: pd.DataFrame, headers: dict[str, str]) -> Response:
        '''Checks the DataFrame columns to the reversed column map.'''
        # reverse to check the user defined names
        rev_column_map: dict = {v: k for k, v in headers.items()}

        found: set[str]= set()

        for col in df.columns:
            low_col: str = col.lower()

            if len(found) == len(rev_column_map):
                break

            if low_col in rev_column_map:
                found.add(low_col)

        if len(found) != len(headers):
            missing_columns: list[str] = [key for key in rev_column_map if key not in found]

            column_str: str = "column header" if len(missing_columns) == 1 else "column headers"

            return utils.generate_response(status='error', message=f'File is missing {column_str}: {", ".join(missing_columns)}')

        return utils.generate_response(status='success', message=f"Found columns {','.join(found)}")
    
    def get_metadata(self) -> Metadata:
        '''Gets the metadata in a dictionary response.'''
        return META

    def run_updater(self) -> None:
        '''Runs the Updater for the application.
        
        WARNING: This will exit the current program with a code 3 and run the separate update installer.
        '''
        updater_cmd: list[str] = [
            str(self._project_root / UPDATER)
        ]

        self.logger.info("Updating application")

        utils.run_cmd(updater_cmd)
        exit(3)