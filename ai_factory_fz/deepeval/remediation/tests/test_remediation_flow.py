import json

import pytest
from remediation_helpers import FakeRunner, make_task, make_validated, sample_report

from remediation.flow import RemediationError, RemediationFlow
from remediation.findings import extract_findings
from remediation.schemas import Disposition, RemediationBacklog, TriageResult
from remediation.status import RemediationStatus, STATUS_END, STATUS_START


def write_report(run_dir, report=None):
    evidence = run_dir / "app" / "lib" / "api" / "api_client.dart"   # the file the triage builders say was checked
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("// hand-written client\n", encoding="utf-8")
    path = run_dir / "eval_report_flow.json"
    path.write_text(json.dumps(report or sample_report()), encoding="utf-8")
    return path


def scripted(n_findings=2):
    ids = [f"F-{i:03d}" for i in range(1, n_findings + 1)]
    return FakeRunner({
        "analyze_eval_report": TriageResult(findings=[make_validated(i) for i in ids]),
        "plan_remediation": RemediationBacklog(summary="two fixes", tasks=[make_task(finding_ids=ids)]),
    })


def n_findings():
    from remediation.findings import extract_findings
    return len(extract_findings(sample_report()))


def test_run_stops_at_awaiting_approval_and_writes_artifacts(tmp_path):
    report = write_report(tmp_path)
    flow = RemediationFlow(tmp_path, scripted(n_findings()), report)
    status = flow.run()
    d = tmp_path / "remediation"
    assert status.step("report").state == "done"
    assert status.step("triage").state == "awaiting_approval"
    assert status.step("fix").state == "pending"
    for name in ("status.json", "baseline/eval_report.json", "findings.json", "triage.json", "backlog.json", "backlog.md", "history.jsonl"):
        assert (d / name).is_file(), name
    assert RemediationStatus.load(d / "status.json").step("triage").state == "awaiting_approval"


def test_rerun_after_the_gate_makes_no_model_calls_and_keeps_baseline(tmp_path):
    report = write_report(tmp_path)
    runner = scripted(n_findings())
    RemediationFlow(tmp_path, runner, report).run()
    baseline = (tmp_path / "remediation" / "baseline" / "eval_report.json").read_text(encoding="utf-8")
    calls = len(runner.calls)
    report.write_text(json.dumps({"changed": True}), encoding="utf-8")
    status = RemediationFlow(tmp_path, runner, report).run()
    assert len(runner.calls) == calls and status.step("triage").state == "awaiting_approval"
    assert (tmp_path / "remediation" / "baseline" / "eval_report.json").read_text(encoding="utf-8") == baseline


def test_approve_marks_tasks_approved_and_triage_done_once(tmp_path):
    report = write_report(tmp_path)
    flow = RemediationFlow(tmp_path, scripted(n_findings()), report)
    flow.run()
    status = flow.approve()
    assert status.step("triage").state == "done"
    backlog = RemediationBacklog.model_validate_json((tmp_path / "remediation" / "backlog.json").read_text(encoding="utf-8"))
    assert {t.status for t in backlog.tasks} == {"approved"}
    with pytest.raises(RemediationError, match="not waiting"):
        flow.approve()


def test_rejected_tasks_stay_rejected_on_approve(tmp_path):
    report = write_report(tmp_path)
    flow = RemediationFlow(tmp_path, scripted(n_findings()), report)
    flow.run()
    path = tmp_path / "remediation" / "backlog.json"
    backlog = RemediationBacklog.model_validate_json(path.read_text(encoding="utf-8"))
    backlog.tasks[0].status = "rejected"
    backlog.dispositions = [Disposition(finding_id=f.id, disposition="needs_evidence", reason="rejected by reviewer")
                            for f in extract_findings(sample_report())]
    path.write_text(backlog.model_dump_json(indent=2), encoding="utf-8")
    flow.approve()
    assert RemediationBacklog.model_validate_json(path.read_text(encoding="utf-8")).tasks[0].status == "rejected"


