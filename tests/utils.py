from pathlib import Path
from io import BytesIO
import random

def randomizer(_: str, *args) -> str:
    '''Chooses a random element from the given list and returns it.'''
    size: int = len(args)

    return args[random.randint(0, size - 1)]

def get_bytesio(path: Path | str) -> BytesIO:
    '''Reads from a file and return the bytes wrapped with BytesIO.'''
    with open(path, "r") as file:
        content: list[str] = file.readlines()

    # removing the row for parsing
    content = content[1:]
    csv_bytes: bytes = "".join(content).encode()

    return BytesIO(csv_bytes)

def get_csv(path: Path, *, drop_first_row: bool = False) -> Path | None:
    ext: str = ".csv"

    for file in path.iterdir():
        if file.suffix.lower() == ext:
            if drop_first_row:
                content: str = ""
                with open(file, "r") as f:
                    f.readline()
                    content = f.read()
                with open(file, "w") as f:
                    f.write(content) 

            return file
    
    return None