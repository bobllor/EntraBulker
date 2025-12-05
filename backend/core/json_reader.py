from logger import Log
from pathlib import Path
from typing import Any, Literal
from support import utils
import json, os
import tempfile as tf

class Reader:
    def __init__(self, path: Path | str, *, 
        defaults: dict[str, Any] = None, 
        logger: Log = None,
        update_only: bool = False,
        is_test: bool = False,
        project_root: Path = None):
        '''Used to support CRUD operations on JSON data for the program.
        
        Parameters
        ----------
            path: Path | str
                A StrPath of the JSON file. All folders will be created up to the file.
            
            defaults: dict[str, Any], default None
                The default data that must exist in the file. These are the default values
                of the settings. If given, it will validate and correct the default values only.
            
            logger: Log, default None
                The logger, by default it is None- creating a new instance with no special features.
            
            update_only: bool, default False
                Disables insertion and deletion in the Reader. By default it is false.
            
            is_test: bool, default False
                Boolean to indicate if the Reader is a test instance or not. This enables deletion of default keys,
                but otherwise functions normally.
            
            project_root: Path | str, default `None`
                The path to the project root. This is where the temporary files are written to
                before being moved into the given path. By default it is None, using the
                temporary FS as the location.
        '''
        # NOTE: because i code on linux this has to be a string due to a PosixPath issue with pywebview
        self.path: str = str(path)
        self._pathpath: Path = Path(path) if isinstance(path, str) else path
        self._name: str = Path(self.path).name

        self._project_root: Path = project_root

        self.logger: Log = logger or Log()
        self.update_only: bool = update_only
        self._is_test: bool = is_test

        self._mkfiles()

        self._content: dict[str, Any] = self.read()

        # ensures all keys are lowercase.
        lowered_content: dict[str, Any] = self._lower_keys()
        if self._content != lowered_content:
            self._content = lowered_content
            self.write(self._content)

        self._defaults = defaults
        # used for validating unupdatable defaults
        self._update_reader_flag: bool = False
        if defaults:
            self.logger.info(f"Validating {self._name}")
            self._validate_defaults(defaults)

            if self.update_only:
                temp_dict: dict[str, Any] = self._validate_unupdatable_defaults(self._content, self._defaults)

                if self._update_reader_flag:
                    self._content = temp_dict
                    self.write(self._content)
    
    def get_content(self) -> dict[str, Any]:
        '''Returns the dictionary contents.'''
        return self._content
    
    def get_path(self) -> Path:
        '''Returns the Path of the reader.'''
        return self._pathpath

    def read(self) -> dict[str, Any]:
        '''Returns the contents of the .json file in a dictionary format.'''
        content: dict[str, Any] = {}
        try:
            with open(self.path, "r") as file:
                content = json.load(file)
        except json.decoder.JSONDecodeError:
            self.logger.error(f"JSON file was empty, failed to read")

            self.write(content)
        
        return content

    def write(self, data: dict[str, Any]) -> None:
        '''Writes data to the file.'''
        # only write, append does not work.
        with tf.NamedTemporaryFile("w", delete=False, dir=self._project_root) as file:
            temp_file: str = file.name

            json.dump(data, file)
            os.replace(temp_file, self.path)
            self.logger.info(f"File {self._name} written")
    
    def insert(self, key: str, value: Any) -> dict[str, Any]:
        '''Inserts a single key-value pair into the structure.

        It returns a response in the form of a dictionary.
        '''
        update_res: dict[str, Any] = self._update_only_check()
        if update_res["status"] == "error":
            return update_res

        if key in self._content:
            self.logger.warning(f"Insertion failed: key {key} already exists")
            return utils.generate_response(status="error", message="Failed to insert, key already exists")

        self._content[key] = value
        self.write(self._content) 

        self.logger.info(f"Inserted key {key} with value: {value}")

        return utils.generate_response(message=f"Successfully inserted {key}", status_code=200)
    
    def insert_many(self, data: dict[str, Any]) -> dict[str, Any]:
        '''Inserts multiple key-value pairs into the structure.''' 
        update_res: dict[str, Any] = self._update_only_check()
        if update_res["status"] == "error":
            return update_res

        success_ops: int = 0
        for key, value in data.items():
            if key in self._content:
                self.logger.warning(f"Insertion failed: key {key} already exists")
                continue

            self._content[key] = value
            self.logger.info(f"Inserted key {key} with value: {value}")
            success_ops += 1

        self.write(self._content) 

        data_len: int = len(data)
        self.logger.info(
            f"Inserted into {self._name} with "
            f"{data_len} {'items' if data_len == 0 or data_len > 1 else 'item'}"
        )

        return utils.generate_response(
            message=f"Inserted {success_ops}/{len(data)} values, failed: {len(data) - success_ops}", 
            status_code=200
        )
    
    def update(self, key: str, value: Any) -> dict[str, Any]:
        '''Updates a key with the value.
        
        A dictionary response is generated and returned, indicating the status and message.

        Parameters
        ----------
            key: str
                The key being updated.

            value: Any
                Any value the key is updated to.
        '''
        if key not in self._content:
            self.logger.error(f"Update failed: key {key} does not exist")
            return utils.generate_response(status="error", message="Failed to update key", status_code=500)

        self._content[key] = value
        self.write(self._content)

        self.logger.info(f"Updated {key} with {value}")

        return utils.generate_response(message=f"Successfully updated key {key}", status_code=200)
    
    def update_search(self, key: str, value: Any, *, main_key: str = None, data: dict[str, Any] = None) -> dict[str, Any]:
        '''Recursively updates a key with the value. This handles updating nested keys and 
        keys of the same name that can be found in multiple parent keys, by targeting a specific parent.
        
        A dictionary response is generated and returned, indicating the status and message.

        Parameters
        ----------
            key: str
                The key being updated.

            value: Any
                Any value the key is updated to.

            main_key: str, default None
                The key that represents the nested key. This is expected to be a dictionary
                within the dictionary. If given and not found, then the first `key` match
                will be changed, if it exists.
            
            data: dict[str, Any], default None
                The data being recusirvely searched. By default it is None, using the Reader
                as the data being searched by default. 
        '''
        if data is None:
            data = self._content
        
        res: dict[str, Any] = utils.generate_response(
            status="error", 
            message="Failed to update key, key does not exist",
        )
        for k in data.keys():
            if main_key is not None:
                if main_key in data:
                    res = self.update_search(key, value, data=data[main_key])

                    return res
            else:
                if key in data:
                    data[key] = value

                    debug_val: Any = utils.format_value(value)

                    self.logger.info(f"Updated key {key} with value {debug_val}")

                    return utils.generate_response(message="Successfully updated key")

            if isinstance(data[k], dict):
                res = self.update_search(key, value, data=data[k], main_key=main_key)

                if res["status"] == "success":
                    return res

        return res
    
    def insert_update_many(self, data: dict[str, Any]) -> dict[str, Any]:
        '''Inserts contents of a dictionary into the Reader. If the key aleady exists,
        then it will update the Reader instead.'''
        update_res: dict[str, Any] = self._update_only_check()
        if update_res["status"] == "error":
            return update_res

        self.logger.debug(f"Given data: {data}")

        for key, val in data.items():
            self._content[key] = val

            if key in self._content:
                self.logger.info(f"Updated key {key} with {val}")
            else:
                self.logger.info(f"Inserted key {key} with {val}")
        
        self.write(self._content)

        return utils.generate_response("success", message="Successfully inserted keys", status_code=200) 
    
    def clear(self) -> None:
        '''Clears the entire Reader, except default keys.'''
        new_content: dict[str, Any] = {}
        for key in self._defaults.keys():
            if key in self._content:
                new_content[key] = self._content[key]
            else:
                new_content[key] = self._defaults[key]
            
        self._content = new_content
        self.write(self._content)
    
    def delete(self, key: str) -> dict[str, Any]:
        '''Deletes a key from the file.'''
        update_res: dict[str, Any] = self._update_only_check()
        if update_res["status"] == "error":
            return update_res

        if key in self._defaults and not self._is_test:
            self.logger.warning(f"Default key {key} was attempted to be deleted")
            return utils.generate_response(status="error", message="Failed to delete key")
        elif key not in self._content:
            self.logger.info(f"Key {key} does not exist in {self._content} for removal")
            return utils.generate_response(status="error", message="Unable to find key")
        
        del self._content[key]
        self.write(self._content)

        self.logger.info(f"Deleted key {key}")
        return utils.generate_response(message=f"Successfully deleted {key}")
    
    def get(self, key: str, *, data: dict[str, Any] = None) -> Any:
        '''Gets the value stored at the key.
        
        If the key cannot be found, then None is returned.

        Parameters
        ----------
            key: str
                The key that is being searched for.
            
            data: dict[str, Any], default None
                The data dictionary. When calling the method, **do not pass data** into this
                argument. The only acceptable data is the **`Reader` content**, which by default
                is set to the content if it is `None`.
        '''
        if data is None:
            data = self._content
        if key in data:
            return data[key]
        
        for c_value in data.values():
            if isinstance(c_value, dict):
                value: Any = self.get(key, data=c_value)

                if value is not None:
                    return value
        
        return None
    
    def get_search(self, key: str, *, data: dict[str, Any] = None, parent_key: str = None) -> Any:
        '''Gets the value stored at the key. This uses a parent key to target a specific section
        in case that there are multiple nested keys of the same name.
        
        Parameters
        ----------
            key: str
                The key that is being searched for.
            
            data: dict[str, Any], default None
                The data dictionary. When calling the method, **do not pass data** into this
                argument. The only acceptable data is the **`Reader` content**, which by default
                is set to the content if it is `None`.
            
            parent_key: str, default None
                The parent key to target. This is used to target a certain section within the Reader,
                used for targeting a key that can possibly be found in other sections. By default it is None,
                and will be treated as a normal get() if None.
        '''
        if data is None:
            data = self._content
            
        value: Any = None
        if parent_key is None:
            value = self.get(key, data=data) 
        else:
            for d_key, d_val in data.items():
                if isinstance(d_val, dict):
                    # consume the parent key if the parent key is found
                    if d_key == parent_key:
                        parent_key = None

                    value = self.get_search(key, data=d_val, parent_key=parent_key)

                    if value is not None:
                        return value

        return value

    def _mkfiles(self):
        '''Creates the file, including all directories. If they exist, then this does nothing.'''
        if not self._pathpath.parent.exists():
            self._pathpath.parent.mkdir(parents=True, exist_ok=True)
        
        if not self._pathpath.exists():
            self._pathpath.touch()
            # need to initialize it with a empty data
            with tf.NamedTemporaryFile("w", delete=False, dir=self._project_root) as file:
                file.write("{}")

                os.replace(file.name, self.path)

            self.logger.info(f"JSON file did not exist, created JSON file: {self.path}")
        
    def _lower_keys(self, new_content: dict[str, Any] = None, content: dict[str, Any] = None):
        '''Recursively lowercases all the keys, if any are not lowercase. Used to normalize key usage.
        
        Parameters
        ----------
            new_content: dict[str, Any], default None
                The new lowercased content. This is expected to be an empty dictionary, which
                by default is None and handled in the method.

            content: dict[str, Any], default None
                The content read from the file. By default it is None, using the read file.
        '''
        if content is None:
            content = self._content
        if new_content is None:
            new_content = {}

        for key in content:
            content_val: Any = content[key]

            if isinstance(content_val, dict):
                content_val = self._lower_keys(None, content=content_val)

            new_content[key.lower()] = content_val
        
        return new_content
    
    def _validate_defaults(self, default_data: dict[str, Any]):
        '''Validates a JSON file for any incorrect values or missing keys from
        a given data dictionary. 

        If it is missing or it has an invalid value then it will correct the data.
        '''
        has_corrected: bool = False
        for d_key, d_value in default_data.items():
            exists: bool = d_key in self._content
            if not exists or not isinstance(self._content[d_key], type(d_value)):
                self._content[d_key] = d_value

                if not exists:
                    self.logger.warning(f"Missing default key {d_key}")
                    self.logger.info(f"Default key {d_key} added with value {d_value}")
                elif not isinstance(self._content[d_key], type(d_value)):
                    self.logger.info(f"Incorrect default key {d_key} value given")

                if not has_corrected: 
                    has_corrected = True
        
        if has_corrected:
            self.write(self._content)
    
    def _validate_unupdatable_defaults(self, reader_data: dict[str, Any], default_data: dict[str, Any]):
        '''Validates a JSON file that is not updatable, ensuring that the keys match
        the dictionary values given 1:1.
        
        Unlike validate_defaults, this removes all extra keys and resets values to defaults
        if any values are invalid. This does not check for missing default keys, in which case validate_defaults
        is used.

        It returns a new Reader dictionary data of corrected data, if any.
        '''
        new_data: dict[str, Any] = {}

        for key, val in reader_data.items():
            if key not in default_data:
                self.logger.info(f"Found invalid key {key}")

                self._update_reader_flag = True
                continue

            # the keys are guaranteed to exist here    
            if not isinstance(val, type(default_data[key])):
                self.logger.warning(f"Invalid key {key} found with invalid type {type(val)}, expected type: {type(default_data[key])}")

                new_data[key] = default_data[key]
                self.logger.info(f"Corrected key {key}")
            else:
                new_data[key] = val

            if isinstance(val, dict):
                temp_data: dict[str, Any] = self._validate_unupdatable_defaults(val, default_data[key])

                new_data[key] = temp_data
            
        return new_data
    
    def _update_only_check(self) -> dict[str, Any]:
        '''Checks if the Reader is update only before an insertion/deletion action.
        If it is a test instance then this does not apply.
        
        It returns a response of an error message if it fails.
        '''
        if self.update_only and not self._is_test:
            self.logger.info(f"Reader {self._name} attempted an insertion/deletion, it is not allowed")
            return utils.generate_response("error", message=f"Cannot insert or delete Reader {self._name}")
        
        return utils.generate_response(message="Can be updated")