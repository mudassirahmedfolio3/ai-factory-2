"""The deepeval project duplicates the status markers; they must match the remediation package."""

import re
from pathlib import Path

from remediation import status

HTML_REPORT = Path(__file__).resolve().parents[2] / "eval_report_html.py"


def _literal(text: str, name: str) -> str:
    m = re.search(rf'^{name}\s*=\s*"([^"]*)"', text, re.M)
    assert m, f"{name} not found in {HTML_REPORT}"
    return m.group(1)


def test_status_markers_match_the_deepeval_report_generator():
    text = HTML_REPORT.read_text(encoding="utf-8")
    assert _literal(text, "STATUS_START") == status.STATUS_START
    assert _literal(text, "STATUS_END") == status.STATUS_END
