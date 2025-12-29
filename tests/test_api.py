from pathlib import Path
from backend.api.api import API
from tests.fixtures import api, df, mock
from typing import Any
from backend.core.parser import Parser
from backend.support.vars import DEFAULT_HEADER_MAP, DEFAULT_SETTINGS_MAP, AZURE_HEADERS, VERSION
from backend.support.types import ManualCSVProps, APISettings, Formatting, Response
from io import BytesIO
from unittest.mock import patch, Mock
import numpy as np
import pandas as pd
import backend.support.utils as utils
import tests.utils as ttils
import random, string, requests

def test_generate_csv_normal(tmp_path: Path, api: API, df: pd.DataFrame):
    # creating a baseline dataframe for comparison in the end
    parser: Parser = Parser(df)

    parser.apply(
        DEFAULT_HEADER_MAP["opco"], func=ttils.randomizer, 
        args=("company one", "company two", "company three", "random")
    )
    
    opcos: list[str] = parser.get_rows(DEFAULT_HEADER_MAP["opco"])
    opco_map: dict[str, str] = api.opco.get_content()
    names: list[str] = parser.get_rows(DEFAULT_HEADER_MAP["name"])

    usernames: list[str] = utils.generate_usernames(names, opcos, opco_map)

    df = parser.get_df()

    res: dict[str, Any] = api.generate_azure_csv(df)

    if res["status"] == "error":
        raise AssertionError("Failed to generate CSV")

    file: Path = None
    for path in tmp_path.iterdir():
        if "csv" in path.name:
            file = path
    
    if file is None:
        raise AssertionError("Failed to generate CSV")

    csv_bytes: BytesIO = ttils.get_bytesio(file) 
    new_df: pd.DataFrame = pd.read_csv(csv_bytes)

    created_usernames: set[str] = {val for val in new_df[AZURE_HEADERS["username"]].to_dict().values()}

    for username in usernames:
        if username not in created_usernames:
            raise AssertionError(f"Username {username} not found, CSV generation failed")
    
def test_generate_csv_two_names(tmp_path: Path, api: API, df: pd.DataFrame):
    api.generate_azure_csv(df)
    base_csv: Path = ttils.get_csv(tmp_path)
    base_df: pd.DataFrame = pd.read_csv(ttils.get_bytesio(base_csv))

    df_copy: pd.DataFrame = df.copy(deep=True)
    names: list[str] = df_copy[DEFAULT_HEADER_MAP["name"]].to_list()

    first_names: list[str] = []
    last_names: list[str] = []

    for name in names:
        split_name: list[str] = name.split()

        first_names.append(split_name[0])
        last_names.append(" ".join(split_name[1:]))
    
    df_copy[DEFAULT_HEADER_MAP["first_name"]] = pd.Series(first_names)
    df_copy[DEFAULT_HEADER_MAP["last_name"]] = pd.Series(last_names)

    df_copy = df_copy.drop([DEFAULT_HEADER_MAP["name"]], axis=1)

    api.update_setting("two_name_column_support", True)

    res: Response = api.generate_azure_csv(df_copy)

    if res["status"] != "success":
        raise AssertionError(f"Failed to generate CSV for two names support: {res}")
    
    new_csv: Path = ttils.get_csv(tmp_path, ignore_files=[base_csv])

    new_df: pd.DataFrame = pd.read_csv(ttils.get_bytesio(new_csv))

    new_len: int = len(new_df)
    base_len: int = len(base_df)

    new_usernames: list[str] = new_df[AZURE_HEADERS["username"]].to_list()
    base_usernames: list[str] = base_df[AZURE_HEADERS["username"]].to_list()

    new_names: list[str] = new_df[AZURE_HEADERS["name"]].to_list()
    base_names: list[str] = base_df[AZURE_HEADERS["name"]].to_list()

    assert new_len == base_len and new_usernames == base_usernames \
        and new_names == base_names

