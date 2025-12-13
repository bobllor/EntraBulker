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
    def __init__(self, project_root: Path, *, logger: Log = None):
        '''Updater class.
        
        This does not replace the updater itself, and only replaces the other
        files. For the updater to be replaced, it will require manual updates.

        Parameters
        ----------
            project_root: Path
                The project root, the ZIP file is downloaded in the root's parent.
            
            logger: Log, default None
                The Log class. By default it is None, printing to stdout.
        '''
        self.project_root: Path = project_root
        self.logger: Log = logger or Log()
        
        # all files will be worked on in here before being moved into the main directory
        # this also makes it easier to clean up everything
        self._temp_dir: Path = self.project_root / "temp"
        # the single folder in the zip
        self._zip_folder: Path = self._temp_dir / FILE_NAMES["zip_folder"]

        if self._temp_dir.exists() and self._temp_dir.is_dir():
            utils.unlink_path(self._temp_dir)

        if not self._temp_dir.exists():
            self._temp_dir.mkdir(exist_ok=True, parents=True)

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
        url = url.strip()
        res: Response = requests.get(url)
        self.logger.info("Starting ZIP file download")
        self.logger.debug(f"Request on {url}")

        out_res: cResponse = utils.generate_response(message="")

        self.logger.debug(f"GET status: {res.status_code}")
        if res.status_code != 200:
            out_res["status"] = "error"
            out_res["message"] = "Failed to download ZIP file"
            self.logger.error(f"Failed to request, url: {url} | GET status: {res.status_code}")

            return out_res

        content_res: list[dict[str, Any]] = res.json()

        if len(content_res) < 1:
            out_res["status"] = "error"
            out_res["message"] = "Unknown error occurred"
            self.logger.error(f"Content response is empty: {content_res}")

            return out_res

        content: dict[str, Any] = content_res[0]
        zip_url: str = content["assets"][0]["browser_download_url"]
        zip_name: str = zip_url.split("/")[-1]

        try:
            with requests.get(zip_url) as r:
                # TODO: error handle here please!
                # NOTE: there was a massive headache when writing my test cases
                # it turns out for some reason, NamedTemporaryFile does not write
                # file bytes properly, it always attempts to decode with utf-8 causing errors.
                # why does this occur? i have no fucking idea.
                with open(self._temp_dir / zip_name, "wb") as file:
                    for chunk in r.iter_content(8024):
                        file.write(chunk)
        except Exception as e:
            self.logger.error(f"Exception occurred while downloading file: {e}")

            out_res["status"] = "error"
            out_res["message"] = "An error occurred while downloading the files"

            return out_res
        
        self._zip_file_path = self._temp_dir / zip_name

        out_res["message"] = f"Successfully downloaded {zip_name} to {self._temp_dir}"
        self.logger.info(f"Downloaded {zip_name} to {self._temp_dir}")

        return out_res
    
    def unzip(self, zip_path: Path) -> cResponse:
        '''Unzips the contents of the ZIP file into the temporary directory.'''
        res: cResponse = utils.generate_response(message=f"Extracted files to {self._temp_dir}")

        if zip_path is None or not zip_path.exists():
            res["status"] = "error"
            res["message"] = f"An unexpected error occurred while extracting the ZIP file"

            self.logger.error(f"Given zip_path {zip_path} does not exist")
            self.logger.debug(f"Temp directory location: {self._temp_dir}")

            return res

        with ZipFile(zip_path, "r") as file:
            file.extractall(self._temp_dir)
        
        return res
    
    def update(self, *, ignore_files: Iterable[str] = []) -> cResponse:
        '''Updates the application by moving the files from the temporary folder
        into the project root.

        Parameters
        ----------
            ignore_files: Iterable[str], default []
                Any Iterable of strings that are the file names, not the full path,
                used to ignore during replacement. By default it is an empty list. 
        '''
        res: cResponse = utils.generate_response(message="Successfully updated application")
        self.logger.debug(f"Files to ignore for update: {ignore_files}")

        ignore_set: set[str] = {f.lower() for f in ignore_files}

        for file in self._temp_dir.iterdir():
            file_name: str = file.name
            file_root: Path = self.project_root / file_name

            if file_name.lower() in ignore_set:
                self.logger.info(f"Given file {file} cannot be replaced")
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
        
        return res
    
    def remove_app_folders(self, folders: list[Path | str], *, ignore_folders: Iterable[str] = []) -> cResponse:
        '''Removes the application folders. This removes all files recursively from the given folders.

        Parameters
        ----------
            folders: list[Path | str]
                A list of Paths or string paths for folder removal, prior to being
                replaced. These are the folders of the application artifacts,
                not the dynamically generated folders during usage.
            
            ignore_folders: Iterable[str], default []
                Any iterable of strings to ignore. This is expected to be the folder
                names, not full paths. By default it is an empty list.
        '''
        res: Response = utils.generate_response(message="No folders removed")

        self.logger.debug(f"Folders to remove: {folders}")
        self.logger.debug(f"Folders to ignore: {ignore_folders}")

        folder_remove_count: int = 0
    
        ignore_set = {f.lower() for f in ignore_folders}

        for folder in folders:
            path: Path = folder if isinstance(folder, Path) else Path(folder)

            if path == self.project_root or path.name.lower() in ignore_set:
                self.logger.warning(f"Given path {path} cannot be removed")
                continue

            if path.exists():
                if path.is_dir():
                    self.logger.info(f"Removing folder {path}")
                    utils.unlink_path(path)
                    folder_remove_count += 1
        
        if folder_remove_count > 0:
            res["message"] = f"Removed {folder_remove_count} {'folders' if folder_remove_count > 1 else 'folder'}"

        return res
    
    def cleanup(self) -> None:
        '''Removes the temporary folder holding the files for the Updater class.'''
        utils.unlink_path(self._temp_dir)
    
    @property
    def zip_file(self) -> Path | None:
        '''Returns the Path to the zip file.
        
        If `download_zip` was not called, this will return None.
        '''
        return self._zip_file_path
    
    @property
    def temp_dir(self) -> Path:
        '''Returns the Path to the temporary directory '''
        return self._temp_dir