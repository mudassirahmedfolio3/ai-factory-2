"""Guardrail wrapper with the same contract as the pipeline's `artifact_guardrail` (crews/base.py).

A guardrail receives the task output and returns (True, output) or (False, message); the runner feeds the
message back to the model for a retry. Kept here so this package imports nothing from the pipeline."""

from typing import Any, Callable

from pydantic import BaseModel


def artifact_guardrail(model: type[BaseModel], check: Callable[[Any], list[str]]) -> Callable[[Any], tuple[bool, Any]]:
    """Wrap a list-of-errors check as a task guardrail."""

    def guardrail(output: Any) -> tuple[bool, Any]:
        artifact = output.pydantic
        if artifact is None:
            try:
                artifact = model.model_validate_json(output.raw)
            except Exception as e:
                return False, f"Output does not match the required structure: {e}"
        errors = check(artifact)
        if errors:
            return False, "Fix these problems and return the full corrected output:\n- " + "\n- ".join(errors)
        return True, artifact.model_dump_json()

    return guardrail
