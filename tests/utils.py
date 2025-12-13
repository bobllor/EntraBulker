from pathlib import Path
from io import BytesIO
import random

def randomizer(_: str, *args) -> str:
    '''Chooses a random element from the given list and returns it.'''
    size: int = len(args)

    return args[random.randint(0, size - 1)]

def get_bytesio(path: Path | str) -> BytesIO:
    '''Reads from a CSV file and return the bytes wrapped with BytesIO.

    The first row automatically is dropped, this assumes the CSV file is the 
    Azure file.
    '''
    with open(path, "r") as file:
        content: list[str] = file.readlines()

    # removing the row for parsing
    content = content[1:]
    csv_bytes: bytes = "".join(content).encode()

    return BytesIO(csv_bytes)

def get_csv(path: Path, *, ignore_files: list[Path] = []) -> Path | None:
    ext: str = ".csv"

    ignore: set[str] = {file.name.lower() for file in ignore_files}

    for file in path.iterdir():
        if file.suffix.lower() == ext:
            if file.name.lower() not in ignore:
                return file
    
    return None

def get_paths(path: Path) -> list[str]:
    '''Traverses a given path and returns a list of absolute paths of all files
    in the given path.

    The first element in the list is the given path.
    '''
    data: list[str] = []

    for child in path.iterdir():
        data.append(str(child))

        if child.is_dir():
            temp_data: list[str] = get_paths(child)

            data.extend(temp_data)

    return data