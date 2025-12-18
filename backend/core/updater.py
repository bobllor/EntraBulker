from pathlib import Path
from zipfile import ZipFile
from requests import Response
from typing import Any, Iterable
from support.types import Response as cResponse
from logger import Log
from support.vars import FILE_NAMES
import support.utils as utils
import requests, os, shutil

class Updater:
    def __init__(self, project_root: Path, *, temp_project_folder: Path = None, logger: Log = None):
        '''Updater class.
        
        This does not replace the updater.exe itself, only replacing the primary
        application files. For the updater to be replaced, it will require 
        manual updates.

        Parameters
        ----------
            project_root: Path
                The project root. This is not the Path of the entire application folder, 
                but is the Path to the folder that holds the main application files.
            
            temp_project_folder: Path
                The path to the project folder of the ZIP file. This is the extracted files in the
                temporary folder. By default it is None, using `entrabulker` as its default folder name.
            
            logger: Log, default None
                The Log class. By default it is None, printing to stdout.
        '''
        self.project_root: Path = project_root
        self.logger: Log = logger or Log()
        
        # all files will be worked on in here before being moved into the main directory
        # this also makes it easier to clean up everything
        # the temp dir will not be in the main project root, but will be in the outside parent.
        self._temp_dir: Path = self.project_root / "temp"
        self._temp_project_folder: Path = temp_project_folder or self._temp_dir / FILE_NAMES["project_folder"]

        if self._temp_dir.exists() and self._temp_dir.is_dir():
            utils.unlink_path(self._temp_dir)
        self._create_temp_dir()

        self._zip_file_path: Path = None
    
    def download_zip(self, url: str) -> cResponse:
        '''Downloads the zip file from the specified url. It will download the file
        to the project root in a temporary folder. 
        
        The ZIP file property is also set in the method.
        
        Parameters
        ----------
            url: str
                The url to the ZIP file. This is expected to be the
                GitHub API releases url.
        '''
        out_res: cResponse = utils.generate_response(message="")

        url = url.strip()
        try:
            res: Response = requests.get(url)
        except Exception as e:
            out_res["status"] = "error"
            out_res["message"] = "Failed to request data"
            self.logger.error(f"Failed to request url {url}: {e}")

            return out_res

        self.logger.info("Starting ZIP file download")
        self.logger.debug(f"Request on {url}")

        self.logger.debug(f"GET status: {res.status_code}")
        if res.status_code != 200:
            out_res["status"] = "error"
            out_res["message"] = f"Failed to request data"
            self.logger.error(f"Failed to request on url {url}: {res.status_code}")

            return out_res

        try:
            content_res: list[dict[str, Any]] = res.json()
        except requests.exceptions.JSONDecodeError as e:
            out_res["status"] = "error"
            out_res["message"] = f"Unexpected data received"

            self.logger.error(f"Failed to parse JSON on url {url}: {e}")

            return out_res

        if len(content_res) < 1:
            out_res["status"] = "error"
            out_res["message"] = f"Failed to read data"
            self.logger.error(f"Response for content is empty: {content_res}")

            return out_res

        content: dict[str, Any] = content_res[0]
        zip_url: str = content["assets"][0]["browser_download_url"]
        zip_name: str = zip_url.split("/")[-1]

        self._create_temp_dir()
        try:
            with requests.get(zip_url) as r:
                r.raise_for_status()
                # NOTE: there was a massive headache when writing my test cases
                # it turns out for some reason, NamedTemporaryFile does not write
                # file bytes properly, it always attempts to decode with utf-8 causing errors.
                # why does this occur? i have no fucking idea.
                with open(self._temp_dir / zip_name, "wb") as file:
                    for chunk in r.iter_content(8024):
                        file.write(chunk)
        except (Exception, requests.exceptions.HTTPError) as e:
            self.logger.error(f"Error while downloading from {url}: {e}")

            out_res["status"] = "error"
            out_res["message"] = "Failed to download the ZIP file"

            return out_res
        
        self._zip_file_path = self._temp_dir / zip_name

        out_res["message"] = f"Downloaded {zip_name} to temp"
        self.logger.info(f"Downloaded {zip_name} to {self._temp_dir}")

        return out_res
    
    def unzip(self, zip_path: Path) -> cResponse:
        '''Unzips the contents of the ZIP file into the temporary directory.'''
        res: cResponse = utils.generate_response(message=f"Extracted files to temp")

        if zip_path is None or not zip_path.exists():
            res["status"] = "error"
            res["message"] = f"An unexpected error occurred while extracting the ZIP file"

            self.logger.error(f"Given zip_path {zip_path} does not exist")
            self.logger.debug(f"Temp directory location: {self._temp_dir}")

            return res

        with ZipFile(zip_path, "r") as file:
            file.extractall(self._temp_dir)
        
        self.logger.info(f"Extracted ZIP contents to {self._temp_dir}")
        
        return res
    
    def update(self, apps_path: Path, *, ignore_files: Iterable[str] = []) -> cResponse:
        '''Updates the application by moving the files from the temporary folder
        into the project root.

        Parameters
        ----------
            apps_path: Path
                The path to the unzipped files. Since the ZIP file contains a single folder that
                holds all the other files, this is expected to be that folder name.

            ignore_files: Iterable[str], default []
                Any Iterable of strings that are the file names, not the full path,
                used to ignore during replacement. The file names in the Path 
                are checked with the list. By default it is an empty list. 
        '''
        res: cResponse = utils.generate_response(message="Updated application")

        self.logger.debug(f"Files to ignore for update: {ignore_files}")
        self.logger.info(f"Replacing files in root {self.project_root} with {apps_path}")

        ignore_set: set[str] = {f.lower() for f in ignore_files}

        if not apps_path.exists():
            res["message"] = f"Unable to find project folder {apps_path.name}"
            res["status"] = "error"

            self.logger.warning(f"Failed to find {apps_path}")

            return res

        for file in apps_path.iterdir():
            file_name: str = file.name
            file_root: Path = self.project_root / file_name

            if file_name.lower() in ignore_set:
                self.logger.warning(f"Given file {file} cannot be replaced")
                continue

            # if for some reason the files still exist, we will manually remove it here.
            if file_root.exists():
                self.logger.warning(f"File {file_root} exists in the root folder")

                if not file_root.is_dir():
                    file_root.unlink()
                else:
                    shutil.rmtree(file_root, ignore_errors=True)

                self.logger.info(f"Removed file {file_root}")

            os.replace(file, file_root)
            self.logger.info(f"Replaced file {file_root}")
        
        return res
    
    def cleanup(self) -> cResponse:
        '''Removes the temporary folder holding the files for the Updater class.
        
        It will always return a success.
        '''
        res: cResponse = utils.generate_response(message=f"Removed temp folder")

        if self._temp_dir.exists():
            self.logger.info(f"Removing contents of {self._temp_dir}")
            utils.unlink_path(self._temp_dir)
        
        return res
    
    def _create_temp_dir(self) -> None:
        '''Creates the temporary directory, if it does not exist.'''
        if not self._temp_dir.exists():
            self._temp_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created temp folder {self._temp_dir}")
    
    @property
    def zip_file(self) -> Path | None:
        '''The Path to the zip file.
        
        If `download_zip` was not called, this will return None.
        '''
        return self._zip_file_path
    
    @property
    def temp_dir(self) -> Path:
        '''The Path to the temporary folder.'''
        return self._temp_dir
    
    @property
    def temp_project_folder(self) -> Path:
        '''The Path of the project folder located in the temporary folder.'''
        return self._temp_project_folder