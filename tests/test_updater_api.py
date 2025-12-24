from tests.fixtures import updater_api, mock
from backend.api.updater_api import UpdaterAPI
from unittest.mock import patch, Mock
from backend.support.types import Response
import requests

# all but a few methods are already part of test_updater

@patch("backend.api.updater_api.utils.get_version")
def test_check_version(mock: Mock, updater_api: UpdaterAPI):
    mock.return_value = {
        "status": "success",
        "message": "Successful execution",
        "content": "v1.0.1",
        "exception": None,
    }

    res: Response = updater_api.check_version("https://someurl.com/api/version")

    assert res["status"] == "success" and res["content"] == True

@patch("backend.support.utils.requests.get", side_effect=requests.exceptions.HTTPError("HTTP error occurred"))
def test_error_check_version(mock: Mock, updater_api: UpdaterAPI):
    res: Response = updater_api.check_version("https://someurl.com/api/version")

    assert res["status"] == "error" and res["content"] == False