def test_generate_csv_bad_two_names(tmp_path: Path, api: API, df: pd.DataFrame):
    base_len: int = len(df) // 2

    df_copy: pd.DataFrame = df.copy(deep=True)
    names: list[str] = df_copy[DEFAULT_HEADER_MAP["name"]].to_list()

    first_names: list[str | bool] = []
    last_names: list[str] = []

    for i, name in enumerate(names):
        split_name: list[str] = name.split()

        if i % 2 == 0:
            first_names.append(True)
        else:
            first_names.append(split_name[0])
        last_names.append(" ".join(split_name[1:]))
    
    df_copy[DEFAULT_HEADER_MAP["first_name"]] = pd.Series(first_names)
    df_copy[DEFAULT_HEADER_MAP["last_name"]] = pd.Series(last_names)
    
    api.update_setting("two_name_column_support", True)

    res: Response = api.generate_azure_csv(df_copy)

    if res["status"] == "error":
        raise AssertionError(f"Failed to generate CSV: {res}")
    
    csv_file: Path = ttils.get_csv(tmp_path)
    new_df: pd.DataFrame = pd.read_csv(ttils.get_bytesio(csv_file))

    assert len(new_df) == base_len

def test_generate_csv_multiple_template(tmp_path: Path, api: API, df: pd.DataFrame):
    res: Response = api.update_setting("enabled", True, "template")
    res: Response = api.update_setting("text", "[NAME] is cool", "template")

    assert res["status"] != "error"

    parser: Parser = Parser(df)
    parser.apply(DEFAULT_HEADER_MAP["name"], func=utils.format_name)

    dataframes: list[pd.DataFrame] = [parser.get_df(), parser.get_df()]

    for frame in dataframes:
        res = api.generate_azure_csv(frame)

        assert res["status"] != "error"

    base_len: int = len(dataframes)
    base_row_len: int = len(parser.get_df()) * 2
        
    csv_count: int = 0
    for file in (tmp_path).iterdir():
        if ".csv" in file.suffix:
            csv_count += 1
    
    template_folder_count: int = 0
    template_count: int = 0
    for file in (tmp_path / "templates").iterdir():
        if file.is_dir():
            template_folder_count += 1

            for _ in file.iterdir():
                template_count += 1
    
    assert base_len == csv_count and base_len == template_folder_count and \
        template_count == base_row_len

def test_generate_csv_empty_file(api: API, df: pd.DataFrame):
    empty_df: pd.DataFrame = df.copy(deep=True).iloc[0:0]

    res: Response = api.generate_azure_csv(empty_df)

    assert res["status"] == "error" and "empty" in res["message"]

def test_generate_csv_empty_validate_file(api: API, df: pd.DataFrame):
    parser: Parser = Parser(df)

    parser.apply(DEFAULT_HEADER_MAP["name"], func=lambda _: np.nan)

    res: Response = api.generate_azure_csv(parser.get_df())

    assert res["status"] == "error" and "is empty after validation" in res["message"]

def test_generate_csv_dupe_names(tmp_path: Path, api: API, df: pd.DataFrame):
    dupe_name: str = "John Doe"
    
    df[DEFAULT_HEADER_MAP["name"]] = df[DEFAULT_HEADER_MAP["name"]].apply(
        func=lambda x: x if random.randint(0, 1) == 0 else dupe_name
    )

    names: list[str] = df[DEFAULT_HEADER_MAP["name"]].to_list()

    api.generate_azure_csv(df)

    file: Path = ttils.get_csv(tmp_path)
    
    if file is None:
        raise AssertionError("Failed to generate CSV")

    csv_bytes: BytesIO = ttils.get_bytesio(file) 
    new_df: pd.DataFrame = pd.read_csv(csv_bytes)

    dupe_count: int = 0
    for username in new_df[AZURE_HEADERS["username"]].to_list():
        username: str = username.replace(".", " ")
        base_name: str = dupe_name

        if base_name in username:
            if dupe_count != 0:
                base_name += str(dupe_count)

            if base_name not in username:
                raise AssertionError(f"Expected {base_name} in {username}")

            dupe_count += 1

    # checks if the full name is not affecte dby the changes. 
    for i, name in enumerate(new_df[AZURE_HEADERS["name"]].to_list()):
        if names[i] != name:
            raise AssertionError(f"Name {name} does not match base name {names[i]}") 

