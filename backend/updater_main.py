from logger import Log
from api.updater_api import UpdaterAPI
from support.vars import PROJECT_ROOT
import webview

if __name__ == "__main__":
    api: UpdaterAPI = UpdaterAPI(project_root=PROJECT_ROOT)
    size: tuple[int, int] = (300, 200)

    title: str = f'EntraBulker Updater'
    url: str = 'http://localhost:5172/' 

    webview.create_window(title, url, js_api=api, min_size=size, resizable=False)
    webview.start(debug=True)