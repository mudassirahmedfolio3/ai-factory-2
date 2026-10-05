"""Runs real crewai Crews through TaskRunner with a scripted fake LLM (no API calls)."""

import json
from typing import Any

import pytest
from crewai.llms.base_llm import BaseLLM
from pydantic import BaseModel

from agentic_sdlc.crews.base import PhaseError, TaskRunner, artifact_guardrail
from agentic_sdlc.registry.agents import AgentRegistry
from agentic_sdlc.registry.models import ModelRegistry
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.settings import load_config


class Answer(BaseModel):
    items: list[str]


class ScriptedLLM(BaseLLM):
    """Returns queued replies in order. A reply that is an Exception is raised."""

    replies: list[Any] = []
    prompts: list[str] = []

    def call(self, messages, tools=None, callbacks=None, available_functions=None,
             from_task=None, from_agent=None, response_model=None):
        self.prompts.append(json.dumps(messages, default=str))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    def supports_function_calling(self) -> bool:
        return False


def final(payload: dict) -> str:
    return f"Thought: I have the answer.\nFinal Answer: {json.dumps(payload)}"


class FakeModels(ModelRegistry):
    def __init__(self, scripts: dict[str, list[Any]]):
        super().__init__({"agents": {"customer": {"model": "fake/a", "fallbacks": ["fake/b"]}}})
        self.llms = {m: ScriptedLLM(model=m, replies=list(r), prompts=[]) for m, r in scripts.items()}

    def build_llm(self, agent_key, model=None):
        return self.llms[model or "fake/a"]


TASKS = {
    "t": {"agent": "customer", "description": "Context: {ctx}. List items.", "expected_output": "Items."}
}


def make_runner(scripts) -> tuple[TaskRunner, FakeModels]:
    models = FakeModels(scripts)
    agents = AgentRegistry(load_config("agents"), models, Profile.load("flutter_nestjs_ecommerce"))
    return TaskRunner(agents, tasks=TASKS), models


def test_structured_output_and_usage():
    runner, models = make_runner({"fake/a": [final({"items": ["a", "b"]})]})
    result = runner.run("p", "t", {"ctx": '{"json": "with braces"}'}, Answer)
    assert result.artifact == Answer(items=["a", "b"])
    assert result.usage.model == "fake/a" and result.usage.agent == "customer"
    assert "with braces" in models.llms["fake/a"].prompts[0]


def test_guardrail_feedback_triggers_a_retry():
    runner, models = make_runner({"fake/a": [final({"items": []}), final({"items": ["ok"]})]})
    guard = artifact_guardrail(Answer, lambda a: [] if a.items else ["items must not be empty"])
    result = runner.run("p", "t", {"ctx": "x"}, Answer, guardrail=guard)
    assert result.artifact.items == ["ok"]
    assert "items must not be empty" in models.llms["fake/a"].prompts[-1]


def test_falls_back_to_next_model_when_primary_fails():
    runner, _ = make_runner({
        "fake/a": [RuntimeError("provider down")] * 5,
        "fake/b": [final({"items": ["from fallback"]})],
    })
    result = runner.run("p", "t", {"ctx": "x"}, Answer)
    assert result.artifact.items == ["from fallback"]
    assert result.usage.model == "fake/b"


def test_parse_structured_output_from_final_answer_fence():
    from agentic_sdlc.crews.base import parse_structured_output

    raw = 'Thought: done.\nFinal Answer:\n```json\n{"items": ["x"]}\n```'
    assert parse_structured_output(Answer, raw).items == ["x"]


def test_raises_when_every_model_fails():
    runner, _ = make_runner({"fake/a": [RuntimeError("down")] * 5, "fake/b": [RuntimeError("down")] * 5})
    with pytest.raises(PhaseError, match="failed on all models"):
        runner.run("p", "t", {"ctx": "x"}, Answer)
