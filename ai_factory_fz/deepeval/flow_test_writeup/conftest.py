import sys
from pathlib import Path

# common.py lives one folder up, next to pyproject.toml
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
