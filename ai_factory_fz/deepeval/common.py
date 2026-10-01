"""Shared helpers: find a pipeline run, read its artifacts, build a DeepEval judge.

Point the tests at a run with DEEPEVAL_RUN_DIR=<path to runs/<run_id>>.
Without it the newest folder in ../runs is used. If no run (or no artifact) exists, tests skip.
"""

import json
import os
from pathlib import Path

import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

RUNS_DIR = Path(os.environ.get("SDLC_RUNS_DIR", Path(__file__).resolve().parent.parent / "runs"))
MAX_CHARS = 30_000


def run_dir() -> Path:
    env = os.environ.get("DEEPEVAL_RUN_DIR")
    if env:
        path = Path(env)
    else:
        runs = sorted((p for p in RUNS_DIR.glob("*") if p.is_dir()), key=lambda p: p.stat().st_mtime)
        if not runs:
            pytest.skip(f"No pipeline run found in {RUNS_DIR}; set DEEPEVAL_RUN_DIR")
        path = runs[-1]
    if not path.is_dir():
        pytest.skip(f"Run folder not found: {path}")
    return path


def read(*rel_paths: str) -> str:
    """Concatenate the given files from the run; skip the test if none exist."""
    root, parts = run_dir(), []
    for rel in rel_paths:
        f = root / rel
        if f.is_file():
            parts.append(f"### {rel}\n{f.read_text(encoding='utf-8', errors='replace')}")
    if not parts:
        pytest.skip(f"None of {rel_paths} exist in {root}")
    return "\n\n".join(parts)[:MAX_CHARS]


def read_glob(*patterns: str) -> str:
    """Like read(), for glob patterns relative to the run folder."""
    root = run_dir()
    files = sorted({f for pat in patterns for f in root.glob(pat) if f.is_file()})
    if not files:
        pytest.skip(f"No files match {patterns} in {root}")
    return read(*[f.relative_to(root).as_posix() for f in files])


def original_brief() -> str:
    """The brief the run was started with (the customer agent's input), kept in state.json."""
    state = run_dir() / "state.json"
    brief = json.loads(state.read_text(encoding="utf-8")).get("brief", "") if state.is_file() else ""
    if not brief:
        pytest.skip(f"No brief found in {state}")
    return brief


def brief() -> str:
    """The customer's expanded product brief (the spec writer's input)."""
    return read("docs/product_brief.md")


def judge_model():
    """OpenAI (DeepEval's default) when OPENAI_API_KEY is set, otherwise Claude via ANTHROPIC_API_KEY."""
    if os.environ.get("OPENAI_API_KEY") or not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    from deepeval.models import AnthropicModel

    return AnthropicModel(model=os.environ.get("DEEPEVAL_JUDGE_MODEL", "claude-sonnet-5-5"))


def judge(name: str, criteria: str, input_text: str, output_text: str, threshold: float = 0.6) -> None:
    """Score `output_text` against `criteria` with an LLM judge and fail below `threshold`."""
    metric = GEval(
        name=name,
        criteria=criteria,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=threshold,
        model=judge_model(),
    )
    assert_test(LLMTestCase(input=input_text, actual_output=output_text), [metric])
