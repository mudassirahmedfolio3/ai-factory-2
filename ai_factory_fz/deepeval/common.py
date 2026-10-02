"""Shared helpers: find a pipeline run, read its artifacts, build a DeepEval judge.

Point the tests at a run with DEEPEVAL_RUN_DIR=<path to runs/<run_id>>.
Without it the newest folder in ../runs is used. If no run (or no artifact) exists, tests skip.
"""

import json
import os
import re
from pathlib import Path

import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

RUNS_DIR = Path(os.environ.get("SDLC_RUNS_DIR", Path(__file__).resolve().parent.parent / "runs"))
MAX_CHARS = 30_000
PASS_THRESHOLD = float(os.environ.get("DEEPEVAL_THRESHOLD", "0.6"))  # a score from 0 to 1 passes at or above this
RESULTS: dict[tuple[str, str], list[dict]] = {}  # (test file, test name) -> judge scores, filled by judge()


def find_run_dir() -> Path | None:
    """The run being evaluated (DEEPEVAL_RUN_DIR, else the newest folder in the runs dir), or None."""
    env = os.environ.get("DEEPEVAL_RUN_DIR")
    if env:
        path = Path(env)
    else:
        runs = sorted((p for p in RUNS_DIR.glob("*") if p.is_dir()), key=lambda p: p.stat().st_mtime)
        path = runs[-1] if runs else None
    return path if path and path.is_dir() else None


def run_dir() -> Path:
    path = find_run_dir()
    if path is None:
        pytest.skip(f"No pipeline run found in {RUNS_DIR} (or DEEPEVAL_RUN_DIR is not a folder); set DEEPEVAL_RUN_DIR")
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


def current_test_key() -> tuple[str, str] | None:
    """(file name, test function) of the running test, read from pytest's PYTEST_CURRENT_TEST."""
    m = re.search(r"([^\\/:]+\.py)::(\w+)", os.environ.get("PYTEST_CURRENT_TEST", ""))
    return (m.group(1), m.group(2)) if m else None


def judge(name: str, criteria: str, input_text: str, output_text: str, threshold: float = PASS_THRESHOLD) -> None:
    """Score `output_text` against `criteria` with an LLM judge (0 to 1) and fail below `threshold`.

    The score and the judge's reason are saved in RESULTS for the pass/fail report (see conftest.py)."""
    metric = GEval(
        name=name,
        criteria=criteria,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=threshold,
        model=judge_model(),
    )
    error = None
    try:
        assert_test(LLMTestCase(input=input_text, actual_output=output_text), [metric])
    except AssertionError as exc:
        error = exc
        raise
    finally:
        key = current_test_key()
        if key:
            score, reason = _score_of(metric, error)
            RESULTS.setdefault(key, []).append(
                {"metric": name, "score": score, "threshold": threshold, "reason": reason, "criteria": criteria}
            )


def ask_llm(prompt: str) -> str:
    """One plain text answer from the same judge model the tests use (used for the report's written analysis)."""
    model = judge_model()
    if model is None:
        from deepeval.models import GPTModel

        model = GPTModel()
    out = model.generate(prompt)
    return out[0] if isinstance(out, tuple) else str(out)


def _score_of(metric, error) -> tuple[float | None, str | None]:
    """assert_test scores a copy of the metric, so read the result from DeepEval's test run (or the failure text)."""
    if metric.score is not None:
        return metric.score, metric.reason
    try:
        from deepeval.test_run import global_test_run_manager

        cases = global_test_run_manager.get_test_run().test_cases
        data = (cases[-1].metrics_data or [None])[-1] if cases else None
        if data is not None and data.score is not None:
            return data.score, data.reason
    except Exception:
        pass
    m = re.search(r"score: ([0-9.]+)", str(error)) if error else None
    return (float(m.group(1)) if m else None), (str(error) if error else None)
