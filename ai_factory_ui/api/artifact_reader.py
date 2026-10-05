from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import ARTIFACTS_DIR, AUDIT_DIR, FZ_RUNS_DIR, RUNS_DIR, RUN_STATE_PATH

STALE_RUN_MINUTES = 30


def _fz_worker_live_for_run(run_id: str | None) -> bool:
    """True when an fz_worker process is running for this run_id."""
    if not run_id:
        return False
    try:
        from fz_run_manager import _worker_pids_for_run, worker_process_alive

        if _worker_pids_for_run(run_id.strip()):
            return True
        info = __import__("fz_run_manager", fromlist=["read_worker_info"]).read_worker_info()
        if info and str(info.get("run_id") or "") == run_id and worker_process_alive():
            return True
    except Exception:
        pass
    return False


def _normalize_run_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mark abandoned 'running' snapshots as stale — but never while the worker is still alive."""
    if not state:
        return state
    run_id = str(state.get("run_id") or "")
    if _fz_worker_live_for_run(run_id):
        # Long M2 agent steps may not touch state.json for 30+ minutes; keep UI as running.
        if state.get("status") in ("running", "stale", "failed"):
            return {**state, "status": "running", "is_live": True, "error": None}
        return state
    if state.get("status") != "running":
        return state
    updated = state.get("updated_at", "")
    try:
        ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60
        if age_min > STALE_RUN_MINUTES:
            state = {
                **state,
                "status": "stale",
                "is_live": False,
                "error": state.get("error")
                or "Run stopped responding (no worker updates). Use History → Generate another release to resume.",
            }
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

    live_run_ids: set[str] = set()
    try:
        from fz_run_manager import _list_fz_worker_processes

        live_run_ids = {rid for _, rid in _list_fz_worker_processes() if rid}
    except Exception:
        pass

    runs: list[dict[str, Any]] = []
    current = get_current_run_state()
    if current:
        rid = str(current.get("run_id") or "")
        status = (current.get("status") or "").lower()
        is_live = bool(rid and rid in live_run_ids)
        if is_live and status in ("stale", "failed"):
            current = {**current, "status": "running", "error": None}
        runs.append({**current, "is_live": is_live})

    if FZ_RUNS_DIR.is_dir():
        for run_dir in sorted(FZ_RUNS_DIR.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            rid = run_dir.name
            live = _run_state_from_fz_workspace(
                rid, live_run_ids=live_run_ids, include_artifacts=False, include_usage=False,
            )
            if live:
                live["is_live"] = bool(live.get("is_live"))
                runs.append(live)

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


def _enrich_from_fz_workspace_state(payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Merge live fz state.json fields (work items, pipeline steps) into API payloads."""
    state_path = FZ_RUNS_DIR / run_id / "state.json"
    if not state_path.is_file():
        archived = RUNS_DIR / run_id / "fz_workspace" / "state.json"
        state_path = archived if archived.is_file() else state_path
    if not state_path.is_file():
        return payload
    import json

    try:
        raw = state_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return payload

    from fz_bridge import build_progress_summary_from_dict

    merged = {**payload, "build_progress": build_progress_summary_from_dict(data)}

    try:
        _ensure_fz_pythonpath()
        from agentic_sdlc.state import ProjectState
        from fz_bridge import infer_ui_phase, infer_ui_stage_index, pipeline_steps_for_state

        state = ProjectState.model_validate(data)
        ui_status = str(payload.get("status") or state.status or "running")
        if ui_status == "stale":
            ui_status = "running"
        merged["phase"] = infer_ui_phase(state)
        merged["ui_active_stage"] = infer_ui_stage_index(state)
        steps = pipeline_steps_for_state(state, ui_status if ui_status != "stale" else "running")
        if steps:
            merged["pipeline_steps"] = steps
    except Exception:
        pass

    return merged


