"""Assemble structured dossier data from an fz run workspace (read-only)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import yaml

from artifact_reader import read_audit_events
from config import FZ_RUNS_DIR, RUNS_DIR
from dossier.enrichment import (
    build_agent_activity,
    build_timeline_extended,
    infer_passes,
    pass_summaries,
    read_worker_log,
)
from dossier.transcripts import load_transcript_entries
from dossier.labels import agent_display_name, phase_display_name

MAX_MD_CHARS = 48_000
MAX_ARTIFACT_LIST = 200


@dataclass
class DossierContext:
    run_id: str
    generated_at: str
    is_draft: bool
    status: str
    profile: str
    pipeline: str
    brief: str
    stop_reason: str
    product_name: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


def _read_text(path: Path, limit: int = MAX_MD_CHARS) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n\n… (truncated for PDF size)"
    return text


def _resolve_run_root(run_id: str) -> tuple[Path, Path]:
    """Live fz workspace first, then archived fz_workspace copy."""
    live_root = FZ_RUNS_DIR / run_id
    live_state = live_root / "state.json"
    if live_state.is_file():
        return live_state, live_root
    archived_state = RUNS_DIR / run_id / "fz_workspace" / "state.json"
    if archived_state.is_file():
        return archived_state, archived_state.parent
    raise FileNotFoundError(f"No state.json for run {run_id} (checked {live_state} and {archived_state})")


def _load_state(run_id: str) -> tuple[dict[str, Any], Path]:
    state_path, root = _resolve_run_root(run_id)
    data = json.loads(state_path.read_text(encoding="utf-8"))
    return data, root


def _md_to_html(md: str) -> str:
    if not md.strip():
        return "<p><em>Not available yet.</em></p>"
    try:
        import markdown

        return markdown.markdown(
            md,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        )
    except Exception:
        return f"<pre>{escape(md)}</pre>"


def _parse_openapi(run_root: Path) -> list[dict[str, str]]:
    for rel in ("docs/openapi.yaml", "docs/openapi.yml", "app/openapi.yaml", "server/openapi.yaml"):
        path = run_root / rel
        if not path.is_file():
            continue
        try:
            spec = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(spec, dict):
            continue
        paths = spec.get("paths") or {}
        rows: list[dict[str, str]] = []
        for path_key, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, op in methods.items():
                if method.startswith("x-") or not isinstance(op, dict):
                    continue
                if method.lower() not in (
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "head",
                    "options",
                ):
                    continue
                rows.append(
                    {
                        "method": method.upper(),
                        "path": path_key,
                        "operation_id": str(op.get("operationId") or ""),
                        "summary": str(op.get("summary") or op.get("description") or "")[:240],
                    }
                )
        rows.sort(key=lambda r: (r["path"], r["method"]))
        return rows
    return []


def _collect_test_files(run_root: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"app": [], "server": []}
    app_test = run_root / "app" / "test"
    if app_test.is_dir():
        for p in sorted(app_test.rglob("*")):
            if p.is_file() and p.suffix in (".dart",):
                out["app"].append(p.relative_to(run_root).as_posix())
    server_test = run_root / "server" / "test"
    if server_test.is_dir():
        for p in sorted(server_test.rglob("*")):
            if p.is_file() and p.suffix in (".ts", ".js"):
                out["server"].append(p.relative_to(run_root).as_posix())
    for sub in ("server/src",):
        base = run_root / sub
        if base.is_dir():
            for p in sorted(base.rglob("*.spec.ts")):
                out["server"].append(p.relative_to(run_root).as_posix())
    return out


def _list_artifacts(run_root: Path) -> list[str]:
    items: list[str] = []
    for folder in ("docs", "reports", "app", "server"):
        base = run_root / folder
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file():
                rel = p.relative_to(run_root).as_posix()
                if any(part in rel for part in (".dart_tool", "node_modules", "/build/", "\\build\\")):
                    continue
                items.append(rel)
                if len(items) >= MAX_ARTIFACT_LIST:
                    return items
    return items


def _screenshot_paths(run_root: Path, state: dict[str, Any]) -> list[tuple[str, Path]]:
    release = state.get("release") or {}
    raw = release.get("device_screenshots") or []
    found: list[tuple[str, Path]] = []
    for entry in raw:
        p = Path(entry)
        if not p.is_absolute():
            p = run_root / entry
        if p.is_file():
            found.append((entry, p))
    shots_dir = run_root / "reports" / "screenshots"
    if shots_dir.is_dir():
        for p in sorted(shots_dir.glob("*")):
            if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                found.append((p.name, p))
    return found[:24]


def _bug_key(b: dict[str, Any]) -> str:
    return str(b.get("id") or b.get("title") or "")


def _qa_fix_narrative(qa_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group QA reports by milestone and infer fix progression across rounds."""
    by_ms: dict[str, list[dict[str, Any]]] = {}
    for report in qa_reports:
        mid = report.get("milestone_id") or "M?"
        by_ms.setdefault(mid, []).append(report)

    narratives: list[dict[str, Any]] = []
    for mid, reports in sorted(by_ms.items()):
        round_rows: list[dict[str, Any]] = []
        prev_bug_ids: set[str] = set()
        for i, report in enumerate(reports, start=1):
            bugs = report.get("bugs") or []
            bug_ids = {_bug_key(b) for b in bugs if _bug_key(b)}
            fixed_since_last = sorted(prev_bug_ids - bug_ids) if i > 1 else []
            prev_bug_ids = bug_ids
            round_rows.append(
                {
                    "round": i,
                    "passed": bool(report.get("passed")),
                    "summary": report.get("summary") or "",
                    "bugs": bugs,
                    "tests_added": report.get("tests_added") or [],
                    "fixed_bug_ids": fixed_since_last,
                }
            )
        narratives.append({"milestone_id": mid, "rounds": round_rows})
    return narratives


