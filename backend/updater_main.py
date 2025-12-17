from logger import Log
from api.updater_api import UpdaterAPI
from core.updater import Updater
from support.vars import PROJECT_ROOT
import webview, sys

if __name__ == "__main__":
    updater: Updater = Updater(PROJECT_ROOT) 
    api: UpdaterAPI = UpdaterAPI(updater)
    size: tuple[int, int] = (400, 250)
    
    # TODO: add a flag checker to ensure this cant be run normally, only through the main app.
    flag: str = sys.argv[-1]

    title: str = f'EntraBulker Updater'
    url: str = 'http://localhost:5172/' 

    window: webview.Window = webview.create_window(title, url, js_api=api, width=size[0], height=size[1], min_size=size, resizable=False)
    api.set_window(window)

    webview.start(debug=True)