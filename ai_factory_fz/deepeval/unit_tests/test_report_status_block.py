import eval_report as e


def test_markdown_report_carries_the_status_markers():
    assert "<!-- remediation-status:start -->" in e.STATUS_PLACEHOLDER_MD
    assert "<!-- remediation-status:end -->" in e.STATUS_PLACEHOLDER_MD
    assert "Remediation not started" in e.STATUS_PLACEHOLDER_MD


def test_write_creates_md_json_and_html(tmp_path):
    report = {
        "run": "r", "generated": "now", "pass_threshold": 0.6, "level_meaning": {},
        "overall": {"verdict": "PASS", "confidence": None, "confidence_level": "-", "passed": 0, "failed": 0, "skipped": 0},
        "agents": [], "structure_checks": [], "tests": [],
    }
    paths = e.write(report, tmp_path, "eval_report_x")
    assert {p.suffix for p in paths} == {".json", ".md", ".html"}
    assert "<!-- remediation-status:start -->" in (tmp_path / "eval_report_x.md").read_text(encoding="utf-8")
    assert "<!-- remediation-status:start -->" in (tmp_path / "eval_report_x.html").read_text(encoding="utf-8")
