"""Usage tracker budget tests."""

from __future__ import annotations

import os

from ai_factory.usage_tracker import UsageTracker


def test_usage_percent_with_budget(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_TOKEN_BUDGET", "1000")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    tracker = UsageTracker()
    tracker.record_call(
        usage={"prompt_tokens": 400, "completion_tokens": 100},
        estimated=False,
        agent="Product Manager",
        task="Write PRD",
        model="claude-sonnet-4-6",
    )
    snap = tracker.snapshot()
    assert snap.total_tokens == 500
    assert snap.usage_percent == 50.0
    assert snap.provider == "anthropic"
    assert len(snap.activities) == 1
    assert snap.activities[0]["agent"] == "Product Manager"
    assert snap.activities[0]["model"] == "claude-sonnet-4-6"


def test_budget_warning(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_TOKEN_BUDGET", "100")
    tracker = UsageTracker()
    tracker.record_call(usage={"prompt_tokens": 95, "completion_tokens": 0}, estimated=False)
    assert "90%" in (tracker.budget_warning() or "")


def test_running_and_completed_activity(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cursor_cli")
    tracker = UsageTracker()
    call_id = tracker.begin_activity(
        call_id="call-1",
        model="auto",
        agent="Flutter Engineer",
        task="Generate architecture sketch",
    )
    snap = tracker.snapshot()
    assert snap.activities[-1]["status"] == "running"
    assert snap.activities[-1]["label"] == "Flutter Engineer · Generate architecture sketch"

    tracker.finish_activity(
        call_id,
        prompt="x" * 400,
        completion="y" * 200,
        estimated=True,
    )
    done = tracker.snapshot().activities[-1]
    assert done["status"] == "completed"
    assert done["total_tokens"] > 0


def test_finish_activity_is_idempotent_for_tokens():
    tracker = UsageTracker()
    call_id = tracker.begin_activity(call_id="dup")
    tracker.finish_activity(
        call_id,
        usage={"prompt_tokens": 100, "completion_tokens": 20},
        estimated=False,
    )
    tracker.finish_activity(
        call_id,
        usage={"prompt_tokens": 999, "completion_tokens": 999},
        estimated=False,
    )
    snap = tracker.snapshot()
    assert snap.total_tokens == 120
    assert snap.llm_calls == 1
    assert snap.activities[-1]["total_tokens"] == 120
