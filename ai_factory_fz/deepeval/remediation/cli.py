"""remediate: run, approve, resume or show the status of a DeepEval remediation cycle.

  uv run python deepeval/remediate.py run     --run-dir runs/<id> --report runs/<id>/eval_report_flow.json
  uv run python deepeval/remediate.py approve --run-id <id>
  uv run python deepeval/remediate.py status  --run-id <id>
(run from ai_factory_fz, so the pipeline environment is available for the Project Manager calls)
"""

import argparse
import os
from pathlib import Path

from remediation.flow import RemediationError, RemediationFlow
from remediation.status import RemediationStatus, refresh_report_headers

# Same default as the pipeline (agentic_sdlc.settings.RUNS_DIR): <ai_factory_fz>/runs, or SDLC_RUNS_DIR.
RUNS_DIR = Path(os.environ.get("SDLC_RUNS_DIR", Path(__file__).resolve().parents[2] / "runs"))


def build_runner(run_dir: Path):
    """A TaskRunner for the Project Manager. Imports the pipeline lazily: only the real model calls need it."""
    from remediation.runner import build_runner as build

    return build(run_dir)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="remediate.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("run", "resume", "approve", "status"):
        s = sub.add_parser(name)
        where = s.add_mutually_exclusive_group(required=True)
        where.add_argument("--run-dir", type=Path, help="Path to the run folder")
        where.add_argument("--run-id", help="Run id inside the runs folder")
        if name in ("run", "resume"):
            s.add_argument("--report", type=Path, help="eval_report*.json to start from (default: newest in the run)")
    return p


def _print_status(status: RemediationStatus) -> None:
    print("\n".join(status.lines()))
    if status.note:
        print(f"\n{status.note}")


def main(argv: list[str] | None = None, runner_factory=None) -> int:
    args = _parser().parse_args(argv)
    if args.run_dir:
        run_dir = args.run_dir.resolve()
    else:
        run_dir = (RUNS_DIR / args.run_id).resolve()
        if not run_dir.is_relative_to(RUNS_DIR.resolve()):
            print(f"--run-id must name a folder inside {RUNS_DIR}: {args.run_id}")
            return 2
    if not run_dir.is_dir():
        print(f"Run folder not found: {run_dir}")
        return 2
    if args.command == "status":
        try:
            status = RemediationStatus.load(run_dir / "remediation" / "status.json")
        except (ValueError, OSError) as e:
            print(f"remediation/status.json is unreadable ({str(e).splitlines()[0]}). Fix or delete it to start the cycle again.")
            return 1
        if (run_dir / "remediation").is_dir():
            refresh_report_headers(run_dir, status)
        _print_status(status)
        return 0
    runner = (runner_factory or build_runner)(run_dir) if args.command != "approve" else None
    try:
        flow = RemediationFlow(run_dir, runner, getattr(args, "report", None))
    except (ValueError, OSError) as e:
        print(f"remediation/status.json is unreadable ({str(e).splitlines()[0]}). Fix or delete it to start the cycle again.")
        return 1
    if args.command == "approve":
        try:
            status = flow.approve()
        except RemediationError as e:
            print(str(e))
            return 2
        _print_status(status)
        return 0
    try:
        status = flow.run()
    except RemediationError as e:
        print(str(e))
        return 1
    except Exception as e:   # the flow has already saved the failed state
        print(f"{type(e).__name__}: {e}")
        _print_status(flow.status)
        return 1
    _print_status(status)
    return 1 if any(s.state in ("failed", "blocked") for s in status.steps) else 0
