import eval_report_html as h

REPORT = {
    "run": "r1", "generated": "2026-10-02T10:00:00", "pass_threshold": 0.6,
    "level_meaning": {"HIGH": "0.80 to 1.00", "MEDIUM": "0.60 to 0.79", "LOW": "below 0.60"},
    "overall": {"verdict": "FAIL", "confidence": 0.7, "confidence_level": "MEDIUM", "passed": 1, "failed": 1, "skipped": 0},
    "agents": [{
        "agent": "frontend_developer", "verdict": "FAIL", "confidence": 0.3, "confidence_level": "LOW",
        "lowest_score": 0.3, "passed": 0, "failed": 1, "skipped": 0, "level_reasoning": "Because <b>low</b>",
        "analysis": {"why_score": "w", "level_justification": "l", "strengths": ["s"], "gaps": ["<script>alert(1)</script>"], "improvements": ["i"]},
        "tests": [{"agent": "frontend_developer", "file": "f.py", "test": "t", "outcome": "failed", "score": 0.3,
                   "level": "LOW", "criteria": "c", "reason": "bad & worse"}],
    }],
    "structure_checks": [], "tests": [],
}


def test_html_has_summary_status_markers_and_agent_details():
    page = h.to_html(REPORT)
    assert page.startswith("<!doctype html>") and "frontend_developer" in page and "LOW" in page
    assert "<!-- remediation-status:start -->" in page and "Remediation not started" in page
    assert "Why this score" in page or "why_score" in page.lower() or "w</" in page


def test_html_escapes_model_text():
    page = h.to_html(REPORT)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page and "bad &amp; worse" in page and "&lt;b&gt;low&lt;/b&gt;" in page


def test_html_without_analysis_still_renders():
    r = {**REPORT, "agents": [{**REPORT["agents"][0], "analysis": None}]}
    assert "frontend_developer" in h.to_html(r)
