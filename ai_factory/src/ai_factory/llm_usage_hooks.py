"""Register CrewAI event listeners for accurate LLM token usage (Anthropic/OpenAI/etc.)."""

from __future__ import annotations

from ai_factory.usage_tracker import get_usage_tracker

_registered = False


def _agent_label(event: object) -> str:
    role = getattr(event, "agent_role", None) or ""
    if role:
        return str(role).strip()
    agent = getattr(event, "from_agent", None)
    if agent is not None:
        for attr in ("role", "name"):
            value = getattr(agent, attr, None)
            if value:
                return str(value).strip()
    return ""


def _task_label(event: object) -> str:
    name = getattr(event, "task_name", None) or ""
    if name:
        return str(name).strip()
    task = getattr(event, "from_task", None)
    if task is not None:
        for attr in ("name", "description"):
            value = getattr(task, attr, None)
            if value:
                text = str(value).strip()
                return text[:120] if len(text) > 120 else text
    return ""


def register_usage_listeners() -> None:
    """Hook CrewAI LLM events for token usage and live model activity."""
    global _registered
    if _registered:
        return
    _registered = True

    try:
        from crewai.events.event_bus import crewai_event_bus
        from crewai.events.types.llm_events import LLMCallCompletedEvent, LLMCallStartedEvent
    except ImportError:
        return

    @crewai_event_bus.on(LLMCallStartedEvent)
    def _on_llm_call_started(_source: object, event: LLMCallStartedEvent) -> None:
        call_id = event.call_id or event.event_id
        if not call_id:
            return
        tracker = get_usage_tracker()
        ctx = tracker.peek_call_context()
        get_usage_tracker().begin_activity(
            call_id=str(call_id),
            model=str(event.model or ctx.get("model", "")),
            agent=_agent_label(event) or ctx.get("agent", ""),
            task=_task_label(event) or ctx.get("task", ""),
        )

    @crewai_event_bus.on(LLMCallCompletedEvent)
    def _on_llm_call_completed(_source: object, event: LLMCallCompletedEvent) -> None:
        call_id = event.call_id or event.started_event_id or event.event_id
        if not call_id:
            return
        usage = event.usage
        tracker = get_usage_tracker()
        ctx = tracker.peek_call_context()
        tracker.finish_activity(
            str(call_id),
            usage=usage,
            estimated=not bool(usage),
            model=str(event.model or ctx.get("model", "")),
            agent=_agent_label(event) or ctx.get("agent", ""),
            task=_task_label(event) or ctx.get("task", ""),
        )
