"""Thread-safe LLM usage tracking for live run state."""

from __future__ import annotations

import json
import os
import threading
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

_call_context: ContextVar[dict[str, str]] = ContextVar(
    "llm_call_context", default={"agent": "", "task": "", "model": ""}
)


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _token_budget() -> int:
    raw = os.getenv("ANTHROPIC_TOKEN_BUDGET") or os.getenv("LLM_TOKEN_BUDGET") or "0"
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def _provider_label() -> str:
    return os.getenv("LLM_PROVIDER", "openai").strip().lower()


def _display_model(model: str) -> str:
    raw = (model or "").strip()
    if raw and raw != "auto":
        return raw.split("/")[-1]
    provider = _provider_label()
    if provider in ("cursor_cli", "cursor_proxy"):
        return "Cursor"
    if provider == "anthropic":
        return os.getenv("ANTHROPIC_STRONG_MODEL", "claude-sonnet-4-6")
    if provider == "groq":
        return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return os.getenv("LLM_STRONG_MODEL", "gpt-4o")


def _activity_label(agent: str, task: str) -> str:
    agent = (agent or "").strip()
    task = (task or "").strip()
    if agent and task:
        return f"{agent} · {task}"
    return agent or task or "LLM call"


@dataclass
class UsageActivity:
    id: str
    model: str
    agent: str
    task: str
    label: str
    status: str  # running | completed | failed
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated: bool = False
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "model": self.model,
            "agent": self.agent,
            "task": self.task,
            "label": self.label,
            "status": self.status,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated": self.estimated,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


@dataclass
class UsageSnapshot:
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_calls: int = 0
    actual_calls: int = 0
    token_budget: int = 0
    usage_percent: float = 0.0
    provider: str = ""
    activities: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, int | float | str | list[dict[str, Any]]]:
        return {
            "llm_calls": self.llm_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_calls": self.estimated_calls,
            "actual_calls": self.actual_calls,
            "token_budget": self.token_budget,
            "usage_percent": self.usage_percent,
            "provider": self.provider,
            "activities": self.activities,
        }