def test_report_without_findings_needs_no_model_and_no_approval(tmp_path):
    report = sample_report()
    report["tests"] = [t for t in report["tests"] if t["outcome"] == "passed"]
    for a in report["agents"]:
        a["analysis"] = {"gaps": [], "improvements": []}
        a["verdict"], a["confidence_level"] = "PASS", "HIGH"
    runner = FakeRunner({})
    status = RemediationFlow(tmp_path, runner, write_report(tmp_path, report)).run()
    assert runner.calls == []
    assert status.step("triage").state == "done" and "nothing to remediate" in status.step("triage").reason.lower()


def test_missing_report_blocks_with_a_reason(tmp_path):
    status = RemediationFlow(tmp_path, FakeRunner({}), tmp_path / "missing.json").run()
    assert status.step("report").state == "blocked" and "not found" in status.step("report").reason
    assert RemediationStatus.load(tmp_path / "remediation" / "status.json").step("report").state == "blocked"


def test_corrupt_report_fails_report_step_with_a_reason_and_can_be_fixed(tmp_path):
    bad = tmp_path / "eval_report_flow.json"
    bad.write_text("{oops", encoding="utf-8")
    status = RemediationFlow(tmp_path, FakeRunner({}), bad).run()
    assert status.step("report").state == "failed" and "valid JSON" in status.step("report").reason
    assert not (tmp_path / "remediation" / "baseline" / "eval_report.json").exists()
    write_report(tmp_path)
    status = RemediationFlow(tmp_path, scripted(n_findings()), bad).run()
    assert status.step("triage").state == "awaiting_approval"


def _set_step_state(tmp_path, index, state):
    path = tmp_path / "remediation" / "status.json"
    status = RemediationStatus.load(path)
    status.steps[index].state = state
    status.save(path)


def test_run_resumes_a_step_left_running_by_a_crash(tmp_path):
    report = write_report(tmp_path)
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    _set_step_state(tmp_path, 1, "running")
    status = RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    assert status.step("triage").state == "awaiting_approval"


def test_run_resumes_a_report_step_left_running(tmp_path):
    report = write_report(tmp_path)
    (tmp_path / "remediation").mkdir()
    RemediationStatus().save(tmp_path / "remediation" / "status.json")
    _set_step_state(tmp_path, 0, "running")
    status = RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    assert status.step("triage").state == "awaiting_approval"


def test_missing_baseline_is_never_recopied(tmp_path):
    report = write_report(tmp_path)
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    baseline = tmp_path / "remediation" / "baseline" / "eval_report.json"
    baseline.unlink()
    with pytest.raises(RemediationError, match="baseline report is missing") as e:
        RemediationFlow(tmp_path, FakeRunner({}), report).run()
    assert "delete remediation/status.json" in str(e.value)
    assert not baseline.exists()


def test_invalid_cached_triage_is_regenerated(tmp_path):
    report = write_report(tmp_path)
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    d = tmp_path / "remediation"
    (d / "triage.json").write_text('{"findings": [', encoding="utf-8")
    (d / "backlog.json").unlink()
    _set_step_state(tmp_path, 1, "running")
    runner = scripted(n_findings())
    status = RemediationFlow(tmp_path, runner, report).run()
    assert status.step("triage").state == "awaiting_approval" and runner.calls
    TriageResult.model_validate_json((d / "triage.json").read_text(encoding="utf-8"))
    assert "cache_invalid" in (d / "history.jsonl").read_text(encoding="utf-8")
    assert not list(d.rglob("*.tmp"))


def test_approve_with_invalid_backlog_raises_remediation_error(tmp_path):
    report = write_report(tmp_path)
    flow = RemediationFlow(tmp_path, scripted(n_findings()), report)
    flow.run()
    (tmp_path / "remediation" / "backlog.json").write_text("{", encoding="utf-8")
    with pytest.raises(RemediationError, match="backlog.json"):
        flow.approve()


