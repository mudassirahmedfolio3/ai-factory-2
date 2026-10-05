"""Runs one configured task with one agent, with structured output and model fallback."""

import json
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

# CrewAI 1.15.x: output_pydantic + task guardrails skip initial export, then retry via
# _export_output / LLM converter paths that can raise "Agent must be provided if converter_cls
# is not specified." We validate in TaskRunner instead (raw task output only).
_MAX_VALIDATION_RETRIES = 2

_JSON_TASK_SUFFIX = (
    "\n\nOutput format: respond with one JSON object only (no markdown wrappers or prose). "
    "Put OpenAPI and Prisma content in the openapi_yaml and prisma_schema string fields."
)



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


def _retryable_output_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        m in text
        for m in (
            "json",
            "pydantic",
            "convert",
            "validation",
            "structure",
            "parse",
            "no json object",
            "final answer",
        )
    )


def parse_structured_output(model: type[T], raw: str | BaseModel) -> T:
    """Parse Crew final answers (plain JSON or text wrapping a JSON object) into ``model``."""
    if isinstance(raw, BaseModel):
        return model.model_validate(raw.model_dump())
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty output")
    if "Final Answer:" in text:
        text = text.split("Final Answer:")[-1].strip()
    if "```" in text:
        for part in text.split("```"):
            chunk = part.strip()
            if chunk.lower().startswith("json"):
                chunk = chunk[4:].strip()
            if chunk.startswith("{"):
                text = chunk
                break
    try:
        return model.model_validate_json(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in output")
    return model.model_validate(json.loads(text[start : end + 1]))


def artifact_guardrail(model: type[T], check: Callable[[T], list[str]]) -> Guardrail:
    """Wrap a list-of-errors check as a crewai task guardrail."""

    def guardrail(output: TaskOutput) -> tuple[bool, Any]:
        artifact = output.pydantic
        if artifact is None:
            try:
                artifact = parse_structured_output(model, output.raw)
            except Exception as e:
                return False, f"Output does not match the required structure: {e}"
        errors = check(artifact)  # type: ignore[arg-type]
        if errors:
            return False, "Fix these problems and return the full corrected output:\n- " + "\n- ".join(errors)
        # Return canonical JSON so CrewAI can populate task pydantic without an LLM re-converter
        # (avoids CrewAI bug: converter fallback with agent=None when guardrails are enabled).
        return True, artifact.model_dump_json()

    return guardrail


class TaskRunner:
    def __init__(
        self,
        agents: AgentRegistry,
        tasks: dict[str, dict[str, Any]] | None = None,
        verbose: bool = False,
        workspace: Any | None = None,
    ):
        self.agents = agents
        self.tasks = tasks if tasks is not None else load_config("tasks")
        self.verbose = verbose
        self.workspace = workspace

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
        last_error: Exception | None = None

        use_runner_validation = guardrail is not None
        max_attempts = (_MAX_VALIDATION_RETRIES + 1) if use_runner_validation else 1

        for model in self.agents.models.spec_for(agent_key).candidates():
            agent = self.agents.build(agent_key, model, with_tools=with_tools)
            validation_feedback = feedback
            model_failed = False

            for _attempt in range(max_attempts):
                attempt_description = fill_template(tdef["description"], inputs) + feedback_text(validation_feedback)
                if use_runner_validation:
                    attempt_description += _JSON_TASK_SUFFIX
                # Structured output on the task, but no Crew guardrail (we validate in this loop).
                task = Task(
                    description=attempt_description,
                    expected_output=(tdef["expected_output"].strip() + (" (as JSON)" if use_runner_validation else "")),
                    agent=agent,
                    output_pydantic=output_model,
                )
                crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=self.verbose)
                started = datetime.now(timezone.utc)
                t0 = time.perf_counter()
                try:
                    out = crew.kickoff()
                except Exception as e:  # provider errors, guardrail exhaustion, bad output
                    if is_usage_limit(str(e)):
                        raise UsageLimitError(f"Usage limit reached ({model}): {e}") from e
                    if use_runner_validation and _retryable_output_error(e) and _attempt + 1 < max_attempts:
                        validation_feedback = (
                            f"Your last response could not be parsed or validated: {e}. "
                            "Return one complete JSON object matching the schema."
                        )
                        log.info("Task %s kickoff retry %s/%s on %s: %s", task_key, _attempt + 1, max_attempts, model, e)
                        continue
                    log.warning("Task %s failed on %s: %s", task_key, model, e)
                    last_error = e
                    model_failed = True
                    break
                ended = datetime.now(timezone.utc)
                duration_ms = int((time.perf_counter() - t0) * 1000)
                raw = getattr(out, "raw", "") or ""

                try:
                    artifact = out.pydantic if getattr(out, "pydantic", None) is not None else parse_structured_output(
                        output_model, raw
                    )
                except Exception as e:
                    validation_feedback = f"Output does not match the required structure: {e}"
                    if _attempt + 1 < max_attempts:
                        log.info("Task %s parse retry %s/%s on %s", task_key, _attempt + 1, max_attempts, model)
                        continue
                    last_error = e
                    model_failed = True
                    break

                if guardrail is not None:
                    task_output = TaskOutput(
                        description=task.description or "",
                        raw=raw if isinstance(raw, str) else str(raw),
                        pydantic=artifact,
                        agent=getattr(agent, "role", agent_key),
                    )
                    ok, guard_result = guardrail(task_output)
                    if not ok:
                        validation_feedback = guard_result if isinstance(guard_result, str) else str(guard_result)
                        if _attempt + 1 < max_attempts:
                            log.info("Task %s guardrail retry %s/%s on %s", task_key, _attempt + 1, max_attempts, model)
                            continue
                        last_error = RuntimeError(validation_feedback)
                        model_failed = True
                        break

                usage = out.token_usage
                if self.workspace is not None:
                    try:
                        from agentic_sdlc.build.transcript_log import append_transcript

                        append_transcript(
                            self.workspace.root,
                            started_at=started.isoformat(),
                            ended_at=ended.isoformat(),
                            duration_ms=duration_ms,
                            phase=phase,
                            agent_key=agent_key,
                            task_key=task_key,
                            model=model,
                            workdir=".",
                            success=True,
                            exit_code=0,
                            prompt=attempt_description,
                            data={"result": raw, "structured_output": artifact.model_dump(mode="json")},
                            stdout=raw if isinstance(raw, str) else str(raw),
                        )
                    except OSError:
                        pass
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

            if model_failed:
                continue
        raise PhaseError(f"Task '{task_key}' failed on all models for '{agent_key}': {last_error}")
