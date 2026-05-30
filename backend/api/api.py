from core.json_reader import Reader
from core.parser import Parser
from core.azure_writer import AzureWriter
from support.types import GenerateCSVProps, ManualCSVProps, APISettings, Response, HeaderMap
from support.types import Password, Formatting, TemplateMap, Metadata, UserData
from base64 import b64decode
from io import BytesIO
from logger import Log
from pathlib import Path
from typing import Any, Literal, TypedDict, Callable
from support.vars import DEFAULT_SETTINGS_MAP, PROJECT_ROOT, META, UPDATER_PATH, VERSION
from copy import deepcopy
from dataclasses import dataclass
import support.utils as utils
import pandas as pd
import webview

ReaderType = Literal["excel", "opco", "settings"]

@dataclass
class AzureFileState:
    '''Primarily used for flattening multiple uploaded files into a single file output. 
    It tracks the upload ID of the file.
    '''
    # The ID of the current upload, used to track files to an AzureState. If given, the
    # other fields of the class will be reused to flatten into a single file.
    upload_id: str = ""
    # The output file name for the bulk CSV. It will also be generated for Graph due to
    # the initial password login being part of it.
    output_name: str = ""
    # The template directory name for the template text files. This is optional and is applied
    # if the setting for the templates are enabled.
    template_dir_name: str = ""
    # Skips the version row in the output, e.g. "version:v1.0". This only applies to
    # multiple uploaded files, if it is a single file it will do nothing.
    skip_version_row: bool = False

