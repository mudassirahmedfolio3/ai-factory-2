"""Load agent transcripts from run workspace (jsonl + failure dumps)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MAX_TRANSCRIPT_ENTRIES = 10_000
PDF_TRANSCRIPT_BODY_CHARS = 12_000


def load_transcript_entries(run_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    jsonl = run_root / "reports" / "agent_transcript.jsonl"
    if jsonl.is_file():
        for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    fail_dir = run_root / "reports" / "agent_failures"
    if fail_dir.is_dir():
        for path in sorted(fail_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(data, dict):
                continue
            stem = path.name[:-5] if path.name.endswith(".json") else path.stem
            parts = stem.split("-", 2)
            task_key = parts[1] if len(parts) > 2 else stem
            model = parts[2] if len(parts) > 2 else ""
            entries.append(
                {
                    "started_at": "",
                    "ended_at": "",
                    "agent": task_key,
                    "task_key": task_key,
                    "model": model,
                    "success": False,
                    "source_file": path.name,
                    "stdout_excerpt": data.get("stdout") or "",
                    "stderr_excerpt": data.get("stderr") or "",
                    "exit_code": data.get("exit_code"),
                }
            )

    entries.sort(key=lambda e: (e.get("started_at") or e.get("ended_at") or "", e.get("task_key") or ""))
    if len(entries) > MAX_TRANSCRIPT_ENTRIES:
        return entries[:MAX_TRANSCRIPT_ENTRIES]
    return entries


def format_transcript_for_pdf(entry: dict[str, Any]) -> str:
    """Single transcript block for PDF appendix."""
    parts: list[str] = []
    header = (
        f"{entry.get('started_at') or '—'} → {entry.get('ended_at') or '—'} · "
        f"{entry.get('agent') or ''} · {entry.get('task_key') or ''} · {entry.get('model') or ''} · "
        f"{'OK' if entry.get('success') else 'FAIL'}"
    )
    parts.append(header)
    if entry.get("prompt"):
        parts.append("--- Prompt (excerpt) ---")
        parts.append(str(entry["prompt"]))
    if entry.get("assistant_result"):
        parts.append("--- Assistant result ---")
        parts.append(str(entry["assistant_result"]))
    conv = entry.get("conversation")
    if isinstance(conv, list) and conv:
        parts.append("--- Conversation (structured) ---")
        parts.append(json.dumps(conv, indent=2, ensure_ascii=False, default=str)[:PDF_TRANSCRIPT_BODY_CHARS])
    if entry.get("stdout_excerpt"):
        parts.append("--- CLI stdout (excerpt) ---")
        parts.append(str(entry["stdout_excerpt"]))
    if entry.get("stderr_excerpt"):
        parts.append("--- stderr ---")
        parts.append(str(entry["stderr_excerpt"]))
    body = "\n".join(parts)
    if len(body) > PDF_TRANSCRIPT_BODY_CHARS:
        body = body[:PDF_TRANSCRIPT_BODY_CHARS] + f"\n… (truncated for PDF; full text in reports/agent_transcript.jsonl)"
    return body
