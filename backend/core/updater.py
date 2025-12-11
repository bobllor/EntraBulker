from pathlib import Path
from zipfile import ZipFile
from requests import Response
from typing import Any
from support.types import Response as cResponse
from logger import Log
import tempfile as tf
import support.utils as utils
import requests, os

# NOTE: all functions that returns a response will have additional keys: 

# each call will be its own separate call on the frontend.
# this is to update the progress bar from each Response return
# and in case of a single error, cancel out the process completely.

class Updater:
    def __init__(self, project_root: Path, *, logger: Log = None):
        self.project_root: Path = project_root
        self.logger: Log = logger or Log()

        self.temp_dir: Path = self.project_root / "temp"

        if self.temp_dir.exists() and self.temp_dir.is_dir():
            utils.unlink_path(self.temp_dir)

        if not self.temp_dir.exists():
            self.temp_dir.mkdir(exist_ok=True, parents=True)

        self.zip_path: Path = None
    
    def download_zip(self, url: str) -> cResponse:
        '''Downloads the zip file from the specified url. It will download the file
        to the project root in a temporary folder.
        
        It will return a Response with a `path` key of the ZIP file output.
        
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

        out_res: cResponse = utils.generate_response(message="", path="")

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

        temp_file: str = ""
        with requests.get(zip_url, stream=True) as r:
            # TODO: error handle here please!
            with tf.NamedTemporaryFile("wb", delete=False, dir=self.project_root) as file:
                temp_file = file.name

                for chunk in r.iter_content(chunk_size=8192):
                    file.write(chunk) 
        
        self.zip_file = self.project_root / zip_name
        os.replace(temp_file, self.zip_file)

        out_res["path"] = self.zip_file
        out_res["message"] = f"Successfully downloaded {zip_name}"
        self.logger.info(f"Downloaded {zip_name} to {self.project_root}")

        return out_res
    
    def unzip(self, path: Path) -> cResponse:
        '''Unzips the contents of the ZIP file into the temporary directory.'''
        with ZipFile(path, "r") as file:
            file.extractall(self.temp_dir)
    
    def update(self) -> cResponse:
        '''Updates the application files.
        
        This is expected to be called after the `unzip` method,
        '''
    
    def cleanup(self) -> None:
        '''Removes the temporary directory holding the files for the Updater class.'''
        utils.unlink_path(self.temp_dir)