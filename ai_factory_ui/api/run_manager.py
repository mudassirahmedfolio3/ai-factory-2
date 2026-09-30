from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from config import AI_FACTORY_ROOT, FACTORY_ENGINE, RUN_STATE_PATH


def _ensure_factory_env() -> None:
    load_dotenv(AI_FACTORY_ROOT / ".env", override=True)
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider == "groq" and not os.getenv("GROQ_API_KEY", "").strip():
        raise RuntimeError(
            "GROQ_API_KEY is missing in ai_factory/.env — add your key and save the file (Ctrl+S)."
        )
    if provider == "openai" and not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY is missing in ai_factory/.env")
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY", "").strip():
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing in ai_factory/.env — add your Claude key and restart the API."
        )
    api_key = os.getenv("CURSOR_API_KEY", "").strip()
    if provider == "cursor_proxy" and not api_key:
        raise RuntimeError(
            "CURSOR_API_KEY is missing in ai_factory/.env — add your key from "
            "https://cursor.com/dashboard/integrations"
        )
    if provider == "cursor_cli":
        agent_cli = shutil.which("agent") or shutil.which("agent.cmd")
        local_agent = Path.home() / "AppData" / "Local" / "cursor-agent" / "agent.cmd"
        if not agent_cli and not local_agent.exists() and not api_key:
            raise RuntimeError(
                "Cursor CLI (agent) is required when LLM_PROVIDER=cursor_cli. "
                "Install: irm 'https://cursor.com/install?win32=true' | iex — "
                "or run `agent login` / set CURSOR_API_KEY in ai_factory/.env"
            )

_lock = threading.Lock()
_active_thread: threading.Thread | None = None
_active_process: subprocess.Popen | None = None


def _worker_alive() -> bool:
    if FACTORY_ENGINE == "fz":
        from fz_run_manager import worker_process_alive

        return worker_process_alive()
    return bool(_active_thread and _active_thread.is_alive())


def is_running() -> bool:
    state = _read_run_state()
    return bool(state and state.get("status") == "running" and _worker_alive())


def _recover_orphaned_complete_run() -> bool:
    """Promote finished runs that never reached finalize_project to completed."""
    state = _read_run_state()
    if not state or state.get("status") != "running":
        return False
    if _worker_alive():
        return False
    if state.get("factory_engine") == "fz":
        from config import FZ_RUNS_DIR

        run_id = state.get("run_id", "")
        fz_state_path = FZ_RUNS_DIR / run_id / "state.json"
        if fz_state_path.is_file():
            fz = json.loads(fz_state_path.read_text(encoding="utf-8"))
            if fz.get("status") != "completed":
                return False
        else:
            return False
    else:
        checks = state.get("checks") or {}
        approvals = state.get("approvals") or {}
        if not (
            checks.get("post_deploy_passed")
            and approvals.get("release") == "approved"
        ):
            return False
    state["status"] = "completed"
    state["phase"] = "complete"
    for step in state.get("pipeline_steps", []):
        step["status"] = "completed"
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state.pop("error", None)
    RUN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return True


def _reconcile_stale_run() -> None:
    """If run_state says running but no worker thread, recover or mark stale."""
    state = _read_run_state()
    if not state or state.get("status") != "running":
        return
    if _worker_alive():
        return
    if _recover_orphaned_complete_run():
        return
    state = _read_run_state() or state
    state["status"] = "stale"
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["error"] = state.get("error") or "Run interrupted (API restarted or worker stopped)."
    RUN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def reconcile_run_state() -> None:
    """Recover completed or stale runs before serving API state."""
    _recover_orphaned_complete_run()
    _reconcile_stale_run()


def current_live_run_id() -> str | None:
    state = _read_run_state()
    if state and state.get("status") == "running" and is_running():
        return state.get("run_id")
    return None


def _read_run_state() -> dict[str, Any] | None:
    if not RUN_STATE_PATH.exists():
        return None
    return json.loads(RUN_STATE_PATH.read_text(encoding="utf-8"))


def _write_failed_state(message: str) -> None:
    state = _read_run_state() or {}
    state["status"] = "failed"
    state["phase"] = state.get("phase", "kickoff")
    state["error"] = message
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    RUN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _run_flow(inputs: dict[str, Any]) -> None:
    original_cwd = os.getcwd()
    try:
        os.chdir(AI_FACTORY_ROOT)
        sys.path.insert(0, str(AI_FACTORY_ROOT / "src"))

        load_dotenv(AI_FACTORY_ROOT / ".env", override=True)

        # Force fresh ai_factory imports (uvicorn --reload only watches api/)
        for mod in list(sys.modules):
            if mod == "ai_factory" or mod.startswith("ai_factory."):
                del sys.modules[mod]

        from ai_factory.main import CHECKPOINT, AIFactoryFlow

        flow = AIFactoryFlow(checkpoint=CHECKPOINT)
        flow.kickoff(inputs=inputs)
    except Exception as exc:
        _write_failed_state(str(exc))
        raise
    finally:
        os.chdir(original_cwd)


def start_run(
    project_name: str = "ecommerce-flutter-app",
    client_brief: str = "",
    complexity: str = "standard",
    max_releases: int | None = None,
    autonomy_level: str = "L2",
    deploy_environment: str = "staging",
) -> dict[str, Any]:
    global _active_thread

    with _lock:
        _reconcile_stale_run()
        if is_running():
            run_id = (_read_run_state() or {}).get("run_id", "")
            raise RuntimeError(f"RUN_IN_PROGRESS:{run_id}")

        if FACTORY_ENGINE == "fz":
            from fz_run_manager import start_fz_run_unlocked

            return start_fz_run_unlocked(
                project_name=project_name,
                client_brief=client_brief,
                complexity=complexity,
                max_releases=max_releases,
                autonomy_level=autonomy_level,
                deploy_environment=deploy_environment,
            )

        _ensure_factory_env()

        sys.path.insert(0, str(AI_FACTORY_ROOT / "src"))
        from ai_factory.complexity import get_profile

        profile = get_profile(complexity)
        resolved_releases = max_releases if max_releases is not None else profile.max_releases

        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        inputs = {
            "project_name": project_name,
            "client_brief": client_brief,
            "complexity": profile.id,
            "max_releases": resolved_releases,
            "autonomy_level": autonomy_level,
            "deploy_environment": deploy_environment,
            "run_id": run_id,
            "run_status": "running",
        }

        _active_thread = threading.Thread(
            target=_run_flow,
            args=(inputs,),
            name=f"ai-factory-{run_id}",
            daemon=True,
        )
        _active_thread.start()

        return {
            "run_id": run_id,
            "status": "started",
            "project_name": project_name,
            "complexity": profile.id,
            "estimated_minutes": profile.estimated_minutes,
        }
