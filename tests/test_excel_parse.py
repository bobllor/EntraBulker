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