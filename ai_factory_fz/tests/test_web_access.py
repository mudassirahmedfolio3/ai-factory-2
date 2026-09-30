"""Web access for the Architect and the developers only, on both the Claude Code and API paths."""

import json

from agentic_sdlc.llms.backend import Backend
from agentic_sdlc.llms.claude_code import ClaudeCodeLLM
from agentic_sdlc.registry.agents import WEB_GUIDANCE, AgentRegistry
from agentic_sdlc.registry.models import ModelRegistry
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.settings import load_config

WEB_AGENTS = {"architect", "backend_developer", "frontend_developer"}


def registry(backend=Backend.CLAUDE_CODE, definitions=None):
    return AgentRegistry(definitions or load_config("agents"), ModelRegistry(load_config("models"), backend),
                         Profile.load("flutter_nestjs_ecommerce"), tool_resolver=lambda name: None)


def test_only_architect_and_developers_have_web_access():
    reg = registry()
    with_web = {a for a in reg.keys() if reg.web_rules(a)}
    assert with_web == WEB_AGENTS
    assert reg.web_rules("architect") == ["WebSearch", "WebFetch"]
    assert WEB_GUIDANCE in reg.definition("backend_developer")["backstory"]
    assert WEB_GUIDANCE not in reg.definition("qa_engineer")["backstory"]


def test_domain_list_limits_page_reads():
    defs = load_config("agents")
    defs["architect"]["web"] = ["docs.nestjs.com", "pub.dev"]
    assert registry(definitions=defs).web_rules("architect") == [
        "WebSearch", "WebFetch(domain:docs.nestjs.com)", "WebFetch(domain:pub.dev)"]


def test_claude_code_llm_enables_only_the_web_tools():
    agent = registry().build("architect")
    assert isinstance(agent.llm, ClaudeCodeLLM)
    cmd = agent.llm.build_command("sys", None)
    assert cmd[cmd.index("--tools") + 1] == "WebSearch,WebFetch"
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    assert cmd[cmd.index("--allowedTools") + 1: cmd.index("--allowedTools") + 3] == ["WebSearch", "WebFetch"]
    plain = registry().build("customer").llm.build_command("sys", None)
    assert plain[plain.index("--tools") + 1] == "" and "--allowedTools" not in plain


def test_review_only_tasks_get_no_web():
    agent = registry().build("backend_developer", with_tools=False)
    assert agent.llm.web_rules == [] and agent.tools == []


def test_api_path_gets_crewai_web_tools(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    names = [t.name for t in registry(Backend.API).build("architect").tools]
    assert any("website" in n.lower() for n in names) and not any("search the internet" in n.lower() for n in names)
    monkeypatch.setenv("SERPER_API_KEY", "k")
    assert len(registry(Backend.API).build("architect").tools) == 2
    assert registry(Backend.API).build("customer").tools == []


def test_coding_worker_allows_web_for_developers_not_qa(tmp_path):
    from agentic_sdlc.artifacts.reports import WorkItemResult
    from agentic_sdlc.build.coders import ClaudeCodeWorker, Job
    from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner
    from agentic_sdlc.workspace import Workspace
    ws = Workspace.create("r", runs_dir=tmp_path)
    reg = registry()
    worker = ClaudeCodeWorker(reg, load_config("tasks"), ws, SandboxRunner(ws, reg.profile.sandbox, SandboxMode.DOCKER))
    for agent, expected in (("backend_developer", True), ("qa_engineer", False)):
        cmd = worker.build_command(Job("build", agent, "implement_work_item", {}, WorkItemResult, ".", None), "m", "s")
        allowed = cmd[cmd.index("--allowedTools") + 1: cmd.index("--disallowedTools")]
        assert ("WebSearch" in allowed and "WebFetch" in allowed) is expected, agent