def test_model_failure_marks_triage_failed_and_run_can_retry(tmp_path):
    report = write_report(tmp_path)

    class Boom(FakeRunner):
        def run(self, *a, **k):
            raise RuntimeError("model down")

    with pytest.raises(RuntimeError, match="model down"):
        RemediationFlow(tmp_path, Boom({}), report).run()
    assert RemediationStatus.load(tmp_path / "remediation" / "status.json").step("triage").state == "failed"
    status = RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    assert status.step("triage").state == "awaiting_approval"


def test_report_header_markers_are_refreshed(tmp_path):
    report = write_report(tmp_path)
    md = tmp_path / "eval_report_flow.md"
    md.write_text(f"# R\n{STATUS_START}\nremediation not started\n{STATUS_END}\n", encoding="utf-8")
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    text = md.read_text(encoding="utf-8")
    assert "AWAITING APPROVAL" in text and "remediation not started" not in text


def test_history_is_append_only(tmp_path):
    report = write_report(tmp_path)
    flow = RemediationFlow(tmp_path, scripted(n_findings()), report)
    flow.run()
    first = (tmp_path / "remediation" / "history.jsonl").read_text(encoding="utf-8").splitlines()
    flow.approve()
    after = (tmp_path / "remediation" / "history.jsonl").read_text(encoding="utf-8").splitlines()
    assert after[: len(first)] == first and len(after) > len(first)


# ---------- final review wave ----------

def _edit_backlog(tmp_path, fn):
    path = tmp_path / "remediation" / "backlog.json"
    backlog = RemediationBacklog.model_validate_json(path.read_text(encoding="utf-8"))
    fn(backlog)
    path.write_text(backlog.model_dump_json(indent=2), encoding="utf-8")


def _cycle(tmp_path):
    flow = RemediationFlow(tmp_path, scripted(n_findings()), write_report(tmp_path))
    flow.run()
    return flow


def test_approve_refuses_an_edited_backlog_that_breaks_the_guardrails(tmp_path):
    flow = _cycle(tmp_path)

    def damage(b):
        t = b.tasks[0]
        t.owners, t.depends_on, t.finding_ids = ["wizard"], [t.id], [*t.finding_ids, "F-999"]

    _edit_backlog(tmp_path, damage)
    with pytest.raises(RemediationError, match="not valid") as e:
        flow.approve()
    assert "wizard" in str(e.value) and "F-999" in str(e.value)
    assert flow.status.step("triage").state == "awaiting_approval"
    assert RemediationStatus.load(tmp_path / "remediation" / "status.json").step("triage").state == "awaiting_approval"


def test_approve_refuses_unexpected_task_status(tmp_path):
    flow = _cycle(tmp_path)

    def damage(b):
        b.tasks[0].status = "done"

    _edit_backlog(tmp_path, damage)
    with pytest.raises(RemediationError, match="R-001"):
        flow.approve()


def test_rejected_task_needs_a_disposition_for_its_findings(tmp_path):
    flow = _cycle(tmp_path)
    ids = [f.id for f in extract_findings(sample_report())]

    def reject(b):
        b.tasks[0].status = "rejected"

    _edit_backlog(tmp_path, reject)
    with pytest.raises(RemediationError, match="neither a task nor a disposition") as e:
        flow.approve()
    assert all(i in str(e.value) for i in ids)
    assert flow.status.step("triage").state == "awaiting_approval"

    def document(b):
        b.dispositions = [Disposition(finding_id=i, disposition="needs_evidence", reason="reviewer declined") for i in ids]

    _edit_backlog(tmp_path, document)
    assert flow.approve().step("triage").state == "done"
    backlog = RemediationBacklog.model_validate_json((tmp_path / "remediation" / "backlog.json").read_text(encoding="utf-8"))
    assert backlog.tasks[0].status == "rejected"