def _enrich_product_display_name(payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    if payload.get("product_name"):
        return payload
    state_path = FZ_RUNS_DIR / run_id / "state.json"
    if not state_path.is_file():
        return payload
    try:
        _ensure_fz_pythonpath()
        from agentic_sdlc.state import ProjectState
        from fz_bridge import infer_product_display_name

        state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
        slug = str(payload.get("project_name") or run_id)
        return {**payload, "product_name": infer_product_display_name(state, slug)}
    except Exception:
        return payload


def get_run(run_id: str) -> dict[str, Any] | None:
    from fz_emulator import flutter_project_ready

    current = get_current_run_state()
    if current and current.get("run_id") == run_id:
        live = _fz_worker_live_for_run(run_id)
        payload = {**current, "is_live": live, "flutter_ready": flutter_project_ready(run_id, current)}
        if live and payload.get("status") in ("stale", "failed"):
            payload["status"] = "running"
            payload["error"] = None
        return _enrich_from_fz_workspace_state(
            _enrich_product_display_name(payload, run_id),
            run_id,
        )

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
        return _enrich_from_fz_workspace_state(
            _enrich_product_display_name(payload, run_id),
            run_id,
        )

    # Live fz workspace still on disk (e.g. failed before archive).
    live_fz = _run_state_from_fz_workspace(run_id)
    if live_fz:
        live_fz["flutter_ready"] = flutter_project_ready(run_id, live_fz)
        return _enrich_from_fz_workspace_state(
            _enrich_product_display_name(live_fz, run_id),
            run_id,
        )

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


def _run_state_from_fz_workspace(
    run_id: str,
    *,
    live_run_ids: set[str] | None = None,
    include_artifacts: bool = True,
    include_usage: bool = True,
) -> dict[str, Any] | None:
    state_path = FZ_RUNS_DIR / run_id / "state.json"
    if not state_path.is_file():
        return None
    try:
        _ensure_fz_pythonpath()
        from agentic_sdlc.state import ProjectState
        from fz_bridge import (
            _usage_payload,
            build_progress_summary,
            infer_product_display_name,
            infer_ui_phase,
            infer_ui_stage_index,
            list_fz_artifacts,
            pipeline_steps_for_state,
        )

        state = ProjectState.model_validate_json(state_path.read_text(encoding="utf-8"))
        if live_run_ids is None:
            from fz_run_manager import _worker_pids_for_run

            live_workers = bool(_worker_pids_for_run(run_id))
        else:
            live_workers = run_id in live_run_ids
        ui_status = (
            "completed"
            if state.status == "completed"
            else ("failed" if state.status in ("stopped", "failed") else state.status)
        )
        if state.status == "running" and not live_workers:
            ui_status = "stale"
        slug = state.brief.split("\n")[0].strip("# ").strip() if state.brief else run_id
        pipe_status = "completed" if state.status == "completed" else ui_status
        if pipe_status == "stale":
            pipe_status = "running"
        return {
            "run_id": run_id,
            "project_name": slug or run_id,
            "product_name": infer_product_display_name(state, slug or run_id),
            "phase": infer_ui_phase(state),
            "ui_active_stage": infer_ui_stage_index(state),
            "status": ui_status,
            "is_live": state.status == "running" and live_workers,
            "factory_engine": "fz",
            "artifacts_index": list_fz_artifacts(run_id) if include_artifacts else [],
            "usage": _usage_payload(state) if include_usage else {},
            "error": state.stop_reason or None,
            "pipeline_steps": pipeline_steps_for_state(state, pipe_status),
            "build_progress": build_progress_summary(state),
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
    """Read an artifact for a run.

    When ``run_id`` is set, only that run's archived/fz files are considered —
    never the shared live ``artifacts/`` folder (that caused stale PRDs from
    earlier projects to leak into unrelated runs).
    """
    if run_id:
        for root_name in ("fz_workspace", "artifacts"):
            archived = RUNS_DIR / run_id / root_name / path
            if archived.is_file():
                return archived.read_text(encoding="utf-8")

        fz_live = FZ_RUNS_DIR / run_id / path
        if fz_live.is_file():
            return fz_live.read_text(encoding="utf-8")
        return None

    current = get_current_run_state()
    resolved_run_id = current.get("run_id") if current else None
    if resolved_run_id:
        for root_name in ("fz_workspace", "artifacts"):
            archived = RUNS_DIR / resolved_run_id / root_name / path
            if archived.is_file():
                return archived.read_text(encoding="utf-8")
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
