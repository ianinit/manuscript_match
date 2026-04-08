import sys
from pathlib import Path

# Add the project root to sys.path to allow imports from core and ui
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from ui.app import run_app

if __name__ == "__main__":
    run_app()
