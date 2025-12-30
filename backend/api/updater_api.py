from logger import Log
from core.updater import Updater
from support.vars import PROJECT_ROOT, FILE_NAMES, VERSION, META
from support.types import Response
from pathlib import Path
import support.utils as utils
import webview

class UpdaterAPI:
    def __init__(self, updater: Updater, *, logger: Log = None, window: webview.Window = None, is_prod: bool = False):
        '''Updater API. Each method must be called manually in the front end.
        This does **not** update the updater itself.
        
        Parameters
        ----------
            updater: Updater
                The Updater class used to update the program in its application files.
            
            logger: Log, default None
                The Log class. By default it is None, using an instance that defaults to
                the stdout terminal.
            
            window: webview.Window, default None
                The window of the webview. By default it is None, and can be set via the
                set_window method.
            
            is_prod: bool, default False
                Indicates whether or not the API should be in production or development mode.
                This is only used by the frontend.
        '''
        self.logger: Log = logger or Log()

        self.updater: Updater = updater

        self.is_prod: bool = is_prod
        # pywebview, not added in due to CI fails
        self._window: webview.Window = window
    
    def set_window(self, window: webview.Window) -> None:
        '''Sets the Window for pywebview.

        Parameters
        ----------
        window: webview.Window
            The pywebview Window. 
        '''
        self._window = window
    
    def is_production(self) -> Response:
        '''Returns a response with `content` boolean indicating if the program
        is in production or development.
        '''
        self.logger.debug(f"Is production: {self.is_prod}")
        res: Response = utils.generate_response(message="Request successful", content=self.is_prod)

        return res

    def download_zip(self, url: str = None) -> Response:
        '''Begins the ZIP download process.'''
        if url is None:
            url = META["releases_url"]

        res: Response = self.updater.download_zip(url)

        return res
    
    def unzip(self) -> Response:
        zip_path: Path = self.updater.zip_file
        res: Response = self.updater.unzip(zip_path)

        return res
    
    def clean(self) -> Response:
        '''Cleans up the files from the download.'''
        res: Response = self.updater.cleanup()

        return res
    
    def check_version(self, url: str = None) -> Response:
        '''Checks the version and returns a Response.
        
        It contains a new key `content` that holds a bool value, indicating
        if an update is needed or not.
        '''
        if url is None:
            url = META["version_url"]

        out_res: Response = utils.get_version(url)

        self.logger.debug(f"Check version response: {out_res}")
        
        res: Response = utils.generate_response(message="Version check successful", content=False)
        res["content"] = utils.compare_version(VERSION, out_res["content"])

        if out_res["status"] == "error" or out_res["exception"] is not None:
            self.logger.error(f"Failed to request on {url}: {out_res}")
            res["message"] = out_res["message"]
            res["content"] = False
            res["status"] = "error"
        
        self.logger.debug(f"Version response: {res}")

        return res
    
    def update(self) -> Response:
        '''Updates the core files in the project root folder.'''
        apps_path: Path = self.updater.temp_project_folder
        # not including the updater files, these have to be manually updated.
        res: Response = self.updater.update(apps_path, ignore_files=["udist", FILE_NAMES["updater_exe"]])

        return res
    
    def start_main_app(self) -> Response:
        '''Starts the main application. This will quit the current application.'''
        # due to the updater application being out of the main app folder, this
        # path is different
        main_app: Path = Path(FILE_NAMES["apps_folder"]) / FILE_NAMES["app_exe"]
        res: Response = utils.generate_response(message="Successfully started application")

        if not main_app.exists():
            res["status"] = "error"
            res["message"] = "Application does not exist"

            self.logger.warning(f"{main_app} does not exist")

            return res

        # NOTE: this might need to be manually tested.
        # as on 12/17/2025 2:59 PM: it confirm works.
        self.logger.info(f"Starting main application")
        app_path: str = str(PROJECT_ROOT / FILE_NAMES["app_exe"])

        self._window.destroy()
        out: str = utils.run_cmd([app_path], cwd=str(PROJECT_ROOT / FILE_NAMES["apps_folder"])) 
        self.logger.info(f"Ran command {[app_path]}, out: {out}")

        if out != "":
            self.logger.error(f"Failed to run updater: {out}")
            res["status"] = "error"
            res["message"] = "Failed to run executable"

            return res

        exit(0)

        return res