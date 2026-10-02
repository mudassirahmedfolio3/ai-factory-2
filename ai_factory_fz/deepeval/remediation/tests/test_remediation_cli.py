import json

from remediation_helpers import FakeRunner, make_task, make_validated, sample_report

from remediation.cli import main
from remediation.findings import extract_findings
from remediation.schemas import RemediationBacklog, TriageResult


def factory(tmp_path):
    ids = [f.id for f in extract_findings(sample_report())]
    runner = FakeRunner({
        "analyze_eval_report": TriageResult(findings=[make_validated(i) for i in ids]),
        "plan_remediation": RemediationBacklog(summary="s", tasks=[make_task(finding_ids=ids)]),
    })
    return lambda run_dir: runner


def report(run_dir):
    """Write the report plus the file the triage fixtures say was checked."""
    evidence = run_dir / "app" / "lib" / "api" / "api_client.dart"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("// hand-written client\n", encoding="utf-8")
    p = run_dir / "eval_report_flow.json"
    p.write_text(json.dumps(sample_report()), encoding="utf-8")
    return p


def test_run_then_status_then_approve(tmp_path, capsys):
    rp = report(tmp_path)
    assert main(["run", "--run-dir", str(tmp_path), "--report", str(rp)], factory(tmp_path)) == 0
    assert main(["status", "--run-dir", str(tmp_path)], factory(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "AWAITING APPROVAL" in out and "1. DeepEval report: DONE" in out
    assert main(["approve", "--run-dir", str(tmp_path)], factory(tmp_path)) == 0
    assert main(["approve", "--run-dir", str(tmp_path)], factory(tmp_path)) == 2


def test_missing_report_returns_1(tmp_path, capsys):
    assert main(["run", "--run-dir", str(tmp_path), "--report", str(tmp_path / "no.json")], factory(tmp_path)) == 1
    assert "not found" in capsys.readouterr().out


def test_status_without_a_cycle_says_so(tmp_path, capsys):
    assert main(["status", "--run-dir", str(tmp_path)], factory(tmp_path)) == 0
    assert "pending" in capsys.readouterr().out.lower()


def test_run_id_resolves_inside_runs_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("remediation.cli.RUNS_DIR", tmp_path)
    (tmp_path / "myrun").mkdir()
    assert main(["status", "--run-id", "myrun"], factory(tmp_path)) == 0
    assert main(["status", "--run-id", "nope"], factory(tmp_path)) == 2


def test_run_id_outside_runs_dir_is_refused(tmp_path, monkeypatch, capsys):
    runs = tmp_path / "runs"
    runs.mkdir()
    (tmp_path / "x").mkdir()
    monkeypatch.setattr("remediation.cli.RUNS_DIR", runs)
    assert main(["status", "--run-id", "../x"], factory(tmp_path)) == 2
    assert capsys.readouterr().out.strip()


def test_run_dir_with_spaces_works(tmp_path):
    run = tmp_path / "my run"
    run.mkdir()
    rp = report(run)
    assert main(["run", "--run-dir", str(run), "--report", str(rp)], factory(tmp_path)) == 0


def test_missing_baseline_prints_message_and_returns_1(tmp_path, capsys):
    rp = report(tmp_path)
    assert main(["run", "--run-dir", str(tmp_path), "--report", str(rp)], factory(tmp_path)) == 0
    (tmp_path / "remediation" / "baseline" / "eval_report.json").unlink()
    capsys.readouterr()
    assert main(["resume", "--run-dir", str(tmp_path)], factory(tmp_path)) == 1
    assert "baseline report is missing" in capsys.readouterr().out


def test_unexpected_error_prints_type_and_status_and_returns_1(tmp_path, capsys):
    rp = report(tmp_path)

    class Boom:
        def run(self, *a, **k):
            raise ValueError("model exploded")

    assert main(["run", "--run-dir", str(tmp_path), "--report", str(rp)], lambda run_dir: Boom()) == 1
    out = capsys.readouterr().out
    assert "ValueError: model exploded" in out and "Project Manager triage and backlog: FAILED" in out


def test_corrupt_status_json_is_a_readable_message(tmp_path, capsys):
    (tmp_path / "remediation").mkdir()
    (tmp_path / "remediation" / "status.json").write_text("{not json", encoding="utf-8")
    assert main(["status", "--run-dir", str(tmp_path)], factory(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "status.json" in out and "Traceback" not in out
