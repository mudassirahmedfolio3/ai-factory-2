"""Run one ai_factory_fz SDLC flow in a standalone process (required for CrewAI asyncio).

Invoked by fz_run_manager:
  python fz_worker.py '<json payload>'
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any


def _bootstrap_paths() -> Path:
    api_dir = Path(__file__).resolve().parent
    root = api_dir.parents[1]
    fz_root = Path(os.environ.get("AI_FACTORY_FZ_ROOT", root / "ai_factory_fz")).resolve()
    os.environ["SDLC_HOME"] = str(fz_root)
    os.environ["PYTHONUTF8"] = "1"
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.path.insert(0, str(fz_root / "src"))
    sys.path.insert(0, str(api_dir))
    os.chdir(fz_root)
    return fz_root


def _publish_from_disk(run_id: str, project_name: str, complexity: str, checkpoint_msg: str = "") -> None:
    from agentic_sdlc.settings import RUNS_DIR
    from agentic_sdlc.state import ProjectState
    from fz_bridge import publish_fz_run_state

    state_path = RUNS_DIR / run_id / "state.json"
    if not state_path.is_file():
        return
    state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
    publish_fz_run_state(state, project_name=project_name, complexity=complexity, checkpoint_msg=checkpoint_msg)


def _watch_state(run_id: str, project_name: str, complexity: str, stop: threading.Event) -> None:
    last_mtime = 0.0
    last_heartbeat = 0.0
    while not stop.is_set():
        try:
            from agentic_sdlc.settings import RUNS_DIR

            state_path = RUNS_DIR / run_id / "state.json"
            now = time.time()
            if state_path.is_file():
                mtime = state_path.stat().st_mtime
                if mtime != last_mtime:
                    last_mtime = mtime
                    _publish_from_disk(run_id, project_name, complexity, checkpoint_msg="Checkpoint")
                elif now - last_heartbeat >= 120:
                    # Keep run_state.updated_at fresh during long agent steps (avoids false "stale").
                    last_heartbeat = now
                    _publish_from_disk(run_id, project_name, complexity, checkpoint_msg="Worker active")
        except Exception as exc:
            print(f"state watch error: {exc}", file=sys.stderr)
        stop.wait(2.0)


def main() -> int:
    from dotenv import load_dotenv

    from agentic_sdlc.flow import SDLCFlow
    from agentic_sdlc.state import ProjectState
    from fz_bridge import archive_fz_run, log_fz_audit, publish_fz_run_state
    from fz_run_manager import _ensure_fz_env, _resolve_brief, _resolve_milestones

    fz_root = _bootstrap_paths()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    load_dotenv(fz_root / ".env", override=True)
    _ensure_fz_env()
    from agentic_sdlc.env_toolchain import apply_toolchain_path

    apply_toolchain_path()

    if len(sys.argv) < 2:
        print("Usage: python fz_worker.py '<json>'", file=sys.stderr)
        return 2

    payload = json.loads(sys.argv[1])
    run_id = payload["run_id"]
    project_name = payload["project_name"]
    client_brief = payload.get("client_brief", "")
    complexity = payload.get("complexity", "standard")
    pipeline = (payload.get("pipeline") or os.environ.get("SDLC_PIPELINE", "pipeline.ui")).strip()
    if pipeline.endswith(".yaml"):
        pipeline = pipeline[:-5]

    milestones = _resolve_milestones(complexity)
    if milestones:
        os.environ["SDLC_BUILD_MILESTONES"] = milestones
    else:
        os.environ.pop("SDLC_BUILD_MILESTONES", None)

    brief = _resolve_brief(client_brief, project_name)
    profile = "flutter_nestjs_ecommerce"

    seed = ProjectState(
        run_id=run_id,
        profile=profile,
        pipeline=pipeline,
        brief=brief,
        status="running",
    )
    publish_fz_run_state(seed, project_name=project_name, complexity=complexity, checkpoint_msg="Queued")
    log_fz_audit(run_id, "run_started", "started", "console", {"complexity": complexity, "pipeline": pipeline})

    stop = threading.Event()
    watcher = threading.Thread(
        target=_watch_state,
        args=(run_id, project_name, complexity, stop),
        name=f"fz-state-watch-{run_id}",
        daemon=True,
    )
    watcher.start()

    try:
        # Must use plain SDLCFlow — subclassing breaks CrewAI flow method discovery.
        if payload.get("resume"):
            from agentic_sdlc.workspace import Workspace

            restore_json = Workspace.open(run_id).load_state_json()
            flow = SDLCFlow(restore_json=restore_json)
            flow.kickoff(inputs={"run_id": run_id})
        else:
            flow = SDLCFlow()
            flow.kickoff(inputs={"run_id": run_id, "profile": profile, "brief": brief, "pipeline": pipeline})

        publish_fz_run_state(flow.state, project_name=project_name, complexity=complexity, checkpoint_msg="Finished")
        archive_fz_run(flow.state, project_name, complexity)
        log_fz_audit(
            run_id,
            "run_finished",
            flow.state.status,
            "console",
            {"stop_reason": flow.state.stop_reason or None},
        )
        if flow.state.status == "completed":
            return 0
        return 1
    except Exception as exc:
        import run_manager as rm

        rm._write_failed_state(str(exc))
        log_fz_audit(run_id, "run_failed", "failed", "console", {"error": str(exc)})
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        stop.set()
        watcher.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
