from typing import Any
from backend.support.types import Response
from pathlib import Path
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

def test_generate_password():
    password: str = utils.generate_password()

    assert isinstance(password, str)

def test_generate_custom_password():
    pass_length: int = 15
    password: str = utils.generate_password(pass_length, use_punctuations=True, use_uppercase_letters=True)

    assert isinstance(password, str) and len(password) == pass_length

def test_unlink_path(tmp_path: Path):
    files: list[str] = ["file1.txt", "file2.txt", "file3.txt"]
    folders: list[str] = ["folder1", "folder2"]

    def create_files(path: Path, files: list[str]):
        for file in files:
            file_path: Path = path / file

            file_path.touch(exist_ok=True)

    tmp_folder: Path = tmp_path / "unlinker"

    tmp_folder.mkdir(exist_ok=True, parents=True)
    create_files(tmp_folder, files)

    for folder in folders:
        folder_path: Path = tmp_folder / folder

        folder_path.mkdir(parents=True, exist_ok=True)

        create_files(folder_path, files)
    
    def count_files(path: Path, num: int) -> int:
        if not path.is_dir():
            return 1

        # accounts for directory 
        num += 1
        for child in path.iterdir():
            val: int = count_files(child, 0)

            num += val
        
        return num

    total_files: int = count_files(tmp_folder, 0)

    utils.unlink_path(tmp_folder)

    post_file_count: int = count_files(tmp_path, 0)

    assert total_files != 0 and post_file_count == 1

def test_run_cmd(tmp_path: Path):
    file_name: str = "test.txt"

    cmd: list[str] = [
        "touch",
        str(tmp_path) + "/" + file_name
    ]

    utils.run_cmd(cmd)
    found: bool = False

    for child in tmp_path.iterdir():
        if file_name in child.name:
            found = True
            break
    
    assert found

def test_blacklist_run_cmd():
    cmd: list[str] = [
        "rm",
        "a-non-existent-file-here.txt",
    ]

    _, err = utils.run_cmd(cmd)

    assert err != "" and "rm" in err

def test_err_run_cmd():
    file: str = "fdsa"
    cmd: list[str] = [
        "ls",
        file
    ]

    _, err = utils.run_cmd(cmd)

    assert err != "" and f"cannot access '{file}'" in err