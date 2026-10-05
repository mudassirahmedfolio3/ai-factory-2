"""Append Release 2 expansion to an fz run brief (safe JSON round-trip)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_MARKER = "Release 2 — expand ShopEase"
DEFAULT_PIPELINE = "pipeline.client.release2"
DEFAULT_PASS1_BEFORE = 10


def _wi_number(wid: str) -> int | None:
    try:
        return int(str(wid).split("-", 1)[1])
    except (IndexError, ValueError):
        return None


def _prepare_pass2_replan(
    data: dict,
    *,
    pass1_before: int,
    pipeline: str,
) -> None:
    """Pass 1 left PRD/backlog/arch in state; clear planning artifacts so resume replans Release 2."""
    build = data.get("build") or {}
    items = build.get("items") or {}
    pass1 = [k for k in items if str(k).startswith("WI-") and (_wi_number(k) or 0) < pass1_before]
    if not pass1 or not all(items[k].get("status") == "done" for k in pass1):
        missing = [k for k in pass1 if items[k].get("status") != "done"]
        raise SystemExit(
            f"Pass 1 not complete: need all WI-* before {pass1_before} done. Not done: {missing or 'none found'}"
        )
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
    data["pipeline"] = pipeline
    # Gates must rerun after replan; stale approvals would skip PRD/architecture review.
    history = data.get("gate_history") or []
    data["gate_history"] = [g for g in history if g.get("gate") not in ("prd", "architecture")]
    # Keep build.items / milestones (Pass 1 done); new WIs from replanning merge via setdefault.


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge Release 2 expansion into fz state.json")
    parser.add_argument("state_json", type=Path)
    parser.add_argument("expansion_md", type=Path)
    parser.add_argument("--marker", default=DEFAULT_MARKER, help="Skip append if this text is already in brief")
    parser.add_argument("--pipeline", default=DEFAULT_PIPELINE, help="Pipeline stem for Pass 2 replan")
    parser.add_argument(
        "--pass1-before",
        type=int,
        default=DEFAULT_PASS1_BEFORE,
        help="All WI-* with number strictly less than this must be done (lighting: 13 = WI-001..012)",
    )
    parser.add_argument(
        "--set-running",
        action="store_true",
        help="Set status=running immediately (default: keep completed until UI resume)",
    )
    args = parser.parse_args()

    data = json.loads(args.state_json.read_text(encoding="utf-8"))
    expansion = args.expansion_md.read_text(encoding="utf-8").strip()
    brief = (data.get("brief") or "").strip()
    if args.marker not in brief:
        data["brief"] = brief + "\n\n" + expansion + "\n"
    _prepare_pass2_replan(data, pass1_before=args.pass1_before, pipeline=args.pipeline)
    if args.set_running:
        data["status"] = "running"
        data["stop_reason"] = ""
    args.state_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {args.state_json} (pipeline={args.pipeline}, pass1_before={args.pass1_before})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
