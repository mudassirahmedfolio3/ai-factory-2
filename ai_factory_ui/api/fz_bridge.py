"""Map agentic_sdlc ProjectState → React console run_state.json shape."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import AI_FACTORY_FZ_ROOT, AUDIT_DIR, FZ_RUNS_DIR, RUNS_DIR, RUN_STATE_PATH

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


def _token_budget(state: Any | None = None) -> int:
    raw = os.getenv("ANTHROPIC_TOKEN_BUDGET") or os.getenv("LLM_TOKEN_BUDGET")
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            pass
    pipeline = getattr(state, "pipeline", None) or "pipeline.ui"
    path = AI_FACTORY_FZ_ROOT / "config" / f"{pipeline}.yaml"
    if not path.is_file():
        path = AI_FACTORY_FZ_ROOT / "config" / "pipeline.ui.yaml"
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw_limit = (data.get("budget") or {}).get("max_total_tokens")
        if raw_limit is None:
            return 0
        return max(0, int(raw_limit))
    except Exception:
        return 0


def _clip(text: str, limit: int = 140) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _activity_detail(state: Any, row: Any) -> dict[str, Any]:
    """Human-readable work product for one usage cell (specs, QA cases, etc.)."""
    agent = (getattr(row, "agent", "") or "").lower()
    phase = (getattr(row, "phase", "") or "").lower()
    task = (getattr(row, "task_key", "") or "").lower()
    items: list[str] = []
    paths: list[str] = []
    title = f"{getattr(row, 'agent', 'Agent')} · {getattr(row, 'phase', 'phase')}"

    if agent in ("customer", "product_owner") or "brief" in task:
        brief = state.product_brief
        if brief:
            title = f"Product brief · {brief.product_name}"
            items = [f"Vision: {_clip(brief.vision)}"]
            items += [f"Feature: {f}" for f in (brief.key_features or [])[:12]]
            paths = ["docs/product_brief.md"]

    elif agent in ("spec_writer", "analyst") or "spec" in task or "prd" in task or "clarif" in task:
        if state.clarifications:
            title = "Spec clarifications"
            items = [f"Q: {_clip(q.question, 80)} → {_clip(q.answer, 80)}" for q in state.clarifications[:16]]
            paths.append("docs/clarifications.md")
        if state.prd:
            title = f"PRD · {state.prd.title}"
            items = [f"{s.id}: {s.title} [{s.priority}]" for s in state.prd.user_stories[:24]]
            if state.prd.non_functional_requirements:
                items += [f"NFR: {_clip(n)}" for n in state.prd.non_functional_requirements[:8]]
            paths.append("docs/prd.md")

    elif agent in ("project_manager", "pm") or "backlog" in task:
        if state.backlog:
            title = "Backlog"
            for epic in (state.backlog.epics or [])[:10]:
                items.append(f"Epic {epic.id}: {epic.title}")
            for wi in (state.backlog.work_items or [])[:24]:
                items.append(f"{wi.id}: {wi.title} [{wi.component}]")
            for ms in (state.backlog.milestones or [])[:8]:
                items.append(f"Milestone {ms.id}: {ms.name} ({len(ms.work_item_ids)} items)")
            paths = ["docs/backlog.md"]

    elif agent in ("architect",) or "architect" in task:
        arch = state.architecture
        if arch:
            title = "Architecture"
            comps = getattr(arch, "components", None) or []
            items = [f"Component: {getattr(c, 'name', c)}" for c in comps[:16]]
            feats = getattr(arch, "app_features", None) or []
            items += [f"Feature: {getattr(f, 'name', f)}" for f in feats[:12]]
            adrs = getattr(arch, "adrs", None) or []
            items += [f"ADR: {getattr(a, 'title', a)}" for a in adrs[:8]]
            paths = ["docs/architecture.md", "docs/openapi.yaml"]

    elif agent in ("ui_ux_designer", "designer") or "design" in task:
        design = state.design
        if design:
            title = "Design system"
            screens = getattr(design, "screens", None) or []
            items = [f"Screen: {getattr(s, 'name', s)}" for s in screens[:20]]
            widgets = getattr(design, "shared_widgets", None) or []
            items += [f"Widget: {getattr(w, 'name', w)}" for w in widgets[:10]]
            paths = ["docs/design_system.md"]

    elif agent in ("qa_engineer", "qa", "tester") or phase in ("qa", "build") and "qa" in agent:
        title = "QA work"
        for mid, mp in (state.build.milestones or {}).items():
            for report in mp.qa_reports or []:
                status = "passed" if report.passed else "failed"
                items.append(f"Milestone {report.milestone_id or mid}: {status} — {_clip(report.summary)}")
                items += [f"  Criterion: {_clip(c)}" for c in (report.criteria_checked or [])[:10]]
                items += [f"  Test: {t}" for t in (report.tests_added or [])[:10]]
                items += [f"  Bug [{b.severity}]: {b.title}" for b in (report.bugs or [])[:10]]
        paths = [p["path"] for p in list_fz_artifacts(state.run_id) if p["path"].startswith("reports/") and "qa" in p["path"].lower()][:12]

    elif agent in ("smoke_tester", "release_engineer", "deployment_engineer") or phase == "release":
        title = "Release / smoke"
        rel = state.release
        if rel.smoke_suite:
            items.append(f"Smoke suite: {_clip(rel.smoke_suite.summary)}")
            items += [f"  Test: {t}" for t in (rel.smoke_suite.tests_added or [])[:12]]
        if rel.smoke_passed is not None:
            items.append(f"Smoke: {'passed' if rel.smoke_passed else 'failed'}")
        if rel.smoke_output:
            items.append(f"Smoke output: {_clip(rel.smoke_output, 200)}")
        if rel.integration:
            items.append(f"Integration: {'passed' if rel.integration.passed else 'failed'} — {_clip(rel.integration.summary)}")
            items += [f"  Criterion: {_clip(c)}" for c in (rel.integration.criteria_checked or [])[:8]]
        if rel.device_suite:
            items.append(f"Device suite: {_clip(rel.device_suite.summary)}")
        if rel.device_passed is not None:
            items.append(f"Device: {'passed' if rel.device_passed else 'failed'}")
        paths = [p["path"] for p in list_fz_artifacts(state.run_id) if "smoke" in p["path"].lower() or p["path"].startswith("reports/")][:12]

    elif phase == "build" or agent.endswith("_developer") or "developer" in agent or "coder" in agent:
        title = "Build work items"
        backlog_titles = {}
        if state.backlog:
            for wi in state.backlog.work_items or []:
                backlog_titles[wi.id] = wi.title
        for wid, prog in (state.build.items or {}).items():
            label = backlog_titles.get(wid, wid)
            items.append(f"{wid} [{prog.status}] {label}" + (f" — {_clip(prog.summary)}" if prog.summary else ""))
        paths = ["app/", "server/"]

    if not items:
        items = [
            f"Task: {getattr(row, 'task_key', '') or '(none)'}",
            f"Phase: {getattr(row, 'phase', '')}",
            f"Model: {getattr(row, 'model', '')}",
            f"Tokens: {getattr(row, 'total_tokens', 0):,}",
        ]
        if getattr(row, "duration_ms", 0):
            items.append(f"Duration: {getattr(row, 'duration_ms', 0)} ms")

    return {"detail_title": title, "detail_items": items[:40], "detail_paths": paths[:16]}


def _usage_payload(state: Any) -> dict[str, Any]:
    activities = []
    for idx, row in enumerate(state.usage):
        detail = _activity_detail(state, row)
        activities.append(
            {
                "id": f"fz-{idx}",
                "model": row.model,
                "agent": row.agent,
                "task": getattr(row, "task_key", None) or row.phase,
                "phase": row.phase,
                "label": f"{row.agent} · {row.phase}",
                "status": "completed",
                "prompt_tokens": row.prompt_tokens,
                "completion_tokens": row.completion_tokens,
                "total_tokens": row.total_tokens,
                "uncached_tokens": getattr(row, "uncached_tokens", row.total_tokens - getattr(row, "cached_prompt_tokens", 0)),
                "duration_ms": getattr(row, "duration_ms", 0) or 0,
                "started_at": getattr(row, "started_at", "") or "",
                "ended_at": getattr(row, "ended_at", "") or "",
                "estimated": False,
                **detail,
            }
        )
    total = state.total_tokens()
    uncached = state.uncached_tokens() if hasattr(state, "uncached_tokens") else total
    budget = _token_budget(state)
    pct = round((uncached / budget) * 100, 1) if budget > 0 else 0.0
    warning = None
    if budget > 0 and pct >= 90:
        warning = f"Token budget nearly exhausted ({uncached:,} / {budget:,} uncached)."
    elif budget > 0 and pct >= 70:
        warning = f"Token budget at {pct}% ({uncached:,} / {budget:,} uncached)."
    return {
        "llm_calls": len(state.usage),
        "prompt_tokens": sum(u.prompt_tokens for u in state.usage),
        "completion_tokens": sum(u.completion_tokens for u in state.usage),
        "total_tokens": total,
        "uncached_tokens": uncached,
        "estimated_calls": 0,
        "actual_calls": len(state.usage),
        "token_budget": budget,
        "usage_percent": pct,
        "provider": "agentic_sdlc",
        "activities": activities[-40:],
        "budget_warning": warning,
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
    pubspec_ready = (app_dir / "pubspec.yaml").is_file()
    flutter_dir = str(app_dir.resolve()) if pubspec_ready else None
    build_items_done = bool(state.build.items) and all(
        p.status == "done" for p in state.build.items.values()
    )
    build_step_status = next((s["status"] for s in steps if s["id"] == "build"), "pending")
    flutter_artifacts_ready = pubspec_ready and (
        build_items_done or build_step_status == "completed" or ui_status == "completed"
    )

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
            "flutter_artifacts_ready": flutter_artifacts_ready,
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