class API:
    def __init__(self, *, 
            excel_reader: Reader, 
            settings_reader: Reader,
            opco_reader: Reader, 
            logger: Log = None,
            project_root: Path = PROJECT_ROOT,
            window: webview.Window = None,
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
            
            window: webview.Window, default None
                The window of webview. By default it is None, and can be set
                via the method set_window.
        '''
        self.excel: Reader = excel_reader
        self.settings: Reader = settings_reader
        self.opco: Reader = opco_reader
        self.logger: Log = logger or Log()

        # pywebview, not added in due to CI fails
        self._window: webview.Window = window

        self.readers: dict[ReaderType, Reader] = {
            "settings": self.settings,
            "opco": self.opco,
            "excel": self.excel,
        }

        self._project_root: Path = project_root

        self.file_state: AzureFileState = AzureFileState()

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
        df_response: Response = self._get_df(content)
        if df_response["status"] == "error":
            return df_response
        df: pd.DataFrame = df_response["content"]

        if upload_id is None:
            upload_id = utils.get_id(divisor=2)

        parse_res: Response = self._start_parse_df(df)
        if parse_res["status"] == "error":
            self.logger.critical(f"Failed to parse DataFrame: {parse_res}")
            return parse_res 

        # why i did it this way i dont know. 
        # any changes now will break a lot of the tests and how
        # it is designed in the frontend. me: 5-30-26
        res["message"] += parse_res["message"]
        parser: Parser = parse_res["content"]

        self._start_nameopco_col_to_string(parser)
        user_data: UserData = self._start_extract_user_data(parser)

        writer: AzureWriter = self._get_azure_writer(
            full_names=user_data["full_names"], 
            usernames=user_data["usernames"], 
            names=user_data["full_names"],
            passwords=user_data["passwords"],
        )

        self.file_state = self._new_azure_file_state(upload_id)

        writer.write(Path(self.get_reader_value("settings", "output_dir")) 
            / self.file_state.output_name, skip_version=self.file_state.skip_version_row)
        self.logger.info(f"Generated {self.file_state.output_name} at {self.get_reader_value('settings', 'output_dir')}")

        # only applicable if flatten_csv is true. operations where each file generates an output will
        # not be affected by this.
        self.file_state.skip_version_row = True
        
        self._write_template(writer)

        # NOTE: any failures will require an update to the context in the frontend. 
        self.logger.debug(f"Azure CSV generated: {res}")

        return res

    def _write_template(self, writer: AzureWriter):
        '''Generates the template text files and folders. This requires the
        templates option to be enabled, if it is not then it will do nothing.
        '''
        res: Response = utils.generate_response(message="")
        templates: TemplateMap = self.settings.get("template")
        if templates["enabled"]:
            temp_res: Response = self._generate_template(templates["text"], writer, self.file_state.template_dir_name)

            # NOTE: the only error here is if the text is too long.
            if temp_res["status"] == "error":
                self.logger.warning(f"{res['message']}, text trimmed to 1250 characters from {len(templates['text'])}")

                # max char is 1250, and only triggers if the text is > 1250.
                self.update_setting("text", templates["text"][:1250], "template")
    
    def generate_graph_azure(self, content: GenerateCSVProps | pd.DataFrame, upload_id: str = None) -> Response:
        '''Parses the content of the file and generates the users via Graph REST API.'''
        # NOTE: if errors occur the message will be different
        res: Response = utils.generate_response(message="Added users")
        df_res: Response = self._get_df(content)
        if df_res["status"] == "error":
            return df_res
        df: pd.DataFrame = df_res["content"]

        valid_res: Response = self._start_validate_df(df)
        if valid_res["status"] == "error":
            return valid_res
        
        parser: Parser = self._start_parse_df(df)
    
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
            names=names,
            passwords=passwords
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
    
    def set_window(self, window: webview.Window) -> None:
        '''Sets the pywebview window.
        
        window: webview.Window
            The pywebview Window.
        '''
        self._window = window
    
    def _get_azure_writer(self, *,
        full_names: list[str],
        usernames: list[str],
        names: list[str],
        passwords: list[str]) -> AzureWriter:
        '''Creates an AzureWriter with the data set for writing.
        
        Parameters
        ----------
            full_names: list[str]
                A list of full names that is used as the display name. These are the unedited
                names.
            
            usernames: list[str]
                A list of user principal names. This is a email login-identifier for Azure, an
                example being `someuser@domain.com`.
            
            names: list[str]
                A list of names used to fill in the 'givenName' and 'surname' properties (first/last).
                A list of full names can be given, as it will be parsed into the first and last names
                automatically.
            
            passwords: list[str]
                A list of passwords for the user.
        '''
        writer: AzureWriter = AzureWriter(logger=self.logger, project_root=self._project_root)

        writer.set_full_names(full_names)
        writer.set_names(names)
        writer.set_usernames(usernames)
        writer.set_block_sign_in(len(full_names), [])
        writer.set_passwords(passwords)

        return writer

    def _generate_template(self, text: str, writer: AzureWriter, dir_name: str) -> Response:
        res: Response = utils.generate_response(message="")
        if text.strip() == "":
            res["status"] = "error"
            res["message"] = ", unable to generate text files due to empty text entry"

            return res

        template_res: Response = writer.write_template(
            self.settings.get("output_dir"), 
            text=text, 
            dir_name=dir_name,
        )

        if template_res["status"] == "error":
            res["status"] = "error"
            res["message"] = ", failed to generate text files"
        elif template_res["status"] == "success":
            # NOTE: this is appended to the final successful message
            res["message"] = " and generated text files"
        
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

            res["message"] += ", the password settings has been reset to its default values due to an error"

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
    
    def check_version(self, url: str = None) -> Response:
        '''Checks the version of the program from the repsitory through a request. This
        compares the version of the program to the one in the repository.
        
        It returns a Response with a new key `has_update` of a bool indicating if an update
        is needed or not.

        In case of any errors, this will always return False.

        Parameters
        ----------
            url: str, default None
                The URL for the request. By default it is None, and will use a default URL.
        '''
        # NOTE: the message is not intended to be used on the frontend.
        res: Response = utils.generate_response(message="Successfully checked version", content=False)
        if url is None:
            url = META["version_url"]

        out_res: Response = utils.get_version(url)
        res["content"] = utils.compare_version(VERSION, out_res["content"])

        self.logger.debug(f"Check version response: {out_res}")

        if out_res["status"] == "error" or out_res["exception"] is not None:
            self.logger.error(f"Failed to request on {url}: {out_res}")
            res["message"] = out_res["message"]
            res["content"] = False
            res["status"] = "error"

            return res

        self.logger.debug(f"Version response: {res}")
        
        return res

    def run_updater(self) -> Response:
        '''Runs the Updater for the application.

        This will end the current application and launch the updater.

        In case of a failure or the path doesn't exist, then an error will occur and return to the program
        with a Response.
        '''
        res: Response = utils.generate_response(message="Updating application")
        updater_cmd: list[str] = [
            str(UPDATER_PATH)
        ]

        if not UPDATER_PATH.exists():
            res["status"] = "error"
            res["message"] = f"{UPDATER_PATH} does not exist"

            self.logger.warning(f"Failed to run updater: {res}, expected path: {UPDATER_PATH}")

            return res

        self.logger.info("Updating application")
        self.logger.debug(f"Updater path: {UPDATER_PATH}")

        self._window.destroy()
        out: str = utils.run_cmd(updater_cmd, cwd=str(PROJECT_ROOT.parent))
        self.logger.info(f"Ran command: {updater_cmd}, out: {out}")

        if out != "":
            self.logger.error(f"Failed to run updater: {out}")
            res["status"] = "error"
            res["message"] = "Failed to run executable"

            return res

        exit(0)
        
        # this will never be reached but leaving it here for best practices.
        return res
    
    def _get_df(self, content: GenerateCSVProps | pd.DataFrame) -> Response:
        '''Parses the content and returns a Response containing a DataFrame.
        
        If content is already a DataFrame, then it will return the DataFrame. This is only
        relevant to test cases.

        If an error occurs, then it will return an error Response.
        '''
        df: pd.DataFrame = None
        res: Response = utils.generate_response(content=None)
        file_name: str = ""

        if isinstance(content, dict):
            delimited: list[str] = content['b64'].split(',')
            file_name = content['fileName']

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
        
        res["content"] = df
        if df is None:
            self.logger.critical(f"Failed to parse content, got None for DataFrame: {file_name}")
            res["status"] = "error"
            res["message"] = "An unknown error occurred while reading file"

        return res
    
    def _start_validate_df(self, df: pd.DataFrame) -> Response:
        '''Starts the validation of the DataFrame. It is a wrapper that calls self._validate_df.
        
        It checks the DataFrame and the headers data defined in the Excel mapping configuration file:
            - The header values are checked for duplicate entries
            - Columns are checked for duplicate entries
            - Columns defined in the header values exists in the DataFrame
        
        No modifications are done on the DataFrame. It will return a Response indicating if the
        DataFrame is valid.
        '''
        excel_columns: HeaderMap = self.excel.get_content()
        settings: APISettings = self.settings.get_content()

        self.logger.debug(f"Headers: {excel_columns}")
        valid_res: Response = self._validate_df(
            df,
            excel_columns,
            two_name_column_support=settings["two_name_column_support"],
        )

        if valid_res["status"] == "error":
            self.logger.error(f"Error validating DataFrame, message: {valid_res['message']}")

        return valid_res

    def _start_parse_df(self, df: pd.DataFrame) -> Response:
        '''Parses the DataFrame and corrects bad data. It will return the Parser used
        to parse the DataFrame in the 'content' of the Response.
        
        Any errors that occur will also be returned as an error Response.
        '''
        res: Response = utils.generate_response(message="CSV generated")

        parser: Parser = Parser(df)
        res["content"] = parser

        base_len: int = parser.length

        excel_columns: HeaderMap = self.excel.get_content()
        settings: APISettings = self.settings.get_content()

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

        # not considered an error
        if dropped_rows > 0:
            rows_str: str = "rows" if dropped_rows > 1 else "row"
            res["message"] += f", dropped {dropped_rows}/{base_len} {rows_str} from file due to missing values"
        
        return res

    def _start_nameopco_col_to_string(self, parser: Parser):
        '''Converts the columns 'name' and 'opco' of the Excel mappings. It
        uses the values given by the config from the user.

        This will modify the DataFrame given in Parser in place.
        ''' 
        # the user defined headers (values).
        # the key is the internal name, the value is the user defined columns.
        # however there are only two required keys: name and opco.
        excel_columns: HeaderMap = self.excel.get_content()

        # ensure only strings are being worked with here. 
        parser.apply(excel_columns["name"], func=lambda x: str(x))
        parser.apply(excel_columns["opco"], func=lambda x: str(x))

    def _start_extract_user_data(self, parser: Parser) -> UserData:
        '''Extracts the user data from the DataFrame.

        It will return a UserData object containing the information for
        the users for bulking/adding to Entra ID.
        '''
        excel_columns: HeaderMap = self.excel.get_content()
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

        passwords: list[str] = []
        for _ in range(len(usernames)):
            pass_res: Response = self.generate_password()
            password: str = pass_res["content"]

            passwords.append(password)

        data: UserData = {
            "usernames": usernames,
            "full_names": full_names,
            "passwords": passwords,
        }

        return data

    def _new_azure_file_state(self, upload_id: str) -> AzureFileState:
        '''Creates a new Azure file state if the given upload ID does not match
        the current ID in the state.

        If the upload ID matches the current ID, then it will return the original
        state.
        '''
        file_state: AzureFileState = self.file_state

        # determines whether or not to create a new file or append to an existing file
        # by default file_state.upload_id is empty
        # this is always reset on every run if flatten csv is not used.
        if upload_id != self.file_state.upload_id:
            curr_date: str = utils.get_date()
            uuid: str = utils.get_id()

            csv_name: str = f"{curr_date}-az-bulk-{uuid}.csv"
            template_dir_name: str = f"{curr_date}-{uuid}"

            file_state = AzureFileState(upload_id, csv_name, template_dir_name)
            self.logger.info(f"Created new file state: {file_state.__dict__}")
        else:
            self.logger.info(f"State already exists for {upload_id}")
        
        return file_state
    
    def _validate_df(self, df: pd.DataFrame, headers: HeaderMap, *, two_name_column_support: bool = False) -> Response:
        '''Validate the DataFrame and its headers. It will return a Response indicating an
        error/success and a message with the error if applicable.

        Do not run directly, instead run self._run_validate_df() as it is a wrapper around this method.
        
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