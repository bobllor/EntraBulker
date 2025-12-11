from logger import Log
from updater import Updater
from support.vars import PROJECT_ROOT
from pathlib import Path

class UpdaterAPI:
    def __init__(self, *, project_root: Path = PROJECT_ROOT, logger: Log = None):
        '''Updater API. Each method must be called manually in the front end.'''
        self.logger: Log = logger or Log()
        self.updater: Updater = Updater(project_root, logger=self.logger)