from core.json_reader import Reader
from api.api import API
from logger import Log
from support.vars import DEFAULT_HEADER_MAP, DEFAULT_OPCO_MAP, DEFAULT_SETTINGS_MAP, PROJECT_ROOT, VERSION
import webview

EXCEL_FILE: str = 'excel-mapping.json'
SETTINGS_FILE: str = 'settings.json'
OPCO_FILE: str = "opco-mapping.json"
EXCEL_PATH: str = f'config/{EXCEL_FILE}'
SETTINGS_PATH: str = f'config/{SETTINGS_FILE}'
OPCO_PATH: str = f"config/{OPCO_FILE}"
LOGS_PATH: str = f"logs"

if __name__ == '__main__':
    logger: Log = Log()

    excel_reader: Reader = Reader(EXCEL_PATH, defaults=DEFAULT_HEADER_MAP, update_only=True, logger=logger, project_root=PROJECT_ROOT)
    settings_reader: Reader = Reader(SETTINGS_PATH, defaults=DEFAULT_SETTINGS_MAP, update_only=True, logger=logger, project_root=PROJECT_ROOT)
    opco_reader: Reader = Reader(OPCO_PATH, defaults=DEFAULT_OPCO_MAP, logger=logger, project_root=PROJECT_ROOT)

    api: API = API(
        settings_reader=settings_reader, 
        excel_reader=excel_reader,
        opco_reader=opco_reader,
        logger=logger,
        project_root=PROJECT_ROOT
    )
    size: tuple[int, int] = (1080, 720)

    title: str = f'EntraBulker {VERSION}'
    url: str = 'http://localhost:5173/'

    window: webview.Window = webview.create_window(title, url, js_api=api, min_size=size)
    api.set_window(window)
    webview.start(debug=True)