"""CrewAI LLM that runs each call through headless Claude Code (`claude -p`).

Used when CLAUDE_CODE_ENABLE=true (see backend.py). Claude Code authenticates with
CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`), which is passed through the environment.
ANTHROPIC_API_KEY is removed from the subprocess environment so it cannot take precedence.

Each call is isolated: no Claude Code tools, no settings/hooks/MCP servers, no CLAUDE.md
(it runs in an empty temp directory), and no saved session. Claude Code acts as a
plain completion engine; CrewAI still owns the agent loop, tools and output parsing.
"""

import json
import os
import shutil
import subprocess
import tempfile
from typing import Any

from crewai.events.types.llm_events import LLMCallType
from crewai.llms.base_llm import BaseLLM
from pydantic import BaseModel

# Linux limits one argv string to 128 KiB; longer system prompts go on stdin instead.
_MAX_ARG_CHARS = 100_000


class ClaudeCodeError(RuntimeError):
    pass


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # content blocks
        return "\n".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return "" if content is None else str(content)


def split_messages(messages: str | list[dict[str, Any]]) -> tuple[str, str]:
    """Turn chat messages into (system prompt, single prompt text) for `claude -p`."""
    if isinstance(messages, str):
        return "", messages
    system = "\n\n".join(_text(m.get("content")) for m in messages if m.get("role") == "system")
    turns = [m for m in messages if m.get("role") != "system"]
    if len(turns) == 1:
        return system, _text(turns[0].get("content"))
    # Multi-turn history (e.g. a CrewAI agent after tool calls): replay it as a transcript.
    lines = [f"[{m.get('role', 'user').upper()}]\n{_text(m.get('content'))}" for m in turns]
    lines.append("Continue as the ASSISTANT from where the transcript ends. Reply with the next assistant message only.")
    return system, "\n\n".join(lines)


class ClaudeCodeLLM(BaseLLM):
    llm_type: str = "claude_code"
    effort: str | None = None
    timeout: float = 900
    cli_path: str = "claude"

    def build_command(self, system: str, response_model: type[BaseModel] | None) -> list[str]:
        cmd = [
            self.cli_path, "-p",
            "--output-format", "json",
            "--model", self.model,
            "--tools", "",
            "--no-session-persistence",
            "--setting-sources", "",
            "--strict-mcp-config",
        ]
        if system and len(system) <= _MAX_ARG_CHARS:
            cmd += ["--system-prompt", system]
        if self.effort:
            cmd += ["--effort", self.effort]
        if response_model is not None:
            cmd += ["--json-schema", json.dumps(response_model.model_json_schema())]
        return cmd

    def call(self, messages, tools=None, callbacks=None, available_functions=None,
             from_task=None, from_agent=None, response_model=None):
        system, prompt = split_messages(messages)
        if system and len(system) > _MAX_ARG_CHARS:
            prompt = f"{system}\n\n{prompt}"
        if self.stop:
            prompt += "\n\n(Stop your reply before any of these markers: " + ", ".join(self.stop) + ")"
        cmd = self.build_command(system, response_model)

        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        self._emit_call_started_event(messages=messages, tools=tools, callbacks=callbacks,
                                      available_functions=available_functions,
                                      from_task=from_task, from_agent=from_agent)
        workdir = tempfile.mkdtemp(prefix="sdlc-claude-")
        try:
            proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                  timeout=self.timeout, env=env, cwd=workdir)
        except subprocess.TimeoutExpired as e:
            self._emit_call_failed_event(error=f"timed out after {self.timeout}s", from_task=from_task, from_agent=from_agent)
            raise ClaudeCodeError(f"claude -p timed out after {self.timeout}s") from e
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

        data = self._parse(proc)
        if data.get("is_error") or data.get("subtype") != "success":
            msg = f"claude -p failed ({data.get('subtype')}): {data.get('result') or proc.stderr.strip()[-500:]}"
            self._emit_call_failed_event(error=msg, from_task=from_task, from_agent=from_agent)
            raise ClaudeCodeError(msg)

        self._track_token_usage_internal(data.get("usage") or {})
        structured = data.get("structured_output")
        text = json.dumps(structured) if structured is not None else (data.get("result") or "")
        text = self._apply_stop_words(text)
        self._emit_call_completed_event(response=text, call_type=LLMCallType.LLM_CALL, from_task=from_task,
                                        from_agent=from_agent, messages=messages, usage=data.get("usage"))
        return text

    @staticmethod
    def _parse(proc: subprocess.CompletedProcess) -> dict[str, Any]:
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            data = None
        if not isinstance(data, dict):
            detail = (proc.stderr or proc.stdout).strip()[-800:]
            raise ClaudeCodeError(f"claude -p exited {proc.returncode} without JSON output: {detail}")
        return data

    def _apply_stop_words(self, text: str) -> str:
        for stop in self.stop or []:
            idx = text.find(stop)
            if idx > 0:
                text = text[:idx]
        return text

    def supports_function_calling(self) -> bool:
        return False  # CrewAI falls back to its text (ReAct) tool-calling format

    def supports_stop_words(self) -> bool:
        return True

    def get_context_window_size(self) -> int:
        return 200_000
