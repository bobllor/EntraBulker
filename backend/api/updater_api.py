from logger import Log
from core.updater import Updater
from support.vars import PROJECT_ROOT, REPO_URL
from support.types import Response
from pathlib import Path
import webview

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
        res: Response = self.updater.download_zip(REPO_URL)

        return res
    
    def clean(self) -> Response:
        '''Cleans up the files from the download.'''
        res: Response = self.updater.cleanup()

        return res
    
    def start_main_app(self) -> None:
        '''Starts the main application. This will quit current application.'''
        self.logger.info(f"Starting main application")
        self._window.destroy()