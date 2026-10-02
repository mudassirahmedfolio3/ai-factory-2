"""ClaudeCodeWorker against a fake `claude` executable; worker selection per model."""

import json
import stat
import sys

from agentic_sdlc.artifacts.reports import WorkItemResult
from agentic_sdlc.build.coders import ClaudeCodeWorker, CrewAIWorker, Job, make_worker
from agentic_sdlc.llms.backend import Backend
from agentic_sdlc.registry.agents import AgentRegistry
from agentic_sdlc.registry.models import ModelRegistry
from agentic_sdlc.registry.profiles import Profile
from agentic_sdlc.settings import load_config
from agentic_sdlc.tools.sandbox_exec import SandboxMode, SandboxRunner
from agentic_sdlc.workspace import Workspace

REPLY = {
    "type": "result", "subtype": "success", "is_error": False, "result": "",
    "structured_output": {"summary": "added signup", "files_changed": ["src/auth.ts"], "checks_passed": True},
    "modelUsage": {"claude-opus-5-5": {"inputTokens": 100, "outputTokens": 50, "cacheReadInputTokens": 9000, "cacheCreationInputTokens": 400}},
}


def fake_cli(tmp_path, reply):
    log = tmp_path / "call.json"
    script = tmp_path / "claude"
    script.write_text(
        f"#!{sys.executable}\nimport json, os, sys\n"
        f"json.dump({{'argv': sys.argv[1:], 'stdin': sys.stdin.read(), 'cwd': os.getcwd(), "
        f"'db': os.environ.get('DATABASE_URL'), 'key': 'ANTHROPIC_API_KEY' in os.environ}}, open({str(log)!r}, 'w'))\n"
        f"sys.stdout.write({json.dumps(reply)!r})\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script), log


def setup(tmp_path, mode, backend=Backend.CLAUDE_CODE):
    profile = Profile.load("flutter_nestjs_ecommerce")
    ws = Workspace.create("r", runs_dir=tmp_path)
    (ws.root / "server").mkdir(exist_ok=True)
    sandbox = SandboxRunner(ws, profile.sandbox, mode)
    agents = AgentRegistry(load_config("agents"), ModelRegistry(load_config("models"), backend), profile,
                           tool_resolver=lambda name: None)
    return profile, ws, sandbox, agents


def job():
    return Job("build", "backend_developer", "implement_work_item",
               {"item_id": "WI-005", "item_title": "Sign up", "item_description": "d", "component": "backend",
                "milestone": "M2", "stories": "s", "done_items": "-", "docs_dir": "/x", "checks": "npm test", "problems": "(none)"},
               WorkItemResult, "server", "node")


def test_claude_code_worker_local_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "leak")
    profile, ws, sandbox, agents = setup(tmp_path, SandboxMode.LOCAL)
    monkeypatch.setattr(sandbox, "unavailable_reason", lambda rt: None)
    cli, log = fake_cli(tmp_path, REPLY)
    worker = ClaudeCodeWorker(agents, load_config("tasks"), ws, sandbox, cli_path=cli)

    result = worker.run(job())

    assert result.artifact.summary == "added signup"
    rec = json.loads(log.read_text())
    argv = rec["argv"]
    assert rec["cwd"] == str(ws.root / "server")
    assert argv[argv.index("--model") + 1] == "claude-haiku-4-5-20251001"
    assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
    allowed = argv[argv.index("--allowedTools") + 1 : argv.index("--disallowedTools")]
    assert {"Read", "Edit", "Write", "Bash(npm test)", "Bash(npm test *)"} <= set(allowed)
    assert not any(a.startswith("Bash(flutter") for a in allowed)
    assert f"Edit(/{ws.root}/docs/**)" in argv
    assert "Implement work item WI-005 (backend): Sign up" in rec["stdin"]
    assert "Run these commands with Bash" in rec["stdin"]
    assert rec["db"].startswith("postgresql://") and rec["key"] is False
    u = result.usage
    assert (u.prompt_tokens, u.cached_prompt_tokens, u.completion_tokens, u.uncached_tokens) == (9500, 9000, 50, 550)


