"""Builders shared by the remediation tests."""

from remediation.schemas import Finding, RemediationTask, ValidatedFinding


def make_finding(id: str = "F-001", **kw) -> Finding:
    base = dict(
        id=id, kind="failed_test", source_test="test_frontend_developer.py::test_uses_generated_api_client",
        agent="frontend_developer", score=0.3, level="LOW",
        original_text="ApiClient is hand-written, not generated.", evidence="Criteria: uses generated client",
    )
    return Finding(**{**base, **kw})


def make_validated(finding_id: str = "F-001", **kw) -> ValidatedFinding:
    base = dict(
        finding_id=finding_id, classification="verified_defect", classification_reason="api_client.dart is hand-written",
        evidence_checked=["app/lib/api/api_client.dart"], root_cause="No generated client step",
        root_cause_status="confirmed", severity="medium", evidence_confidence="high",
        verification_method="Re-run test_uses_generated_api_client",
    )
    return ValidatedFinding(**{**base, **kw})


def make_task(id: str = "R-001", **kw) -> RemediationTask:
    base = dict(
        id=id, title="Use a generated API client", problem="Hand-written ApiClient",
        finding_ids=["F-001"], validation_status="verified_defect", root_cause="No generated client",
        root_cause_status="confirmed", owners=["frontend_developer"], steps=["Generate client from openapi.yaml"],
        acceptance_criteria=["All calls go through the generated client"], verification="DeepEval re-run",
        priority="P2", priority_rationale="Contract drift risk", needs_human_approval=False,
    )
    return RemediationTask(**{**base, **kw})


def sample_report() -> dict:
    """A small eval_report.json: one failed test, one MEDIUM agent with gaps, one clean HIGH agent."""
    return {
        "run": "sample-manual", "pass_threshold": 0.6,
        "overall": {"verdict": "FAIL", "confidence": 0.7, "confidence_level": "MEDIUM", "passed": 2, "failed": 1, "skipped": 0},
        "agents": [
            {"agent": "frontend_developer", "verdict": "FAIL", "confidence": 0.5, "confidence_level": "LOW",
             "analysis": {"gaps": ["ApiClient is hand-written"], "improvements": ["Generate the client from openapi.yaml"]}},
            {"agent": "customer", "verdict": "PASS", "confidence": 0.7, "confidence_level": "MEDIUM",
             "analysis": {"gaps": ["US-only rule not stated"], "improvements": ["Add a US-only constraint"]}},
            {"agent": "architect", "verdict": "PASS", "confidence": 0.9, "confidence_level": "HIGH",
             "analysis": {"gaps": ["minor wording"], "improvements": []}},
        ],
        "tests": [
            {"agent": "frontend_developer", "file": "test_frontend_developer.py", "test": "test_uses_generated_api_client",
             "outcome": "failed", "score": 0.3, "level": "LOW", "criteria": "Uses the generated client",
             "reason": "ApiClient is a hand-written Dio wrapper"},
            {"agent": "architect", "file": "test_architect.py", "test": "test_openapi_complete_and_usable",
             "outcome": "passed", "score": 0.9, "level": "HIGH", "criteria": "c", "reason": "good"},
            {"agent": "customer", "file": "test_customer.py", "test": "test_answers_direct_and_consistent",
             "outcome": "passed", "score": 0.7, "level": "MEDIUM", "criteria": "c", "reason": "ok"},
        ],
    }


from dataclasses import dataclass  # noqa: E402
from types import SimpleNamespace  # noqa: E402


@dataclass
class UsageRecord:
    """The attributes of the pipeline's UsageRecord that the flow reads."""

    phase: str
    agent: str
    model: str
    total_tokens: int = 0


@dataclass
class TaskResult:
    artifact: object
    usage: UsageRecord


class FakeRunner:
    """Stands in for TaskRunner: returns scripted artifacts and applies the real guardrail to them."""

    def __init__(self, replies: dict):
        self.replies = replies
        self.calls: list[tuple[str, dict]] = []

    def run(self, phase, task_key, inputs, output_model, guardrail=None, agent_key=None, with_tools=True, feedback=""):
        self.calls.append((task_key, inputs))
        artifact = self.replies[task_key]
        if guardrail is not None:
            ok, message = guardrail(SimpleNamespace(pydantic=artifact, raw=artifact.model_dump_json()))
            assert ok, message
        return TaskResult(artifact=artifact, usage=UsageRecord(phase=phase, agent=agent_key or "project_manager", model="fake"))
