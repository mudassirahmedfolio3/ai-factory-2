"""Shared steps for both eval pipelines: create an SDLC run, then score it with DeepEval.

Step 1  `uv run kickoff` in ai_factory_fz creates runs/<run_id>/ (gates auto-approved).
Step 2  `uv run deepeval test run ...` in this project scores that run (DEEPEVAL_RUN_DIR is set for you).
Standard library only. Run it from ai_factory_fz/deepeval: `uv run python run/<script>.py`.
"""

import argparse
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

DEEPEVAL_DIR = Path(__file__).resolve().parent.parent      # ai_factory_fz/deepeval
FZ_ROOT = DEEPEVAL_DIR.parent                              # ai_factory_fz
RUNS_DIR = Path(os.environ.get("SDLC_RUNS_DIR", FZ_ROOT / "runs"))
AGENT_TESTS = DEEPEVAL_DIR / "agent_test_writeup"
FLOW_TEST = DEEPEVAL_DIR / "flow_test_writeup" / "test_end_to_end_flow.py"

AGENTS = [
    "customer", "spec_writer", "project_manager", "architect", "ui_ux_designer",
    "backend_developer", "frontend_developer", "qa_engineer", "deployment_engineer",
    "integration_pass", "smoke_tester",
]


def add_common_args(parser: argparse.ArgumentParser, default_pipeline: str) -> None:
    parser.add_argument("--pipeline", default=default_pipeline,
                        help=f"SDLC pipeline config in ai_factory_fz/config (default: {default_pipeline})")
    parser.add_argument("--profile", default=None, help="SDLC profile (default: the project's default)")
    parser.add_argument("--agent", choices=AGENTS, help="Score only this agent's tests")
    parser.add_argument("--flow-only", action="store_true", help="Run only the end-to-end flow test")
    parser.add_argument("--no-tests", action="store_true", help="Create the run but do not score it")
    parser.add_argument("--skip-run", metavar="RUN_ID", help="Do not create a run; score this existing run id")
    parser.add_argument("--dry-run", action="store_true", help="Print the commands without running them")


def make_run_id(hint: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", hint.lower()).strip("-")[:30]
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}"
    return f"{stamp}-eval-{slug}" if slug else f"{stamp}-eval"


def _run(cmd: list[str], cwd: Path, env: dict[str, str], dry: bool) -> int:
    print(f"\n$ (in {cwd})  {' '.join(cmd)}", flush=True)
    if dry:
        return 0
    return subprocess.run(cmd, cwd=cwd, env=env).returncode


def create_run(brief_file: Path, run_id: str, args) -> int:
    cmd = ["uv", "run", "kickoff", "--brief", str(brief_file), "--pipeline", args.pipeline, "--run-id", run_id]
    if args.profile:
        cmd += ["--profile", args.profile]
    env = {**os.environ, "SDLC_GATE_MODE": os.environ.get("SDLC_GATE_MODE", "auto")}
    return _run(cmd, FZ_ROOT, env, args.dry_run)


def score_run(run_id: str, args) -> int:
    env = {**os.environ, "DEEPEVAL_RUN_DIR": str(RUNS_DIR / run_id)}
    if args.flow_only:
        targets = [FLOW_TEST]
    elif args.agent:
        targets = [AGENT_TESTS / f"test_{args.agent}.py"]
    else:
        targets = [AGENT_TESTS, FLOW_TEST]
    failed = 0
    for target in targets:
        rel = target.relative_to(DEEPEVAL_DIR).as_posix()
        failed |= _run(["uv", "run", "deepeval", "test", "run", rel], DEEPEVAL_DIR, env, args.dry_run)
    return failed


def run_pipeline(brief_file: Path, run_id: str, args) -> int:
    """Create the SDLC run (unless --skip-run), then score it. Returns a process exit code."""
    if args.skip_run:
        run_id = args.skip_run
    else:
        code = create_run(brief_file, run_id, args)
        if code != 0:
            print(f"\nWarning: the SDLC run exited with code {code}. It may have stopped early; "
                  f"tests for missing artifacts will be skipped. Resume it with: uv run resume {run_id}")
    print(f"\nRun folder: {RUNS_DIR / run_id}")
    if args.no_tests:
        return 0
    return score_run(run_id, args)
