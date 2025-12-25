from pathlib import Path
from support.vars import PROJECT_ROOT
import http.server as http
import threading, os

class LocalServer:
    def __init__(self, index_dir: Path | str):
        '''Class for creating a local web server. It uses an ephemeral port by default.
        
        Parameters
        ----------
            index_dir: Path | str
                The StrPath to the directory holding the HTML file. The HTML file is
                expected to be an SPA.
        '''
        # is this allowed? only way i can think of due to parameter issues. it works, whatever.
        class Handler(http.SimpleHTTPRequestHandler):
            def __init__(self, *args):
                super().__init__(*args, directory=index_dir)

        self._server: http.HTTPServer = http.HTTPServer(("127.0.0.1", 0), Handler)

    def run(self) -> threading.Thread:
        '''Starts the web server on a non-blocking daemonic thread.
        
        This will return the Thread object used to start the thread.
        '''
        thread: threading.Thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        thread.start()

        return thread
    
    @property
    def url(self) -> str:
        '''The url to access the server via localhost.'''
        return "http://localhost" + f":{self.port}"
    
    @property
    def port(self) -> int:
        '''The server port of the web server.'''
        return self._server.server_port