def test_claude_code_worker_gets_no_bash_when_the_toolchain_is_unavailable(tmp_path, monkeypatch):
    profile, ws, sandbox, agents = setup(tmp_path, SandboxMode.DOCKER)
    monkeypatch.setattr(sandbox, "unavailable_reason", lambda rt: "Docker is not usable")
    cli, log = fake_cli(tmp_path, REPLY)
    ClaudeCodeWorker(agents, load_config("tasks"), ws, sandbox, cli_path=cli).run(job())
    rec = json.loads(log.read_text())
    assert not any(a.startswith("Bash(") for a in rec["argv"])
    assert "You cannot run commands" in rec["stdin"]


def test_failed_claude_code_run_tries_fallback_then_raises(tmp_path):
    import pytest
    from agentic_sdlc.crews.base import PhaseError

    profile, ws, sandbox, agents = setup(tmp_path, SandboxMode.DOCKER)
    cli, _ = fake_cli(tmp_path, {**REPLY, "is_error": True, "result": "rate limited", "structured_output": None})
    with pytest.raises(PhaseError, match="rate limited"):
        ClaudeCodeWorker(agents, load_config("tasks"), ws, sandbox, cli_path=cli).run(job())


def test_worker_choice_follows_the_backend(tmp_path):
    _, ws, sandbox, cc_agents = setup(tmp_path, SandboxMode.DOCKER, Backend.CLAUDE_CODE)
    _, _, _, api_agents = setup(tmp_path, SandboxMode.DOCKER, Backend.API)
    tasks = load_config("tasks")
    assert isinstance(make_worker("backend_developer", cc_agents, tasks, ws, sandbox), ClaudeCodeWorker)
    assert isinstance(make_worker("backend_developer", api_agents, tasks, ws, sandbox), CrewAIWorker)


def test_docker_mode_installs_wrappers_and_allows_the_same_bash_commands(tmp_path, monkeypatch):
    profile, ws, sandbox, agents = setup(tmp_path, SandboxMode.DOCKER)
    monkeypatch.setattr(sandbox, "unavailable_reason", lambda rt: None)
    cli, log = fake_cli(tmp_path, REPLY)
    ClaudeCodeWorker(agents, load_config("tasks"), ws, sandbox, cli_path=cli).run(job())
    rec = json.loads(log.read_text())
    assert "Bash(npm test)" in rec["argv"]
    assert "one command per Bash call" in rec["stdin"]
    wrapper = ws.root / ".sdlc" / "bin" / "npm"
    text = wrapper.read_text()
    assert "agentic_sdlc.tools.sandbox_cli" in text and "--runtime node" in text and "-- npm" in text
    assert wrapper.stat().st_mode & 0o111


def test_sandbox_cli_runs_in_the_callers_directory_with_the_allow_list(tmp_path, monkeypatch):
    from agentic_sdlc.tools import sandbox_cli
    from agentic_sdlc.tools.sandbox_exec import SandboxResult

    ws = Workspace.create("r", runs_dir=tmp_path)
    (ws.root / "server").mkdir(exist_ok=True)
    seen = {}

    def fake_execute(self, runtime, workdir, argv, extra_env=None, host_network=False, timeout_s=None):
        seen.update(runtime=runtime, workdir=workdir, argv=argv)
        return SandboxResult(exit_code=3, output="ran\n")

    monkeypatch.setattr("agentic_sdlc.tools.sandbox_exec.SandboxRunner._execute", fake_execute)
    monkeypatch.chdir(ws.root / "server")
    code = sandbox_cli.main(["--workspace", str(ws.root), "--profile", "flutter_nestjs_ecommerce", "--runtime", "node", "--", "npm", "test"])
    assert code == 3 and seen == {"runtime": "node", "workdir": "server", "argv": ["npm", "test"]}
    assert sandbox_cli.main(["--workspace", str(ws.root), "--profile", "flutter_nestjs_ecommerce", "--runtime", "node", "--", "rm", "-rf", "/"]) == 126


def test_usage_limit_stops_without_trying_the_fallback_model(tmp_path):
    import pytest
    from agentic_sdlc.crews.base import UsageLimitError

    profile, ws, sandbox, agents = setup(tmp_path, SandboxMode.DOCKER)
    cli, log = fake_cli(tmp_path, {**REPLY, "is_error": False, "result": "You've hit your session limit · resets 8:10pm", "structured_output": None})
    with pytest.raises(UsageLimitError, match="resets 8:10pm"):
        ClaudeCodeWorker(agents, load_config("tasks"), ws, sandbox, cli_path=cli).run(job())
    assert "claude-haiku-4-5-20251001" in json.loads(log.read_text())["argv"]  # primary model (Haiku-only config)
