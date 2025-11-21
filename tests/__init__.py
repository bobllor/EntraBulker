from pathlib import Path
import sys, os

backend_dir: str = "backend"

project_root: str = str(Path(__file__).parent.parent.absolute() / backend_dir)
sys.path.insert(0, project_root)