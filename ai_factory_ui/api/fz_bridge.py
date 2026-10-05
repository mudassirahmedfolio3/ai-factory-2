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


def _work_item_components(state: Any) -> dict[str, str]:
    """Map work item id → component (frontend, backend, infra, shared)."""
    backlog = getattr(state, "backlog", None)
    if backlog is None:
        return {}
    items = getattr(backlog, "work_items", None) or []
    out: dict[str, str] = {}
    for wi in items:
        wid = getattr(wi, "id", None) or (wi.get("id") if isinstance(wi, dict) else None)
        comp = getattr(wi, "component", None) or (wi.get("component") if isinstance(wi, dict) else "")
        if wid:
            out[str(wid)] = str(comp or "")
    return out


def _item_status(items: Any, wid: str) -> str:
    if isinstance(items, dict):
        p = items.get(wid)
    else:
        p = getattr(items, "get", lambda _k: None)(wid) if hasattr(items, "get") else None
    if p is None:
        return "todo"
    return p.get("status") if isinstance(p, dict) else getattr(p, "status", "todo")


def _any_incomplete_work_items(items: Any) -> bool:
    if not items:
        return False
    values = items.values() if isinstance(items, dict) else []
    for p in values:
        st = p.get("status") if isinstance(p, dict) else getattr(p, "status", "todo")
        if st in ("todo", "blocked", "failed"):
            return True
    return False


def _milestone_qa_in_progress(state: Any) -> bool:
    """True when every WI in a milestone is done/blocked but milestone QA is not finished."""
    milestones = getattr(state.build, "milestones", {}) or {}
    items = getattr(state.build, "items", {}) or {}
    backlog = getattr(state, "backlog", None)
    if backlog is None:
        return False
    for m in getattr(backlog, "milestones", None) or []:
        mid = getattr(m, "id", None) or (m.get("id") if isinstance(m, dict) else None)
        wids = getattr(m, "work_item_ids", None) or (m.get("work_item_ids") if isinstance(m, dict) else [])
        if not mid or not wids:
            continue
        mp = milestones.get(str(mid)) if isinstance(milestones, dict) else None
        if mp is None:
            continue
        mstat = mp.get("status") if isinstance(mp, dict) else getattr(mp, "status", "todo")
        if mstat == "done":
            continue
        if all(_item_status(items, str(w)) in ("done", "blocked") for w in wids):
            return True
    return False


def _milestone_qa_in_progress_dict(data: dict[str, Any]) -> bool:
    backlog = data.get("backlog")
    build = data.get("build") or {}
    milestones = build.get("milestones") or {}
    items = build.get("items") or {}
    if not backlog or not isinstance(backlog, dict):
        return False
    for ms in backlog.get("milestones") or []:
        if not isinstance(ms, dict):
            continue
        mid = ms.get("id")
        wids = ms.get("work_item_ids") or []
        if not mid or not wids:
            continue
        mp = milestones.get(str(mid)) if isinstance(milestones, dict) else None
        if mp is None:
            continue
        mstat = mp.get("status") if isinstance(mp, dict) else "todo"
        if mstat == "done":
            continue
        if all(_item_status(items, str(w)) in ("done", "blocked") for w in wids):
            return True
    return False


