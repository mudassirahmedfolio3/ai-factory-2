"""Dossier-only enrichment: passes, agent activity, worker log (read-only; no run side effects)."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config import ARTIFACTS_DIR
from dossier.labels import agent_display_name

# Dossier export only — does not affect factory runs.
MAX_TIMELINE = 10_000
MAX_AGENT_ACTIVITY = 10_000
MAX_LOG_CHARS = 4_000_000


def worker_log_path(run_id: str) -> Path:
    return ARTIFACTS_DIR / "logs" / f"fz_worker_{run_id}.log"


def read_worker_log(run_id: str) -> str:
    path = worker_log_path(run_id)
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > MAX_LOG_CHARS:
        return text[-MAX_LOG_CHARS:]
    return text


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_pass(ts: str, pass_start: str, pass_end: str | None) -> bool:
    t = _parse_ts(ts)
    if t is None:
        return True
    start = _parse_ts(pass_start)
    if start and t < start:
        return False
    if pass_end:
        end = _parse_ts(pass_end)
        if end and t >= end:
            return False
    return True


def infer_passes(audit: list[dict[str, Any]], worker_log: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Infer release/worker passes from audit run_started and worker session markers."""
    starts: list[dict[str, Any]] = []
    for a in audit:
        if a.get("event") == "run_started":
            starts.append({"timestamp": a.get("timestamp") or "", "details": a.get("details") or {}})

    for m in re.finditer(
        r"=== Worker session (\S+) resume=(True|False) ===",
        worker_log,
    ):
        ts = m.group(1)
        if not any(s.get("timestamp") == ts for s in starts):
            starts.append({"timestamp": ts, "details": {"resume": m.group(2) == "True"}})

    if not starts:
        usage = state.get("usage") or []
        first = next((u.get("started_at") for u in usage if isinstance(u, dict) and u.get("started_at")), "")
        starts = [{"timestamp": first or "", "details": {}}]

    starts.sort(key=lambda s: s.get("timestamp") or "")

    passes: list[dict[str, Any]] = []
    for i, start in enumerate(starts):
        end_ts = starts[i + 1]["timestamp"] if i + 1 < len(starts) else None
        resume = i > 0 or bool((start.get("details") or {}).get("resume"))
        passes.append(
            {
                "pass_number": i + 1,
                "label": f"Pass {i + 1}" + (" (resume)" if resume else ""),
                "started_at": start.get("timestamp") or "",
                "ended_at": end_ts or "",
                "resume": resume,
            }
        )
    return passes


def parse_worker_log_events(log_text: str) -> list[dict[str, str]]:
    """Extract flow methods and worker sessions from fz_worker console output."""
    events: list[dict[str, str]] = []
    if not log_text:
        return events

    for m in re.finditer(
        r"=== Worker session (\S+) resume=(True|False) ===",
        log_text,
    ):
        events.append(
            {
                "when": m.group(1),
                "agent": "Factory worker",
                "action": "worker_session",
                "detail": f"resume={m.group(2)}",
                "source": "worker_log",
            }
        )

    last_method: str | None = None
    for line in log_text.splitlines():
        if "Method:" not in line:
            continue
        mm = re.search(r"Method:\s+(\S+)", line)
        if not mm:
            continue
        method = mm.group(1)
        if "Running" in line or "🔄" in line:
            last_method = method
        elif "Completed" in line or "✅" in line:
            if last_method == method:
                events.append(
                    {
                        "when": "",
                        "agent": "SDLCFlow",
                        "action": method,
                        "detail": "flow method completed",
                        "source": "worker_log",
                    }
                )
                last_method = None

    # De-dupe consecutive identical flow completions
    deduped: list[dict[str, str]] = []
    for ev in events:
        if deduped and deduped[-1]["action"] == ev["action"] and deduped[-1]["detail"] == ev["detail"]:
            continue
        deduped.append(ev)
    return deduped


