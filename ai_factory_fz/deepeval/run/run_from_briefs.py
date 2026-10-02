"""Pipeline 1: run the SDLC from a brief file in ai_factory_fz/briefs/, then score it with DeepEval.

  uv run python run/run_from_briefs.py --list
  uv run python run/run_from_briefs.py --brief demo_mini
  uv run python run/run_from_briefs.py --brief ecommerce_mvp --pipeline pipeline
"""

import argparse
import sys
from pathlib import Path

from pipeline_common import FZ_ROOT, add_common_args, make_run_id, run_pipeline

BRIEFS_DIR = FZ_ROOT / "briefs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--brief", help="Brief name in briefs/ (with or without .md) or a path to a .md file")
    parser.add_argument("--list", action="store_true", help="List the briefs and exit")
    add_common_args(parser, default_pipeline="pipeline.demo")
    args = parser.parse_args()

    briefs = sorted(BRIEFS_DIR.glob("*.md"))
    if args.list:
        print("\n".join(b.stem for b in briefs) or f"No briefs in {BRIEFS_DIR}")
        return 0
    if not args.brief and not args.skip_run:
        parser.error("give --brief <name> (see --list)")

    brief_file = Path()
    if args.brief:
        candidate = Path(args.brief)
        brief_file = candidate if candidate.is_file() else BRIEFS_DIR / (args.brief.removesuffix(".md") + ".md")
        if not brief_file.is_file():
            parser.error(f"Brief not found: {brief_file}. Available: {', '.join(b.stem for b in briefs)}")
    return run_pipeline(brief_file, make_run_id(brief_file.stem), args)


if __name__ == "__main__":
    sys.exit(main())
