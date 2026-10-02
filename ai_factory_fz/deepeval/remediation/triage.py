"""Project Manager task: classify each DeepEval finding against the run's evidence."""

from pathlib import Path
from typing import Any

from remediation.guardrails import artifact_guardrail
from remediation.schemas import Finding, TriageResult
from remediation.validation import check_triage

PHASE = "remediation"


def triage_findings(runner, findings: list[Finding], context: dict[str, str],
                    run_dir: Path | None = None) -> tuple[TriageResult, Any]:
    inputs = {"findings": "\n".join(f.model_dump_json() for f in findings), **context}
    result = runner.run(
        PHASE, "analyze_eval_report", inputs, TriageResult,
        guardrail=artifact_guardrail(TriageResult, lambda t: check_triage(t, findings, run_dir)),
        agent_key="project_manager", with_tools=False,
    )
    return result.artifact, result.usage