def _component_agent_map(state: dict[str, Any]) -> dict[str, str]:
    profile = state.get("profile") or ""
    defaults = {
        "frontend": "frontend_developer",
        "backend": "backend_developer",
        "infra": "deployment_engineer",
        "shared": "backend_developer",
    }
    if not profile:
        return defaults
    try:
        import yaml
        from config import AI_FACTORY_FZ_ROOT

        path = AI_FACTORY_FZ_ROOT / "profiles" / profile / "profile.yaml"
        if path.is_file():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            comps = data.get("components") or {}
            out = dict(defaults)
            for name, cfg in comps.items():
                if isinstance(cfg, dict) and cfg.get("agent"):
                    out[name] = str(cfg["agent"])
            return out
    except Exception:
        pass
    return defaults


def _synthetic_build_activity(state: dict[str, Any]) -> list[dict[str, str]]:
    """Reconstruct coding-agent turns from WI attempts (when usage[] is incomplete)."""
    comp_agents = _component_agent_map(state)
    wi_meta = {
        w.get("id"): w
        for w in (state.get("backlog") or {}).get("work_items") or []
        if isinstance(w, dict)
    }
    rows: list[dict[str, str]] = []
    for wid, prog in sorted(((state.get("build") or {}).get("items") or {}).items()):
        if not isinstance(prog, dict):
            continue
        wi = wi_meta.get(wid) or {}
        agent_key = comp_agents.get(wi.get("component") or "", "developer")
        attempts = int(prog.get("attempts") or 0)
        if attempts <= 0 and prog.get("status") != "done":
            continue
        n = max(attempts, 1 if prog.get("status") == "done" else 0)
        for i in range(1, n + 1):
            task = "implement_work_item" if i == 1 else "fix_work_item"
            summary = (prog.get("summary") or "")[:220]
            rows.append(
                {
                    "when": "",
                    "agent": agent_display_name(agent_key),
                    "action": task,
                    "detail": f"{wid} attempt {i}/{n}" + (f" — {summary}" if summary and i == n else ""),
                    "source": "build_state",
                    "work_item_id": wid,
                    "attempt_index": i,
                    "attempt_total": n,
                }
            )
    return rows