def test_generate_manual_csv(tmp_path: Path, api: API, df: pd.DataFrame):
    parser: Parser = Parser(df)

    names: list[str] = parser.get_rows("full name")
    opcos: list[str] = [
        ttils.randomizer("", "company one", "company two", "company three", "random")
        for _ in range(len(names))
    ]

    usernames: list[str] = utils.generate_usernames(names, opcos, api.opco.get_content())

    manual_content: list[ManualCSVProps] = []

    for i, name in enumerate(names):
        opco: str = opcos[i]

        content_dict: ManualCSVProps = {}
        content_dict["name"] = name
        content_dict["opco"] = opco

        manual_content.append(content_dict)

    api.generate_manual_csv(manual_content) 

    file: Path = None
    for path in tmp_path.iterdir():
        if "csv" in path.name:
            file = path
    
    if file is None:
        raise AssertionError("Failed to generate CSV")

    csv_bytes: BytesIO = ttils.get_bytesio(file) 
    new_df: pd.DataFrame = pd.read_csv(csv_bytes)

    created_usernames: set[str] = {val for val in new_df[AZURE_HEADERS["username"]].to_dict().values()}

    for username in usernames:
        if username not in created_usernames:
            raise AssertionError(f"Username {username} not found in {created_usernames}, CSV generation failed")

def test_manual_generate_csv_dupe_names(tmp_path: Path, api: API, df: pd.DataFrame):
    dupe_name: str = "John Doe"
    names: list[str] = df[DEFAULT_HEADER_MAP["name"]].to_list()
    opcos: list[str] = df[DEFAULT_HEADER_MAP["opco"]].to_list()

    for i in range(len(names)):
        random_val: int = random.randint(0, 1)
        names[i] = names[i] if random_val == 0 else dupe_name

    manual_content: list[ManualCSVProps] = []

    for i, name in enumerate(names):
        opco: str = opcos[i]

        content: ManualCSVProps = {}
        content["name"] = name
        content["opco"] = opco

        manual_content.append(content)
    
    api.generate_manual_csv(manual_content)

    file: Path = None
    for path in tmp_path.iterdir():
        if "csv" in path.name:
            file = path
    
    if file is None:
        raise AssertionError("Failed to generate manual CSV")

    csv_bytes: BytesIO = ttils.get_bytesio(file) 
    new_df: pd.DataFrame = pd.read_csv(csv_bytes)

    dupe_count: int = 0
    for username in new_df[AZURE_HEADERS["username"]].to_list():
        username: str = username.replace(".", " ")
        base_name: str = dupe_name

        if base_name in username:
            if dupe_count != 0:
                base_name += str(dupe_count)

            if base_name not in username:
                raise AssertionError(f"Expected {base_name} in {username}")

            dupe_count += 1

    for i, name in enumerate(new_df[AZURE_HEADERS["name"]].to_list()):
        if names[i] != name:
            raise AssertionError(f"Name {name} does not match base name {names[i]}") 
    
def test_generate_csv_invalid_text(api: API, df: pd.DataFrame):
    # max chars is 1250 by default
    string_chars: str = string.ascii_letters
    chars: list[str] = [string_chars[random.randint(0, len(string_chars) - 1)] for _ in range(1251)]
    text: str = "".join(chars)

    api.update_setting("text", text, "template")
    api.update_setting("enabled", True, "template")

    res: Response = api.generate_azure_csv(df) 

    assert res["status"] == "error"

def test_generate_csv_multiple(tmp_path: Path, api: API, df: pd.DataFrame):
    parser: Parser = Parser(df)
    parser.apply(col_name=DEFAULT_HEADER_MAP["name"], func=utils.format_name)

    dataframes: list[pd.DataFrame] = [parser.get_df(), parser.get_df(), parser.get_df()]
    ids: list[str] = [str(i) for i in range(len(dataframes))]

    for i, dataframe in enumerate(dataframes):
        res: Response = api.generate_azure_csv(dataframe, ids[i])

        if res["status"] != "success":
            raise AssertionError(f"Failed to generate CSV file: {res}")

    file_count: int = 0 
    for file in tmp_path.iterdir():
        if "csv" in file.suffix:
            file_count += 1
    
    assert file_count == len(dataframes)

