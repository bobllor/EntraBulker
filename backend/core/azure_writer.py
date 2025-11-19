from typing import Literal
from support.vars import AZURE_HEADERS, AZURE_VERSION
from logger import Log
from support.types import Response
from pathlib import Path
import pandas as pd
import support.utils as utils

HeadersKey = Literal["name", "username", "password", "first_name", "last_name", "block_sign_in"]

class AzureWriter:
    def __init__(self, *, logger: Log = None): 
        '''Azure CSV writing class, an empty AzureHeaders is initialized
        and must be setup prior to running AzureWriter.write().'''
        self._headers_data: dict[HeadersKey, list[str]] = {
            val: [] for val in AZURE_HEADERS.values()
        }
        
        self.logger: Log = logger or Log()
    
    def set_full_names(self, names: list[str]):
        '''Sets the full names for the data.'''
        self.logger.info(f"Setting full names")
        self.logger.debug(f"Full names data: {names}")
        self._headers_data[AZURE_HEADERS["name"]] = names
    
    def set_usernames(self, usernames: list[str]):
        '''Sets the usernames of the users.

        Parameters
        ----------
            usernames: list[str]
                List of names of usernames.
        '''
        self.logger.info(f"Setting usernames")
        self.logger.debug(f"Username data: {usernames}")
        self._headers_data[AZURE_HEADERS["username"]] = usernames
    
    def set_passwords(self, passwords: list[str]) -> None:
        '''Sets the passwords of the data.'''
        self.logger.info(f"Setting passwords")
        self._headers_data[AZURE_HEADERS["password"]] = passwords
    
    def set_block_sign_in(self, capacity: int, blockages: list[str] = []) -> None:
        '''Sets the block sign in for the users.
        
        Parameters
        ----------
            capacity: int
                The max capacity of the list for the CSV. This is obtained from any list
                that is not the blockages list, that are used in AzureWriter. It is used to
                auto generate default values if the blockages list is less than the capacity.

            blockages: list[str]
                List of blockages. If the size of blockages is less than the capacity, then
                the remaining spaces are filled with `No` as the default value.
        '''
        # i am not actually sure how to let the user define these in the frontend.
        if len(blockages) < capacity:
            for _ in range(capacity - len(blockages)):
                blockages.append("No")
            
        self.logger.info(f"Setting block sign in")
        self._headers_data[AZURE_HEADERS["block_sign_in"]] = blockages
    
    def set_names(self, names: list[str]) -> None:
        '''Sets the first and last names of the data. If more than two names are given,
        then all non-last names are placed in the first name.'''
        first_names: list[str] = []
        last_names: list[str] = []

        for name in names:
            name_list: list[str] = name.split()

            first_name: str = " ".join(name_list[0:-1])
            last_name: str = name_list[-1]

            first_names.append(first_name)
            last_names.append(last_name)
        
        self.logger.info(f"Setting first and last names")
        self.logger.debug(f"Names data: {names}")
        self._headers_data[AZURE_HEADERS["first_name"]] = first_names
        self._headers_data[AZURE_HEADERS["last_name"]] = last_names
    
    def write(self, out: Path | str) -> None:
        '''Write to a CSV file.
        
        Parameter
        ---------
            out: Path | str
                A StrPath that is the output of the file. All directories will be created
                if the directories does not exist.
        '''
        path: Path = out if isinstance(out, Path) else Path(out)

        if not path.parent.exists():
            path.mkdir(parents=True, exist_ok=True)
        
        # azure version must be specified on the first row.
        with open(path, "w") as file:
            file.write(AZURE_VERSION+"\n")
        
        df: pd.DataFrame = pd.DataFrame(self._headers_data)

        df.to_csv(path, mode="a", index=False)
    
    def write_template(self, out: Path | str, *, text: str, start_date: str = None) -> Response:
        '''Writes the template text for each user. A Response is returned with the standard keys and
        `output_dir`, being the folder of the created files.
        
        A templates folder is created if it does not exist, and sub-folders holding the text files
        are created in the templates folder.

        Before calling this method, ensure that the 
        the Writer has data set for `full names`, `usernames`, and `passwords`.

        Parameters
        ----------
            out: Path | str
                The output path for the files. This is the parent folder that the
                `templates` folder is generated in.

            text: str
                The text used in the template.
        '''
        if start_date is None:
            start_date = utils.get_date()

        folder_name: str = f"templates-{start_date}"

        path: Path = out / "templates" if isinstance(out, Path) else Path(out) / "templates"
        path = path / folder_name

        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        names: list[str] = self._headers_data[AZURE_HEADERS["name"]]
        usernames: list[str] = self._headers_data[AZURE_HEADERS["username"]]
        passwords: list[str] = self._headers_data[AZURE_HEADERS["password"]]

        res: Response = self._validates_template_write(names, usernames, passwords)

        if res["status"] == "error":
            return res
        
        text_count: int = 0

        for i, name in enumerate(names): 
            username: str = usernames[i]
            password: str = passwords[i]

            file_name: str = f"{i+1}{name}-{start_date}.txt"

            # NOTE: calculated values are with a Response return will always be in the key "content".
            text_res: Response = utils.generate_text(text=text, username=username, name=name, password=password)
            
            if text_res["status"] == "success":
                text_count += 1
            elif text_res["status"] == "error":
                self.logger.error(f"Failed to generate text file: {text_res}")

            with open(path / file_name, "w") as file:
                file.write(text_res["content"])
        
        return utils.generate_response(message=f"Created {text_count} files", output_dir=str(path))
    
    def get_data(self, key: HeadersKey) -> list[str]:
        '''Gets the specified data.'''
        return self._headers_data[key]
    
    def get_keys(self) -> list[str]:
        '''Gets the keys for the data.'''
        return [key for key in self._headers_data]
    
    def _validates_template_write(self, names: list[str], usernames: list[str], passwords: list[str]) -> Response:
        '''Validates the data used in the Template writing.
        
        Parameters
        ----------
            names: list[str]
                The list of names of the Headers data.

            usernames: list[str]
                The list of usernames of the Headers data.

            passwords: list[str]
                The list of passwords of the Headers data.
        '''
        error_res: Response = utils.generate_response("error", message="")
        success_res: Response = utils.generate_response(message="Successful validation")

        defaults: dict[str, list[str]] = {
            "names": names,
            "usernames": usernames,
            "passwords": passwords,
        }

        # if any value is > or < the base length, then we exit with an error
        base_len: int = len(names)

        for key, item in defaults.items():
            if len(item) == 0:
                error_res["message"] = f"Got 0 items in {key}, failed to run"
                return error_res

            if len(item) < base_len:
                error_res["message"] = f"Key {key} has less items than expected"
                return error_res
            elif len(item) > base_len:
                error_res["message"] = f"Key {key} has more items than expected"

        return success_res