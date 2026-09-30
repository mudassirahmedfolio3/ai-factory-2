from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

API_DIR = Path(__file__).resolve().parent
ROOT = API_DIR.parents[1]
load_dotenv(API_DIR / ".env", override=False)
AI_FACTORY_ROOT = Path(os.getenv("AI_FACTORY_ROOT", ROOT / "ai_factory")).resolve()
AI_FACTORY_FZ_ROOT = Path(os.getenv("AI_FACTORY_FZ_ROOT", ROOT / "ai_factory_fz")).resolve()
# integrated_ai_factory branch defaults to agentic_sdlc; set FACTORY_ENGINE=legacy for ai_factory.
FACTORY_ENGINE = os.getenv("FACTORY_ENGINE", "fz").strip().lower()
FZ_RUNS_DIR = Path(os.getenv("SDLC_RUNS_DIR", AI_FACTORY_FZ_ROOT / "runs")).resolve()
ARTIFACTS_DIR = AI_FACTORY_ROOT / "artifacts"
AUDIT_DIR = ARTIFACTS_DIR / "audit"
RUNS_DIR = ARTIFACTS_DIR / "runs"
RUN_STATE_PATH = ARTIFACTS_DIR / "run_state.json"