def test_generate_csv_formatter(tmp_path: Path, api: API, df: pd.DataFrame):
    # case / style / type
    format_keys: list[str] = sorted([key for key in DEFAULT_SETTINGS_MAP["format"].keys()])
    format_values: list[str] = ["lower", "f last", "no space"]

    for i, key in enumerate(format_keys):
        val: str = format_values[i]

        res: dict[str, Any] = api.update_setting(key, val, "format")

        if res["status"] != "success":
            raise AssertionError(f"Failed to update settings key: {res}")
    
    formatter: Formatting = api.get_reader_value("settings", "format")

    barser: Parser = Parser(df)

    barser.apply(DEFAULT_HEADER_MAP["name"], func=utils.format_name)

    names: list[str] = barser.get_rows(DEFAULT_HEADER_MAP["name"])
    opcos: list[str] = barser.get_rows(DEFAULT_HEADER_MAP["opco"])

    opco_map: dict[str, str] = api.get_reader_content("opco")

    usernames: set[str] = set()

    for i, name in enumerate(names):
        opco: str = opcos[i]

        username: str = utils.generate_username(
            name, opco, opco_map,
            format_case=formatter["format_case"],
            format_type=formatter["format_type"],
            format_style=formatter["format_style"],
        )

        usernames.add(username)
    
    res: Response = api.generate_azure_csv(df)

    file: Path = ttils.get_csv(tmp_path)

    if file is None:
        raise AssertionError(f"CSV file failed to generate")
    
    new_data: pd.DataFrame = pd.read_csv(ttils.get_bytesio(file))

    parser: Parser = Parser(new_data)
    new_usernames: list[str] = parser.get_rows(AZURE_HEADERS["username"])

    for username in new_usernames:
        if username not in usernames:
            raise AssertionError(f"Got formatted {username}, not found in {usernames}")

def test_generate_csv_flatten(tmp_path: Path, api: API, df: pd.DataFrame):
    parser: Parser = Parser(df)
    parser.apply(DEFAULT_HEADER_MAP["name"], func=utils.format_name)
    
    parser_dfs: list[pd.DataFrame] = [parser.get_df(), parser.get_df()]
    upload_id: str = "asd123flelo"

    for parser_df in parser_dfs:
        res: Response = api.generate_azure_csv(parser_df, upload_id)

        if res["status"] != "success":
            raise AssertionError(f"Failed to generate CSV: {res}")
    
    csv_file: Path = ttils.get_csv(tmp_path)
    csv_len: int = 0

    with open(csv_file, "r") as f:
        content: list[str] = f.readlines()

        # drops the version row and the column headers
        # NOTE: len(df) does not include the headers!
        csv_len = len(content) - 2

    csv_df: pd.DataFrame = pd.read_csv(ttils.get_bytesio(csv_file))

    assert len(csv_df) == csv_len

def test_generate_csv_templates(tmp_path: Path, api: API, df: pd.DataFrame):
    res: Response = api.update_setting("enabled", True, "template")

    if res["message"] == "error":
        raise AssertionError(f"Failed to update setting: {res}")
    
    parser: Parser = Parser(df)
    parser.apply(DEFAULT_HEADER_MAP["name"], func=utils.format_name)

    base_len: int = len(df)

    res = api.generate_azure_csv(parser.get_df(), "123")

    if res["message"] == "error":
        raise AssertionError(f"Failed to generate CSV and templates: {res}")
    
    template_len: int = 0
    for file in (tmp_path / "templates").iterdir():
        if file.is_dir():
            for _ in file.iterdir():
                template_len += 1
    
    assert base_len == template_len

def test_generate_csv_flatten_templates(tmp_path: Path, api: API, df: pd.DataFrame):
    res: Response = api.update_setting("enabled", True, "template")
    res = api.update_setting("flatten_csv", True)

    if res["message"] == "error":
        raise AssertionError(f"Failed to update setting: {res}")
    
    parser: Parser = Parser(df)
    parser.apply(DEFAULT_HEADER_MAP["name"], func=utils.format_name)

    base_len: int = len(df) * 2
    base_id: str = "123"

    for frame in [parser.get_df(), parser.get_df()]:
        res = api.generate_azure_csv(frame, base_id)
        if res["message"] == "error":
            raise AssertionError(f"Failed to generate CSV and templates: {res}")
    
    template_len: int = 0
    for file in (tmp_path / "templates").iterdir():
        if file.is_dir():
            for _ in file.iterdir():
                template_len += 1
    
    assert base_len == template_len

def test_get_value(api: API):
    excel_val: Any = api.get_reader_value("excel", "name")
    settings_val: Any = api.get_reader_value("settings", "output_dir")
    opco_val: Any = api.get_reader_value("opco", "company one")

    for val in [excel_val, settings_val, opco_val]:
        if val == "":
            raise AssertionError("Got empty key")
    
    fail_val: Any = api.get_reader_value("settings", "non")

    if fail_val != "": raise AssertionError(f"Got value when expecting an empty string")

