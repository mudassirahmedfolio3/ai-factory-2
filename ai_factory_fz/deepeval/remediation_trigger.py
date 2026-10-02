"""Start the remediation process when a DeepEval report has been written (opt-in: DEEPEVAL_REMEDIATE=1)."""

import os
import subprocess
from pathlib import Path

FZ_ROOT = Path(__file__).resolve().parent.parent
WINDOWS_FLAGS = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW) if os.name == "nt" else 0


def maybe_start(run_dir: Path, report_json: Path) -> Path | None:
    """Launch `uv run remediate run` in the background. Returns the log path, or None when disabled or the launch
    failed. Never raises: remediation must not break the evaluation session."""
    if os.environ.get("DEEPEVAL_REMEDIATE") != "1":
        return None
    try:
        run_dir = Path(run_dir).resolve()
        log = run_dir / "remediation" / "trigger.log"
        cmd = ["uv", "run", "python", str(Path(__file__).resolve().parent / "remediate.py"), "run", "--run-dir", str(run_dir), "--report", str(Path(report_json).resolve())]
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("ab") as out:
            subprocess.Popen(cmd, cwd=FZ_ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             creationflags=WINDOWS_FLAGS, start_new_session=(os.name != "nt"))
        return log
    except Exception:  # noqa: BLE001 - never let the trigger fail the test session
        return None
