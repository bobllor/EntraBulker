from logging import Logger, DEBUG, Formatter, StreamHandler, FileHandler, Handler, setLoggerClass
from datetime import datetime
from typing import TypedDict, Literal, TextIO
from pathlib import Path
import sys

# this value will be the same as soon as the server is launched.
# this keeps all logs in one day on the same day.
DEFAULT_FILENAME: str = datetime.now().strftime("%Y-%m-%d.log")
DEFAULT_DATEFMT: str = "%Y-%m-%d %H:%M:%S"

class LogLevelOptions(TypedDict):
    log_level: str | int
    stream_level: str | int
    file_level: str | int

class Log(Logger):
    def __init__(self, 
    name: str = __name__,
    *, 
    log_dir: Path | str = None,
    levels: LogLevelOptions = {},
    stream: TextIO = sys.stdout,
    file_name: str = None,
    logfmt: str = "%(asctime)s:%(filename)s:%(name)s [%(levelname)s] %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S"):
        '''Create a new logging instance.
        
        Parameters
        ----------
            name: str default __name__
                The name of the logger. By default, it uses the __name__ variable, or
                in other words __main__.
            
            log_path: Path | str, default None
                The path to the log directory. By default it is None, meaning it will not write a log file.
                If a path is given, then the output of the log file will be to the given directory.
            
            levels: LogLevelOptions default {}
                A dictionary that holds the logging levels of the logger, stream handler, and file handler.
                The keys are "log_level", "stream_level", and "file_level". By default **all levels are debug**.
            
            stream: TextIO default sys.stdout
                The stream output of the StreamHandler. By default it prints out to the console, sys.stdout.
            
            file_name: str, default None
                The file name of the log. By default it is None and will use an attached date formatted as 
                `%Y-%m-%d.log`.
            
            logfmt: str default TIME FILENAME LOGNAME [LEVEL] MESSAGE
                The format of the log message.
        
            datefmt: str default YY-MM-DD HH-MM-SS
                The format for the date of the log.
        '''
        super().__init__(name)

        stream_handler: StreamHandler = StreamHandler(stream)
        file_handler: FileHandler = None
        formatter: Formatter = Formatter(fmt=logfmt, datefmt=datefmt)
        if file_name is None:
            file_name = DEFAULT_FILENAME
        else:
            file_name = datetime.now().strftime(file_name)

        if log_dir is not None:
            new_log_dir: Path = Path("")
            if isinstance(log_dir, str):
                new_log_dir = Path(log_dir)
            elif isinstance(log_dir, Path):
                new_log_dir = log_dir
            
            if not new_log_dir.exists():
                new_log_dir.mkdir(parents=True, exist_ok=True)

            log_file: Path = new_log_dir / file_name
            file_handler = FileHandler(log_file)

        handlers: list[tuple[str, Handler]] = [
            ("stream_level", stream_handler)
        ]
        if file_handler is not None:
            handlers.append(("file_level", file_handler))

        for level_key, hdlr in handlers:
            hdlr.setFormatter(formatter)
            hdlr.setLevel(levels.get(level_key, DEBUG))

            self.addHandler(hdlr)

        self.setLevel(levels.get("log_level", DEBUG))
    
    def set_logger(self) -> None:
        '''Sets the Log for the logger class for module-level use.'''
        setLoggerClass(Log) 