from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import ARTIFACTS_DIR, AUDIT_DIR, FZ_RUNS_DIR, RUNS_DIR, RUN_STATE_PATH

STALE_RUN_MINUTES = 30


def _normalize_run_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mark abandoned 'running' snapshots as stale so the UI does not look stuck."""
    if not state or state.get("status") != "running":
        return state
    updated = state.get("updated_at", "")
    try:
        ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60
        if age_min > STALE_RUN_MINUTES:
            state = {**state, "status": "stale", "is_live": False}
    except (ValueError, TypeError):
        pass
    return state


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_current_run_state() -> dict[str, Any] | None:
    return _normalize_run_state(read_json(RUN_STATE_PATH))


def list_runs() -> list[dict[str, Any]]:
    from fz_emulator import flutter_project_ready

    runs: list[dict[str, Any]] = []
    current = get_current_run_state()
    if current and current.get("status") == "running":
        runs.append({**current, "is_live": True})

    if RUNS_DIR.exists():
        for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            snap = read_json(run_dir / "snapshot.json")
            if snap:
                snap["is_live"] = False
                state = read_json(run_dir / "run_state.json") or {}
                usage = state.get("usage")
                if not usage or not usage.get("activities"):
                    rebuilt = _usage_from_fz_state(run_dir.name)
                    if rebuilt:
                        usage = rebuilt
                if usage:
                    snap["usage"] = usage
                runs.append(snap)

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for run in runs:
        rid = run.get("run_id", "")
        if rid and rid in seen:
            continue
        if rid:
            seen.add(rid)
        unique.append({**run, "flutter_ready": flutter_project_ready(rid, run)})
    return unique


def get_run(run_id: str) -> dict[str, Any] | None:
    from fz_emulator import flutter_project_ready

    current = get_current_run_state()
    if current and current.get("run_id") == run_id:
        return {
            **current,
            "is_live": current.get("status") == "running",
            "flutter_ready": flutter_project_ready(run_id, current),
        }

    archived = read_json(RUNS_DIR / run_id / "snapshot.json")
    if archived:
        state = read_json(RUNS_DIR / run_id / "run_state.json") or {}
        # Full run_state (usage, checks, …) with snapshot metadata on top for status/labels.
        payload = {
            **state,
            **archived,
            "is_live": False,
        }
        if state.get("usage"):
            payload["usage"] = state["usage"]
        usage = payload.get("usage") or {}
        # Older archives may have totals but no per-agent activity rows — rebuild from fz state.
        if not usage.get("activities"):
            rebuilt = _usage_from_fz_state(run_id)
            if rebuilt:
                payload["usage"] = rebuilt
        if state.get("pipeline_steps") and not payload.get("pipeline_steps"):
            payload["pipeline_steps"] = state["pipeline_steps"]
        if state.get("checks") and not payload.get("checks"):
            payload["checks"] = state["checks"]
        if state.get("approvals") and not payload.get("approvals"):
            payload["approvals"] = state["approvals"]
        if state.get("error") and not payload.get("error"):
            payload["error"] = state["error"]
        if not payload.get("artifacts_index"):
            payload["artifacts_index"] = state.get("artifacts_index") or _list_archived_artifacts(run_id)
        payload["flutter_ready"] = flutter_project_ready(run_id, payload)
        return payload

    # Live fz workspace still on disk (e.g. failed before archive).
    live_fz = _run_state_from_fz_workspace(run_id)
    if live_fz:
        live_fz["flutter_ready"] = flutter_project_ready(run_id, live_fz)
        return live_fz

    if flutter_project_ready(run_id):
        return {
            "run_id": run_id,
            "project_name": run_id,
            "status": "completed",
            "phase": "complete",
            "is_live": False,
            "flutter_ready": True,
            "pipeline_steps": [],
        }
    return None


def _ensure_fz_pythonpath() -> None:
    import sys

    from config import AI_FACTORY_FZ_ROOT

    src = str(AI_FACTORY_FZ_ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _usage_from_fz_state(run_id: str) -> dict[str, Any] | None:
    """Rebuild usage payload from agentic_sdlc state.json when UI archive lacks it."""
    state_path = FZ_RUNS_DIR / run_id / "state.json"
    archived_state = RUNS_DIR / run_id / "fz_workspace" / "state.json"
    path = state_path if state_path.is_file() else archived_state
    if not path.is_file():
        return None
    try:
        _ensure_fz_pythonpath()
        from agentic_sdlc.state import ProjectState
        from fz_bridge import _usage_payload

        state = ProjectState.model_validate_json(path.read_text(encoding="utf-8"))
        return _usage_payload(state)
    except Exception:
        return None


def _run_state_from_fz_workspace(run_id: str) -> dict[str, Any] | None:
    state_path = FZ_RUNS_DIR / run_id / "state.json"
    if not state_path.is_file():
        return None
    try:
        _ensure_fz_pythonpath()
        from agentic_sdlc.state import ProjectState
        from fz_bridge import _usage_payload, infer_ui_phase, list_fz_artifacts

        state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
        return {
            "run_id": run_id,
            "project_name": run_id,
            "phase": infer_ui_phase(state),
            "status": (
                "completed"
                if state.status == "completed"
                else ("failed" if state.status == "stopped" else state.status)
            ),
            "is_live": False,
            "factory_engine": "fz",
            "artifacts_index": list_fz_artifacts(run_id),
            "usage": _usage_payload(state),
            "error": state.stop_reason or None,
            "pipeline_steps": [],
        }
    except Exception:
        return None


def _list_archived_artifacts(run_id: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for root_name in ("fz_workspace", "artifacts"):
        base = RUNS_DIR / run_id / root_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                rel = path.relative_to(base).as_posix()
                items.append({"path": rel, "category": rel.split("/")[0]})
    return items


def read_artifact(path: str, run_id: str | None = None) -> str | None:
    if run_id:
        for root_name in ("fz_workspace", "artifacts"):
            archived = RUNS_DIR / run_id / root_name / path
            if archived.is_file():
                return archived.read_text(encoding="utf-8")

    resolved_run_id = run_id
    if not resolved_run_id:
        current = get_current_run_state()
        if current:
            resolved_run_id = current.get("run_id")

    if resolved_run_id:
        fz_live = FZ_RUNS_DIR / resolved_run_id / path
        if fz_live.is_file():
            return fz_live.read_text(encoding="utf-8")

    live = ARTIFACTS_DIR / path
    if live.is_file():
        return live.read_text(encoding="utf-8")
    return None


def read_audit_events(run_id: str | None = None, since: int = 0) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    audit_dirs = [AUDIT_DIR]
    if run_id and (RUNS_DIR / run_id / "audit").exists():
        audit_dirs = [RUNS_DIR / run_id / "audit"]

    for audit_dir in audit_dirs:
        if not audit_dir.exists():
            continue
        for audit_file in sorted(audit_dir.glob("*.jsonl")):
            for line in audit_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if run_id and entry.get("run_id") and entry["run_id"] != run_id:
                    continue
                events.append(entry)

    events.sort(key=lambda e: e.get("timestamp", ""))
    return events[since:]
