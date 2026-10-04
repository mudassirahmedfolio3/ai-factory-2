"""Append Release 2 expansion to an fz run brief (safe JSON round-trip)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

MARKER = "Release 2 — expand ShopEase"


def _wi_number(wid: str) -> int | None:
    try:
        return int(str(wid).split("-", 1)[1])
    except (IndexError, ValueError):
        return None


def _prepare_pass2_replan(data: dict) -> None:
    """Pass 1 left PRD/backlog/arch in state; clear planning artifacts so resume replans Release 2."""
    build = data.get("build") or {}
    items = build.get("items") or {}
    pass1 = [k for k in items if str(k).startswith("WI-") and (_wi_number(k) or 0) < 10]
    if not pass1 or not all(items[k].get("status") == "done" for k in pass1):
        return
    # Drop failed Pass 2 attempt todos (wrong plan) so replan gets clean WI slots.
    for wid in list(items.keys()):
        if str(wid).startswith("WI-") and items[wid].get("status") == "todo":
            del items[wid]
    data["product_brief"] = None
    data["clarifications"] = []
    data["prd"] = None
    data["architecture"] = None
    data["design"] = None
    data["backlog"] = None
    data["pipeline"] = "pipeline.client.release2"
    # Gates must rerun after replan; stale approvals would skip PRD/architecture review.
    history = data.get("gate_history") or []
    data["gate_history"] = [g for g in history if g.get("gate") not in ("prd", "architecture")]
    # Keep build.items / milestones (Pass 1 done); new WIs from replanning merge via setdefault.


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: merge_release2_brief.py <state.json> <expansion.md>", file=sys.stderr)
        return 2
    state_path = Path(sys.argv[1])
    expansion_path = Path(sys.argv[2])
    data = json.loads(state_path.read_text(encoding="utf-8"))
    expansion = expansion_path.read_text(encoding="utf-8").strip()
    brief = (data.get("brief") or "").strip()
    if MARKER not in brief:
        data["brief"] = brief + "\n\n" + expansion + "\n"
    _prepare_pass2_replan(data)
    data["status"] = "running"
    data["stop_reason"] = ""
    state_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
