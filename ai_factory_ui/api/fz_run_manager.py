"""Run ai_factory_fz (agentic_sdlc) from the FastAPI console with UI-compatible state."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from config import AI_FACTORY_FZ_ROOT, ARTIFACTS_DIR, FZ_RUNS_DIR, RUN_STATE_PATH
from fz_bridge import COMPLEXITY_MINUTES, log_fz_audit, publish_fz_run_state

WORKER_INFO_PATH = ARTIFACTS_DIR / "fz_worker.json"
FZ_PYTHON = AI_FACTORY_FZ_ROOT / ".venv" / "Scripts" / "python.exe"
FZ_WORKER_SCRIPT = Path(__file__).resolve().parent / "fz_worker.py"


def _ensure_fz_env() -> None:
    load_dotenv(AI_FACTORY_FZ_ROOT / ".env", override=True)
    os.environ["SDLC_HOME"] = str(AI_FACTORY_FZ_ROOT)
    os.environ.setdefault("SDLC_GATE_MODE", "auto")

    provider = os.getenv("LLM_PROVIDER", "cursor_cli").strip().lower() or "cursor_cli"
    if provider in ("cursor_cli", "cursor_proxy"):
        if provider == "cursor_proxy" and not os.getenv("CURSOR_API_KEY", "").strip():
            raise RuntimeError(
                "CURSOR_API_KEY is missing in ai_factory_fz/.env — required for LLM_PROVIDER=cursor_proxy."
            )
        return

    claude_code = os.getenv("CLAUDE_CODE_ENABLE", "false").strip().lower() == "true"
    if claude_code:
        if not os.getenv("CLAUDE_CODE_OAUTH_TOKEN", "").strip():
            raise RuntimeError(
                "CLAUDE_CODE_OAUTH_TOKEN is missing in ai_factory_fz/.env — run `claude setup-token`."
            )
    elif not os.getenv("ANTHROPIC_API_KEY", "").strip():
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing in ai_factory_fz/.env — add your Claude API key, "
            "or set LLM_PROVIDER=cursor_cli for development."
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


def resolve_pipeline_name() -> str:
    """Pipeline config stem under ai_factory_fz/config/ (e.g. pipeline.client)."""
    raw = os.environ.get("SDLC_PIPELINE", "pipeline.ui").strip()
    if raw.endswith(".yaml"):
        raw = raw[:-5]
    path = AI_FACTORY_FZ_ROOT / "config" / f"{raw}.yaml"
    if not path.is_file():
        return "pipeline.ui"
    return raw


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
    if _list_fz_worker_processes():
        return True
    info = read_worker_info()
    if info and _pid_alive(int(info.get("pid", 0))):
        return True
    return False


def _terminate_pid_tree(pid: int) -> None:
    if pid <= 0:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        )
        return
    try:
        os.kill(pid, 15)
    except OSError:
        pass


def _parse_run_id_from_cmdline(cmdline: str) -> str | None:
    if not cmdline:
        return None
    match = re.search(r'run_id["\\]*\s*:\s*["\\]*([0-9]{8}-[0-9]{6})', cmdline)
    if match:
        return match.group(1)
    match = re.search(r'"run_id"\s*:\s*"([^"]+)"', cmdline)
    return match.group(1).strip() if match else None


def _list_fz_worker_processes() -> list[tuple[int, str | None]]:
    """Return (pid, run_id) for each live fz_worker.py process."""
    rows: list[tuple[int, str | None]] = []
    if sys.platform == "win32":
        try:
            ps = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { $_.CommandLine -and ($_.CommandLine -match 'fz_worker\\.py') } | "
                    "Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            raw = (ps.stdout or "").strip()
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict):
                    data = [data]
                for row in data:
                    try:
                        pid = int(row.get("ProcessId", 0))
                    except (TypeError, ValueError):
                        continue
                    if pid > 0:
                        rows.append((pid, _parse_run_id_from_cmdline(str(row.get("CommandLine") or ""))))
        except Exception:
            pass
    else:
        try:
            out = subprocess.run(
                ["pgrep", "-af", "fz_worker.py"],
                capture_output=True,
                text=True,
                check=False,
            )
            for line in (out.stdout or "").splitlines():
                parts = line.strip().split(None, 1)
                if not parts:
                    continue
                try:
                    pid = int(parts[0])
                except ValueError:
                    continue
                cmd = parts[1] if len(parts) > 1 else ""
                rows.append((pid, _parse_run_id_from_cmdline(cmd)))
        except Exception:
            pass
    return rows


def _iter_fz_worker_pids() -> list[int]:
    """Find live fz_worker.py process IDs (Windows + Unix)."""
    pids = [pid for pid, _ in _list_fz_worker_processes()]
    info = read_worker_info()
    if info:
        try:
            pid = int(info.get("pid", 0))
            if pid > 0 and _pid_alive(pid):
                pids.append(pid)
        except (TypeError, ValueError):
            pass
    return sorted(set(pids), reverse=True)


def _worker_pids_for_run(run_id: str) -> list[int]:
    rid = run_id.strip()
    return [pid for pid, proc_run in _list_fz_worker_processes() if proc_run == rid]


def _terminate_fz_worker_pids(pids: list[int]) -> None:
    import run_manager as rm

    for pid in sorted(set(pids), reverse=True):
        _terminate_pid_tree(pid)
    proc = rm._active_process
    if proc is not None and proc.poll() is None and proc.pid in pids:
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
        if rm._active_process is proc:
            rm._active_process = None
    _clear_worker_info()


def reconcile_fz_run_state() -> None:
    """Sync UI + fz workspace when workers are gone but state still says running."""
    import run_manager as rm

    alive_runs = {rid for _, rid in _list_fz_worker_processes() if rid}
    ui = rm._read_run_state() or {}
    ui_run = str(ui.get("run_id") or "")
    if ui.get("factory_engine") == "fz" and ui.get("status") == "running" and ui_run:
        if ui_run not in alive_runs:
            rm._reconcile_stale_run()
    if not FZ_RUNS_DIR.is_dir():
        return
    for run_dir in FZ_RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue
        state_path = run_dir / "state.json"
        if not state_path.is_file():
            continue
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("status") != "running":
            continue
        rid = str(data.get("run_id") or run_dir.name)
        if rid in alive_runs:
            continue
        data["status"] = "stopped"
        data["stop_reason"] = data.get("stop_reason") or "Worker stopped (orphaned or crashed)."
        state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if ui_run == rid and ui.get("status") == "running":
            rm._write_failed_state(data["stop_reason"])


def terminate_fz_workers(reason: str = "Superseded by a new run") -> list[str]:
    """Kill all fz worker process trees and mark their runs stopped. Returns stopped run ids."""
    import run_manager as rm
    from config import FZ_RUNS_DIR

    stopped: list[str] = []
    info = read_worker_info() or {}
    known_run = str(info.get("run_id") or "")
    state = rm._read_run_state() or {}
    state_run = str(state.get("run_id") or "")

    proc = rm._active_process
    if proc is not None and proc.poll() is None:
        _terminate_pid_tree(proc.pid)
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
        if rm._active_process is proc:
            rm._active_process = None

    for pid in _iter_fz_worker_pids():
        _terminate_pid_tree(pid)

    for run_id in {known_run, state_run} - {""}:
        fz_state_path = FZ_RUNS_DIR / run_id / "state.json"
        if not fz_state_path.is_file():
            continue
        try:
            data = json.loads(fz_state_path.read_text(encoding="utf-8"))
            if data.get("status") in ("completed", "failed", "stopped"):
                continue
            data["status"] = "stopped"
            data["stop_reason"] = reason
            fz_state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            stopped.append(run_id)
        except (json.JSONDecodeError, OSError):
            pass

    _clear_worker_info()
    return stopped


def _worker_env() -> dict[str, str]:
    env = os.environ.copy()
    env["SDLC_HOME"] = str(AI_FACTORY_FZ_ROOT)
    env.setdefault("SDLC_GATE_MODE", "auto")
    env.setdefault("SDLC_SANDBOX", "local")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    env.setdefault("GCM_INTERACTIVE", "never")
    env.setdefault("GIT_OPTIONAL_LOCKS", "0")
    env["AI_FACTORY_FZ_ROOT"] = str(AI_FACTORY_FZ_ROOT)
    load_dotenv(AI_FACTORY_FZ_ROOT / ".env", override=True)
    for key in (
        "LLM_PROVIDER",
        "CURSOR_API_KEY",
        "CURSOR_PROXY_MODEL",
        "CURSOR_PROXY_BASE_URL",
        "CURSOR_AGENT_CWD",
        "CURSOR_AGENT_TIMEOUT",
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_ENABLE",
        "SDLC_SANDBOX",
    ):
        val = os.getenv(key)
        if val is not None:
            env[key] = val
    sys.path.insert(0, str(AI_FACTORY_FZ_ROOT / "src"))
    from agentic_sdlc.env_toolchain import enrich_path

    enrich_path(env)
    return env


def _monitor_fz_process(proc: subprocess.Popen, run_id: str) -> None:
    import run_manager as rm

    try:
        proc.wait()
        if proc.returncode != 0:
            state = rm._read_run_state() or {}
            msg = f"FZ worker exited with code {proc.returncode}."
            log_tail = ""
            info = read_worker_info()
            if info and info.get("log_path"):
                log_path = Path(info["log_path"])
                if log_path.is_file():
                    log_tail = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
            if log_tail:
                msg += f"\n\n{log_tail}"
            fz_path = FZ_RUNS_DIR / run_id / "state.json"
            if fz_path.is_file():
                try:
                    data = json.loads(fz_path.read_text(encoding="utf-8"))
                    if data.get("status") not in ("completed", "stopped", "failed"):
                        data["status"] = "stopped"
                        data["stop_reason"] = msg[:2000]
                        fz_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                except (json.JSONDecodeError, OSError):
                    pass
            if state.get("run_id") == run_id and state.get("status") == "running":
                rm._write_failed_state(msg)
                log_fz_audit(run_id, "run_failed", "failed", "console", {"exit_code": proc.returncode})
    finally:
        if rm._active_process is proc:
            rm._active_process = None
        _clear_worker_info()


def _live_worker_run_id() -> str | None:
    procs = _list_fz_worker_processes()
    if not procs and not worker_process_alive():
        return None
    run_ids = sorted({rid for _, rid in procs if rid})
    if len(run_ids) == 1:
        return run_ids[0]
    if len(run_ids) > 1:
        return run_ids[0]
    info = read_worker_info() or {}
    rid = str(info.get("run_id") or "").strip()
    if rid:
        return rid
    import run_manager as rm

    state = rm._read_run_state() or {}
    if state.get("status") == "running" and worker_process_alive():
        return str(state.get("run_id") or "") or None
    return None


def _resume_run_metadata(run_id: str) -> tuple[str, str, str]:
    """Return project_name, complexity, pipeline for an existing fz run."""
    from artifact_reader import get_run

    run = get_run(run_id)
    project_name = run_id
    complexity = "standard"
    pipeline = resolve_pipeline_name()
    if run:
        project_name = str(run.get("project_name") or project_name)
        complexity = str(run.get("complexity") or complexity)
    state_path = FZ_RUNS_DIR / run_id / "state.json"
    if state_path.is_file():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            pipeline = str(data.get("pipeline") or pipeline)
        except json.JSONDecodeError:
            pass
    return project_name, complexity, pipeline


def _spawn_fz_worker(payload: dict[str, Any], run_id: str, log_path: Path) -> subprocess.Popen[Any]:
    import run_manager as rm

    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.is_file() and log_path.stat().st_size > 0:
        with log_path.open("a", encoding="utf-8") as prev:
            prev.write(
                f"\n\n=== Worker session {datetime.now(timezone.utc).isoformat()} "
                f"resume={bool(payload.get('resume'))} ===\n\n"
            )
    log_mode = "a" if log_path.is_file() and log_path.stat().st_size > 0 else "w"
    with log_path.open(log_mode, encoding="utf-8") as log_handle:
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
    rm._active_thread = threading.Thread(
        target=_monitor_fz_process,
        args=(proc, run_id),
        name=f"ai-factory-fz-monitor-{run_id}",
        daemon=True,
    )
    rm._active_thread.start()
    return proc


def resume_fz_run_unlocked(run_id: str, *, force: bool = True) -> dict[str, Any]:
    """Continue an existing fz run. ``force`` replaces stuck workers for the same run_id."""
    import run_manager as rm

    reconcile_fz_run_state()

    if not FZ_PYTHON.is_file():
        raise RuntimeError(
            "ai_factory_fz venv not found. Run: cd ai_factory_fz && ..\\ai_factory\\.venv\\Scripts\\uv.exe sync"
        )
    if not FZ_WORKER_SCRIPT.is_file():
        raise RuntimeError(f"Missing worker script: {FZ_WORKER_SCRIPT}")

    state_path = FZ_RUNS_DIR / run_id / "state.json"
    if not state_path.is_file():
        raise RuntimeError(f"Run {run_id} not found under ai_factory_fz/runs/")

    live = _live_worker_run_id()
    if live and live != run_id:
        raise RuntimeError(f"RUN_IN_PROGRESS:{live}")

    existing = _worker_pids_for_run(run_id)
    if existing:
        if force:
            _terminate_fz_worker_pids(existing)
            time.sleep(1.5)
            reconcile_fz_run_state()
            existing = _worker_pids_for_run(run_id)
            if existing:
                _terminate_fz_worker_pids(existing)
                time.sleep(0.5)
        else:
            info = read_worker_info() or {}
            return {
                "run_id": run_id,
                "status": "already_running",
                "message": "This run is already in progress",
                "worker_pid": info.get("pid") or existing[0],
                "factory_engine": "fz",
            }

    _ensure_fz_env()
    project_name, complexity, pipeline = _resume_run_metadata(run_id)

    sys.path.insert(0, str(AI_FACTORY_FZ_ROOT / "src"))
    from agentic_sdlc.state import ProjectState

    state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
    state.status = "running"
    state.stop_reason = ""
    publish_fz_run_state(
        state,
        project_name=project_name,
        complexity=complexity,
        checkpoint_msg="Resuming run",
    )

    payload = {
        "run_id": run_id,
        "resume": True,
        "project_name": project_name,
        "complexity": complexity,
        "pipeline": pipeline,
    }

    log_dir = ARTIFACTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"fz_worker_{run_id}.log"
    proc = _spawn_fz_worker(payload, run_id, log_path)

    return {
        "run_id": run_id,
        "status": "resumed",
        "project_name": project_name,
        "complexity": complexity,
        "estimated_minutes": COMPLEXITY_MINUTES.get(complexity, 90),
        "factory_engine": "fz",
        "worker_pid": proc.pid,
    }


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
    pipeline = resolve_pipeline_name()
    payload = {
        "run_id": run_id,
        "project_name": project_name,
        "client_brief": client_brief,
        "complexity": complexity,
        "pipeline": pipeline,
    }

    log_dir = ARTIFACTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"fz_worker_{run_id}.log"
    proc = _spawn_fz_worker(payload, run_id, log_path)

    # Seed UI state immediately (worker process publishes checkpoints as it runs).
    brief = _resolve_brief(client_brief, project_name)
    sys.path.insert(0, str(AI_FACTORY_FZ_ROOT / "src"))
    from agentic_sdlc.state import ProjectState

    seed = ProjectState(
        run_id=run_id,
        profile="flutter_nestjs_ecommerce",
        pipeline=pipeline,
        brief=brief,
        status="running",
    )
    publish_fz_run_state(seed, project_name=project_name, complexity=complexity, checkpoint_msg="Starting worker")

    return {
        "run_id": run_id,
        "status": "started",
        "project_name": project_name,
        "complexity": complexity,
        "estimated_minutes": COMPLEXITY_MINUTES.get(complexity, 90),
        "factory_engine": "fz",
        "worker_pid": proc.pid,
    }
