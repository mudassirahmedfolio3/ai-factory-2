import json

import pytest
from remediation_helpers import sample_report

from remediation.findings import ReportFormatError, extract_findings, load_report


def test_failed_tests_become_findings_with_verbatim_text():
    findings = extract_findings(sample_report())
    failed = [f for f in findings if f.kind == "failed_test"]
    assert len(failed) == 1
    f = failed[0]
    assert f.source_test == "test_frontend_developer.py::test_uses_generated_api_client"
    assert f.original_text == "ApiClient is a hand-written Dio wrapper"
    assert "Uses the generated client" in f.evidence and f.score == 0.3 and f.agent == "frontend_developer"


def test_gaps_of_non_high_agents_become_findings_with_suggestions():
    gaps = [f for f in extract_findings(sample_report()) if f.kind == "gap"]
    texts = {f.original_text for f in gaps}
    assert "US-only rule not stated" in texts and "ApiClient is hand-written" in texts
    assert "minor wording" not in texts  # architect is HIGH and passed
    customer = next(f for f in gaps if f.agent == "customer")
    assert customer.suggestions == ["Add a US-only constraint"]


def test_ids_are_sequential_and_unique():
    ids = [f.id for f in extract_findings(sample_report())]
    assert ids == [f"F-{i:03d}" for i in range(1, len(ids) + 1)]


def test_report_without_failures_or_gaps_gives_no_findings():
    report = sample_report()
    report["tests"] = [t for t in report["tests"] if t["outcome"] == "passed"]
    for a in report["agents"]:
        a["analysis"] = {"gaps": [], "improvements": []}
        a["verdict"], a["confidence_level"] = "PASS", "HIGH"
    assert extract_findings(report) == []


def test_missing_sections_raise_a_readable_error():
    with pytest.raises(ReportFormatError, match="tests"):
        extract_findings({"agents": []})


def test_agent_without_analysis_is_skipped_not_fatal():
    report = sample_report()
    report["agents"][1].pop("analysis")
    assert all(f.agent != "customer" or f.kind != "gap" for f in extract_findings(report))


def test_load_report_rejects_missing_and_corrupt_files(tmp_path):
    with pytest.raises(ReportFormatError, match="not found"):
        load_report(tmp_path / "nope.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ReportFormatError, match="valid JSON"):
        load_report(bad)
    good = tmp_path / "good.json"
    good.write_text(json.dumps(sample_report()), encoding="utf-8")
    assert load_report(good)["run"] == "sample-manual"