def test_approve_with_missing_or_invalid_inputs_is_a_readable_error(tmp_path):
    flow = _cycle(tmp_path)
    d = tmp_path / "remediation"
    (d / "triage.json").write_text("{", encoding="utf-8")
    with pytest.raises(RemediationError, match="triage.json"):
        flow.approve()
    (d / "findings.json").unlink()
    with pytest.raises(RemediationError, match="findings.json"):
        flow.approve()


def test_stale_cached_backlog_is_regenerated_on_resume(tmp_path):
    report = write_report(tmp_path)
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    d = tmp_path / "remediation"
    _edit_backlog(tmp_path, lambda b: b.tasks[0].finding_ids.append("F-404"))
    _set_step_state(tmp_path, 1, "running")
    runner = scripted(n_findings())
    status = RemediationFlow(tmp_path, runner, report).run()
    assert status.step("triage").state == "awaiting_approval"
    assert [c[0] for c in runner.calls] == ["plan_remediation"]
    assert "F-404" not in (d / "backlog.json").read_text(encoding="utf-8")
    assert "cache_invalid" in (d / "history.jsonl").read_text(encoding="utf-8")


def test_cached_triage_with_invented_evidence_is_regenerated_with_the_backlog(tmp_path):
    report = write_report(tmp_path)
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    d = tmp_path / "remediation"
    triage = TriageResult.model_validate_json((d / "triage.json").read_text(encoding="utf-8"))
    triage.findings[0].evidence_checked = ["app/invented.dart"]
    (d / "triage.json").write_text(triage.model_dump_json(), encoding="utf-8")
    _set_step_state(tmp_path, 1, "running")
    runner = scripted(n_findings())
    RemediationFlow(tmp_path, runner, report).run()
    assert [c[0] for c in runner.calls] == ["analyze_eval_report", "plan_remediation"]


def test_triage_with_invented_evidence_path_is_rejected_by_the_guardrail(tmp_path):
    report = write_report(tmp_path)
    ids = [f"F-{i:03d}" for i in range(1, n_findings() + 1)]
    runner = FakeRunner({
        "analyze_eval_report": TriageResult(findings=[make_validated(i, evidence_checked=["app/invented.dart"]) for i in ids]),
        "plan_remediation": RemediationBacklog(summary="s", tasks=[make_task(finding_ids=ids)]),
    })
    with pytest.raises(AssertionError, match="do not invent paths"):
        RemediationFlow(tmp_path, runner, report).run()


def test_non_utf8_report_file_does_not_stop_the_flow(tmp_path):
    report = write_report(tmp_path)
    (tmp_path / "eval_report_old.md").write_bytes(b"\xff\xfe" + STATUS_START.encode() + b"\xff" + STATUS_END.encode())
    status = RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    assert status.step("triage").state == "awaiting_approval"


def test_header_shows_live_status_after_deepeval_rewrites_the_report(tmp_path):
    report = write_report(tmp_path)
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    md = tmp_path / "eval_report_flow.md"
    placeholder = f"# R\n{STATUS_START}<p>Remediation not started.</p>{STATUS_END}\n"
    md.write_text(placeholder, encoding="utf-8")
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    assert "AWAITING APPROVAL" in md.read_text(encoding="utf-8")
    md.write_text(placeholder, encoding="utf-8")
    from remediation.cli import main
    assert main(["status", "--run-dir", str(tmp_path)]) == 0
    assert "AWAITING APPROVAL" in md.read_text(encoding="utf-8")


def test_a_different_report_is_ignored_with_an_event_and_a_note(tmp_path):
    report = write_report(tmp_path)
    RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    report.write_text(json.dumps({"changed": True}), encoding="utf-8")
    status = RemediationFlow(tmp_path, scripted(n_findings()), report).run()
    assert "newer DeepEval report" in status.note
    assert "new_report_ignored" in (tmp_path / "remediation" / "history.jsonl").read_text(encoding="utf-8")
    assert "newer DeepEval report" in RemediationStatus.load(tmp_path / "remediation" / "status.json").note
