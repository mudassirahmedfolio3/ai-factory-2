"""Collects every test outcome and, at the end of the session, writes the pass/fail report.

Writes eval_report.md and eval_report.json into the run folder being evaluated and prints a per-agent
confidence table. See eval_report.py for how confidence is worked out."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_report  # noqa: E402
from common import find_run_dir  # noqa: E402

OUTCOMES: dict[tuple[str, str], str] = {}


def pytest_runtest_logreport(report):
    """Keep one outcome per test: the call result, or the setup result if setup did not pass."""
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        file, _, name = report.nodeid.replace("\\", "/").rpartition("/")[2].partition("::")
        OUTCOMES[(file, name.split("[")[0])] = report.outcome


def pytest_terminal_summary(terminalreporter):
    if not OUTCOMES:
        return
    run = find_run_dir()
    result = eval_report.build(OUTCOMES, run.name if run else "(no run folder)")
    terminalreporter.section("DeepEval report")
    for line in eval_report.to_terminal(result):
        terminalreporter.write_line(line)
    if run is None:
        return
    try:
        paths = eval_report.write(result, run, eval_report.report_name(OUTCOMES))
    except OSError as exc:
        terminalreporter.write_line(f"Could not write the report: {exc}")
        return
    terminalreporter.write_line("")
    for p in paths:
        terminalreporter.write_line(f"Report: {p}")
