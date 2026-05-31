from tests.fixtures import api, JSON, df
from backend.api.api import API
from backend.support.types import Response
from pathlib import Path
import tests.utils as ttils
import pandas as pd

def test_generate_graph_azure(tmp_path: Path, api: API, df: pd.DataFrame):
    # WIP
    assert True