from pathlib import Path
from typing import Any
from backend.support.vars import DEFAULT_HEADER_MAP, DEFAULT_OPCO_MAP, AZURE_HEADERS, AZURE_VERSION
from backend.support.types import Response
from backend.core.azure_writer import AzureWriter, HeadersKey
from backend.core.parser import Parser
from tests.fixtures import df
from faker import Faker
from io import BytesIO
import pandas as pd
import backend.support.utils as utils
import tests.utils as ttils
import numpy as np
import random

# this is faked and cleaned data, no sensitive leaks.
test_json: Path = Path(__file__).parent / "data.json"

# columns
FULL_NAME: str = "full name"
OPERATING_COMPANY: str = "operating company"
COUNTRY: str = "country/territory"
NUMBER: str = "number"
DESCRIPTION: str = "short description"

def test_read_excel():
    df: pd.DataFrame = pd.read_json(test_json)

    parser: Parser = Parser(df)

    assert len(parser.get_columns()) > 0

def test_get_excel_data():
    df: pd.DataFrame = pd.read_json(test_json)
    parser: Parser = Parser(df)

    assert len(parser.get_rows("full name")) > 0

def test_apply_name():
    df: pd.DataFrame = pd.read_json(test_json)
    parser: Parser = Parser(df)

    # adding fake names to the name columns
    parser.apply(
        col_name=FULL_NAME, 
        func=lambda x: x + " " + " ".join([Faker().last_name() for _ in range(0, random.randint(1, 3))])
    )

    parser.apply(col_name=FULL_NAME, func=utils.format_name)

    for name in parser.get_rows(FULL_NAME):
        name: str = name
        arr: list[str] = name.split()

        if len(arr) != 2:
            raise AssertionError("Name parsing failed got %s", name)
    
    assert True

def test_fill_nan():
    df: pd.DataFrame = pd.read_json(test_json)
    parser: Parser = Parser(df)

    # filling all columns with nan first.
    parser.apply(OPERATING_COMPANY, func=lambda _: np.nan)
    parser.fillna(OPERATING_COMPANY, DEFAULT_HEADER_MAP["opco"])

    for opco in parser.get_rows(DEFAULT_HEADER_MAP["opco"]):
        if opco == np.nan:
            raise AssertionError(f"Failed to fill empty rows for {DEFAULT_HEADER_MAP['opco']}")

def test_validate_df():
    df: pd.DataFrame = pd.read_json(test_json)
    parser: Parser = Parser(df)

    res: dict[str, Any] = parser.validate(DEFAULT_HEADER_MAP)

    if res["status"] != "success":
        raise AssertionError(
            f"Failed to validate headers, got {parser.get_columns()}, \
            expected values {[val for val in DEFAULT_HEADER_MAP.values()]}", 
        )

def test_validate_fail_df_duplicate_columns(df: pd.DataFrame):
    df.insert(len(df.columns), DEFAULT_HEADER_MAP["name"], [f"Name {i}" for i in range(len(df))], allow_duplicates=True)
    df.insert(len(df.columns), DEFAULT_HEADER_MAP["opco"], [f"{i}" for i in range(len(df))], allow_duplicates=True)
    parser: Parser = Parser(df)

    res: Response = parser.validate(DEFAULT_HEADER_MAP)

    res_msg: str = res["message"]

    assert res["status"] == "error" and DEFAULT_HEADER_MAP["name"].lower() in res_msg \
        and DEFAULT_HEADER_MAP["opco"].lower() in res_msg

def test_validate_fail_df_missing_headers(df: pd.DataFrame):
    parser: Parser = Parser(df)
    modified_defaults = DEFAULT_HEADER_MAP.copy()

    modified_defaults["name"] = "name"
    modified_defaults["opco"] = "organization"

    res: Response = parser.validate(modified_defaults)

    assert res["status"] == "error" and modified_defaults["name"] in res["message"] \
        and modified_defaults["opco"] in res["message"]
    
def test_validate_fail_df_duplicate_headers(df: pd.DataFrame):    
    parser: Parser = Parser(df)
    modified_defaults = DEFAULT_HEADER_MAP.copy()

    modified_defaults["name"] = "organization"
    modified_defaults["opco"] = "organization"

    res: Response = parser.validate(modified_defaults)

    assert res["status"] == "error" and "duplicate values" in res["message"].lower() \
        and modified_defaults["name"] in res["message"].lower()

def test_write_new_csv(tmp_path: Path):
    df: pd.DataFrame = pd.read_json(test_json)
    parser: Parser = Parser(df)

    res: dict[str, Any] = parser.validate(DEFAULT_HEADER_MAP)

    if res["status"] != "success":
        raise AssertionError(
            f"Failed to validate headers, got {parser.get_columns()}, \
            expected values {[val for val in DEFAULT_HEADER_MAP.values()]}", 
        )

    parser.apply(DEFAULT_HEADER_MAP["name"], func=utils.format_name)
    parser.drop_empty_rows(DEFAULT_HEADER_MAP["name"])
    parser.fillna(DEFAULT_HEADER_MAP["opco"], "Operating Company")

    parser.apply(
        DEFAULT_HEADER_MAP["opco"], func=ttils.randomizer, 
        args=("company one", "company two", "company three", "random")
    )

    opco_map: dict[str, str] = {
        "default": DEFAULT_OPCO_MAP["default"],
        "company one": "company.one.org",
        "company two": "companytwo.com",
        "company three": "company.three.nhs.gov"
    }

    names: list[str] = parser.get_rows(DEFAULT_HEADER_MAP["name"])
    opcos: list[str] = parser.get_rows(DEFAULT_HEADER_MAP["opco"])
    passwords: list[str] = [utils.generate_password() for _ in range(len(names))]

    usernames: list[str] = utils.generate_usernames(
        names, opcos, opco_map
    )

    writer: AzureWriter = AzureWriter(project_root=tmp_path)

    writer.set_full_names(names)
    writer.set_usernames(usernames)
    writer.set_passwords(passwords)
    writer.set_block_sign_in(len(names))
    writer.set_names(names)

    writer.write(tmp_path / "out.csv")

    output: Path = tmp_path / "out.csv"
    csv_bytes: BytesIO = ttils.get_bytesio(output)
    
    df: pd.DataFrame = pd.read_csv(csv_bytes)

    for key in writer.get_keys():
        df_data: list[Any] = df[key].to_list()
        base_data: list[str] = writer.get_data(key)

        if not df_data == base_data:
            raise AssertionError(f"Failed to match baseline: {base_data}, got: {df_data}")

def test_drop_validate_data(df: pd.DataFrame):
    parser: Parser = Parser(df)

    number: int = 100

    parser.apply(DEFAULT_HEADER_MAP["name"], func=lambda _: np.nan)
    parser.apply(DEFAULT_HEADER_MAP["opco"], func=lambda _: number)

    parser.apply(DEFAULT_HEADER_MAP["opco"], func=lambda x: str(x))

    for opco in parser.get_rows(DEFAULT_HEADER_MAP["opco"]):
        if not isinstance(opco, str) and opco != str(number):
            raise AssertionError(f"Failed to convert column to string: {parser.get_rows(DEFAULT_HEADER_MAP['opco'])}")

    dropped_name_rows: int = parser.drop_empty_rows(DEFAULT_HEADER_MAP["name"])
    dropped_opco_rows: int = parser.drop_empty_rows(DEFAULT_HEADER_MAP["opco"])

    dropped_rows: int = dropped_name_rows + dropped_opco_rows

    assert dropped_rows != 0