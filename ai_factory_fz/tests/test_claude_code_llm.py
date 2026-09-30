"""ClaudeCodeLLM tests against a fake `claude` executable (no real Claude Code calls)."""

import json
import stat
import sys

import pytest
from pydantic import BaseModel

from agentic_sdlc.llms.claude_code import ClaudeCodeError, ClaudeCodeLLM, split_messages

FAKE_CLI = """#!{python}
import json, os, sys
record = {{"argv": sys.argv[1:], "stdin": sys.stdin.read(), "has_api_key": "ANTHROPIC_API_KEY" in os.environ, "cwd": os.getcwd()}}
with open({log!r}, "w") as f:
    json.dump(record, f)
sys.stdout.write({reply})
"""


def fake_cli(tmp_path, reply: dict | str) -> tuple[str, "Path"]:
    log = tmp_path / "call.json"
    script = tmp_path / "claude"
    body = repr(json.dumps(reply) if isinstance(reply, dict) else reply)
    script.write_text(FAKE_CLI.format(python=sys.executable, log=str(log), reply=body))
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script), log


OK = {
    "type": "result", "subtype": "success", "is_error": False, "result": "Final Answer: hi",
    "usage": {"input_tokens": 100, "output_tokens": 20, "cache_read_input_tokens": 10, "cache_creation_input_tokens": 0},
}


def test_call_isolates_claude_code_and_tracks_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    cli, log = fake_cli(tmp_path, OK)
    llm = ClaudeCodeLLM(model="claude-opus-5-5", effort="high", cli_path=cli)

    out = llm.call([{"role": "system", "content": "You are X."}, {"role": "user", "content": "Say hi"}])

    assert out == "Final Answer: hi"
    rec = json.loads(log.read_text())
    argv = rec["argv"]
    assert argv[argv.index("--model") + 1] == "claude-opus-5-5"
    assert argv[argv.index("--tools") + 1] == ""
    assert argv[argv.index("--system-prompt") + 1] == "You are X."
    assert argv[argv.index("--effort") + 1] == "high"
    assert "--no-session-persistence" in argv and "--strict-mcp-config" in argv
    assert rec["stdin"] == "Say hi"
    assert rec["has_api_key"] is False
    assert "sdlc-claude-" in rec["cwd"]
    usage = llm.get_token_usage_summary()
    assert (usage.prompt_tokens, usage.completion_tokens) == (110, 20)


def test_structured_output_uses_json_schema(tmp_path):
    class Out(BaseModel):
        n: int

    cli, log = fake_cli(tmp_path, {**OK, "result": "", "structured_output": {"n": 3}})
    out = ClaudeCodeLLM(model="m", cli_path=cli).call("give n", response_model=Out)
    assert json.loads(out) == {"n": 3}
    argv = json.loads(log.read_text())["argv"]
    assert json.loads(argv[argv.index("--json-schema") + 1])["properties"]["n"]["type"] == "integer"


def test_stop_words_trim_the_reply(tmp_path):
    cli, _ = fake_cli(tmp_path, {**OK, "result": "Action: x\nObservation: made up"})
    llm = ClaudeCodeLLM(model="m", cli_path=cli, stop=["\nObservation:"])
    assert llm.call("go") == "Action: x"


def test_error_result_raises(tmp_path):
    cli, _ = fake_cli(tmp_path, {**OK, "is_error": True, "subtype": "error_during_execution", "result": "Not logged in"})
    with pytest.raises(ClaudeCodeError, match="Not logged in"):
        ClaudeCodeLLM(model="m", cli_path=cli).call("go")


def test_non_json_output_raises(tmp_path):
    cli, _ = fake_cli(tmp_path, "oops, not json")
    with pytest.raises(ClaudeCodeError, match="without JSON output"):
        ClaudeCodeLLM(model="m", cli_path=cli).call("go")


def test_multi_turn_history_becomes_a_transcript():
    system, prompt = split_messages([
        {"role": "system", "content": "S"},
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "Action: fs_read"},
        {"role": "user", "content": "Observation: file"},
    ])
    assert system == "S"
    assert prompt.index("[USER]\ntask") < prompt.index("[ASSISTANT]\nAction: fs_read") < prompt.index("Observation: file")
    assert prompt.endswith("Reply with the next assistant message only.")