def test_update_key(api: API):
    prev_val: str = api.get_reader_value("excel", "name")
    
    var: str = "CHANGED VALUE"
    res: dict[str, Any] = api.update_key("excel", "name", var)

    if res["status"] == "error":
        raise AssertionError(f"Failed to update key: {res}")
    
    new_val: str = api.get_reader_value("excel", "name")

    assert prev_val != new_val and new_val == var

def test_update_default_key(api: API):
    prev_val: str = api.get_reader_value("opco", "default")

    var: str = "NEW DEFAULT"
    res: dict[str, Any] = api.update_key("opco", "default", var)

    new_val: str = api.get_reader_value("opco", "default")

    assert res["status"] != "error" and prev_val != new_val and new_val == var

def test_insert_update_rm_many(api: API):
    data: dict[str, str] = {
        "default": "5555",
        "company one": "t444",
        "company two": "123",
        "inserted key": "11",
    }

    api.insert_update_rm_many("opco", data)

    new_data: dict[str, str] = api.get_reader_content("opco")

    # company three should be removed as it does not exist in data.
    # inserted key is inserted. 
    assert "company three" not in new_data and "inserted key" in new_data

def test_update_search(api: API):
    target: str = "format"
    keys: tuple[str] = ("format_style", "format_case", "format_type")

    new_style: str = "f last"
    new_case: str = "lower"
    new_type: str = "no space"
    values: tuple[str] = (new_style, new_case, new_type)

    for i in range(len(keys)):
        key: str = keys[i]
        value: str = values[i]

        res: dict[str, Any] = api.update_setting(key, value, target)

        if res["status"] != "success":
            raise AssertionError(f"Failed to update setting: {res}")
    
    settings: APISettings = api.get_reader_content("settings")
    formatter: Formatting = settings["format"]
    
    new_values: dict[str, str] = {val: key for key, val in formatter.items()}

    for val in values:
        if val not in new_values:
            raise AssertionError(f"Failed to update key: {val}")

def test_get_content(api: API):
    data: dict[str, Any] = api.get_reader_content("opco")

    assert data == api.opco.get_content()

def test_generate_password(api: API):
    api.update_setting("use_punctuations", True, "password")

    res_one: Response = api.generate_password()

    upper_count: int = 0
    for c in res_one["content"]:
        if c in string.ascii_uppercase:
            upper_count += 1

    if res_one["status"] == "error":
        raise AssertionError(f"Failed to generate password with punctuations: {res_one}")

    api.update_setting("use_punctuations", False, "password")
    api.update_setting("use_uppercase", True, "password")

    res_two: Response = api.generate_password()

    punctuation_count: int = 0
    for c in res_two["content"]:
        if c in string.punctuation:
            punctuation_count += 1

    default_pass_len: int = DEFAULT_SETTINGS_MAP["password"]["length"]

    assert len(res_one["content"]) == default_pass_len and len(res_two["content"]) == default_pass_len \
        and punctuation_count == 1 and upper_count == 1

def test_generate_bad_password(api: API):
    api.update_setting("password", None)

    res: Response = api.generate_password()

    assert res["status"] == "success" and "default values" in res["message"].lower() \
        and len(res["content"]) == DEFAULT_SETTINGS_MAP["password"]["length"]

@patch("backend.api.api.utils.get_version")
def test_check_version(mock: Mock, api: API):
    mock.return_value = {
        "status": "success",
        "message": "Successfully checked version",
        "content": "v1.1.5",
        "exception": None,
    }

    url: str = "https://afakeurl-goeshere.com/api/text.txt"

    res: Response = api.check_version(url)

    assert res["content"] == True

    mock.return_value = {
        "status": "success",
        "message": "Successfully checked version",
        "content": VERSION,
        "exception": None,
    }

    res = api.check_version(url)

    assert res["content"] == False

@patch("backend.api.api.utils.get_version")
def test_error_status_check_version(mock: Mock, api: API):
    mock.return_value = {
        "status": "error",
        "message": "Failed to receive response from request (400)",
        "content": VERSION,
        "exception": None,
    }

    url: str = "https://afakeurl-goeshere.com/api/text.txt"
    res: Response = api.check_version(url)

    assert res["status"] == "error"

@patch("backend.api.api.utils.get_version")
def test_exception_check_version(mock: Mock, api: API):
    mock.return_value = {
        "status": "error",
        "message": "Failed to check version",
        "content": VERSION,
        "exception": requests.ConnectionError("Connection failed")
    }

    url: str = "https://afakeurl-goeshere.com/api/text.txt"
    res: Response = api.check_version(url)

    assert res["status"] == "error"