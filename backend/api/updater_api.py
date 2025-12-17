from logger import Log
from core.updater import Updater
from support.vars import PROJECT_ROOT, FILE_NAMES
from support.types import Response
from pathlib import Path
import support.utils as utils
import webview

URL: str = "https://api.github.com/repos/bobllor/entra-bulker/releases"
test: str = "https://api.github.com/repos/bobllor/teklabeler/releases"

class UpdaterAPI:
    def __init__(self, updater: Updater, *, logger: Log = None):
        '''Updater API. Each method must be called manually in the front end.'''
        self.logger: Log = logger or Log()

        self.updater: Updater = updater

        self._window = None
    
    def set_window(self, window: webview.Window):
        '''Sets the Window for pywebview.'''
        self._window = window

    def download_zip(self) -> Response:
        '''Begins the ZIP download process.'''
        res: Response = self.updater.download_zip(test)

        return res
    
    def unzip(self) -> Response:
        zip_path: Path = self.updater.zip_file
        res: Response = self.updater.unzip(zip_path)

        return res
    
    def clean(self) -> Response:
        '''Cleans up the files from the download.'''
        res: Response = self.updater.cleanup()

        return res
    
    def update(self) -> Response:
        '''Updates the core files in the project root folder.'''
        apps_path: Path = self.updater.temp_project_folder
        # not including the updater files, these have to be manually updated.
        res: Response = self.updater.update(apps_path, ignore_files=["udist", FILE_NAMES["updater_exe"]])

        return res
    
    def start_main_app(self) -> None:
        '''Starts the main application. This will quit the current application.'''
        self.logger.info(f"Starting main application")
        app_path: str = str(PROJECT_ROOT / FILE_NAMES["app_exe"])

        self._window.destroy()

        utils.run_cmd([app_path]) 
        exit(0)