from tests.fixtures import updater, get
from backend.core.updater import Updater
from backend.support.types import Response
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Any
from zipfile import ZipFile, ZipInfo
from io import BytesIO
import tests.utils as ttils

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

    unzipped_files: list[str] = ttils.get_paths(updater.temp_dir)

    assert len(unzipped_files) != 0

def mk_app(path: Path) -> None:
    '''Creates the folder structure of the application in the given path.''' 
    # unzip -l tests/zip-test.zip to get the folder structure

    append_path = lambda x: path / main_folder / x

    main_folder: Path = Path("sampleapp")
    app_folder: Path = append_path(Path("app"))

    append_app_folder = lambda x: app_folder / x
    config_folder: Path = append_app_folder(Path("config"))
    logs_folder: Path = append_app_folder(Path("logs"))

    updater_file: Path = append_path(Path("updater.exe"))
    main_app: Path = append_app_folder(Path("entrabulker.exe"))

    files_to_make: list[Path] = [updater_file, main_app, config_folder, logs_folder]

    for file in files_to_make:
        if file.suffix != "":
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch()
        else:
            file.mkdir()
        
def set_mock_response(get: get) -> MagicMock:
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