class UsageTracker:
    _MAX_ACTIVITIES = 40

    @staticmethod
    def push_call_context(*, agent: str = "", task: str = "", model: str = "") -> None:
        _call_context.set(
            {
                "agent": agent.strip(),
                "task": task.strip(),
                "model": model.strip(),
            }
        )

    @staticmethod
    def pop_call_context() -> None:
        _call_context.set({"agent": "", "task": "", "model": ""})

    @staticmethod
    def peek_call_context() -> dict[str, str]:
        return dict(_call_context.get())

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._llm_calls = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._estimated_calls = 0
        self._actual_calls = 0
        self._activities: list[UsageActivity] = []
        self._activity_index: dict[str, UsageActivity] = {}

    def reset(self) -> None:
        with self._lock:
            self._llm_calls = 0
            self._prompt_tokens = 0
            self._completion_tokens = 0
            self._estimated_calls = 0
            self._actual_calls = 0
            self._activities = []
            self._activity_index = {}

    def begin_activity(
        self,
        *,
        call_id: str | None = None,
        model: str = "",
        agent: str = "",
        task: str = "",
    ) -> str:
        ctx = self.peek_call_context()
        agent = agent or ctx.get("agent", "")
        task = task or ctx.get("task", "")
        model = model or ctx.get("model", "")
        activity_id = call_id or str(uuid.uuid4())
        display_model = _display_model(model)
        activity = UsageActivity(
            id=activity_id,
            model=display_model,
            agent=agent.strip(),
            task=task.strip(),
            label=_activity_label(agent, task),
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._activities.append(activity)
            self._activity_index[activity_id] = activity
            if len(self._activities) > self._MAX_ACTIVITIES:
                removed = self._activities.pop(0)
                self._activity_index.pop(removed.id, None)
        self._patch_live_run_state()
        return activity_id

    def finish_activity(
        self,
        activity_id: str,
        *,
        prompt: str = "",
        completion: str = "",
        usage: dict[str, Any] | None = None,
        estimated: bool = True,
        status: str = "completed",
        model: str = "",
        agent: str = "",
        task: str = "",
    ) -> None:
        prompt_t, completion_t, is_estimated = self._token_counts(
            prompt=prompt,
            completion=completion,
            usage=usage,
            estimated=estimated,
        )
        ctx = self.peek_call_context()
        agent = agent or ctx.get("agent", "")
        task = task or ctx.get("task", "")
        model = model or ctx.get("model", "")

        with self._lock:
            activity = self._activity_index.get(activity_id)
            already_done = (
                activity is not None
                and activity.status == "completed"
                and status == "completed"
            )
            if activity is None:
                activity = UsageActivity(
                    id=activity_id,
                    model=_display_model(model),
                    agent=agent.strip(),
                    task=task.strip(),
                    label=_activity_label(agent, task),
                    status=status,
                    started_at=datetime.now(timezone.utc).isoformat(),
                )
                self._activities.append(activity)
                self._activity_index[activity_id] = activity
            if model:
                activity.model = _display_model(model)
            if agent:
                activity.agent = agent.strip()
            if task:
                activity.task = task.strip()
            activity.label = _activity_label(activity.agent, activity.task)
            activity.status = status
            activity.completed_at = datetime.now(timezone.utc).isoformat()

            if not already_done:
                activity.prompt_tokens = prompt_t
                activity.completion_tokens = completion_t
                activity.total_tokens = prompt_t + completion_t
                activity.estimated = is_estimated
                self._llm_calls += 1
                self._prompt_tokens += prompt_t
                self._completion_tokens += completion_t
                if is_estimated:
                    self._estimated_calls += 1
                else:
                    self._actual_calls += 1

            if len(self._activities) > self._MAX_ACTIVITIES:
                removed = self._activities.pop(0)
                self._activity_index.pop(removed.id, None)

        self._patch_live_run_state()

    def record_call(
        self,
        *,
        prompt: str = "",
        completion: str = "",
        usage: dict[str, Any] | None = None,
        estimated: bool = True,
        model: str = "",
        agent: str = "",
        task: str = "",
        call_id: str | None = None,
    ) -> None:
        """Record a completed LLM call (creates activity if call_id was not started)."""
        activity_id = call_id or str(uuid.uuid4())
        if call_id and call_id in self._activity_index:
            self.finish_activity(
                activity_id,
                prompt=prompt,
                completion=completion,
                usage=usage,
                estimated=estimated,
                model=model,
                agent=agent,
                task=task,
            )
            return

        self.finish_activity(
            activity_id,
            prompt=prompt,
            completion=completion,
            usage=usage,
            estimated=estimated,
            model=model,
            agent=agent,
            task=task,
        )

    def _token_counts(
        self,
        *,
        prompt: str,
        completion: str,
        usage: dict[str, Any] | None,
        estimated: bool,
    ) -> tuple[int, int, bool]:
        prompt_t = completion_t = 0
        is_estimated = estimated
        if usage:
            prompt_t = int(
                usage.get("prompt_tokens") or usage.get("input_tokens") or 0
            )
            completion_t = int(
                usage.get("completion_tokens") or usage.get("output_tokens") or 0
            )
            if not prompt_t and not completion_t:
                total = int(usage.get("total_tokens") or 0)
                if total:
                    prompt_t = int(total * 0.7)
                    completion_t = total - prompt_t
            is_estimated = False
        if not prompt_t:
            prompt_t = _estimate_tokens(prompt)
        if not completion_t:
            completion_t = _estimate_tokens(completion)
        return prompt_t, completion_t, is_estimated

    def snapshot(self) -> UsageSnapshot:
        with self._lock:
            total = self._prompt_tokens + self._completion_tokens
            budget = _token_budget()
            pct = round((total / budget) * 100, 1) if budget > 0 else 0.0
            if budget > 0:
                pct = min(100.0, pct)
            activities = [a.to_dict() for a in self._activities[-12:]]
            return UsageSnapshot(
                llm_calls=self._llm_calls,
                prompt_tokens=self._prompt_tokens,
                completion_tokens=self._completion_tokens,
                total_tokens=total,
                estimated_calls=self._estimated_calls,
                actual_calls=self._actual_calls,
                token_budget=budget,
                usage_percent=pct,
                provider=_provider_label(),
                activities=activities,
            )

    def budget_warning(self) -> str | None:
        snap = self.snapshot()
        if snap.token_budget <= 0:
            return None
        if snap.usage_percent >= 100:
            return f"Token budget reached ({snap.total_tokens:,} / {snap.token_budget:,})."
        if snap.usage_percent >= 90:
            return f"Token budget at {snap.usage_percent}% ({snap.total_tokens:,} / {snap.token_budget:,})."
        return None

    def _patch_live_run_state(self) -> None:
        try:
            from ai_factory.utils import RUN_STATE_PATH

            if not RUN_STATE_PATH.exists():
                return
            state = json.loads(RUN_STATE_PATH.read_text(encoding="utf-8"))
            if state.get("status") != "running":
                return
            snap = self.snapshot()
            state["usage"] = {
                **snap.to_dict(),
                "budget_warning": self.budget_warning(),
            }
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            RUN_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception:
            return


_tracker = UsageTracker()


def get_usage_tracker() -> UsageTracker:
    return _tracker
