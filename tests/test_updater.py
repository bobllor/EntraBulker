from tests.fixtures import updater, get, TEST_PROGRAM_FILES
from backend.core.updater import Updater
from backend.support.types import Response
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Any
from zipfile import ZipFile, ZipInfo
from io import BytesIO
from backend.support.vars import FILE_NAMES
import tests.utils as ttils
import backend.support.utils as utils
import datetime, time

URL: str = "https://fakeurl.com/api/stuff"

@patch('backend.core.updater.requests.get')
def test_download_zip(get: MagicMock, tmp_path: Path, updater: Updater):
    set_mock_response(get)

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
def test_unzip(get: MagicMock, updater: Updater):
    set_mock_response(get)

    updater.download_zip(URL)
        
    updater.unzip(updater.zip_file)

    unzipped_files: list[str] = utils.get_paths(updater.temp_dir)

    assert len(unzipped_files) != 0

@patch('backend.core.updater.requests.get')
def test_normal_update(get: MagicMock, tmp_path: Path, updater: Updater):
    mk_app(tmp_path)
    set_mock_response(get)

    updater.download_zip(URL)
    updater.unzip(updater.zip_file)

    base_files: list[str] = utils.get_paths(updater.project_root)

    for file in base_files:
        path: Path = Path(file)
        file_name: str = path.name.lower()

        assert FILE_NAMES["app_exe"].lower() != file_name

    updater.update(updater.project_folder / FILE_NAMES["apps_folder"], ignore_files=[FILE_NAMES["updater_exe"], "udist"])

    new_files: list[str] = utils.get_paths(updater.project_root)

    # since mk_app does not generate the entrabulker.exe in the apps folder,
    # this will be used to check if the update was successful.
    found: bool = False
    for file in new_files:
        path: Path = Path(file)
        file_name: str = path.name.lower()

        if file_name == FILE_NAMES["app_exe"].lower():
            found = True
            break
    
    assert found

@patch('backend.core.updater.requests.get')
def test_cleanup(get: MagicMock, updater: Updater):
    set_mock_response(get)

    updater.download_zip(URL)
    updater.unzip(updater.zip_file)

    updater.cleanup()

    assert not updater.project_folder.exists()

def mk_app(path: Path, sleep: int | float = 0) -> None:
    '''Creates the folder structure of the application in the given path.
    
    This does not create the `entrabulker.exe` file.

    Parameters
    ----------
        path: Path
            The Path the application files will be made in.

        sleep: int | float, default `0`
            The sleep time after creating the folders. This is used
            to delay the time creation before the updater is called
            for making new files. By default it is 0 seconds.
    ''' 
    # unzip -l tests/zip-test.zip to get the folder structure
    append_path = lambda x: path / TEST_PROGRAM_FILES /project_folder / x

    # the main project folder and the app for the main files
    project_folder: Path = Path(FILE_NAMES["project_folder"])
    app_folder: Path = append_path(FILE_NAMES["apps_folder"])
    append_app_folder = lambda x: app_folder / x

    # folders inside app (location of the main application files)
    config_folder: Path = append_app_folder(Path("config"))
    logs_folder: Path = append_app_folder(Path("logs"))
    updater_file: Path = append_path(Path(FILE_NAMES["updater_exe"]))

    # folders outside app
    udist_folder: Path = append_path(Path(FILE_NAMES["updater_dist"]))

    files_to_make: list[Path] = [updater_file, config_folder / "settings.json", logs_folder / "logs.log", udist_folder]

    for file in files_to_make:
        if file.suffix != "":
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch()
        else:
            file.mkdir(parents=True, exist_ok=True)
    
    time.sleep(sleep)
        
def set_mock_response(get: get) -> MagicMock:
    '''Sets up the and returns the mock object for requests'''
    mock: Any = get.return_value
    mock.status_code = 200
    mock.json.return_value = [{"assets": [
        {"browser_download_url": "https://fakeurl.com/api/stuff/zip-test.zip"}
    ]}]
    
    zip_bytes: bytes = get_zip()

    mock.iter_content.return_value = [zip_bytes]
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None

    return mock

def get_zip() -> bytes:
    '''Gets the ZIP file in list of bytes.'''
    test_zip: Path = Path(__file__).parent / "zip-test.zip"
    data: bytes = None

    with open(test_zip, "rb") as f:
        data = f.read()
    
    return data