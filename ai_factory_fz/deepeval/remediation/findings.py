"""Turn a DeepEval report (eval_report.json) into normalized findings."""

import json
from pathlib import Path

from remediation.schemas import Finding


class ReportFormatError(ValueError):
    """The report is missing, not JSON, or lacks the sections remediation needs."""


def load_report(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ReportFormatError(f"DeepEval report not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ReportFormatError(f"DeepEval report is not valid JSON ({path}): {e}") from e
    if not isinstance(data, dict):
        raise ReportFormatError(f"DeepEval report must be a JSON object: {path}")
    return data


def extract_findings(report: dict) -> list[Finding]:
    """Failed tests (verbatim judge reason) plus the gaps reported for agents that are not clean HIGH passes."""
    for key in ("tests", "agents"):
        if not isinstance(report.get(key), list):
            raise ReportFormatError(f"DeepEval report has no '{key}' list")
    raw: list[dict] = []
    for t in report["tests"]:
        if t.get("outcome") != "failed":
            continue
        reason = t.get("reason") or "(the judge gave no reason)"
        raw.append(dict(
            kind="failed_test", source_test=f"{t.get('file')}::{t.get('test')}", agent=t.get("agent"),
            score=t.get("score"), level=t.get("level"), original_text=reason,
            evidence=f"Criteria: {t.get('criteria', '')}\nJudge's reason: {reason}",
        ))
    for a in report["agents"]:
        analysis = a.get("analysis") or {}
        if a.get("confidence_level") == "HIGH" and a.get("verdict") == "PASS":
            continue
        suggestions = list(analysis.get("improvements") or [])
        for gap in analysis.get("gaps") or []:
            raw.append(dict(
                kind="gap", source_test=f"agent:{a.get('agent')}", agent=a.get("agent"),
                score=a.get("confidence"), level=a.get("confidence_level"), original_text=gap,
                evidence=f"Gap reported in the analysis of {a.get('agent')} (confidence {a.get('confidence')}, "
                         f"{a.get('confidence_level')})",
                suggestions=suggestions,
            ))
    return [Finding(id=f"F-{i:03d}", **r) for i, r in enumerate(raw, start=1)]
