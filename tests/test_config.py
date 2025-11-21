from pathlib import Path
from backend.core.json_reader import Reader
from typing import Any
from tests.fixtures import reader
from backend.support.vars import DEFAULT_HEADER_MAP, DEFAULT_OPCO_MAP, DEFAULT_SETTINGS_MAP

# NOTE: DEFAULT_HEADER_MAP is the default map for reader.

def test_init_config(reader: Reader):
    assert len(reader.read()) == len(DEFAULT_HEADER_MAP) and \
        len(reader.get_content()) == len(DEFAULT_HEADER_MAP) 

def test_insert(reader: Reader):
    reader.insert("a key", "a value")
    reader.insert("another key", "another value")
    
    assert len(reader.read()) == len(DEFAULT_HEADER_MAP) + 2 and \
        len(reader.get_content()) == len(DEFAULT_HEADER_MAP) + 2

def test_insert_dupe(reader: Reader):
    reader.insert("a key", "a value")
    res: dict[str, Any] = reader.insert("a key", "a value")

    assert res["status"] == "error" and len(reader.read()) == len(DEFAULT_HEADER_MAP) + 1

def test_insert_many(reader: Reader):
    new_data: dict[str, str] = {
        "fish": "city",
        "egg": "head",
    }

    reader.insert_many(new_data)

    assert len(reader.read()) == len(DEFAULT_HEADER_MAP) + len(new_data) and \
        len(reader.get_content()) == len(DEFAULT_HEADER_MAP) + len(new_data)

def test_insert_many_dupe(reader: Reader):
    new_data: dict[str, str] = {
        "chicken": "little",
        "soverign": "tester",
        "opco": "should skip", 
    }

    res: dict[str, Any] = reader.insert_many(new_data)

    assert len(reader.read()) == len(DEFAULT_HEADER_MAP) + len(new_data) - 1 and \
        len(reader.get_content()) == len(DEFAULT_HEADER_MAP) + len(new_data) - 1 \
        and "failed: 1" in res["message"]

def test_validate_config(reader: Reader):
    res: dict[str, Any] = reader.insert("tester", "kharazad")

    if res["status"] != "success":
        raise AssertionError(f"Failed to insert data: {res}") 

    key: str = "opco"
    res = reader.delete(key)

    if key in reader.get_content():
        raise AssertionError(f"Failed to remove key {key} from the JSON")
    
    reader.validate_defaults(DEFAULT_HEADER_MAP)

    assert key in reader.get_content() and key in reader.read()

def test_find_key(reader: Reader):
    key: str = "nest5"
    expected_val: str = "lopem isum"
    reader.insert("nest1", {"nest2": {"nest3": {"nest4": {"padding": None, key: expected_val}}}})

    val: Any = reader.get(key)

    assert val == expected_val

def test_find_invalid_key(reader: Reader):
    reader.insert("nest1", {"nest2": {"nest3": {"nest4": {"padding": None, "nest5": None}}}})

    val: Any = reader.get("whatever")

    assert val is None

def test_update_search(reader: Reader):
    key_to_edit: str = "padding"
    value: str = "yes"

    # target is nest5 padding, nest4 and nest6 have a padding key.
    reader.insert("nest1", 
        {"nest2": {key_to_edit: None, "nest3": {key_to_edit: None, "nest4": {key_to_edit: None}}}})

    res: dict[str, Any] = reader.update_search(key_to_edit, value, main_key="nest4")

    if res["status"] != "success":
        raise AssertionError(f"Failed to update key: {res}")

    nest2: dict[str, Any] = reader.get("nest2")
    nest3: dict[str, Any] = reader.get("nest3")
    nest4: dict[str, Any] = reader.get("nest4")

    assert nest2[key_to_edit] is None and nest3[key_to_edit] is None \
        and nest4[key_to_edit] == value

def test_get_search(reader: Reader):
    key_to_edit: str = "padding"
    value: str = "a long value here"
    parent_key: str = "nest4"

    reader.insert("nest1", 
        {"nest2": {key_to_edit: None, "nest3": {key_to_edit: None, parent_key: {key_to_edit: value}}}})

    new_value: str = reader.get_search(key_to_edit, parent_key=parent_key)

    assert value == new_value