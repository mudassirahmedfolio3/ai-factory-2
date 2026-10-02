"""Project Manager task: group validated findings by root cause into a prioritised backlog."""

from typing import Any

from remediation.guardrails import artifact_guardrail
from remediation.schemas import AGENT_KEYS, Finding, RemediationBacklog, TriageResult
from remediation.validation import check_backlog

PHASE = "remediation"


def plan_backlog(
    runner, findings: list[Finding], triage: TriageResult, context: dict[str, str]
) -> tuple[RemediationBacklog, Any]:
    inputs = {
        "findings": "\n".join(f.model_dump_json() for f in findings),
        "validated_findings": triage.model_dump_json(indent=2),
        "agents": ", ".join(AGENT_KEYS),
        **context,
    }
    result = runner.run(
        PHASE, "plan_remediation", inputs, RemediationBacklog,
        guardrail=artifact_guardrail(RemediationBacklog, lambda b: check_backlog(b, findings, triage)),
        agent_key="project_manager", with_tools=False,
    )
    return result.artifact, result.usage