def _traceability_rows(state: dict[str, Any]) -> list[dict[str, str]]:
    prd = state.get("prd") or {}
    stories = {s.get("id", ""): s for s in (prd.get("user_stories") or []) if isinstance(s, dict)}
    backlog = state.get("backlog") or {}
    work_items = backlog.get("work_items") or []
    build_items = (state.get("build") or {}).get("items") or {}

    rows: list[dict[str, str]] = []
    for wi in work_items:
        if not isinstance(wi, dict):
            continue
        wid = wi.get("id", "")
        story_ids = wi.get("story_ids") or []
        story_titles = []
        for sid in story_ids:
            st = stories.get(sid) or {}
            story_titles.append(f"{sid}: {st.get('title', '')}" if st else sid)
        prog = build_items.get(wid) or {}
        screens = ", ".join(wi.get("screens") or [])
        apis = ", ".join(wi.get("api_operations") or [])
        modules = ", ".join(wi.get("modules") or [])
        rows.append(
            {
                "work_item": f"{wid} — {wi.get('title', '')}",
                "stories": "; ".join(story_titles) or "—",
                "component": wi.get("component") or "",
                "screens": screens or "—",
                "api_ops": apis or "—",
                "modules": modules or "—",
                "build_status": prog.get("status") or "todo",
                "commit": (prog.get("commit") or "")[:12],
            }
        )
    return rows


