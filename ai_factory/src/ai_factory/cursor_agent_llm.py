"""CrewAI LLM backend that calls Cursor CLI with CURSOR_API_KEY (no proxy needed)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from crewai.llms.base_llm import BaseLLM
from crewai.utilities.types import LLMMessage


def _parse_version_dir(name: str) -> int:
    date_part = name.split("-")[0]
    year, month, day = date_part.split(".")
    return int(f"{year}{month.zfill(2)}{day.zfill(2)}")


def _resolve_agent_cli() -> tuple[str, str]:
    """Return (node_exe, index_js) bypassing agent.cmd (Windows cmd line limit)."""
    base = Path.home() / "AppData" / "Local" / "cursor-agent"
    versions_dir = base / "versions"
    if versions_dir.is_dir():
        version_dirs = [
            d
            for d in versions_dir.iterdir()
            if d.is_dir()
            and d.name[0].isdigit()
        ]
        if version_dirs:
            latest = max(version_dirs, key=lambda d: _parse_version_dir(d.name))
            node = latest / "node.exe"
            index = latest / "index.js"
            if node.exists() and index.exists():
                return str(node), str(index)

    agent_bin = shutil.which("agent") or shutil.which("agent.cmd")
    if agent_bin:
        return agent_bin, ""

    local_agent = base / "agent.cmd"
    if local_agent.exists():
        return str(local_agent), ""

    raise RuntimeError(
        "Cursor CLI (agent) not found. Install: irm 'https://cursor.com/install?win32=true' | iex"
    )


def _extract_content(content: str | list[dict[str, Any]] | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and block.get("text"):
                    chunks.append(str(block["text"]))
                elif block.get("content"):
                    chunks.append(str(block["content"]))
            else:
                chunks.append(str(block))
        return "\n".join(chunks)
    return str(content)


def _messages_to_prompt(messages: str | list[LLMMessage]) -> str:
    if isinstance(messages, str):
        return messages
    system_parts: list[str] = []
    user_parts: list[str] = []
    other_parts: list[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = _extract_content(message.get("content"))
        if not content.strip():
            continue
        if role == "system":
            system_parts.append(content)
        elif role == "user":
            user_parts.append(content)
        else:
            other_parts.append(content)
    # Avoid "SYSTEM:" / "USER:" labels — Cursor CLI mis-parses them.
    if user_parts:
        body = user_parts[-1]
        if system_parts:
            return f"{system_parts[-1]}\n\n{body}"
        return body
    if system_parts:
        return system_parts[-1]
    return "\n\n".join(other_parts)


class CursorAgentLLM(BaseLLM):
    """Invoke `agent -p --trust` subprocess using CURSOR_API_KEY."""

    model: str = "auto"
    api_key: str | None = None
    working_dir: str = "."
    timeout_seconds: int = 600
    provider: str = "cursor"

    def call(
        self,
        messages: str | list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any | None = None,
        from_agent: Any | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> str | Any:
        if tools or available_functions:
            raise RuntimeError(
                "CursorAgentLLM does not support tool calling; use openai provider for full crews."
            )

        prompt = _messages_to_prompt(messages)
        prompt = (
            "You are executing an automated CrewAI pipeline task.\n"
            "Produce the complete final deliverable now.\n"
            "Do NOT ask clarifying questions or offer menus — output the artifact only.\n\n"
            f"{prompt}"
        )
        if response_model is not None:
            prompt += (
                "\n\nRespond with valid JSON only matching the requested schema. "
                "No markdown fences."
            )

        api_key = (self.api_key or os.getenv("CURSOR_API_KEY", "")).strip()

        env = os.environ.copy()
        if api_key:
            env["CURSOR_API_KEY"] = api_key

        node_exe, index_js = _resolve_agent_cli()
        cwd = Path(self.working_dir).resolve()
        # Pass prompt via stdin — Windows fails with WinError 206 when the prompt
        # is appended to the command line (Discovery crew prompts exceed ~32k).
        if index_js:
            cmd = [node_exe, index_js, "-p", "--trust"]
        else:
            cmd = [node_exe, "-p", "--trust"]
        result = subprocess.run(
            cmd,
            input=prompt,
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_seconds,
            check=False,
        )

        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"Cursor agent failed (exit {result.returncode}): {stderr}")

        text = (result.stdout or "").strip()
        self._token_usage["successful_requests"] += 1

        if response_model is not None:
            import json

            try:
                return response_model.model_validate_json(text)
            except Exception:
                # Fallback: extract JSON object from response
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    return response_model.model_validate_json(text[start : end + 1])
                raise

        return text
