"""Map agentic_sdlc ProjectState → React console run_state.json shape."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import ARTIFACTS_DIR, AUDIT_DIR, FZ_RUNS_DIR, RUNS_DIR, RUN_STATE_PATH

PIPELINE_STEPS: list[dict[str, Any]] = [
    {"id": "discovery", "label": "Discovery", "phases": ["kickoff", "discovery", "prd_review"]},
    {"id": "design", "label": "Design", "phases": ["design", "planning"]},
    {"id": "sprint", "label": "Sprint", "phases": ["sprint_planning"]},
    {"id": "build", "label": "Build", "phases": ["build"]},
    {"id": "code_review", "label": "Code Review", "phases": ["code_review"]},
    {"id": "security", "label": "Security", "phases": ["security"]},
    {"id": "qa", "label": "QA", "phases": ["qa"]},
    {"id": "release", "label": "Release", "phases": ["release"]},
    {"id": "browser", "label": "Browser", "phases": ["browser", "delivery"]},
    {"id": "client_review", "label": "Client Review", "phases": ["client_review"]},
]

COMPLEXITY_MINUTES = {
    "basic": 15,
    "basic_plus": 30,
    "standard": 90,
    "full": 180,
}


def _step_status(current_phase: str, step_phases: list[str], run_status: str) -> str:
    if run_status == "completed":
        return "completed"
    if run_status in ("failed", "stopped", "stale"):
        if current_phase in step_phases:
            return "failed"
    if current_phase in step_phases:
        return "active"
    current_idx = next((i for i, s in enumerate(PIPELINE_STEPS) if current_phase in s["phases"]), -1)
    step_idx = next((i for i, s in enumerate(PIPELINE_STEPS) if s["phases"] == step_phases), -1)
    if current_idx >= 0 and step_idx >= 0 and step_idx < current_idx:
        return "completed"
    return "pending"


def infer_ui_phase(state: Any) -> str:
    """Best-effort phase label for the React journey map."""
    status = getattr(state, "status", "running")
    if status == "completed":
        return "complete"
    if status == "stopped":
        return "failed"

    if state.prd and not state.gate_approved("prd"):
        return "prd_review"
    if state.architecture and not state.gate_approved("architecture"):
        return "design"
    if state.build.items and any(p.status in ("todo", "blocked", "failed") for p in state.build.items.values()):
        if any(mp.qa_rounds > 0 for mp in state.build.milestones.values()):
            return "qa"
        return "build"
    if state.design and not state.build.items:
        return "build"
    if state.backlog and not state.architecture:
        return "sprint_planning"
    if state.architecture and not state.design:
        return "design"
    if not state.prd:
        return "discovery"
    if state.release.verified:
        return "delivery"
    return "build"


def _usage_payload(state: Any) -> dict[str, Any]:
    activities = []
    for idx, row in enumerate(state.usage):
        activities.append(
            {
                "id": f"fz-{idx}",
                "model": row.model,
                "agent": row.agent,
                "task": row.phase,
                "label": f"{row.agent} · {row.phase}",
                "status": "completed",
                "prompt_tokens": row.prompt_tokens,
                "completion_tokens": row.completion_tokens,
                "total_tokens": row.total_tokens,
                "estimated": False,
            }
        )
    total = state.total_tokens()
    return {
        "llm_calls": len(state.usage),
        "prompt_tokens": sum(u.prompt_tokens for u in state.usage),
        "completion_tokens": sum(u.completion_tokens for u in state.usage),
        "total_tokens": total,
        "estimated_calls": 0,
        "actual_calls": len(state.usage),
        "token_budget": 0,
        "usage_percent": 0.0,
        "provider": "agentic_sdlc",
        "activities": activities[-40:],
        "budget_warning": None,
    }


def list_fz_artifacts(run_id: str) -> list[dict[str, str]]:
    root = FZ_RUNS_DIR / run_id
    if not root.is_dir():
        return []
    items: list[dict[str, str]] = []
    for folder, category in (("docs", "docs"), ("reports", "reports"), ("app", "app"), ("server", "server")):
        base = root / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                items.append({"path": rel, "category": category})
    return items


def publish_fz_run_state(
    state: Any,
    *,
    project_name: str,
    complexity: str,
    checkpoint_msg: str = "",
) -> Path:
    ui_status = "running"
    if state.status == "completed":
        ui_status = "completed"
    elif state.status == "stopped":
        ui_status = "failed"

    phase = infer_ui_phase(state)
    steps = [
        {
            "id": step["id"],
            "label": step["label"],
            "status": _step_status(phase, step["phases"], ui_status),
        }
        for step in PIPELINE_STEPS
    ]

    app_dir = FZ_RUNS_DIR / state.run_id / "app"
    server_dir = FZ_RUNS_DIR / state.run_id / "server"
    flutter_dir = str(app_dir.resolve()) if app_dir.is_dir() else None

    prd_gate = state.gate_approved("prd")
    arch_gate = state.gate_approved("architecture")
    rel_gate = state.gate_approved("release")

    qa_done = any(mp.status in ("done", "partial") for mp in state.build.milestones.values())

    payload = {
        "run_id": state.run_id,
        "project_name": project_name,
        "phase": phase,
        "status": ui_status,
        "release_number": 1,
        "complexity": complexity,
        "estimated_minutes": COMPLEXITY_MINUTES.get(complexity, 90),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_steps": steps,
        "factory_engine": "fz",
        "flutter_project_dir": flutter_dir,
        "server_project_dir": str(server_dir.resolve()) if server_dir.is_dir() else None,
        "checkpoint": checkpoint_msg,
        "checks": {
            "code_review_passed": bool(state.architecture),
            "security_passed": True,
            "qa_passed": qa_done,
            "post_deploy_passed": bool(state.release.verified),
            "deploy_approved": rel_gate,
            "flutter_artifacts_ready": app_dir.is_dir(),
        },
        "approvals": {
            "prd": "approved" if prd_gate else None,
            "release": "approved" if rel_gate else None,
            "deploy": "approved" if state.release.production == "deployed" else None,
        },
        "artifacts_index": list_fz_artifacts(state.run_id),
        "usage": _usage_payload(state),
        "error": state.stop_reason if ui_status == "failed" else None,
    }

    RUN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return RUN_STATE_PATH


def log_fz_audit(run_id: str, event: str, decision: str, agent: str, details: dict | None = None) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "decision": decision,
        "agent": agent,
        "details": details or {},
        "run_id": run_id,
    }
    path = AUDIT_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d')}_audit.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def archive_fz_run(state: Any, project_name: str, complexity: str) -> Path:
    dest = RUNS_DIR / state.run_id
    dest.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "run_id": state.run_id,
        "project_name": project_name,
        "phase": infer_ui_phase(state),
        "status": "completed" if state.status == "completed" else state.status,
        "release_number": 1,
        "complexity": complexity,
        "factory_engine": "fz",
        "archived_at": datetime.now(timezone.utc).isoformat(),
    }
    (dest / "snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    if RUN_STATE_PATH.exists():
        shutil.copy2(RUN_STATE_PATH, dest / "run_state.json")
    src = FZ_RUNS_DIR / state.run_id
    if src.is_dir():
        shutil.copytree(src, dest / "fz_workspace", dirs_exist_ok=True)
    return dest
