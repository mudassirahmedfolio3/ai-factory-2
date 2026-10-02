import pytest

from agentic_sdlc.registry.agents import AgentRegistry
from agentic_sdlc.registry.models import ModelRegistry
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.settings import load_config

ALL_AGENTS = [
    "customer", "spec_writer", "project_manager", "architect", "ui_ux_designer",
    "backend_developer", "frontend_developer", "qa_engineer", "deployment_engineer",
    "integration_pass", "smoke_tester",
]


def test_every_agent_has_a_definition_and_a_model():
    definitions = load_config("agents")
    models = ModelRegistry.from_config()
    assert sorted(definitions) == sorted(ALL_AGENTS)
    for key in ALL_AGENTS:
        assert models.spec_for(key).model.startswith(("claude-code/", "anthropic/"))


def test_tier_and_inline_specs_resolve_with_defaults():
    reg = ModelRegistry({
        "defaults": {"max_tokens": 100},
        "tiers": {"fast": {"model": "a/fast", "fallbacks": ["a/slow", "a/fast"]}},
        "agents": {"x": "fast", "y": {"model": "b/big", "max_tokens": 999}},
    })
    x = reg.spec_for("x")
    assert x.candidates() == ["a/fast", "a/slow"]
    assert x.params == {"max_tokens": 100}
    assert reg.spec_for("y").params == {"max_tokens": 999}


def test_unknown_agent_or_tier_fails_clearly():
    reg = ModelRegistry({"tiers": {}, "agents": {"x": "missing"}})
    with pytest.raises(KeyError, match="unknown tier"):
        reg.spec_for("x")
    with pytest.raises(KeyError, match="No model configured"):
        reg.spec_for("nobody")


def test_every_task_uses_a_known_agent():
    agents = load_config("agents")
    for key, task in load_config("tasks").items():
        assert task["agent"] in agents, key


def test_profile_context_is_added_to_backstory():
    profile = Profile.load("flutter_nestjs_ecommerce")
    reg = AgentRegistry(load_config("agents"), ModelRegistry.from_config(), profile)
    assert "Project conventions" in reg.definition("architect")["backstory"]
    assert "Project conventions" not in reg.definition("customer")["backstory"]


def test_profile_overrides_agent_fields(tmp_path):
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "profile.yaml").write_text("name: p\nagent_overrides:\n  customer:\n    goal: Custom goal\n")
    profile = Profile.load("p", profiles_dir=tmp_path)
    reg = AgentRegistry(load_config("agents"), ModelRegistry.from_config(), profile)
    assert reg.definition("customer")["goal"] == "Custom goal"


def test_agent_with_tools_needs_a_resolver():
    profile = Profile.load("flutter_nestjs_ecommerce")
    reg = AgentRegistry(load_config("agents"), ModelRegistry.from_config(), profile)
    with pytest.raises(RuntimeError, match="tool resolver"):
        reg.build("backend_developer")


def test_backend_switch_routes_anthropic_models(monkeypatch):
    from agentic_sdlc.llms.backend import Backend
    from agentic_sdlc.llms.claude_code import ClaudeCodeLLM
    from agentic_sdlc.llms.cursor_agent import CursorAgentLLM

    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    config = {
        "defaults": {"max_tokens": 100, "timeout": 30},
        "agents": {
            "a": {"model": "anthropic/claude-opus-5-5", "fallbacks": ["anthropic/claude-sonnet-5-5"], "effort": "high"},
            "o": {"model": "openai/gpt-5"},
            "c": {"model": "claude-code/claude-haiku-4-5"},
        },
    }
    cc = ModelRegistry(config, Backend.CLAUDE_CODE)
    assert cc.spec_for("a").candidates() == ["claude-code/claude-opus-5-5", "claude-code/claude-sonnet-5-5"]
    llm = cc.build_llm("a")
    assert isinstance(llm, ClaudeCodeLLM)
    assert (llm.model, llm.effort, llm.timeout) == ("claude-opus-5-5", "high", 30)
    assert cc.spec_for("o").model == "openai/gpt-5"

    api = ModelRegistry(config, Backend.API)
    assert api.spec_for("a").model == "anthropic/claude-opus-5-5"
    assert not isinstance(api.build_llm("a"), ClaudeCodeLLM)
    assert api.spec_for("c").model == "claude-code/claude-haiku-4-5"  # explicit prefix always wins

    monkeypatch.setenv("LLM_PROVIDER", "cursor_cli")
    monkeypatch.setenv("CURSOR_PROXY_MODEL", "auto")
    cursor_llm = api.build_llm("a")
    assert isinstance(cursor_llm, CursorAgentLLM)
    assert cursor_llm.model == "auto"


def test_pipeline_model_overrides():
    from agentic_sdlc.llms.backend import Backend

    reg = ModelRegistry.from_config(load_config("pipeline.demo")["models"])
    reg.backend = Backend.API
    assert reg.spec_for("architect").model == "anthropic/claude-haiku-4-5-20251001"
    assert reg.spec_for("backend_developer").model == "anthropic/claude-haiku-4-5-20251001"
    assert "effort" not in reg.spec_for("architect").params
    assert ModelRegistry.from_config().spec_for("architect").model.endswith("claude-haiku-4-5-20251001")
    with pytest.raises(KeyError, match="unknown agents"):
        ModelRegistry.from_config({"nobody": "fast"})


def test_review_only_tasks_build_developers_without_tools():
    profile = Profile.load("flutter_nestjs_ecommerce")
    reg = AgentRegistry(load_config("agents"), ModelRegistry.from_config(), profile)  # no tool resolver
    agent = reg.build("backend_developer", with_tools=False)
    assert agent.tools == []
