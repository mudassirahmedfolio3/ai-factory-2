"""Unified LLM invocation for basic-path and one-shot calls."""

from __future__ import annotations

from typing import Any

from crewai import LLM

from ai_factory.cursor_agent_llm import CursorAgentLLM
from ai_factory.usage_tracker import get_usage_tracker


def _llm_model_name(llm: Any) -> str:
    if isinstance(llm, str):
        return llm
    return str(getattr(llm, "model", "") or "")


def invoke_llm(
    llm: Any,
    prompt: str,
    *,
    agent_role: str = "",
    task_name: str = "",
) -> str:
    """Call any CrewAI-compatible LLM (AnthropicCompletion, LLM, Cursor CLI, etc.)."""
    tracker = get_usage_tracker()
    model = _llm_model_name(llm)

    if isinstance(llm, CursorAgentLLM):
        return str(
            llm.call(
                prompt,
                from_agent={"role": agent_role} if agent_role else None,
                from_task={"name": task_name} if task_name else None,
            )
        ).strip()

    if isinstance(llm, str):
        llm = LLM(model=llm)

    call = getattr(llm, "call", None)
    if callable(call):
        # CrewAI LLM providers emit LLMCall* events — hooks record usage + activity.
        tracker.push_call_context(agent=agent_role, task=task_name, model=model)
        try:
            result = call(prompt)
        except Exception as exc:
            tracker.pop_call_context()
            msg = str(exc)
            if "not_found_error" in msg or "model:" in msg.lower():
                raise RuntimeError(
                    f"Claude model not found for your API key. "
                    f"Set ANTHROPIC_STRONG_MODEL=claude-sonnet-4-6 and "
                    f"ANTHROPIC_FAST_MODEL=claude-haiku-4-5 in ai_factory/.env. "
                    f"Original: {msg}"
                ) from exc
            raise
        tracker.pop_call_context()
        return str(result).strip()

    raise RuntimeError(
        f"Unsupported LLM type for basic path: {type(llm)} — expected .call() method."
    )
