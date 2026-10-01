"""Runs one configured task with one agent, with structured output and model fallback."""

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Generic, TypeVar

from crewai import Crew, Process, Task
from crewai.tasks.task_output import TaskOutput
from pydantic import BaseModel

from agentic_sdlc.registry.agents import AgentRegistry
from agentic_sdlc.settings import load_config
from agentic_sdlc.state import UsageRecord

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
Guardrail = Callable[[TaskOutput], tuple[bool, Any]]

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


class PhaseError(RuntimeError):
    """A task failed on every configured model."""


class UsageLimitError(PhaseError):
    """The model account's usage limit is reached: retrying (or another model on the same
    account) cannot help until it resets. The run should stop and say when to resume."""


_LIMIT_MARKERS = ("hit your session limit", "usage limit", "hit your limit", "rate limit reached for your plan")


def is_usage_limit(text: str) -> bool:
    return any(m in (text or "").lower() for m in _LIMIT_MARKERS)


@dataclass
class TaskResult(Generic[T]):
    artifact: T
    usage: UsageRecord


def feedback_text(feedback: str) -> str:
    """Appended to a task when its previous attempt was rejected by guardrails."""
    return (f"\n\nYour previous attempt was rejected by automated checks. Fix all of these:\n{feedback}"
            if feedback else "")


def fill_template(template: str, values: dict[str, Any]) -> str:
    """Replace {name} placeholders in one pass, so braces inside values are left alone."""

    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            raise KeyError(f"Missing value for placeholder '{{{key}}}'")
        return str(values[key])

    return _PLACEHOLDER.sub(sub, template)


def artifact_guardrail(model: type[T], check: Callable[[T], list[str]]) -> Guardrail:
    """Wrap a list-of-errors check as a crewai task guardrail."""

    def guardrail(output: TaskOutput) -> tuple[bool, Any]:
        artifact = output.pydantic
        if artifact is None:
            try:
                artifact = model.model_validate_json(output.raw)
            except Exception as e:
                return False, f"Output does not match the required structure: {e}"
        errors = check(artifact)  # type: ignore[arg-type]
        if errors:
            return False, "Fix these problems and return the full corrected output:\n- " + "\n- ".join(errors)
        return True, output

    return guardrail


class TaskRunner:
    def __init__(self, agents: AgentRegistry, tasks: dict[str, dict[str, Any]] | None = None, verbose: bool = False):
        self.agents = agents
        self.tasks = tasks if tasks is not None else load_config("tasks")
        self.verbose = verbose

    def run(
        self,
        phase: str,
        task_key: str,
        inputs: dict[str, Any],
        output_model: type[T],
        guardrail: Guardrail | None = None,
        agent_key: str | None = None,
        with_tools: bool = True,
        feedback: str = "",
    ) -> TaskResult[T]:
        """Run a task from tasks.yaml. `agent_key` overrides the task's default agent;
        with_tools=False runs it without the agent's tools (review-only tasks)."""
        tdef = self.tasks[task_key]
        agent_key = agent_key or tdef["agent"]
        description = fill_template(tdef["description"], inputs) + feedback_text(feedback)
        last_error: Exception | None = None

        for model in self.agents.models.spec_for(agent_key).candidates():
            agent = self.agents.build(agent_key, model, with_tools=with_tools)
            task = Task(
                description=description,
                expected_output=tdef["expected_output"].strip(),
                agent=agent,
                output_pydantic=output_model,
                guardrail=guardrail,
                guardrail_max_retries=2,
            )
            crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=self.verbose)
            started = datetime.now(timezone.utc)
            t0 = time.perf_counter()
            try:
                out = crew.kickoff()
            except Exception as e:  # provider errors, guardrail exhaustion, bad output
                if is_usage_limit(str(e)):
                    raise UsageLimitError(f"Usage limit reached ({model}): {e}") from e
                log.warning("Task %s failed on %s: %s", task_key, model, e)
                last_error = e
                continue
            ended = datetime.now(timezone.utc)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            artifact = out.pydantic or output_model.model_validate_json(out.raw)
            usage = out.token_usage
            return TaskResult(
                artifact=artifact,
                usage=UsageRecord(
                    phase=phase,
                    agent=agent_key,
                    model=model,
                    prompt_tokens=usage.prompt_tokens,
                    cached_prompt_tokens=usage.cached_prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    task_key=task_key,
                    duration_ms=duration_ms,
                    started_at=started.isoformat(),
                    ended_at=ended.isoformat(),
                ),
            )
        raise PhaseError(f"Task '{task_key}' failed on all models for '{agent_key}': {last_error}")
