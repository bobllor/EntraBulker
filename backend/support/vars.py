from pathlib import Path
from .types import HeaderMap, OpcoMap, APISettings, AzureHeaders, Metadata, FileNames
from typing import Literal
from .utils import is_prod
import sys

VERSION: str = "v1.0.0" # this must start with a "v"

META: Metadata = {
    "version": VERSION,
    "version_url": "https://raw.githubusercontent.com/bobllor/EntraBulker/refs/heads/main/VERSION.txt",
    "releases_url": "https://api.github.com/repos/bobllor/entrabulker/releases",
}

# used as the baseline root path
if is_prod():
    PROJECT_ROOT: Path = Path(sys.executable).parent
else:
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
# name of the updater application for updating the application

FILE_NAMES: FileNames = {
    "updater_exe": "updater.exe",
    "app_exe": "entrabulker.exe",
    "updater_dist": "udist",
    "app_dist": "appdist",
    "project_folder": "entrabulker",
    "apps_folder": "apps",
}

MAIN_APP_PATH: Path = PROJECT_ROOT / FILE_NAMES["app_exe"]
UPDATER_PATH: Path = PROJECT_ROOT.parent / FILE_NAMES["updater_exe"]

# NOTE: these are default mappings used to initialize the data.
# the data is based off of ServiceNow naming, but the values can be changed.

AZURE_VERSION: Literal['version:v1.0'] = 'version:v1.0'
# i dont think order matters for the end csv- it may need testing.
AZURE_HEADERS: AzureHeaders = {
    'name': 'Name [displayName] Required',
    'username': 'User name [userPrincipalName] Required',
    'password': 'Initial password [passwordProfile] Required',
    'block_sign_in': 'Block sign in (Yes/No) [accountEnabled] Required',
    'first_name': 'First name [givenName]', 
    'last_name': 'Last name [surname]',
}

# NOTE: value is the column name in the excel/csv file.
# this dict gets reversed when it gets validated in Parser.
DEFAULT_HEADER_MAP: HeaderMap = {
    'opco': 'operating company',
    'name': 'full name',
    'first_name': 'first name',
    'last_name': 'last name',
}

# no @ is used here because it is added in to the username generator
DEFAULT_OPCO_MAP: OpcoMap = {
    'default': 'placeholder.com',
}

DEFAULT_SETTINGS_MAP: APISettings = {
    "output_dir": str(Path().home()),
    "flatten_csv": False,
    "two_name_column_support": False,
    "template": {
        "enabled": False,
        "text": "",
    },
    "format": {
        "format_case": "title",
        "format_style": "first last",
        "format_type": "period",
    },
    "password": {
        "length": 16,
        "use_uppercase": False,
        "use_punctuations": False,
        "use_numbers": False,
    },
}