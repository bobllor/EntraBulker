from backend.logger import Log
from pathlib import Path
from backend.core.json_reader import Reader
from backend.api.api import API
from backend.support.vars import DEFAULT_HEADER_MAP, DEFAULT_SETTINGS_MAP, DEFAULT_OPCO_MAP, FILE_NAMES
from backend.core.updater import Updater
from unittest.mock import patch
import pandas as pd
import pytest

JSON: Path = Path(__file__).parent / "data.json"

@pytest.fixture
def logger():
    logger: Log = Log()

    yield logger

@pytest.fixture
def reader(tmp_path: Path):
    json_name: str = "temp_reader.json"
    json_path: Path = tmp_path / "cfg" / json_name

    yield Reader(json_path, defaults=DEFAULT_HEADER_MAP, is_test=True, project_root=tmp_path)

@pytest.fixture
def settings_reader(tmp_path: Path):
    json_name: str = "settings_temp_config.json"
    json_path: Path = tmp_path / "cfg" / json_name

    yield Reader(json_path, defaults=DEFAULT_SETTINGS_MAP, update_only=True, is_test=True, project_root=tmp_path)

@pytest.fixture(scope="function")
def api(tmp_path: Path):
    config_path: Path = tmp_path / "config"

    excel: Reader = Reader(config_path / "excel.json", defaults=DEFAULT_HEADER_MAP, is_test=True, project_root=tmp_path)
    settings: Reader = Reader(config_path / "settings.json", defaults=DEFAULT_SETTINGS_MAP, is_test=True, project_root=tmp_path)
    opcos: Reader = Reader(config_path / "opcos.json", defaults=DEFAULT_OPCO_MAP, is_test=True, project_root=tmp_path)

    opco_map: dict[str, str] = {
        "default": DEFAULT_OPCO_MAP["default"],
        "company one": "company.one.org",
        "company two": "companytwo.com",
        "company three": "company.three.nhs.gov"
    }

    opcos.insert_many(opco_map)

    api: API = API(excel_reader=excel, settings_reader=settings, opco_reader=opcos, project_root=tmp_path)
    api.set_output_dir(tmp_path)

    yield api

@pytest.fixture
def get():
    with patch('requests.get') as get:
        yield get

@pytest.fixture
def df():
    df: pd.DataFrame = pd.read_json(JSON)

    df = df.rename(mapper=lambda x: x.lower(), axis=1)

    yield df

TEST_PROGRAM_FILES: str = "Program Files"

@pytest.fixture
def updater(tmp_path: Path):
    upd: Updater = Updater(
        tmp_path / TEST_PROGRAM_FILES / FILE_NAMES["project_folder"] / FILE_NAMES["apps_folder"],
        ignore_app_creation=False,
    )

    yield upd