def _legacy_timeline_events(state: dict[str, Any], audit: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Fallback when enrichment yields no timestamped rows."""
    events: list[tuple[str, str, str]] = []
    for g in state.get("gate_history") or []:
        if not isinstance(g, dict):
            continue
        ts = g.get("decided_at") or ""
        label = f"Gate «{g.get('gate')}»: {'approved' if g.get('approved') else 'rejected'}"
        events.append((ts, label, g.get("feedback") or ""))
    for u in state.get("usage") or []:
        if not isinstance(u, dict):
            continue
        if not u.get("started_at"):
            continue
        who = agent_display_name(u.get("agent") or "")
        task = u.get("task_key") or u.get("phase") or ""
        dur = u.get("duration_ms") or 0
        extra = f" ({dur} ms)" if dur else ""
        events.append((u.get("started_at") or "", f"{who} — {task}{extra}", u.get("model") or ""))
    for a in audit:
        ts = a.get("timestamp") or a.get("created_at") or ""
        events.append((ts, a.get("event") or "audit", json.dumps(a.get("details") or {})[:120]))
    events.sort(key=lambda e: e[0] or "")
    return [{"when": w, "what": what, "detail": det} for w, what, det in events]


def _usage_by_agent(state: dict[str, Any]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for u in state.get("usage") or []:
        if not isinstance(u, dict):
            continue
        agent = agent_display_name(u.get("agent") or "")
        b = buckets.setdefault(
            agent,
            {"agent": agent, "calls": 0, "duration_ms": 0, "tokens": 0, "tasks": []},
        )
        b["calls"] += 1
        b["duration_ms"] += int(u.get("duration_ms") or 0)
        b["tokens"] += int(u.get("total_tokens") or 0)
        tk = u.get("task_key") or u.get("phase") or ""
        if tk and tk not in b["tasks"]:
            b["tasks"].append(tk)
    return sorted(buckets.values(), key=lambda x: -x["duration_ms"])


def _known_issues(state: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    release = state.get("release") or {}
    for c in release.get("contract_issues") or []:
        issues.append({"source": "Release contract", "severity": "major", "title": str(c)})
    build = state.get("build") or {}
    for mid, mp in (build.get("milestones") or {}).items():
        if not isinstance(mp, dict):
            continue
        reports = mp.get("qa_reports") or []
        if not reports:
            continue
        last = reports[-1]
        for b in last.get("bugs") or []:
            if not isinstance(b, dict):
                continue
            issues.append(
                {
                    "source": f"QA {mid} (final round)",
                    "severity": b.get("severity") or "minor",
                    "title": b.get("title") or "",
                }
            )
    for wid, prog in (build.get("items") or {}).items():
        if not isinstance(prog, dict):
            continue
        if prog.get("status") in ("blocked", "failed"):
            issues.append(
                {
                    "source": wid,
                    "severity": "blocker",
                    "title": prog.get("reason") or prog.get("summary") or "Work item not completed",
                }
            )
    return issues


def _work_item_dependencies(state: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wi in (state.get("backlog") or {}).get("work_items") or []:
        if isinstance(wi, dict):
            rows.append(
                {
                    "id": wi.get("id", ""),
                    "title": wi.get("title", ""),
                    "depends_on": wi.get("depends_on") or [],
                    "component": wi.get("component") or "",
                }
            )
    return rows


def _user_story_rows(state: dict[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for s in (state.get("prd") or {}).get("user_stories") or []:
        if isinstance(s, dict):
            ac = s.get("acceptance_criteria") or []
            ac_text = "; ".join(
                f"Given {c.get('given', '')} When {c.get('when', '')} Then {c.get('then', '')}"
                for c in ac[:3]
                if isinstance(c, dict)
            )
            rows.append([s.get("id", ""), s.get("title", ""), s.get("priority", ""), ac_text[:320]])
    return rows


def _open_questions(state: dict[str, Any]) -> list[str]:
    qs: list[str] = []
    pb = state.get("product_brief") or {}
    qs.extend(pb.get("open_questions") or [])
    prd = state.get("prd") or {}
    qs.extend(prd.get("open_questions") or [])
    seen: set[str] = set()
    out: list[str] = []
    for q in qs:
        q = str(q).strip()
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


def _commit_log(state: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    backlog = state.get("backlog") or {}
    titles = {w.get("id"): w.get("title") for w in (backlog.get("work_items") or []) if isinstance(w, dict)}
    for wid, prog in ((state.get("build") or {}).get("items") or {}).items():
        if not isinstance(prog, dict):
            continue
        commit = prog.get("commit")
        if not commit:
            continue
        rows.append(
            {
                "work_item": wid,
                "title": titles.get(wid, ""),
                "commit": commit[:12],
                "status": prog.get("status") or "",
                "summary": (prog.get("summary") or "")[:400],
            }
        )
    return rows


def _app_screens(state: dict[str, Any]) -> list[dict[str, str]]:
    design = state.get("design") or {}
    screens = design.get("screens") or []
    rows: list[dict[str, str]] = []
    for s in screens:
        if isinstance(s, dict):
            rows.append(
                {
                    "id": s.get("id") or "",
                    "name": s.get("name") or "",
                    "route": s.get("route") or "",
                    "purpose": (s.get("purpose") or s.get("description") or "")[:300],
                }
            )
    if rows:
        return rows
    arch = state.get("architecture") or {}
    for feat in arch.get("app_features") or []:
        if not isinstance(feat, dict):
            continue
        for name in feat.get("screens") or []:
            rows.append({"id": "", "name": str(name), "route": "", "purpose": feat.get("name") or ""})
    return rows


def build_dossier_context(run_id: str) -> DossierContext:
    state, run_root = _load_state(run_id)
    status = state.get("status") or "unknown"
    is_draft = status == "running"
    pb = state.get("product_brief") or {}
    product_name = pb.get("product_name") or run_id

    audit = read_audit_events(run_id=run_id)
    worker_log = read_worker_log(run_id)
    passes = infer_passes(audit, worker_log, state)
    transcript_entries = load_transcript_entries(run_root)
    agent_activity, activity_stats = build_agent_activity(
        state,
        audit,
        worker_log,
        passes,
        run_root=run_root,
        transcript_entries=transcript_entries,
    )
    timeline, timeline_stats = build_timeline_extended(state, audit, agent_activity)
    if not timeline:
        timeline = _legacy_timeline_events(state, audit)
        timeline_stats = {"timeline_total": len(timeline), "timeline_truncated": 0}
    pass_rows = pass_summaries(passes, agent_activity, state)
    openapi_rows = _parse_openapi(run_root)
    test_files = _collect_test_files(run_root)
    artifacts = _list_artifacts(run_root)
    screenshots = _screenshot_paths(run_root, state)

    build = state.get("build") or {}
    all_qa: list[dict[str, Any]] = []
    for mp in (build.get("milestones") or {}).values():
        if isinstance(mp, dict):
            all_qa.extend(mp.get("qa_reports") or [])

    doc_files = {
        "product_brief": "docs/product_brief.md",
        "clarifications": "docs/clarifications.md",
        "prd": "docs/prd.md",
        "architecture": "docs/architecture.md",
        "design": "docs/design_system.md",
        "backlog": "docs/backlog.md",
    }
    doc_html = {key: _md_to_html(_read_text(run_root / rel)) for key, rel in doc_files.items()}

    qa_md_parts: list[str] = []
    reports_dir = run_root / "reports"
    if reports_dir.is_dir():
        for p in sorted(reports_dir.glob("qa_*.md")):
            qa_md_parts.append(f"## {p.name}\n\n{_read_text(p, 12000)}")
    qa_reports_html = _md_to_html("\n\n".join(qa_md_parts))

    release = state.get("release") or {}

    ctx = DossierContext(
        run_id=run_id,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        is_draft=is_draft,
        status=status,
        profile=state.get("profile") or "",
        pipeline=state.get("pipeline") or "",
        brief=state.get("brief") or "",
        stop_reason=state.get("stop_reason") or "",
        product_name=product_name,
        meta={
            "openapi_rows": openapi_rows,
            "test_files": test_files,
            "artifacts": artifacts,
            "screenshots": [(label, str(path)) for label, path in screenshots],
            "qa_fix_narrative": _qa_fix_narrative(all_qa),
            "traceability": _traceability_rows(state),
            "timeline": timeline,
            "timeline_stats": timeline_stats,
            "activity_stats": activity_stats,
            "passes": pass_rows,
            "agent_activity": agent_activity,
            "transcripts": transcript_entries,
            "worker_log_excerpt": worker_log[-50000:] if worker_log else "",
            "worker_log_chars": len(worker_log),
            "usage_by_agent": _usage_by_agent(state),
            "known_issues": _known_issues(state),
            "open_questions": _open_questions(state),
            "commit_log": _commit_log(state),
            "app_screens": _app_screens(state),
            "audit": audit,
            "doc_html": doc_html,
            "qa_reports_html": qa_reports_html,
            "clarifications": state.get("clarifications") or [],
            "gate_history": state.get("gate_history") or [],
            "build_items": build.get("items") or {},
            "milestones": build.get("milestones") or {},
            "architecture": state.get("architecture") or {},
            "release": release,
            "usage_raw": state.get("usage") or [],
            "total_tokens": sum(int(u.get("total_tokens") or 0) for u in (state.get("usage") or []) if isinstance(u, dict)),
            "work_item_dependencies": _work_item_dependencies(state),
            "user_story_rows": _user_story_rows(state),
        },
    )
    return ctx
