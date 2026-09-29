"""Project paths and YAML loading."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# <project>/src/agentic_sdlc/settings.py -> <project>
PROJECT_ROOT = Path(os.environ.get("SDLC_HOME", Path(__file__).resolve().parents[2]))
CONFIG_DIR = PROJECT_ROOT / "config"
PROFILES_DIR = PROJECT_ROOT / "profiles"
RUNS_DIR = Path(os.environ.get("SDLC_RUNS_DIR", PROJECT_ROOT / "runs"))

# Load <project>/.env whatever the working directory. Real environment variables win.
load_dotenv(PROJECT_ROOT / ".env", override=False)


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_config(name: str, config_dir: Path | None = None) -> dict[str, Any]:
    return load_yaml((config_dir or CONFIG_DIR) / f"{name}.yaml")
