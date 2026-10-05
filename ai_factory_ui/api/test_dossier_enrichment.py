"""Dossier enrichment (passes, agent activity) — read-only."""

from __future__ import annotations

from dossier.enrichment import assign_inferred_timestamps, build_agent_activity, infer_passes, parse_worker_log_events


def test_infer_passes_from_audit() -> None:
    audit = [
        {"event": "run_started", "timestamp": "2026-10-03T04:47:29+00:00", "agent": "console"},
        {"event": "run_failed", "timestamp": "2026-10-03T07:03:52+00:00", "agent": "console"},
        {"event": "run_started", "timestamp": "2026-10-03T07:12:46+00:00", "agent": "console"},
    ]
    passes = infer_passes(audit, "", {})
    assert len(passes) == 2
    assert passes[0]["pass_number"] == 1
    assert passes[1]["label"].endswith("(resume)")


def test_parse_worker_log_flow_methods() -> None:
    log = """
=== Worker session 2026-10-03T10:00:06+00:00 resume=True ===
│  Method: build_phase                                                         │
│  Method: build_phase                                                         │
"""
    events = parse_worker_log_events(log)
    assert any(e["action"] == "worker_session" for e in events)


def test_assign_inferred_timestamps_from_qa_file(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir(parents=True)
    qa_file = reports / "qa_M1_round1.md"
    qa_file.write_text("# qa", encoding="utf-8")
    state = {"build": {"milestones": {"M1": {"qa_reports": [{"passed": True, "summary": "ok"}]}}}}
    rows = [
        {
            "when": "",
            "action": "qa_milestone",
            "milestone_id": "M1",
            "qa_round": 1,
            "pass": 1,
            "source": "qa_report",
        }
    ]
    passes = [{"pass_number": 1, "started_at": "2026-01-01T00:00:00+00:00", "ended_at": ""}]
    assign_inferred_timestamps(rows, state, tmp_path, passes)
    assert rows[0].get("when")
    assert rows[0].get("when_inferred") == "qa_report_mtime"


def test_agent_activity_includes_build_attempts() -> None:
    state = {
        "profile": "",
        "backlog": {
            "work_items": [
                {"id": "WI-001", "component": "frontend", "title": "Setup"},
            ]
        },
        "build": {
            "items": {
                "WI-001": {"status": "done", "attempts": 2, "summary": "Done scaffold"},
            }
        },
        "usage": [],
    }
    rows, _stats = build_agent_activity(state, [], "", [{"pass_number": 1, "started_at": "", "ended_at": ""}])
    actions = [r["action"] for r in rows if r.get("source") == "build_state"]
    assert "implement_work_item" in actions
    assert "fix_work_item" in actions
