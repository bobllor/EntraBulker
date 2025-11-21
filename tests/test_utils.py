from typing import Any
from backend.support.types import Response
import backend.support.utils as utils

def test_hyphen_name_format():
    base_names: list[str] = [
        "John-Doe Smith",
        "John Doe-Smith",
        "John-Doe Smith-Jane",
        "John Doe-Smith Jane",
        "John-Doe Smith Jane",
        "John-Doe Smith-Jane Name-One"
    ]

    valid_names: set[str] = {"John Smith", "John Jane", "John One"}

    for name in base_names:
        new_name: str = utils.format_hyphen_name(name)

        if new_name not in valid_names:
            raise AssertionError(f"Failed to parse {name} to get one of the valid names: {valid_names}")

def test_generate_text():
    text1: str = "The account [USERNAME] is managed by [NAME] with the password [PASSWORD]."
    text2: str = "[NAME] with the password [PASSWORD]."
    text3: str = "password [PASSWORD]."


    keys: dict[str, str] = {
        "user": "[USERNAME]",
        "password": "[PASSWORD]",
        "name": "[NAME]",
    }

    username: str = "test.account@gmail.com"
    name: str = "John Doe"
    password: str = "SomePasswordHere"

    exp_text1: str = text1.replace(keys["user"], username).replace(keys["name"], name).replace(keys["password"], password)
    exp_text2: str = text2.replace(keys["name"], name).replace(keys["password"], password)
    exp_text3: str = text3.replace(keys["password"], password)

    texts: list[str] = [text1, text2, text3]
    exp_texts: list[str] = [exp_text1, exp_text2, exp_text3]

    for i, text in enumerate(texts):
        res: dict[str, Any] = utils.generate_text(text=text, username=username, name=name, password=password)
        exp_text: str = exp_texts[i]
        new_text: str = res["content"]

        if exp_text != new_text:
            raise AssertionError(f"Failed to generate text replacement: got {new_text} expected {exp_text}")

def test_generate_text_args():
    text: str = "The account [USERNAME] is managed by with the password [PASSWORD]."

    username: str = "test.account@gmail.com"
    password: str = "SomePasswordHere"

    res: dict[str, Any] = utils.generate_text(text=text, username=username, password=password)

    exp_test: str = text.replace("[USERNAME]", username).replace("[PASSWORD]", password)

    assert res["content"] == exp_test

def test_generate_text_invalid():
    # max chars is 1250 by default
    chars: list[str] = ["a" for _ in range(1251)]
    text: str = "".join(chars)

    res: Response = utils.generate_text(text=text)

    assert res["status"] == "error"

def test_invalid_name():
    name: str = utils.format_name(" ")

    assert name == "Invalid Name"