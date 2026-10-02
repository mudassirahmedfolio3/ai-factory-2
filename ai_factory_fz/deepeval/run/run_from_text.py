"""Pipeline 2: run the SDLC from brief TEXT (for the React app), then score it with DeepEval.

The text is saved to run/inputs/<run_id>.md and handed to the same kickoff as pipeline 1.

  uv run python run/run_from_text.py --text "A mobile shop where users browse and buy shoes."
  uv run python run/run_from_text.py --file my_brief.md
  uv run python run/run_from_text.py --stdin-json     (reads one JSON object from stdin)

The --stdin-json form is the hook for the React app. It expects: {"brief": "<text>", "name": "<optional>"}
"""

import argparse
import json
import sys
from pathlib import Path

from pipeline_common import add_common_args, make_run_id, run_pipeline

INPUTS_DIR = Path(__file__).resolve().parent / "inputs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="The brief text")
    source.add_argument("--file", type=Path, help="Read the brief text from this file")
    source.add_argument("--stdin-json", action="store_true", help="Read the brief as JSON from stdin")
    parser.add_argument("--name", default="", help="Short name used in the run id")
    add_common_args(parser, default_pipeline="pipeline.ui")
    args = parser.parse_args()

    name, text = args.name, args.text
    if args.file:
        text = args.file.read_text(encoding="utf-8")
        name = name or args.file.stem
    elif args.stdin_json:
        payload = json.load(sys.stdin)
        text, name = payload.get("brief", ""), name or payload.get("name", "")
    if not (text or "").strip() and not args.skip_run:
        parser.error("give the brief with --text, --file or --stdin-json")

    run_id = make_run_id(name or "text")
    brief_file = INPUTS_DIR / f"{run_id}.md"
    if text and not args.dry_run:
        INPUTS_DIR.mkdir(exist_ok=True)
        brief_file.write_text(text.strip() + "\n", encoding="utf-8")
    return run_pipeline(brief_file, run_id, args)


if __name__ == "__main__":
    sys.exit(main())