def _qa_activity(state: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for mid, mp in sorted(((state.get("build") or {}).get("milestones") or {}).items()):
        if not isinstance(mp, dict):
            continue
        for i, report in enumerate(mp.get("qa_reports") or [], start=1):
            if not isinstance(report, dict):
                continue
            passed = "PASS" if report.get("passed") else "FAIL"
            bugs = len(report.get("bugs") or [])
            rows.append(
                {
                    "when": "",
                    "agent": agent_display_name("qa_engineer"),
                    "action": "qa_milestone",
                    "detail": f"{mid} round {i} — {passed}, {bugs} bug(s); {(report.get('summary') or '')[:160]}",
                    "source": "qa_report",
                    "milestone_id": mid,
                    "qa_round": i,
                }
            )
            for bug in report.get("bugs") or []:
                if not isinstance(bug, dict):
                    continue
                rows.append(
                    {
                        "when": "",
                        "agent": agent_display_name("qa_engineer"),
                        "action": "qa_finding",
                        "detail": f"{bug.get('id', '')} [{bug.get('severity', '')}] {bug.get('title', '')}",
                        "source": "qa_report",
                    }
                )
    return rows


def git_commit_times(run_root: Path) -> dict[str, str]:
    if not (run_root / ".git").is_dir():
        return {}
    try:
        proc = subprocess.run(
            ["git", "-C", str(run_root), "log", "--format=%H|%aI"],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if proc.returncode != 0:
        return {}
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "|" not in line:
            continue
        sha, ts = line.split("|", 1)
        sha = sha.strip()
        ts = ts.strip()
        if sha and ts:
            out[sha] = ts
            out[sha[:12]] = ts
    return out


def qa_report_file_times(run_root: Path) -> dict[tuple[str, int], str]:
    times: dict[tuple[str, int], str] = {}
    reports = run_root / "reports"
    if not reports.is_dir():
        return times
    for path in reports.glob("qa_*.md"):
        m = re.match(r"qa_(M\d+)_round(\d+)\.md", path.name, re.I)
        if not m:
            continue
        mid = m.group(1).upper()
        rnd = int(m.group(2))
        ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        times[(mid, rnd)] = ts
    return times


def assign_inferred_timestamps(
    rows: list[dict[str, Any]],
    state: dict[str, Any],
    run_root: Path,
    passes: list[dict[str, Any]],
) -> None:
    """Fill missing `when` using git commits, QA report files, and pass-window interpolation."""
    commit_times = git_commit_times(run_root)
    qa_times = qa_report_file_times(run_root)
    build_items = (state.get("build") or {}).get("items") or {}

    for row in rows:
        if row.get("when"):
            continue
        wid = row.get("work_item_id")
        if wid and row.get("attempt_index") == row.get("attempt_total"):
            commit = (build_items.get(wid) or {}).get("commit")
            if commit:
                ts = commit_times.get(str(commit)) or commit_times.get(str(commit)[:12])
                if ts:
                    row["when"] = ts
                    row["when_inferred"] = "git_commit"
                    continue
        mid = row.get("milestone_id")
        rnd = row.get("qa_round")
        if mid and rnd and row.get("action") == "qa_milestone":
            ts = qa_times.get((str(mid).upper(), int(rnd)))
            if ts:
                row["when"] = ts
                row["when_inferred"] = "qa_report_mtime"
                continue

    for p in passes:
        pass_num = p.get("pass_number")
        start = _parse_ts(p.get("started_at") or "") or datetime(1970, 1, 1, tzinfo=timezone.utc)
        end = _parse_ts(p.get("ended_at") or "") or datetime.now(timezone.utc)
        if end <= start:
            end = start + timedelta(hours=4)

        pass_rows = [r for r in rows if r.get("pass") == pass_num or (pass_num == 1 and r.get("pass") is None)]
        untimed = [r for r in pass_rows if not r.get("when")]
        if not untimed:
            continue
        timed_in_pass = sorted(
            [r for r in pass_rows if r.get("when")],
            key=lambda r: r.get("when") or "",
        )
        cursor = start
        if timed_in_pass:
            last = _parse_ts(timed_in_pass[-1].get("when") or "")
            if last and last > cursor:
                cursor = last
        step = max(timedelta(seconds=30), (end - cursor) / max(len(untimed), 1))
        for i, row in enumerate(untimed):
            ts = cursor + step * (i + 1)
            if ts >= end:
                ts = end - timedelta(seconds=1)
            row["when"] = ts.isoformat()
            row["when_inferred"] = row.get("when_inferred") or "pass_window_interpolation"
            if row.get("pass") is None and pass_num == 1:
                row["pass"] = 1


def transcript_activity_rows(entries: list[dict[str, Any]], passes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        when = entry.get("started_at") or entry.get("ended_at") or ""
        detail = entry.get("task_key") or ""
        if entry.get("assistant_result"):
            detail += " · " + str(entry["assistant_result"])[:120]
        rows.append(
            {
                "when": when,
                "pass": _pass_for_time(when, passes) if when else None,
                "agent": agent_display_name(entry.get("agent") or ""),
                "action": f"transcript:{entry.get('task_key') or 'agent'}",
                "detail": detail[:320],
                "source": "transcript",
                "transcript_id": f"{when}-{entry.get('task_key')}-{entry.get('model')}",
            }
        )
    return rows


def build_agent_activity(
    state: dict[str, Any],
    audit: list[dict[str, Any]],
    worker_log: str,
    passes: list[dict[str, Any]],
    *,
    run_root: Path | None = None,
    transcript_entries: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []

    for u in state.get("usage") or []:
        if not isinstance(u, dict):
            continue
        when = u.get("started_at") or u.get("ended_at") or ""
        agent = agent_display_name(u.get("agent") or "")
        task = u.get("task_key") or u.get("phase") or "task"
        model = u.get("model") or ""
        dur = u.get("duration_ms") or 0
        detail = model
        if dur:
            detail += f" · {dur:,} ms"
        if u.get("total_tokens"):
            detail += f" · {u['total_tokens']:,} tokens"
        pass_num = _pass_for_time(when, passes)
        rows.append(
            {
                "when": when,
                "pass": pass_num,
                "agent": agent,
                "action": task,
                "detail": detail,
                "source": "usage",
            }
        )

    for g in state.get("gate_history") or []:
        if not isinstance(g, dict):
            continue
        when = g.get("decided_at") or ""
        rows.append(
            {
                "when": when,
                "pass": _pass_for_time(when, passes),
                "agent": g.get("decided_by") or "gate",
                "action": f"gate:{g.get('gate')}",
                "detail": "approved" if g.get("approved") else f"rejected — {(g.get('feedback') or '')[:200]}",
                "source": "gate",
            }
        )

    for a in audit:
        when = a.get("timestamp") or ""
        rows.append(
            {
                "when": when,
                "pass": _pass_for_time(when, passes),
                "agent": agent_display_name(a.get("agent") or "console"),
                "action": a.get("event") or "audit",
                "detail": json.dumps(a.get("details") or {}, default=str)[:240],
                "source": "audit",
            }
        )

    for ev in parse_worker_log_events(worker_log):
        rows.append({**ev, "pass": _pass_for_time(ev.get("when") or "", passes)})

    for ev in _synthetic_build_activity(state):
        rows.append({**ev, "pass": None})

    for ev in _qa_activity(state):
        rows.append({**ev, "pass": None})

    if transcript_entries:
        rows.extend(transcript_activity_rows(transcript_entries, passes))

    if run_root is not None:
        assign_inferred_timestamps(rows, state, run_root, passes)

    rows.sort(key=lambda r: (r.get("when") or "9999", r.get("action") or ""))
    total = len(rows)
    truncated = max(0, total - MAX_AGENT_ACTIVITY)
    stats = {"activity_total": total, "activity_truncated": truncated, "timeline_cap": MAX_TIMELINE}
    return rows[:MAX_AGENT_ACTIVITY], stats


def _pass_for_time(ts: str, passes: list[dict[str, Any]]) -> int | None:
    if not passes:
        return None
    for p in passes:
        if _in_pass(ts, p.get("started_at") or "", p.get("ended_at") or None):
            return int(p.get("pass_number") or 0)
    return passes[-1].get("pass_number")


def build_timeline_extended(
    state: dict[str, Any],
    audit: list[dict[str, Any]],
    agent_activity: list[dict[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Unified timeline from agent_activity (includes inferred timestamps)."""
    events: list[tuple[str, str, str]] = []
    for row in agent_activity:
        when = row.get("when") or ""
        if not when:
            continue
        label = f"{row.get('agent', '')} — {row.get('action', '')}"
        if row.get("pass"):
            label = f"[Pass {row['pass']}] {label}"
        if row.get("when_inferred"):
            label += f" ({row['when_inferred']})"
        events.append((when, label, row.get("detail") or ""))

    events.sort(key=lambda e: e[0])
    total = len(events)
    truncated = max(0, total - MAX_TIMELINE)
    if truncated:
        events = events[:MAX_TIMELINE]
    meta = {"timeline_total": total, "timeline_truncated": truncated}
    return [{"when": w, "what": what, "detail": det} for w, what, det in events], meta


def pass_summaries(
    passes: list[dict[str, Any]],
    agent_activity: list[dict[str, Any]],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Attach activity counts and WI progress hints per pass."""
    out: list[dict[str, Any]] = []
    for p in passes:
        num = p.get("pass_number")
        acts = [a for a in agent_activity if a.get("pass") == num]
        out.append(
            {
                **p,
                "activity_count": len(acts),
                "usage_events": len([a for a in acts if a.get("source") == "usage"]),
                "audit_events": len([a for a in acts if a.get("source") == "audit"]),
            }
        )
    if len(out) == 1:
        out[0]["note"] = "Single worker session detected (or no audit run_started markers)."
    return out
