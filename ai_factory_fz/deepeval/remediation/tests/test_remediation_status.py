import pytest

from remediation.status import (
    STATUS_END, STATUS_START, InvalidTransition, RemediationStatus, refresh_report_headers,
)


def test_new_status_has_six_pending_steps_in_order():
    s = RemediationStatus()
    assert [x.key for x in s.steps] == ["report", "triage", "fix", "integration", "qa_smoke", "reevaluate"]
    assert {x.state for x in s.steps} == {"pending"}


def test_steps_must_run_in_order():
    s = RemediationStatus()
    with pytest.raises(InvalidTransition):
        s.set("triage", "running")
    s.set("report", "running")
    s.set("report", "done")
    s.set("triage", "running")
    s.set("triage", "awaiting_approval", "2 tasks")
    assert s.step("triage").reason == "2 tasks" and s.step("triage").updated


def test_done_is_final_and_failed_can_retry():
    s = RemediationStatus()
    s.set("report", "running")
    s.set("report", "done")
    with pytest.raises(InvalidTransition):
        s.set("report", "running")
    s.set("triage", "running")
    s.set("triage", "failed", "boom")
    s.set("triage", "running")


def test_awaiting_approval_can_only_be_approved_or_blocked():
    s = RemediationStatus()
    for step in ("report",):
        s.set(step, "running")
        s.set(step, "done")
    s.set("triage", "running")
    s.set("triage", "awaiting_approval")
    with pytest.raises(InvalidTransition):
        s.set("triage", "running")
    s.set("triage", "done")


def test_save_and_load_roundtrip(tmp_path):
    p = tmp_path / "remediation" / "status.json"
    s = RemediationStatus()
    s.set("report", "running")
    s.save(p)
    assert RemediationStatus.load(p).step("report").state == "running"
    assert RemediationStatus.load(tmp_path / "missing.json").step("report").state == "pending"


def test_blocks_render_all_steps():
    s = RemediationStatus()
    assert "DeepEval report" in s.block_md() and s.block_md().startswith(STATUS_START)
    html = s.block_html()
    assert "<ol" in html and "Re-evaluate with DeepEval" in html and html.endswith(STATUS_END)


def test_refresh_rewrites_only_between_markers(tmp_path):
    md = tmp_path / "eval_report_flow.md"
    md.write_text(f"# Report\n{STATUS_START}\nold\n{STATUS_END}\nBody <b>kept</b>\n", encoding="utf-8")
    html = tmp_path / "eval_report_flow.html"
    html.write_text(f"<h1>R</h1>{STATUS_START}old{STATUS_END}<p>kept</p>", encoding="utf-8")
    no_markers = tmp_path / "eval_report_other.md"
    no_markers.write_text("nothing here", encoding="utf-8")
    s = RemediationStatus()
    s.set("report", "running")
    s.set("report", "done")
    changed = refresh_report_headers(tmp_path, s)
    assert set(changed) == {md, html}
    assert "DONE" in md.read_text(encoding="utf-8") and "Body <b>kept</b>" in md.read_text(encoding="utf-8")
    assert "<p>kept</p>" in html.read_text(encoding="utf-8")
    assert no_markers.read_text(encoding="utf-8") == "nothing here"


def test_block_md_keeps_the_table_intact_for_awkward_reasons():
    s = RemediationStatus()
    s.set("report", "running")
    s.set("report", "failed", "bad | input\nsecond line")
    rows = [r for r in s.block_md().splitlines() if r.startswith("| 1 ")]
    assert rows == ["| 1 | DeepEval report | FAILED | bad \\| input second line |"]


def test_refresh_skips_undecodable_files_and_unbalanced_markers(tmp_path):
    s = RemediationStatus()
    bad = tmp_path / "eval_report_old.md"
    bad.write_bytes(b"\xff" + STATUS_START.encode() + b"\xff" + STATUS_END.encode())
    half = tmp_path / "eval_report_half.md"
    half.write_text(f"x {STATUS_START} no end", encoding="utf-8")
    good = tmp_path / "eval_report_ok.md"
    good.write_text(f"{STATUS_START}old{STATUS_END}", encoding="utf-8")
    assert refresh_report_headers(tmp_path, s) == [good]
    assert half.read_text(encoding="utf-8") == f"x {STATUS_START} no end"
