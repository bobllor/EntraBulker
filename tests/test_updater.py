from tests.fixtures import updater, get
from backend.core.updater import Updater
from backend.support.types import Response
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Any
from zipfile import ZipFile

@patch('backend.core.updater.requests.get')
def test_download_zip(get: MagicMock, tmp_path: Path, updater: Updater):
    url: str = "https://fakeurl.com/api/stuff"

    mock: Any = get.return_value
    mock.status_code = 200
    mock.json.return_value = [{"assets": [
        {"browser_download_url": "https://fakeurl.com/api/stuff/zip-test.zip"}
    ]}] 
    
    zip_bytes: bytes = get_zip()

    mock.iter_content.return_value = [zip_bytes]
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None

    res: Response = updater.download_zip(url)

    for child in (tmp_path / "temp").iterdir():
        if ".zip" == child.suffix.lower():
            file: ZipFile = ZipFile(child, "r")

            for path in file.filelist:
                print(path)

def get_zip() -> bytes:
    '''Gets the ZIP file in list of bytes.'''
    test_zip: Path = Path(__file__).parent / "zip-test.zip"
    data: bytes = None

    with open(test_zip, "rb") as f:
        data = f.read()
    
    return data