def build_progress_summary_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Work-item counts from raw state.json (no ProjectState import)."""
    build = data.get("build") or {}
    items = build.get("items") or {}
    if not isinstance(items, dict):
        items = {}

    titles: dict[str, str] = {}
    ordered_ids: list[str] = []
    milestone_rows: list[dict[str, Any]] = []

    backlog = data.get("backlog")
    if isinstance(backlog, dict):
        for wi in backlog.get("work_items") or []:
            if not isinstance(wi, dict):
                continue
            wid = wi.get("id")
            if not wid:
                continue
            wid = str(wid)
            titles[wid] = str(wi.get("title") or wid)
            if wid not in ordered_ids:
                ordered_ids.append(wid)

        milestones = build.get("milestones") or {}
        for ms in backlog.get("milestones") or []:
            if not isinstance(ms, dict):
                continue
            mid = ms.get("id")
            wids = ms.get("work_item_ids") or []
            if not mid:
                continue
            wids = [str(w) for w in wids]
            done_ms = sum(1 for w in wids if _item_status(items, w) == "done")
            mp = milestones.get(str(mid)) if isinstance(milestones, dict) else None
            mstat = "todo"
            if isinstance(mp, dict):
                mstat = mp.get("status") or "todo"
            milestone_rows.append(
                {
                    "id": str(mid),
                    "done": done_ms,
                    "total": len(wids),
                    "status": str(mstat or "todo"),
                }
            )

    for wid in sorted(items.keys()):
        ws = str(wid)
        if ws.startswith("WI-") and ws not in ordered_ids:
            ordered_ids.append(ws)
            titles.setdefault(ws, ws)

    if not ordered_ids:
        ordered_ids = [str(k) for k in sorted(items.keys()) if str(k).startswith("WI-")]

    done = sum(1 for wid in ordered_ids if _item_status(items, wid) == "done")
    total = len(ordered_ids)

    active_id: str | None = None
    active_status: str | None = None
    for wid in ordered_ids:
        st = _item_status(items, wid)
        if st == "done":
            continue
        active_id = wid
        active_status = st
        break

    run_status = str(data.get("status") or "running")
    fz_phase = "complete" if run_status == "completed" else ("build" if _any_incomplete_work_items(items) else "complete")

    return {
        "total": total,
        "done": done,
        "remaining": max(0, total - done),
        "active_work_item_id": active_id,
        "active_work_item_title": titles.get(active_id, active_id) if active_id else None,
        "active_work_item_status": active_status,
        "qa_in_progress": _milestone_qa_in_progress_dict(data),
        "milestones": milestone_rows,
        "fz_phase": fz_phase,
    }


def build_progress_summary(state: Any) -> dict[str, Any]:
    """Work-item counts and active task for the React console (read-only)."""
    if isinstance(state, dict):
        return build_progress_summary_from_dict(state)
    if hasattr(state, "model_dump"):
        return build_progress_summary_from_dict(state.model_dump(mode="json"))
    data = {
        "status": getattr(state, "status", "running"),
        "build": {"items": getattr(state.build, "items", {}), "milestones": getattr(state.build, "milestones", {})},
        "backlog": getattr(state, "backlog", None),
    }
    if data["backlog"] is not None and hasattr(data["backlog"], "model_dump"):
        data["backlog"] = data["backlog"].model_dump(mode="json")
    summary = build_progress_summary_from_dict(data)
    try:
        summary["fz_phase"] = infer_ui_phase(state)
    except Exception:
        pass
    summary["qa_in_progress"] = _milestone_qa_in_progress(state)
    return summary


def pipeline_steps_for_state(state: Any, ui_status: str) -> list[dict[str, str]]:
    phase = infer_ui_phase(state)
    return [
        {
            "id": step["id"],
            "label": step["label"],
            "status": _step_status(phase, step["phases"], ui_status),
        }
        for step in PIPELINE_STEPS
    ]


def _release_replanning(state: Any) -> bool:
    """Pass 2+ replan: PRD kept while backlog (and often architecture) are regenerated."""
    return bool(getattr(state, "prd", None)) and getattr(state, "backlog", None) is None


def infer_ui_phase(state: Any) -> str:
    """Best-effort phase label for the React pipeline step map (not the 11-stage carousel)."""
    status = getattr(state, "status", "running")
    if status == "completed" and not _release_replanning(state):
        return "complete"
    if status == "stopped" and not _release_replanning(state):
        return "failed"

    if state.prd and not state.gate_approved("prd"):
        return "prd_review"

    items = getattr(state.build, "items", {}) or {}
    if _any_incomplete_work_items(items):
        return "build"

    if _release_replanning(state):
        if not state.architecture:
            return "planning"
        if not state.design:
            return "design"
        return "sprint_planning"

    if items and _milestone_qa_in_progress(state):
        return "qa"

    if state.architecture and not state.gate_approved("architecture"):
        return "design"
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
    if items:
        return "qa"
    return "build"


def _infer_build_stage_index(state: Any) -> int:
    """Backend (5), frontend (6), or deployment (7) from the first incomplete work item."""
    comps = _work_item_components(state)
    items = getattr(state.build, "items", {}) or {}
    if not isinstance(items, dict):
        items = {}
    # Prefer backlog order; include build-only ids (e.g. new WIs before backlog sync).
    candidate_ids = sorted(set(comps.keys()) | {k for k in items if str(k).startswith("WI-")})
    for wid in candidate_ids:
        p = items.get(wid)
        if p is None:
            continue
        st = p.get("status") if isinstance(p, dict) else getattr(p, "status", "todo")
        if st not in ("todo", "blocked", "failed"):
            continue
        comp = comps.get(wid, "")
        if comp == "frontend":
            return 6
        if comp == "infra":
            return 7
        return 5
    return 6 if any(c == "frontend" for c in comps.values()) else 5


def infer_ui_stage_index(state: Any) -> int:
    """Index 0–10 matching React `UI_STAGE_AGENTS` / journey carousel order."""
    status = getattr(state, "status", "running")
    if status == "completed" and not _release_replanning(state):
        return 10

    phase = infer_ui_phase(state)

    if phase == "planning":
        return 2
    if phase == "sprint_planning":
        return 4

    if phase in ("discovery", "kickoff"):
        return 0 if state.product_brief is None else 1
    if phase == "prd_review":
        return 1

    # Active build/QA must win over stale planning gates (Pass 2 replan may leave gates open).
    if phase == "build":
        return _infer_build_stage_index(state)
    if phase == "qa":
        return 8

    if not state.architecture:
        return 2
    if state.architecture and not state.gate_approved("architecture"):
        return 2
    if not state.design:
        return 3
    if not state.backlog:
        return 4

    if phase in ("release", "delivery", "browser", "client_review"):
        return 9 if phase == "browser" else 10
    return 4


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


def _short_product_name(name: str) -> str:
    """Use the brand segment before em/en dash suffixes from expanded briefs."""
    text = (name or "").strip()
    for sep in (" — ", " – ", " - "):
        if sep in text:
            return text.split(sep, 1)[0].strip()
    return text


def infer_product_display_name(state: Any, project_name: str) -> str:
    """Human-facing app title (ShopEase, Lighting …) vs intake slug project_name."""
    pb = getattr(state, "product_brief", None)
    if pb is not None:
        raw = (getattr(pb, "product_name", None) or "").strip()
        if raw:
            return _short_product_name(raw)
    prd = getattr(state, "prd", None)
    if prd is not None:
        title = (getattr(prd, "title", None) or "").strip()
        if title:
            return title
    slug = (project_name or "").strip()
    if slug and slug != getattr(state, "run_id", ""):
        return slug.replace("-", " ").replace("_", " ").title()
    return project_name or "Project"


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
    ui_active_stage = infer_ui_stage_index(state)
    steps = pipeline_steps_for_state(state, ui_status)

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

    display_name = infer_product_display_name(state, project_name)
    payload = {
        "run_id": state.run_id,
        "project_name": project_name,
        "product_name": display_name,
        "phase": phase,
        "ui_active_stage": ui_active_stage,
        "status": ui_status,
        "release_number": 1,
        "complexity": complexity,
        "estimated_minutes": COMPLEXITY_MINUTES.get(complexity, 90),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_steps": steps,
        "build_progress": build_progress_summary(state),
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
