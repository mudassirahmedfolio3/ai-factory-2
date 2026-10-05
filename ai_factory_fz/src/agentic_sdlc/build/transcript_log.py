"""Append-only agent transcript log under reports/ (for dossier export)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_STDOUT_CHARS = 120_000
MAX_PROMPT_CHARS = 24_000
MAX_RESULT_CHARS = 80_000


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… ({len(text) - limit:,} more characters truncated in log file)"


def extract_transcript_payload(data: dict[str, Any] | None, stdout: str) -> dict[str, Any]:
    """Pull human-readable transcript fields from Cursor CLI JSON."""
    out: dict[str, Any] = {"stdout_excerpt": _truncate(stdout or "", MAX_STDOUT_CHARS)}
    if not isinstance(data, dict):
        return out
    for key in ("result", "text", "output", "message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            out["assistant_result"] = _truncate(val, MAX_RESULT_CHARS)
            break
    structured = data.get("structured_output")
    if structured is not None:
        try:
            out["structured_output"] = structured
        except TypeError:
            out["structured_output"] = str(structured)[:8000]
    for key in ("messages", "conversation", "turns", "history"):
        val = data.get(key)
        if isinstance(val, list) and val:
            out["conversation"] = val[:200]
            break
    if data.get("subtype"):
        out["subtype"] = data.get("subtype")
    if data.get("is_error"):
        out["is_error"] = True
    return out


def append_transcript(
    workspace_root: Path,
    *,
    started_at: str,
    ended_at: str,
    duration_ms: int,
    phase: str,
    agent_key: str,
    task_key: str,
    model: str,
    workdir: str,
    success: bool,
    exit_code: int | None,
    prompt: str,
    data: dict[str, Any] | None,
    stdout: str,
    stderr: str = "",
) -> None:
    path = workspace_root / "reports" / "agent_transcript.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_ms": duration_ms,
        "phase": phase,
        "agent": agent_key,
        "task_key": task_key,
        "model": model,
        "workdir": workdir,
        "success": success,
        "exit_code": exit_code,
        "prompt": _truncate(prompt, MAX_PROMPT_CHARS),
        **extract_transcript_payload(data, stdout),
    }
    if stderr.strip():
        entry["stderr_excerpt"] = _truncate(stderr, 8000)
    line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
