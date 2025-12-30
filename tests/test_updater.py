from tests.fixtures import updater, mock, TEST_PROGRAM_FILES
from backend.core.updater import Updater
from backend.support.types import Response
from pathlib import Path
from unittest.mock import patch, Mock
from typing import Any
from zipfile import ZipFile, ZipInfo
from io import BytesIO
from backend.support.vars import FILE_NAMES
import tests.utils as ttils
import backend.support.utils as utils
import requests

URL: str = "https://fakeurl.com/api/stuff"

@patch('backend.core.updater.requests.get')
def test_download_zip(mock: Mock, updater: Updater):
    set_mock_response(mock)

    zip_bytes: bytes = get_zip()

    res: Response = updater.download_zip(URL)

    assert res["status"] == "success"

    base_file_names: set[str] = set()

    for info in ZipFile(BytesIO(zip_bytes), "r").filelist:
        base_file_names.add(info.filename)

    downloaded_file_names: list[str] = []
    for child in updater.temp_dir.iterdir():
        if ".zip" == child.suffix.lower():
            file: ZipFile = ZipFile(child, "r")

            for info in file.filelist:
                downloaded_file_names.append(info.filename)
                assert info.filename in base_file_names

    assert len(downloaded_file_names) == len(base_file_names)

@patch('backend.core.updater.requests.get')
def test_unzip(mock: Mock, updater: Updater):
    set_mock_response(mock)

    updater.download_zip(URL)
        
    updater.unzip(updater.zip_file)

    unzipped_files: list[str] = utils.get_paths(updater.temp_dir)

    assert len(unzipped_files) != 0

# "normal" is needed as running pytest with -k on this command runs all tests for some reason
@patch('backend.core.updater.requests.get')
def test_normal_update(mock: Mock, tmp_path: Path, updater: Updater):
    mk_app(tmp_path)
    set_mock_response(mock)

    updater.download_zip(URL)
    updater.unzip(updater.zip_file)

    # in prod, updater.project_root.parent will not use the parent due to
    # pyinstaller PATH differences. instead it will just use PROJECT_ROOT
    base_files: list[str] = utils.get_paths(updater.project_root.parent)
    # does not include temp files
    base_len: int = 0

    for file in base_files:
        path: Path = Path(file)
        file_name: str = path.name.lower()

        if "temp" in str(path):
            continue

        if not str(updater.temp_dir) in str(path):
            assert FILE_NAMES["app_exe"] != file_name
        
        base_len += 1

    updater.update(
        updater.temp_project_folder / FILE_NAMES["apps_folder"],
        updater.project_root.parent / FILE_NAMES["apps_folder"],
        ignore_files=[FILE_NAMES["updater_exe"], "udist"]
    )
    updater.cleanup()

    new_files: list[str] = utils.get_paths(updater.project_root.parent)
    new_len: int = 0

    # since mk_app does not generate the entrabulker.exe in the apps folder,
    # this will be used to check if the update was successful.
    found: bool = False
    for file in new_files:
        path: Path = Path(file)
        file_name: str = path.name.lower()

        print(path)
        if file_name == FILE_NAMES["app_exe"].lower():
            found = True
        
        new_len += 1

    assert found and new_len == base_len + 1

@patch('backend.core.updater.requests.get')
def test_cleanup(mock: Mock, updater: Updater):
    set_mock_response(mock)

    updater.download_zip(URL)
    updater.unzip(updater.zip_file)

    updater.cleanup()

    assert not updater.temp_project_folder.exists()

@patch('backend.core.updater.requests.get', side_effect=requests.HTTPError("HTTP error"))
def test_error_download_zip(mock: Mock, updater: Updater):
    set_mock_response(mock)

    res: Response = updater.download_zip(URL)

    assert res["status"] == "error"

@patch('backend.core.updater.requests.get')
def test_status_code_download_zip(mock: Mock, updater: Updater):
    mock = set_mock_response(mock)

    mock.status_code = 400
    res: Response = updater.download_zip(URL)

    assert res["status"] == "error"

def test_fail_update(tmp_path: Path, updater: Updater):
    mk_app(tmp_path)

    res: Response = updater.update(updater.temp_project_folder, updater.project_root.parent / FILE_NAMES["apps_folder"])

    assert res["status"] == "error" and "unable to find" in res["message"].lower()

def test_fail_unzip(tmp_path: Path, updater: Updater):
    res: Response = updater.unzip(tmp_path / "nonexistent.zip")

    assert res["status"] == "error"

def mk_app(path: Path) -> None:
    '''Creates the folder structure of the application in the given path.
    
    This does not create the `entrabulker.exe` file.

    Parameters
    ----------
        path: Path
            The Path the application files will be made in.
    ''' 
    # the main project folder and the app for the main files
    project_folder: Path = Path(FILE_NAMES["project_folder"])
    # unzip -l tests/zip-test.zip to get the folder structure
    append_path = lambda x: path / TEST_PROGRAM_FILES / project_folder / x

    app_folder: Path = append_path(FILE_NAMES["apps_folder"])
    append_app_folder = lambda x: app_folder / x

    # files inside app (location of the main application files)
    config_folder: Path = append_app_folder(Path("config"))
    # NOTE: i did not realize but the test zip file structure is incorrect with the dist
    # its not going to be changed though since it only effects the test cases,
    # not the actual production code
    madist_folder: Path = append_app_folder(Path(FILE_NAMES["app_dist"]))

    # files outside app
    udist_folder: Path = append_path(Path(FILE_NAMES["updater_dist"]))
    logs_folder: Path = append_path(Path("logs"))
    updater_file: Path = append_path(Path(FILE_NAMES["updater_exe"]))

    files_to_make: list[Path] = [
        updater_file, 
        config_folder / "settings.json", 
        logs_folder / "logs.log", 
        udist_folder,
        madist_folder,
        madist_folder / "index.html",
        madist_folder / "styles.css",
    ]

    for file in files_to_make:
        if file.suffix != "":
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch()
        else:
            file.mkdir(parents=True, exist_ok=True)
        
def set_mock_response(mock: Any) -> Any:
    '''Sets up the and returns the mock object for requests'''
    mocko: Any = mock.return_value
    mocko.status_code = 200
    mocko.json.return_value = [
        {"assets": [
                {"name": "file.exe", "browser_download_url": "https://fakeurl.com/api/stuff/file.exe"},
                {"name": "zip-test.zip", "browser_download_url": "https://fakeurl.com/api/stuff/zip-test.zip"},
            ]
        }
    ]
    
    zip_bytes: bytes = get_zip()

    mocko.iter_content.return_value = [zip_bytes]
    mocko.__enter__.return_value = mocko
    mocko.__exit__.return_value = None

    return mocko

def get_zip() -> bytes:
    '''Gets the ZIP file in list of bytes.'''
    test_zip: Path = Path(__file__).parent / "zip-test.zip"
    data: bytes = None

    with open(test_zip, "rb") as f:
        data = f.read()
    
    return data