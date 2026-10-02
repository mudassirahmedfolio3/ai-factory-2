import pytest
from remediation_helpers import FakeRunner, make_finding, make_task, make_validated

import re

from remediation.context import gather_context
from remediation.planner import plan_backlog
from remediation.schemas import RemediationBacklog, TriageResult
from remediation.triage import triage_findings
from remediation.runner import load_prompts


def load_config(name):
    assert name == "tasks"
    return load_prompts()


def fill_template(template, values):
    """Same single-pass {name} substitution as the pipeline's fill_template (KeyError when a value is missing)."""
    return re.sub(r"\{(\w+)\}", lambda m: str(values[m.group(1)]), template)


@pytest.fixture
def ctx(tmp_path):
    return gather_context(tmp_path)


def test_prompts_exist_for_the_project_manager_and_fill_with_hostile_text(ctx):
    tasks = load_config("tasks")
    findings = [make_finding(original_text="<script>alert(1)</script> {not_a_placeholder}")]
    inputs = {"findings": "\n".join(f.model_dump_json() for f in findings), **ctx}
    for key in ("analyze_eval_report", "plan_remediation"):
        assert tasks[key]["agent"] == "project_manager"
        assert tasks[key]["expected_output"].strip()
    filled = fill_template(tasks["analyze_eval_report"]["description"], inputs)
    assert "{not_a_placeholder}" in filled and "{findings}" not in filled


def test_plan_prompt_placeholders_are_all_provided(ctx):
    runner = FakeRunner({
        "analyze_eval_report": TriageResult(findings=[make_validated()]),
        "plan_remediation": RemediationBacklog(summary="s", tasks=[make_task()]),
    })
    findings = [make_finding()]
    triage, _ = triage_findings(runner, findings, ctx)
    plan_backlog(runner, findings, triage, ctx)
    for key, inputs in runner.calls:
        # fill_template raises KeyError if a placeholder has no value
        fill_template(load_config("tasks")[key]["description"], inputs)
    assert [k for k, _ in runner.calls] == ["analyze_eval_report", "plan_remediation"]


def test_triage_returns_validated_findings_and_usage(ctx):
    runner = FakeRunner({"analyze_eval_report": TriageResult(findings=[make_validated()])})
    triage, usage = triage_findings(runner, [make_finding()], ctx)
    assert triage.findings[0].classification == "verified_defect" and usage.phase == "remediation"


def test_triage_guardrail_rejects_invented_finding_ids(ctx):
    runner = FakeRunner({"analyze_eval_report": TriageResult(findings=[make_validated("F-777")])})
    with pytest.raises(AssertionError, match="F-777"):
        triage_findings(runner, [make_finding("F-001")], ctx)


def test_plan_guardrail_rejects_unknown_agent(ctx):
    bad = RemediationBacklog(summary="s", tasks=[make_task(owners=["wizard"])])
    runner = FakeRunner({"plan_remediation": bad})
    with pytest.raises(AssertionError, match="wizard"):
        plan_backlog(runner, [make_finding()], TriageResult(findings=[make_validated()]), ctx)


def test_plan_receives_findings_and_triage_json(ctx):
    runner = FakeRunner({"plan_remediation": RemediationBacklog(summary="s", tasks=[make_task()])})
    plan_backlog(runner, [make_finding()], TriageResult(findings=[make_validated()]), ctx)
    _, inputs = runner.calls[0]
    assert "F-001" in inputs["findings"] and "verified_defect" in inputs["validated_findings"]
