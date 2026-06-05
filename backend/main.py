from core.json_reader import Reader
from core.server import LocalServer
from api.api import API
from logger import Log
from support.vars import DEFAULT_HEADER_MAP, DEFAULT_OPCO_MAP, DEFAULT_SETTINGS_MAP, PROJECT_ROOT, VERSION, DEFAULT_GRAPH_MAP
from support.utils import init_window, is_prod
import webview
import os
import truststore

# NOTE: main app is in the apps folder

EXCEL_FILE: str = 'excel-mapping.json'
SETTINGS_FILE: str = 'settings.json'
OPCO_FILE: str = "opco-mapping.json"
GRAPH_FILE: str = "msgraph.json"

EXCEL_PATH: str = f'{str(PROJECT_ROOT)}/config/{EXCEL_FILE}'
SETTINGS_PATH: str = f'{str(PROJECT_ROOT)}/config/{SETTINGS_FILE}'
OPCO_PATH: str = f"{str(PROJECT_ROOT)}/config/{OPCO_FILE}"
GRAPH_PATH: str = f"{str(PROJECT_ROOT)}/config/{GRAPH_FILE}"

# same log location with updater logs
LOGS_PATH: str = f"{str(PROJECT_ROOT.parent)}/logs"

# due to work computers often having self-signed certs,
# this uses the certificates on windows (and others maybe)
truststore.inject_into_ssl()

if __name__ == '__main__':
    # will use the npm port, this is changed if in prod
    port: int = 5173
    url: str = f"http://localhost:{port}"

    if is_prod():
        server: LocalServer = LocalServer("madist")
        server.run()
        url = server.url

    debug, log_path = init_window(LOGS_PATH)

    logger: Log = Log(log_dir=log_path, file_name="app-%Y-%m-%d.log")

    logger.debug(f"Log path: {log_path} | URL: {url} | Debug: {debug} | Root: {os.getcwd()}")

    excel_reader: Reader = Reader(
        EXCEL_PATH, defaults=DEFAULT_HEADER_MAP, update_only=True, logger=logger, project_root=PROJECT_ROOT, lower_value=True
    )
    settings_reader: Reader = Reader(SETTINGS_PATH, defaults=DEFAULT_SETTINGS_MAP, update_only=True, logger=logger, project_root=PROJECT_ROOT)
    opco_reader: Reader = Reader(OPCO_PATH, defaults=DEFAULT_OPCO_MAP, logger=logger, project_root=PROJECT_ROOT)
    graph_reader: Reader = Reader(GRAPH_PATH, defaults=DEFAULT_GRAPH_MAP, logger=logger, project_root=PROJECT_ROOT)

    api: API = API(
        settings_reader=settings_reader, 
        excel_reader=excel_reader,
        opco_reader=opco_reader,
        graph_reader=graph_reader,
        logger=logger,
        project_root=PROJECT_ROOT
    )
    size: tuple[int, int] = (1080, 720)

    title: str = f'EntraBulker {VERSION}'

    window: webview.Window = webview.create_window(title, url, js_api=api, min_size=size)
    api.set_window(window)
    webview.start(debug=debug)