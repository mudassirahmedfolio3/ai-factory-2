from remediation_helpers import make_finding, make_task, make_validated

from remediation.schemas import Disposition, RemediationBacklog, TriageResult
from remediation.validation import check_backlog, check_triage


def backlog(tasks, dispositions=()):
    return RemediationBacklog(summary="s", tasks=list(tasks), dispositions=list(dispositions))


def test_triage_must_cover_every_finding_once():
    findings = [make_finding("F-001"), make_finding("F-002")]
    errors = check_triage(TriageResult(findings=[make_validated("F-001")]), findings)
    assert any("F-002" in e for e in errors)


def test_triage_rejects_unknown_and_duplicate_ids():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001"), make_validated("F-001"), make_validated("F-099")])
    errors = check_triage(triage, findings)
    assert any("duplicate" in e for e in errors) and any("F-099" in e for e in errors)


def test_verified_defect_needs_evidence():
    triage = TriageResult(findings=[make_validated("F-001", evidence_checked=[])])
    errors = check_triage(triage, [make_finding("F-001")])
    assert any("evidence_checked" in e for e in errors)


def test_valid_backlog_has_no_errors():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001")])
    assert check_backlog(backlog([make_task()]), findings, triage) == []


def test_backlog_rejects_unknown_finding_agent_and_duplicate_task_ids():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001")])
    bad = [make_task("R-001", finding_ids=["F-404"]), make_task("R-001", owners=["wizard"])]
    errors = check_backlog(backlog(bad), findings, triage)
    joined = " ".join(errors)
    assert "F-404" in joined and "wizard" in joined and "duplicate" in joined


def test_backlog_rejects_dependency_cycle_and_unknown_dependency():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001")])
    tasks = [make_task("R-001", depends_on=["R-002"]), make_task("R-002", depends_on=["R-001"]),
             make_task("R-003", depends_on=["R-777"])]
    errors = " ".join(check_backlog(backlog(tasks), findings, triage))
    assert "cycle" in errors and "R-777" in errors


def test_every_finding_needs_a_task_or_a_disposition():
    findings = [make_finding("F-001"), make_finding("F-002")]
    triage = TriageResult(findings=[make_validated("F-001"), make_validated("F-002")])
    errors = check_backlog(backlog([make_task()]), findings, triage)
    assert any("F-002" in e for e in errors)
    ok = backlog([make_task()], [Disposition(finding_id="F-002", disposition="needs_evidence", reason="no code")])
    assert check_backlog(ok, findings, triage) == []


def test_false_positive_gets_a_disposition_not_a_task():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001", classification="false_positive_or_exception")])
    errors = check_backlog(backlog([make_task()]), findings, triage)
    assert any("false" in e.lower() for e in errors)


def test_approval_reason_required_when_approval_needed():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001")])
    errors = check_backlog(backlog([make_task(needs_human_approval=True, approval_reason="")]), findings, triage)
    assert any("approval_reason" in e for e in errors)


def test_backlog_markdown_lists_tasks_with_priority_and_owner():
    md = backlog([make_task()]).to_markdown()
    assert "R-001" in md and "P2" in md and "frontend_developer" in md and "F-001" in md


def test_disposition_must_reference_known_finding():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001")])
    bad = backlog([], [Disposition(finding_id="F-404", disposition="needs_evidence", reason="test")])
    errors = check_backlog(bad, findings, triage)
    assert any("F-404" in e for e in errors)


def test_disposition_rejects_duplicates():
    findings = [make_finding("F-001"), make_finding("F-002")]
    triage = TriageResult(findings=[make_validated("F-001"), make_validated("F-002")])
    bad = backlog([], [Disposition(finding_id="F-001", disposition="needs_evidence", reason="a"),
                       Disposition(finding_id="F-001", disposition="needs_evidence", reason="b")])
    errors = check_backlog(bad, findings, triage)
    assert any("duplicate disposition" in e for e in errors)


def test_finding_cannot_be_in_both_task_and_disposition():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001")])
    bad = backlog([make_task()], [Disposition(finding_id="F-001", disposition="needs_evidence", reason="test")])
    errors = check_backlog(bad, findings, triage)
    assert any("both a task and a disposition" in e for e in errors)


def test_no_action_false_positive_requires_false_positive_classification():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001", classification="verified_defect")])
    bad = backlog([], [Disposition(finding_id="F-001", disposition="no_action_false_positive", reason="test")])
    errors = check_backlog(bad, findings, triage)
    assert any("no_action_false_positive" in e for e in errors)


def test_task_validation_status_must_match_cited_findings_classification():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001", classification="verified_defect")])
    bad = backlog([make_task("R-001", validation_status="unverified")])
    errors = check_backlog(bad, findings, triage)
    assert any("R-001" in e and "validation_status" in e for e in errors)


def test_verified_defect_task_requires_at_least_one_verified_defect_finding():
    findings = [make_finding("F-001"), make_finding("F-002")]
    triage = TriageResult(findings=[make_validated("F-001", classification="unverified"),
                                     make_validated("F-002", classification="unverified")])
    bad = backlog([make_task("R-001", finding_ids=["F-001", "F-002"], validation_status="verified_defect")])
    errors = check_backlog(bad, findings, triage)
    assert any("R-001" in e and "verified_defect" in e for e in errors)


def test_evidence_checked_whitespace_entries_do_not_count():
    triage = TriageResult(findings=[make_validated("F-001", evidence_checked=["   ", ""])])
    errors = check_triage(triage, [make_finding("F-001")])
    assert any("evidence_checked" in e for e in errors)


def test_evidence_paths_must_exist_in_the_run(tmp_path):
    run = tmp_path / "run"
    (run / "app").mkdir(parents=True)
    (run / "app" / "real.dart").write_text("x", encoding="utf-8")
    (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    findings = [make_finding("F-001")]

    def errors(*paths, classification="verified_defect"):
        t = TriageResult(findings=[make_validated("F-001", classification=classification, evidence_checked=list(paths))])
        return check_triage(t, findings, run)

    assert errors("app/real.dart", "  ") == []
    assert any("app/invented.dart" in e and "do not invent paths" in e for e in errors("app/real.dart", "app/invented.dart"))
    assert any("../outside.txt" in e for e in errors("../outside.txt", "app/real.dart"))
    assert any("app/invented.dart" in e for e in errors("app/invented.dart", classification="unverified"))
    legacy = TriageResult(findings=[make_validated("F-001", evidence_checked=["app/invented.dart"])])
    assert check_triage(legacy, findings) == []


def test_rejected_task_does_not_cover_its_findings():
    findings = [make_finding("F-001")]
    triage = TriageResult(findings=[make_validated("F-001")])
    rejected = make_task(finding_ids=["F-001"], status="rejected")
    alone = check_backlog(RemediationBacklog(summary="s", tasks=[rejected]), findings, triage)
    assert any("F-001 has neither a task nor a disposition" in e for e in alone)
    disp = Disposition(finding_id="F-001", disposition="needs_evidence", reason="reviewer declined")
    assert check_backlog(RemediationBacklog(summary="s", tasks=[rejected], dispositions=[disp]), findings, triage) == []
    live = make_task(id="R-002", finding_ids=["F-001"])
    both = check_backlog(RemediationBacklog(summary="s", tasks=[rejected, live], dispositions=[disp]), findings, triage)
    assert any("covered by both" in e for e in both)
