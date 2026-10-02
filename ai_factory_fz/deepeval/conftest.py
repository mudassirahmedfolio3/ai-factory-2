"""Collects every test outcome and, at the end of the session, writes the pass/fail report.

Writes eval_report*.md/.json/.html into the run folder being evaluated, prints a per-agent confidence table, and
starts the remediation process when DEEPEVAL_REMEDIATE=1. See eval_report.py and remediation_trigger.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_report  # noqa: E402
import remediation_trigger  # noqa: E402
from common import find_run_dir  # noqa: E402

OUTCOMES: dict[tuple[str, str], str] = {}
EVALUATION_DIRS = ("agent_test_writeup/", "flow_test_writeup/")


def pytest_runtest_logreport(report):
    """Keep one outcome per evaluation test: the call result, or the setup result if setup did not pass."""
    nodeid = report.nodeid.replace("\\", "/")
    if not any(d in nodeid for d in EVALUATION_DIRS):
        return
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        file, _, name = nodeid.rpartition("/")[2].partition("::")
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
    log = remediation_trigger.maybe_start(run, paths[0])
    if log:
        terminalreporter.write_line(f"Remediation started: follow {log}")
