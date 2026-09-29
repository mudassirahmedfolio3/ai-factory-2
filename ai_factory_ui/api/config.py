from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AI_FACTORY_ROOT = Path(os.getenv("AI_FACTORY_ROOT", ROOT / "ai_factory")).resolve()
ARTIFACTS_DIR = AI_FACTORY_ROOT / "artifacts"
AUDIT_DIR = ARTIFACTS_DIR / "audit"
RUNS_DIR = ARTIFACTS_DIR / "runs"
RUN_STATE_PATH = ARTIFACTS_DIR / "run_state.json"
