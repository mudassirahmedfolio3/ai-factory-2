from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import ARTIFACTS_DIR, AUDIT_DIR, RUNS_DIR, RUN_STATE_PATH

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
                runs.append(snap)

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for run in runs:
        rid = run.get("run_id", "")
        if rid and rid in seen:
            continue
        if rid:
            seen.add(rid)
        unique.append(run)
    return unique


def get_run(run_id: str) -> dict[str, Any] | None:
    current = get_current_run_state()
    if current and current.get("run_id") == run_id:
        return {**current, "is_live": current.get("status") == "running"}

    archived = read_json(RUNS_DIR / run_id / "snapshot.json")
    if archived:
        state = read_json(RUNS_DIR / run_id / "run_state.json")
        return {
            **archived,
            "is_live": False,
            "pipeline_steps": (state or {}).get("pipeline_steps", []),
            "artifacts_index": _list_archived_artifacts(run_id),
        }
    return None


def _list_archived_artifacts(run_id: str) -> list[dict[str, str]]:
    base = RUNS_DIR / run_id / "artifacts"
    if not base.exists():
        return []
    items: list[dict[str, str]] = []
    for path in sorted(base.rglob("*")):
        if path.is_file():
            rel = path.relative_to(base).as_posix()
            items.append({"path": rel, "category": rel.split("/")[0]})
    return items


def read_artifact(path: str, run_id: str | None = None) -> str | None:
    if run_id:
        archived = RUNS_DIR / run_id / "artifacts" / path
        if archived.exists():
            return archived.read_text(encoding="utf-8")

    live = ARTIFACTS_DIR / path
    if live.exists():
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
