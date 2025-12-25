from logger import Log
from api.updater_api import UpdaterAPI
from core.updater import Updater
from core.server import LocalServer
from support.utils import is_prod, init_window
from support.vars import PROJECT_ROOT, FILE_NAMES
import webview

if __name__ == "__main__":
    debug, log_path = init_window("updater-logs")

    logger: Log = Log(log_dir=log_path)

    updater: Updater = Updater(PROJECT_ROOT, logger=logger) 
    size: tuple[int, int] = (400, 200)

    title: str = f'EntraBulker Updater'
    url: str = 'http://localhost:5172/' 

    if is_prod():
        server: LocalServer = LocalServer(FILE_NAMES["updater_dist"])
        server.run()
        url = server.url

    api: UpdaterAPI = UpdaterAPI(updater, logger=logger, is_prod=is_prod())

    window: webview.Window = webview.create_window(title, url, js_api=api, width=size[0], height=size[1], min_size=size, resizable=False)
    api.set_window(window)

    webview.start(debug=debug)