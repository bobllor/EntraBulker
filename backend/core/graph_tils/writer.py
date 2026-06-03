from msal_extensions import build_encrypted_persistence, FilePersistence
from pathlib import Path
from typing import Any
from logger import Log

class TokenCacheWriter:
    '''Class used to handle reading and writing the Graph token cache.
    
    By default it is encrypted, but if encryption is unavailable it will default to
    plain text.
    '''
    def __init__(self, cache_root: Path, *, log: Log = None):
        self.cache_path: Path = cache_root / ".mscache.bin"
        self.log: Log = log or Log()

        self.persistence = None
        try:
            self.persistence = build_encrypted_persistence(self.cache_path)
        except:
            self.log.warning(f"Failed to build encrypted file, falling back to plain text")
            self.persistence = FilePersistence(self.cache_path)

    def save(self, content: Any):
        '''Writes the content to the file.'''
        self.log.info(f"Wrote to token cache {self.cache_path}")
        self.persistence.save(content)

    def load(self) -> str:
        '''Reads the data and returns the cache.'''
        data: str = "{}"

        try:
            data = self.persistence.load()
        except Exception as e:
            self.log.error(f"Failed to load cache data ({type(e).__name__}): {e}")

        return data
    
    def exists(self) -> bool:
        '''Checks if the cache exists.'''
        return self.cache_path.exists()