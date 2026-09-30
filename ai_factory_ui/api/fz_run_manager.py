"""Run ai_factory_fz (agentic_sdlc) from the FastAPI console with UI-compatible state."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from config import AI_FACTORY_FZ_ROOT, ARTIFACTS_DIR, RUN_STATE_PATH
from fz_bridge import COMPLEXITY_MINUTES, log_fz_audit, publish_fz_run_state

WORKER_INFO_PATH = ARTIFACTS_DIR / "fz_worker.json"
FZ_PYTHON = AI_FACTORY_FZ_ROOT / ".venv" / "Scripts" / "python.exe"
FZ_WORKER_SCRIPT = Path(__file__).resolve().parent / "fz_worker.py"


def _ensure_fz_env() -> None:
    load_dotenv(AI_FACTORY_FZ_ROOT / ".env", override=True)
    os.environ["SDLC_HOME"] = str(AI_FACTORY_FZ_ROOT)
    os.environ.setdefault("SDLC_GATE_MODE", "auto")

    claude_code = os.getenv("CLAUDE_CODE_ENABLE", "false").strip().lower() == "true"
    if claude_code:
        if not os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip():
            raise RuntimeError(
                "CLAUDE_CODE_OAUTH_TOKEN is missing in ai_factory_fz/.env — run `claude setup-token`."
            )
    elif not os.getenv("ANTHROPIC_API_KEY", "").strip():
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing in ai_factory_fz/.env — add your Claude API key."
        )


def _resolve_brief(client_brief: str, project_name: str) -> str:
    if client_brief.strip():
        title = project_name.strip() or "App"
        return f"# {title}\n\n{client_brief.strip()}"
    default = AI_FACTORY_FZ_ROOT / "briefs" / "ecommerce_mvp.md"
    if default.is_file():
        return default.read_text(encoding="utf-8")
    return f"Build a Flutter + NestJS ecommerce mobile app named {project_name}."


def _resolve_milestones(complexity: str) -> str | None:
    if complexity == "basic":
        return "M1"
    if complexity == "basic_plus":
        return "M1,M2"
    return None


def _write_worker_info(run_id: str, pid: int, log_path: Path) -> None:
    WORKER_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKER_INFO_PATH.write_text(
        json.dumps({"run_id": run_id, "pid": pid, "log_path": str(log_path)}),
        encoding="utf-8",
    )


def _clear_worker_info() -> None:
    if WORKER_INFO_PATH.exists():
        WORKER_INFO_PATH.unlink()


def read_worker_info() -> dict[str, Any] | None:
    if not WORKER_INFO_PATH.exists():
        return None
    try:
        return json.loads(WORKER_INFO_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def worker_process_alive() -> bool:
    import run_manager as rm

    if rm._active_process is not None and rm._active_process.poll() is None:
        return True
    info = read_worker_info()
    if info and _pid_alive(int(info.get("pid", 0))):
        return True
    return False


def _worker_env() -> dict[str, str]:
    env = os.environ.copy()
    env["SDLC_HOME"] = str(AI_FACTORY_FZ_ROOT)
    env.setdefault("SDLC_GATE_MODE", "auto")
    env.setdefault("SDLC_SANDBOX", "local")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    env.setdefault("GCM_INTERACTIVE", "never")
    env.setdefault("GIT_OPTIONAL_LOCKS", "0")
    env["AI_FACTORY_FZ_ROOT"] = str(AI_FACTORY_FZ_ROOT)
    load_dotenv(AI_FACTORY_FZ_ROOT / ".env", override=True)
    for key in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_ENABLE", "SDLC_SANDBOX"):
        val = os.getenv(key)
        if val is not None:
            env[key] = val
    repo_root = AI_FACTORY_FZ_ROOT.parent
    flutter_bin = repo_root / ".tools" / "flutter" / "bin"
    if flutter_bin.is_dir():
        env["PATH"] = str(flutter_bin) + os.pathsep + env.get("PATH", "")
    return env


def _monitor_fz_process(proc: subprocess.Popen, run_id: str) -> None:
    import run_manager as rm

    try:
        proc.wait()
        if proc.returncode != 0:
            state = rm._read_run_state() or {}
            if state.get("run_id") == run_id and state.get("status") == "running":
                log_tail = ""
                info = read_worker_info()
                if info and info.get("log_path"):
                    log_path = Path(info["log_path"])
                    if log_path.is_file():
                        log_tail = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
                rm._write_failed_state(
                    f"FZ worker exited with code {proc.returncode}."
                    + (f"\n\n{log_tail}" if log_tail else "")
                )
                log_fz_audit(run_id, "run_failed", "failed", "console", {"exit_code": proc.returncode})
    finally:
        if rm._active_process is proc:
            rm._active_process = None
        _clear_worker_info()


def start_fz_run_unlocked(
    project_name: str = "ecommerce-flutter-app",
    client_brief: str = "",
    complexity: str = "standard",
    max_releases: int | None = None,  # noqa: ARG001 — kept for API parity
    autonomy_level: str = "L2",  # noqa: ARG001
    deploy_environment: str = "staging",  # noqa: ARG001
) -> dict[str, Any]:
    """Start an fz run. Caller must already hold run_manager._lock."""
    import run_manager as rm

    if not FZ_PYTHON.is_file():
        raise RuntimeError(
            "ai_factory_fz venv not found. Run: cd ai_factory_fz && ..\\ai_factory\\.venv\\Scripts\\uv.exe sync"
        )
    if not FZ_WORKER_SCRIPT.is_file():
        raise RuntimeError(f"Missing worker script: {FZ_WORKER_SCRIPT}")

    _ensure_fz_env()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    payload = {
        "run_id": run_id,
        "project_name": project_name,
        "client_brief": client_brief,
        "complexity": complexity,
    }

    log_dir = ARTIFACTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"fz_worker_{run_id}.log"

    with log_path.open("w", encoding="utf-8") as log_handle:
        proc = subprocess.Popen(
            [str(FZ_PYTHON), str(FZ_WORKER_SCRIPT), json.dumps(payload)],
            cwd=str(AI_FACTORY_FZ_ROOT),
            env=_worker_env(),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )

    rm._active_process = proc
    _write_worker_info(run_id, proc.pid, log_path)

    # Seed UI state immediately (worker process publishes checkpoints as it runs).
    brief = _resolve_brief(client_brief, project_name)
    sys.path.insert(0, str(AI_FACTORY_FZ_ROOT / "src"))
    from agentic_sdlc.state import ProjectState

    seed = ProjectState(
        run_id=run_id,
        profile="flutter_nestjs_ecommerce",
        pipeline="pipeline.ui",
        brief=brief,
        status="running",
    )
    publish_fz_run_state(seed, project_name=project_name, complexity=complexity, checkpoint_msg="Starting worker")

    rm._active_thread = threading.Thread(
        target=_monitor_fz_process,
        args=(proc, run_id),
        name=f"ai-factory-fz-monitor-{run_id}",
        daemon=True,
    )
    rm._active_thread.start()

    return {
        "run_id": run_id,
        "status": "started",
        "project_name": project_name,
        "complexity": complexity,
        "estimated_minutes": COMPLEXITY_MINUTES.get(complexity, 90),
        "factory_engine": "fz",
        "worker_pid": proc.pid,
    }
