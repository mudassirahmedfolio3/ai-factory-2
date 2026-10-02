# DeepEval Remediation, Stage 1 Implementation Plan (trigger, triage, backlog, approval gate)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When DeepEval writes its report, an opt-in trigger starts a Project Manager process that validates the findings, writes a prioritised remediation backlog, shows a six-step status, and stops for human approval.

**Architecture:** A new package `agentic_sdlc.remediation` (plain classes, no model calls except through the existing `TaskRunner`) works on a run folder and keeps its state in `runs/<id>/remediation/`. A `remediate` CLI drives it. The DeepEval project gains an HTML report, status markers in its reports, and a trigger hook that starts `remediate run`. Steps 3-6 (fix loop, re-evaluation) are NOT in this stage.

**Tech Stack:** Python 3.10-3.13, pydantic, CrewAI `TaskRunner` (existing), pytest, uv. Two uv projects: `ai_factory_fz` (pipeline) and `ai_factory_fz/deepeval` (evaluation).

**Spec:** `docs/superpowers/specs/2026-10-02-deepeval-remediation-design.md`

## Global Constraints

- Pass mark and scale are unchanged: judge scores are 0 to 1, a test passes at 0.6 or above.
- Six steps, exact keys and titles: `report` "DeepEval report", `triage` "Project Manager triage and backlog", `fix` "Fix the source of the problem", `integration` "Integration Pass", `qa_smoke` "QA and smoke tests", `reevaluate` "Re-evaluate with DeepEval".
- Step states: `pending`, `running`, `awaiting_approval`, `done`, `failed`, `blocked`. Step `triage` always ends in `awaiting_approval` when there are findings (human gate "A").
- Finding classifications: `verified_defect`, `specification_gap`, `unverified`, `false_positive_or_exception`. A finding is never `verified_defect` without `evidence_checked`.
- Priorities: P0 critical blocker, P1 high impact, P2 normal gap, P3 low-risk improvement, each with a written rationale. No numeric priority scores.
- Task owners are only the existing agent keys: `customer, spec_writer, project_manager, architect, ui_ux_designer, backend_developer, frontend_developer, qa_engineer, deployment_engineer, integration_pass, smoke_tester`.
- IDs of work items, files and requirements are copied from the run, never invented. Missing evidence becomes an investigation task or a recorded limitation.
- The baseline report copy in `remediation/baseline/` and `history.jsonl` are never overwritten or truncated.
- The trigger is opt-in: only when `DEEPEVAL_REMEDIATE=1`. It never blocks the test session.
- No test in this stage calls a real model. Real model use is only in Task 9, with the user's go-ahead.
- Follow existing style: module docstring first line, type hints, `from agentic_sdlc...` imports, tests flat in `ai_factory_fz/tests/`.
- Run `ai_factory_fz` tests with `cd ai_factory_fz && uv run pytest tests/<file> -v`. Run DeepEval-project tests with `cd ai_factory_fz/deepeval && uv run pytest unit_tests -v`.

## Review Focus

1. A report with no failed tests and no gaps: the backlog is empty, step `triage` ends `done` (not `awaiting_approval`) with a reason, and no model call is made (Task 6).
2. Missing or corrupt report JSON: the step ends `blocked` or `failed` with a readable reason, `status.json` is saved, nothing is half-written (Tasks 2 and 6).
3. The model returns tasks that cite unknown finding IDs, unknown agents, a dependency cycle, or a task for a false positive: the guardrail rejects the output instead of saving it (Task 1).
4. Report text containing `<script>` or `{braces}`: the HTML is escaped and the prompt template still fills (Tasks 5 and 8).
5. Re-running `remediate run` after the gate or after a crash does not repeat model calls or overwrite the baseline, and approving twice is refused (Task 6).

---

### Task 1: Schemas and validation

**Files:**
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/__init__.py`
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/schemas.py`
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/validation.py`
- Create: `ai_factory_fz/tests/remediation_helpers.py`
- Test: `ai_factory_fz/tests/test_remediation_schemas.py`

**Interfaces:**
- Produces (used by every later task):
  - `AGENT_KEYS: tuple[str, ...]`
  - `Finding(id, kind, source_test, agent, score, level, original_text, evidence, suggestions)`
  - `ValidatedFinding(finding_id, classification, classification_reason, evidence_checked, root_cause, root_cause_status, severity, evidence_confidence, verification_method)`
  - `TriageResult(findings: list[ValidatedFinding])`
  - `RemediationTask(...)`, `Disposition(finding_id, disposition, reason)`, `RemediationBacklog(summary, tasks, dispositions, limitations)` with `.to_markdown() -> str`
  - `check_triage(triage: TriageResult, findings: list[Finding]) -> list[str]`
  - `check_backlog(backlog: RemediationBacklog, findings: list[Finding], triage: TriageResult) -> list[str]` (empty list = valid)
  - test helpers `make_finding(id="F-001", **kw)`, `make_validated(finding_id="F-001", **kw)`, `make_task(id="R-001", **kw)` in `tests/remediation_helpers.py`.

- [ ] **Step 1: Write the helpers and the failing tests**

`ai_factory_fz/tests/remediation_helpers.py`:

```python
"""Builders shared by the remediation tests."""

from agentic_sdlc.remediation.schemas import Finding, RemediationTask, ValidatedFinding


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
```

`ai_factory_fz/tests/test_remediation_schemas.py`:

```python
from remediation_helpers import make_finding, make_task, make_validated

from agentic_sdlc.remediation.schemas import Disposition, RemediationBacklog, TriageResult
from agentic_sdlc.remediation.validation import check_backlog, check_triage


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agentic_sdlc.remediation'`

- [ ] **Step 3: Implement the schemas**

`ai_factory_fz/src/agentic_sdlc/remediation/__init__.py`:

```python
"""Remediation loop: turn a DeepEval report into a validated, prioritised backlog and (later stages) fixes."""
```

`ai_factory_fz/src/agentic_sdlc/remediation/schemas.py`:

```python
"""Schemas for the DeepEval remediation loop."""

from typing import Literal

from pydantic import BaseModel, Field

AGENT_KEYS = (
    "customer", "spec_writer", "project_manager", "architect", "ui_ux_designer", "backend_developer",
    "frontend_developer", "qa_engineer", "deployment_engineer", "integration_pass", "smoke_tester",
)

Classification = Literal["verified_defect", "specification_gap", "unverified", "false_positive_or_exception"]
Priority = Literal["P0", "P1", "P2", "P3"]
TaskStatus = Literal["proposed", "approved", "rejected", "in_progress", "done", "failed", "blocked"]


class Finding(BaseModel):
    """One normalized item from the DeepEval report, kept verbatim so results trace back to it."""

    id: str = Field(description="F-001, F-002, ...")
    kind: Literal["failed_test", "gap"]
    source_test: str
    agent: str | None = None
    score: float | None = None
    level: str | None = None
    original_text: str
    evidence: str
    suggestions: list[str] = Field(default_factory=list, description="Improvements the report proposed")


class ValidatedFinding(BaseModel):
    finding_id: str
    classification: Classification
    classification_reason: str
    evidence_checked: list[str] = Field(default_factory=list, description="Run files actually inspected")
    root_cause: str
    root_cause_status: Literal["confirmed", "hypothesis"]
    severity: Literal["critical", "high", "medium", "low"]
    evidence_confidence: Literal["low", "medium", "high"]
    verification_method: str


class TriageResult(BaseModel):
    findings: list[ValidatedFinding]


class RemediationTask(BaseModel):
    id: str = Field(description="R-001, R-002, ...")
    title: str
    problem: str
    finding_ids: list[str]
    validation_status: Classification
    root_cause: str
    root_cause_status: Literal["confirmed", "hypothesis"]
    affected_requirements: list[str] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    owners: list[str] = Field(description="Existing agent keys")
    inputs: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    steps: list[str]
    acceptance_criteria: list[str]
    verification: str
    priority: Priority
    priority_rationale: str
    status: TaskStatus = "proposed"
    needs_human_approval: bool
    approval_reason: str = ""


class Disposition(BaseModel):
    """A finding that gets no task, with the reason."""

    finding_id: str
    disposition: Literal["no_action_false_positive", "needs_evidence", "accepted_exception_pending_approval"]
    reason: str


class RemediationBacklog(BaseModel):
    summary: str
    tasks: list[RemediationTask]
    dispositions: list[Disposition] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = ["# Remediation backlog", "", self.summary, ""]
        if self.limitations:
            lines += ["## Limitations", *[f"- {x}" for x in self.limitations], ""]
        lines += ["## Tasks", ""]
        for t in sorted(self.tasks, key=lambda t: (t.priority, t.id)):
            lines += [
                f"### {t.id} [{t.priority}] {t.title}", "",
                f"- Status: {t.status}. Owners: {', '.join(t.owners)}. Depends on: {', '.join(t.depends_on) or 'none'}",
                f"- Findings: {', '.join(t.finding_ids)}. Validation: {t.validation_status}",
                f"- Problem: {t.problem}",
                f"- Root cause ({t.root_cause_status}): {t.root_cause}",
                f"- Priority rationale: {t.priority_rationale}",
                f"- Human approval needed: {'yes, ' + t.approval_reason if t.needs_human_approval else 'no'}",
                "- Steps:", *[f"  - {s}" for s in t.steps],
                "- Acceptance criteria:", *[f"  - {a}" for a in t.acceptance_criteria],
                f"- Verification: {t.verification}", "",
            ]
        if self.dispositions:
            lines += ["## Findings without a task", ""]
            lines += [f"- {d.finding_id}: {d.disposition}. {d.reason}" for d in self.dispositions]
        return "\n".join(lines) + "\n"
```

`ai_factory_fz/src/agentic_sdlc/remediation/validation.py`:

```python
"""Checks on model output (used as task guardrails): a list of error strings, empty when valid."""

from agentic_sdlc.remediation.schemas import AGENT_KEYS, Finding, RemediationBacklog, TriageResult


def check_triage(triage: TriageResult, findings: list[Finding]) -> list[str]:
    known = {f.id for f in findings}
    errors, seen = [], set()
    for v in triage.findings:
        if v.finding_id in seen:
            errors.append(f"duplicate triage entry for {v.finding_id}")
        seen.add(v.finding_id)
        if v.finding_id not in known:
            errors.append(f"{v.finding_id} is not a finding in the report")
        if v.classification == "verified_defect" and not v.evidence_checked:
            errors.append(f"{v.finding_id} is classified verified_defect but evidence_checked is empty")
    for missing in sorted(known - seen):
        errors.append(f"{missing} has no triage entry")
    return errors


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        if any(visit(d) for d in graph[node] if d in graph):
            return True
        state[node] = 2
        return False

    return any(visit(n) for n in graph)


def check_backlog(backlog: RemediationBacklog, findings: list[Finding], triage: TriageResult) -> list[str]:
    known = {f.id for f in findings}
    classes = {v.finding_id: v.classification for v in triage.findings}
    errors, task_ids, covered = [], set(), set()
    for t in backlog.tasks:
        if t.id in task_ids:
            errors.append(f"duplicate task id {t.id}")
        task_ids.add(t.id)
        if not t.finding_ids:
            errors.append(f"{t.id} cites no finding")
        for fid in t.finding_ids:
            covered.add(fid)
            if fid not in known:
                errors.append(f"{t.id} cites unknown finding {fid}")
            elif classes.get(fid) == "false_positive_or_exception":
                errors.append(f"{t.id} is a task for false positive {fid}: give it a disposition instead")
        if not t.owners:
            errors.append(f"{t.id} has no owner")
        for owner in t.owners:
            if owner not in AGENT_KEYS:
                errors.append(f"{t.id} owner '{owner}' is not an existing agent ({', '.join(AGENT_KEYS)})")
        if t.needs_human_approval and not t.approval_reason.strip():
            errors.append(f"{t.id} needs human approval but approval_reason is empty")
    for t in backlog.tasks:
        for dep in t.depends_on:
            if dep not in task_ids:
                errors.append(f"{t.id} depends on unknown task {dep}")
    if _has_cycle({t.id: list(t.depends_on) for t in backlog.tasks}):
        errors.append("task dependencies contain a cycle")
    covered |= {d.finding_id for d in backlog.dispositions}
    for fid in sorted(known - covered):
        errors.append(f"{fid} has neither a task nor a disposition")
    return errors
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_schemas.py -v`
Expected: PASS (10 passed)

- [ ] **Step 5: Commit**

```bash
git add ai_factory_fz/src/agentic_sdlc/remediation ai_factory_fz/tests/remediation_helpers.py ai_factory_fz/tests/test_remediation_schemas.py
git commit -m "feat(remediation): schemas and guardrail checks"
```

---

### Task 2: Findings extraction

**Files:**
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/findings.py`
- Modify: `ai_factory_fz/tests/remediation_helpers.py` (append `sample_report`)
- Test: `ai_factory_fz/tests/test_remediation_findings.py`

**Interfaces:**
- Consumes: `Finding` from Task 1; the `eval_report.json` shape written by `deepeval/eval_report.py`: top-level `run`, `agents` (each with `agent`, `verdict`, `confidence_level`, `analysis` {`gaps`, `improvements`}), `tests` (each with `agent`, `file`, `test`, `outcome`, `score`, `level`, `criteria`, `reason`).
- Produces: `ReportFormatError(ValueError)`, `load_report(path: Path) -> dict`, `extract_findings(report: dict) -> list[Finding]`.

- [ ] **Step 1: Write the failing tests**

Append to `ai_factory_fz/tests/remediation_helpers.py`:

```python


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
```

`ai_factory_fz/tests/test_remediation_findings.py`:

```python
import json

import pytest
from remediation_helpers import sample_report

from agentic_sdlc.remediation.findings import ReportFormatError, extract_findings, load_report


def test_failed_tests_become_findings_with_verbatim_text():
    findings = extract_findings(sample_report())
    failed = [f for f in findings if f.kind == "failed_test"]
    assert len(failed) == 1
    f = failed[0]
    assert f.source_test == "test_frontend_developer.py::test_uses_generated_api_client"
    assert f.original_text == "ApiClient is a hand-written Dio wrapper"
    assert "Uses the generated client" in f.evidence and f.score == 0.3 and f.agent == "frontend_developer"


def test_gaps_of_non_high_agents_become_findings_with_suggestions():
    gaps = [f for f in extract_findings(sample_report()) if f.kind == "gap"]
    texts = {f.original_text for f in gaps}
    assert "US-only rule not stated" in texts and "ApiClient is hand-written" in texts
    assert "minor wording" not in texts  # architect is HIGH and passed
    customer = next(f for f in gaps if f.agent == "customer")
    assert customer.suggestions == ["Add a US-only constraint"]


def test_ids_are_sequential_and_unique():
    ids = [f.id for f in extract_findings(sample_report())]
    assert ids == [f"F-{i:03d}" for i in range(1, len(ids) + 1)]


def test_report_without_failures_or_gaps_gives_no_findings():
    report = sample_report()
    report["tests"] = [t for t in report["tests"] if t["outcome"] == "passed"]
    for a in report["agents"]:
        a["analysis"] = {"gaps": [], "improvements": []}
        a["verdict"], a["confidence_level"] = "PASS", "HIGH"
    assert extract_findings(report) == []


def test_missing_sections_raise_a_readable_error():
    with pytest.raises(ReportFormatError, match="tests"):
        extract_findings({"agents": []})


def test_agent_without_analysis_is_skipped_not_fatal():
    report = sample_report()
    report["agents"][1].pop("analysis")
    assert all(f.agent != "customer" or f.kind != "gap" for f in extract_findings(report))


def test_load_report_rejects_missing_and_corrupt_files(tmp_path):
    with pytest.raises(ReportFormatError, match="not found"):
        load_report(tmp_path / "nope.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ReportFormatError, match="valid JSON"):
        load_report(bad)
    good = tmp_path / "good.json"
    good.write_text(json.dumps(sample_report()), encoding="utf-8")
    assert load_report(good)["run"] == "sample-manual"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_findings.py -v`
Expected: FAIL with `ModuleNotFoundError: ... remediation.findings`

- [ ] **Step 3: Implement**

`ai_factory_fz/src/agentic_sdlc/remediation/findings.py`:

```python
"""Turn a DeepEval report (eval_report.json) into normalized findings."""

import json
from pathlib import Path

from agentic_sdlc.remediation.schemas import Finding


class ReportFormatError(ValueError):
    """The report is missing, not JSON, or lacks the sections remediation needs."""


def load_report(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ReportFormatError(f"DeepEval report not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ReportFormatError(f"DeepEval report is not valid JSON ({path}): {e}") from e
    if not isinstance(data, dict):
        raise ReportFormatError(f"DeepEval report must be a JSON object: {path}")
    return data


def extract_findings(report: dict) -> list[Finding]:
    """Failed tests (verbatim judge reason) plus the gaps reported for agents that are not clean HIGH passes."""
    for key in ("tests", "agents"):
        if not isinstance(report.get(key), list):
            raise ReportFormatError(f"DeepEval report has no '{key}' list")
    raw: list[dict] = []
    for t in report["tests"]:
        if t.get("outcome") != "failed":
            continue
        reason = t.get("reason") or "(the judge gave no reason)"
        raw.append(dict(
            kind="failed_test", source_test=f"{t.get('file')}::{t.get('test')}", agent=t.get("agent"),
            score=t.get("score"), level=t.get("level"), original_text=reason,
            evidence=f"Criteria: {t.get('criteria', '')}\nJudge's reason: {reason}",
        ))
    for a in report["agents"]:
        analysis = a.get("analysis") or {}
        if a.get("confidence_level") == "HIGH" and a.get("verdict") == "PASS":
            continue
        suggestions = list(analysis.get("improvements") or [])
        for gap in analysis.get("gaps") or []:
            raw.append(dict(
                kind="gap", source_test=f"agent:{a.get('agent')}", agent=a.get("agent"),
                score=a.get("confidence"), level=a.get("confidence_level"), original_text=gap,
                evidence=f"Gap reported in the analysis of {a.get('agent')} (confidence {a.get('confidence')}, "
                         f"{a.get('confidence_level')})",
                suggestions=suggestions,
            ))
    return [Finding(id=f"F-{i:03d}", **r) for i, r in enumerate(raw, start=1)]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_findings.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add ai_factory_fz/src/agentic_sdlc/remediation/findings.py ai_factory_fz/tests/remediation_helpers.py ai_factory_fz/tests/test_remediation_findings.py
git commit -m "feat(remediation): extract findings from eval_report.json"
```

---

### Task 3: Status model and report header refresh

**Files:**
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/status.py`
- Test: `ai_factory_fz/tests/test_remediation_status.py`

**Interfaces:**
- Produces:
  - `STEP_DEFS: list[tuple[str, str]]` (key, title), `STATUS_START = "<!-- remediation-status:start -->"`, `STATUS_END = "<!-- remediation-status:end -->"`
  - `InvalidTransition(RuntimeError)`
  - `StepStatus(key, title, state, reason, updated)`
  - `RemediationStatus(steps, round, note)` with `.load(path) -> RemediationStatus` (classmethod; defaults when the file is missing), `.save(path)`, `.step(key) -> StepStatus`, `.set(key, state, reason="")`, `.lines() -> list[str]`, `.block_md() -> str`, `.block_html() -> str`
  - `refresh_report_headers(run_dir: Path, status: RemediationStatus) -> list[Path]` (rewrites the block between the markers in `run_dir/eval_report*.md` and `*.html`).

- [ ] **Step 1: Write the failing tests**

`ai_factory_fz/tests/test_remediation_status.py`:

```python
import pytest

from agentic_sdlc.remediation.status import (
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_status.py -v`
Expected: FAIL with `ModuleNotFoundError: ... remediation.status`

- [ ] **Step 3: Implement**

`ai_factory_fz/src/agentic_sdlc/remediation/status.py`:

```python
"""The six-step status of a remediation cycle, saved to runs/<id>/remediation/status.json."""

import html
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

StepState = Literal["pending", "running", "awaiting_approval", "done", "failed", "blocked"]
STEP_DEFS = [
    ("report", "DeepEval report"),
    ("triage", "Project Manager triage and backlog"),
    ("fix", "Fix the source of the problem"),
    ("integration", "Integration Pass"),
    ("qa_smoke", "QA and smoke tests"),
    ("reevaluate", "Re-evaluate with DeepEval"),
]
STATUS_START = "<!-- remediation-status:start -->"
STATUS_END = "<!-- remediation-status:end -->"
_ALLOWED: dict[str, set[str]] = {
    "pending": {"running", "blocked"},
    "running": {"awaiting_approval", "done", "failed", "blocked"},
    "awaiting_approval": {"done", "blocked"},
    "failed": {"running"},
    "blocked": {"running"},
    "done": set(),
}


class InvalidTransition(RuntimeError):
    pass


class StepStatus(BaseModel):
    key: str
    title: str
    state: StepState = "pending"
    reason: str = ""
    updated: str = ""


def _default_steps() -> list[StepStatus]:
    return [StepStatus(key=k, title=t) for k, t in STEP_DEFS]


class RemediationStatus(BaseModel):
    steps: list[StepStatus] = Field(default_factory=_default_steps)
    round: int = 1
    note: str = ""

    @classmethod
    def load(cls, path: Path) -> "RemediationStatus":
        path = Path(path)
        return cls.model_validate_json(path.read_text(encoding="utf-8")) if path.is_file() else cls()

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(path)

    def step(self, key: str) -> StepStatus:
        for s in self.steps:
            if s.key == key:
                return s
        raise KeyError(f"Unknown remediation step '{key}'")

    def set(self, key: str, state: StepState, reason: str = "") -> None:
        s = self.step(key)
        if state not in _ALLOWED[s.state]:
            raise InvalidTransition(f"Step '{key}' cannot go from {s.state} to {state}")
        if state in ("running", "awaiting_approval", "done"):
            earlier = self.steps[: self.steps.index(s)]
            if any(e.state != "done" for e in earlier):
                raise InvalidTransition(f"Step '{key}' cannot be {state} before the earlier steps are done")
        s.state, s.reason, s.updated = state, reason, datetime.now().isoformat(timespec="seconds")

    def lines(self) -> list[str]:
        return [f"{i}. {s.title}: {s.state.upper().replace('_', ' ')}" + (f" ({s.reason})" if s.reason else "")
                for i, s in enumerate(self.steps, start=1)]

    def block_md(self) -> str:
        rows = [f"{STATUS_START}", f"**Remediation status** (round {self.round})", "",
                "| # | Step | State | Note |", "|---|---|---|---|"]
        rows += [f"| {i} | {s.title} | {s.state.upper().replace('_', ' ')} | {s.reason} |"
                 for i, s in enumerate(self.steps, start=1)]
        rows.append(STATUS_END)
        return "\n".join(rows)

    def block_html(self) -> str:
        items = "".join(
            f'<li class="{html.escape(s.state)}"><b>{html.escape(s.title)}</b>: '
            f'{html.escape(s.state.upper().replace("_", " "))}'
            + (f" ({html.escape(s.reason)})" if s.reason else "") + "</li>"
            for s in self.steps
        )
        return f'{STATUS_START}<ol class="remediation-status">{items}</ol>{STATUS_END}'


def refresh_report_headers(run_dir: Path, status: RemediationStatus) -> list[Path]:
    """Rewrite the status block inside eval_report*.md / *.html that already contain the markers."""
    pattern = re.compile(re.escape(STATUS_START) + r".*?" + re.escape(STATUS_END), re.S)
    changed = []
    for path in sorted(Path(run_dir).glob("eval_report*")):
        if path.suffix not in (".md", ".html"):
            continue
        text = path.read_text(encoding="utf-8")
        if STATUS_START not in text:
            continue
        block = status.block_html() if path.suffix == ".html" else status.block_md()
        path.write_text(pattern.sub(lambda _m: block, text, count=1), encoding="utf-8")
        changed.append(path)
    return changed
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_status.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add ai_factory_fz/src/agentic_sdlc/remediation/status.py ai_factory_fz/tests/test_remediation_status.py
git commit -m "feat(remediation): six-step status model and report header refresh"
```

---

### Task 4: Run context gathering

**Files:**
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/context.py`
- Test: `ai_factory_fz/tests/test_remediation_context.py`

**Interfaces:**
- Produces: `gather_context(run_dir: Path, max_chars: int = 12000) -> dict[str, str]` with the keys `prd, architecture, openapi, design, product_brief, file_listing, code, reports, limitations`. Missing artifacts become `"(not available)"` and are listed in `limitations`. Nothing is read outside `run_dir`.

- [ ] **Step 1: Write the failing tests**

`ai_factory_fz/tests/test_remediation_context.py`:

```python
from agentic_sdlc.remediation.context import gather_context


def make_run(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "prd.md").write_text("PRD text", encoding="utf-8")
    (tmp_path / "docs" / "openapi.yaml").write_text("openapi: 3.1.0", encoding="utf-8")
    (tmp_path / "server" / "src").mkdir(parents=True)
    (tmp_path / "server" / "src" / "main.ts").write_text("bootstrap()", encoding="utf-8")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "qa_m1.md").write_text("QA report", encoding="utf-8")
    return tmp_path


def test_reads_present_artifacts_and_lists_files(tmp_path):
    ctx = gather_context(make_run(tmp_path))
    assert ctx["prd"] == "PRD text" and ctx["openapi"] == "openapi: 3.1.0"
    assert "server/src/main.ts" in ctx["file_listing"] and "bootstrap()" in ctx["code"]
    assert "QA report" in ctx["reports"]


def test_missing_artifacts_are_marked_and_listed_as_limitations(tmp_path):
    ctx = gather_context(make_run(tmp_path))
    assert ctx["architecture"] == "(not available)"
    assert "docs/architecture.md" in ctx["limitations"] and "docs/prd.md" not in ctx["limitations"]


def test_empty_run_does_not_crash(tmp_path):
    ctx = gather_context(tmp_path)
    assert ctx["file_listing"] == "(no source files)" and ctx["code"] == "(no source files)"
    assert ctx["reports"] == "(no reports)"


def test_long_files_are_truncated(tmp_path):
    run = make_run(tmp_path)
    (run / "docs" / "prd.md").write_text("x" * 50_000, encoding="utf-8")
    assert len(gather_context(run, max_chars=1000)["prd"]) <= 1000
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_context.py -v`
Expected: FAIL with `ModuleNotFoundError: ... remediation.context`

- [ ] **Step 3: Implement**

`ai_factory_fz/src/agentic_sdlc/remediation/context.py`:

```python
"""Collect the run artifacts the Project Manager needs as evidence (read-only, bounded)."""

from pathlib import Path

ARTIFACTS = {
    "prd": "docs/prd.md",
    "architecture": "docs/architecture.md",
    "openapi": "docs/openapi.yaml",
    "design": "docs/design_system.md",
    "product_brief": "docs/product_brief.md",
}
CODE_ROOTS = ("server/src", "app/lib", "app/test", "app/integration_test", "server/smoke", "infra")
NOT_AVAILABLE = "(not available)"


def _read(path: Path, limit: int) -> str:
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def gather_context(run_dir: Path, max_chars: int = 12000) -> dict[str, str]:
    run_dir = Path(run_dir)
    ctx: dict[str, str] = {}
    missing: list[str] = []
    for key, rel in ARTIFACTS.items():
        p = run_dir / rel
        if p.is_file():
            ctx[key] = _read(p, max_chars)
        else:
            ctx[key] = NOT_AVAILABLE
            missing.append(rel)

    files = sorted(
        p for root in CODE_ROOTS if (run_dir / root).is_dir() for p in (run_dir / root).rglob("*") if p.is_file()
    )
    ctx["file_listing"] = "\n".join(p.relative_to(run_dir).as_posix() for p in files[:300]) or "(no source files)"
    code = [f"### {p.relative_to(run_dir).as_posix()}\n{_read(p, 3000)}" for p in files[:40]]
    ctx["code"] = "\n\n".join(code)[: max_chars * 2] or "(no source files)"

    reports = sorted((run_dir / "reports").glob("*.md")) if (run_dir / "reports").is_dir() else []
    ctx["reports"] = "\n\n".join(f"### {p.name}\n{_read(p, max_chars)}" for p in reports)[: max_chars * 2] or "(no reports)"
    ctx["limitations"] = "\n".join(f"- missing: {m}" for m in missing) or "none"
    return ctx
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_context.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add ai_factory_fz/src/agentic_sdlc/remediation/context.py ai_factory_fz/tests/test_remediation_context.py
git commit -m "feat(remediation): gather bounded run context as evidence"
```

---

### Task 5: Project Manager prompts, triage and planner

**Files:**
- Modify: `ai_factory_fz/config/tasks.yaml` (append two tasks)
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/triage.py`
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/planner.py`
- Modify: `ai_factory_fz/tests/remediation_helpers.py` (append `FakeRunner`)
- Test: `ai_factory_fz/tests/test_remediation_pm.py`

**Interfaces:**
- Consumes: `check_triage`, `check_backlog` (Task 1); `gather_context` result dict (Task 4); `TaskRunner.run(phase, task_key, inputs, output_model, guardrail, agent_key, with_tools, feedback)` and `artifact_guardrail(model, check)` from `agentic_sdlc.crews.base`.
- Produces:
  - `triage_findings(runner, findings: list[Finding], context: dict[str, str]) -> tuple[TriageResult, UsageRecord]`
  - `plan_backlog(runner, findings: list[Finding], triage: TriageResult, context: dict[str, str]) -> tuple[RemediationBacklog, UsageRecord]`
  - Task keys `analyze_eval_report` and `plan_remediation` in `tasks.yaml`, agent `project_manager`.
  - test helper `FakeRunner(replies: dict[str, BaseModel])` that records `.calls = [(task_key, inputs)]` and runs the guardrail on the scripted reply.

- [ ] **Step 1: Write the failing tests**

Append to `ai_factory_fz/tests/remediation_helpers.py`:

```python


from types import SimpleNamespace  # noqa: E402

from agentic_sdlc.crews.base import TaskResult  # noqa: E402
from agentic_sdlc.state import UsageRecord  # noqa: E402


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
```

`ai_factory_fz/tests/test_remediation_pm.py`:

```python
import pytest
from remediation_helpers import FakeRunner, make_finding, make_task, make_validated

from agentic_sdlc.crews.base import fill_template
from agentic_sdlc.remediation.context import gather_context
from agentic_sdlc.remediation.planner import plan_backlog
from agentic_sdlc.remediation.schemas import RemediationBacklog, TriageResult
from agentic_sdlc.remediation.triage import triage_findings
from agentic_sdlc.settings import load_config


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_pm.py -v`
Expected: FAIL (`KeyError: 'analyze_eval_report'` / `ModuleNotFoundError`)

- [ ] **Step 3: Add the prompts**

Append to `ai_factory_fz/config/tasks.yaml` (keep two-space indentation like the other tasks; do not use `{word}` in text unless it is a real placeholder):

```yaml

analyze_eval_report:
  agent: project_manager
  description: |
    You are the Project Manager acting as the SDLC remediation orchestrator. A DeepEval report judged the
    output of the pipeline's agents. Validate each finding against the run's own artifacts before anyone fixes
    anything. The report is evidence to investigate, not the truth.

    Findings from the DeepEval report (JSON lines, keep their ids):
    {findings}

    Approved PRD:
    {prd}

    Product brief:
    {product_brief}

    Architecture:
    {architecture}

    OpenAPI contract:
    {openapi}

    Design system:
    {design}

    Files in the run:
    {file_listing}

    Source code excerpts:
    {code}

    QA and release reports:
    {reports}

    Known limitations (artifacts that are missing):
    {limitations}

    Rules:
    - Return exactly one entry per finding id, no extras, none missing.
    - Classify every finding as one of: verified_defect (reproducible behaviour or a code, test or contract
      inconsistency you can point to in the files above), specification_gap (a requirement is missing,
      ambiguous, contradictory or not approved), unverified (the evidence above is not enough to confirm or
      reject it), false_positive_or_exception (the files above show the finding is wrong).
    - A test marked failed is NOT proof of a defect. verified_defect needs at least one file in
      evidence_checked that you actually read above. If you cannot show evidence, use unverified.
    - evidence_checked lists real paths from the file list above. Never invent files, work item ids or
      requirement ids.
    - root_cause_status is confirmed only when the files show the cause; otherwise hypothesis.
    - Findings that share a cause should state the same root_cause wording so they can be grouped.
    - severity: critical (security, data loss, business behaviour broken), high, medium, low.
    - verification_method says how to prove the fix (for example which DeepEval test to re-run or which
      acceptance criterion to check).
  expected_output: One validated entry for every finding id.

plan_remediation:
  agent: project_manager
  description: |
    You are the Project Manager. Turn the validated findings into a remediation backlog that the existing
    specialist agents can execute later. Do not fix anything yourself.

    Original findings (JSON lines):
    {findings}

    Validated findings (JSON):
    {validated_findings}

    Approved PRD:
    {prd}

    Architecture:
    {architecture}

    OpenAPI contract:
    {openapi}

    Files in the run:
    {file_listing}

    Known limitations (artifacts that are missing):
    {limitations}

    Existing agents you may assign (use these keys only):
    {agents}

    Rules:
    - Group findings that share a root cause into one task; every task lists all its finding_ids.
    - Every finding id must appear in a task OR in dispositions with a reason. Findings classified
      false_positive_or_exception get a disposition (no_action_false_positive), never a task.
    - unverified findings get an investigation task (steps say what evidence to collect) or a disposition
      needs_evidence.
    - Order work by dependency: business ambiguity goes to customer, then spec_writer, then architect
      (contract), then backend_developer and frontend_developer, ui_ux_designer and deployment_engineer in
      parallel where possible, then integration_pass, then qa_engineer and smoke_tester. Use depends_on with
      task ids (R-001, R-002, ...). No cycles.
    - Developers must not be asked to decide business questions; give those to the customer first.
    - Priority: P0 critical blocker, P1 high impact, P2 normal functional or integration gap, P3 low-risk
      improvement. Write a one-sentence priority_rationale. Do not use numeric scores and do not treat the
      overall DeepEval confidence as a substitute for individual failed tests.
    - needs_human_approval is true for ambiguous business requirements, material architecture changes,
      security-sensitive behaviour, destructive data operations or scope expansion; then give approval_reason.
    - acceptance_criteria and verification must be checkable (a test, an endpoint response, a file state).
    - Use only ids, files and requirement names that appear above. If something needed is missing, say so in
      limitations.
  expected_output: A prioritised remediation backlog with dispositions.
```

- [ ] **Step 4: Implement triage and planner**

`ai_factory_fz/src/agentic_sdlc/remediation/triage.py`:

```python
"""Project Manager task: classify each DeepEval finding against the run's evidence."""

from agentic_sdlc.crews.base import artifact_guardrail
from agentic_sdlc.remediation.schemas import Finding, TriageResult
from agentic_sdlc.remediation.validation import check_triage
from agentic_sdlc.state import UsageRecord

PHASE = "remediation"


def triage_findings(runner, findings: list[Finding], context: dict[str, str]) -> tuple[TriageResult, UsageRecord]:
    inputs = {"findings": "\n".join(f.model_dump_json() for f in findings), **context}
    result = runner.run(
        PHASE, "analyze_eval_report", inputs, TriageResult,
        guardrail=artifact_guardrail(TriageResult, lambda t: check_triage(t, findings)),
        agent_key="project_manager", with_tools=False,
    )
    return result.artifact, result.usage
```

`ai_factory_fz/src/agentic_sdlc/remediation/planner.py`:

```python
"""Project Manager task: group validated findings by root cause into a prioritised backlog."""

from agentic_sdlc.crews.base import artifact_guardrail
from agentic_sdlc.remediation.schemas import AGENT_KEYS, Finding, RemediationBacklog, TriageResult
from agentic_sdlc.remediation.validation import check_backlog
from agentic_sdlc.state import UsageRecord

PHASE = "remediation"


def plan_backlog(
    runner, findings: list[Finding], triage: TriageResult, context: dict[str, str]
) -> tuple[RemediationBacklog, UsageRecord]:
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
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_pm.py -v`
Expected: PASS (6 passed). If the guardrail tests fail because `artifact_guardrail` returns a tuple whose first item is `True` for valid output, re-read `crews/base.py:artifact_guardrail` and adjust only the helper, not the production code.

- [ ] **Step 6: Commit**

```bash
git add ai_factory_fz/config/tasks.yaml ai_factory_fz/src/agentic_sdlc/remediation/triage.py ai_factory_fz/src/agentic_sdlc/remediation/planner.py ai_factory_fz/tests/remediation_helpers.py ai_factory_fz/tests/test_remediation_pm.py
git commit -m "feat(remediation): project manager triage and planning tasks"
```

---

### Task 6: RemediationFlow (steps 1 and 2, approval)

**Files:**
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/flow.py`
- Test: `ai_factory_fz/tests/test_remediation_flow.py`

**Interfaces:**
- Consumes: everything from Tasks 1-5.
- Produces:
  - `RemediationError(RuntimeError)`
  - `RemediationFlow(run_dir: Path, runner, report_path: Path | None = None)` with:
    - `.run() -> RemediationStatus` (steps 1-2, idempotent, stops at `awaiting_approval` or `done` when there is nothing to remediate)
    - `.approve() -> RemediationStatus` (refuses unless `triage` is `awaiting_approval`)
  - Files under `run_dir/remediation/`: `status.json`, `baseline/eval_report.json`, `findings.json`, `triage.json`, `backlog.json`, `backlog.md`, `history.jsonl`.

- [ ] **Step 1: Write the failing tests**

`ai_factory_fz/tests/test_remediation_flow.py`:

```python
import json

import pytest
from remediation_helpers import FakeRunner, make_task, make_validated, sample_report

from agentic_sdlc.remediation.flow import RemediationError, RemediationFlow
from agentic_sdlc.remediation.schemas import RemediationBacklog, TriageResult
from agentic_sdlc.remediation.status import RemediationStatus, STATUS_END, STATUS_START


def write_report(run_dir, report=None):
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
    from agentic_sdlc.remediation.findings import extract_findings
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


def test_corrupt_report_fails_triage_with_a_reason(tmp_path):
    bad = tmp_path / "eval_report_flow.json"
    bad.write_text("{oops", encoding="utf-8")
    status = RemediationFlow(tmp_path, FakeRunner({}), bad).run()
    assert status.step("triage").state == "failed" and "valid JSON" in status.step("triage").reason


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_flow.py -v`
Expected: FAIL with `ModuleNotFoundError: ... remediation.flow`

- [ ] **Step 3: Implement**

`ai_factory_fz/src/agentic_sdlc/remediation/flow.py`:

```python
"""RemediationFlow, stage 1: report -> Project Manager triage and backlog -> human approval.

Steps 3-6 (fix loop, integration, QA and smoke, re-evaluation) are added in later stages."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from agentic_sdlc.remediation.context import gather_context
from agentic_sdlc.remediation.findings import ReportFormatError, extract_findings, load_report
from agentic_sdlc.remediation.planner import plan_backlog
from agentic_sdlc.remediation.schemas import Finding, RemediationBacklog, TriageResult
from agentic_sdlc.remediation.status import RemediationStatus, refresh_report_headers
from agentic_sdlc.remediation.triage import triage_findings


class RemediationError(RuntimeError):
    pass


class RemediationFlow:
    def __init__(self, run_dir: Path, runner, report_path: Path | None = None):
        self.run_dir = Path(run_dir).resolve()
        self.runner = runner
        self.report_path = Path(report_path) if report_path else None
        self.dir = self.run_dir / "remediation"
        self.status = RemediationStatus.load(self.dir / "status.json")

    # ---------- helpers ----------

    def _save(self) -> None:
        self.status.save(self.dir / "status.json")
        refresh_report_headers(self.run_dir, self.status)

    def _set(self, key: str, state: str, reason: str = "") -> None:
        self.status.set(key, state, reason)  # type: ignore[arg-type]
        self._save()
        self._log("step", step=key, state=state, reason=reason)

    def _log(self, event: str, **data) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with (self.dir / "history.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), "event": event, **data}) + "\n")

    def _write_json(self, name: str, model) -> None:
        (self.dir / name).write_text(model.model_dump_json(indent=2), encoding="utf-8")

    def _find_report(self) -> Path | None:
        if self.report_path:
            return self.report_path if self.report_path.is_file() else None
        candidates = sorted(self.run_dir.glob("eval_report*.json"), key=lambda p: p.stat().st_mtime)
        return candidates[-1] if candidates else None

    # ---------- step 1 ----------

    def _step_report(self) -> bool:
        baseline = self.dir / "baseline" / "eval_report.json"
        if self.status.step("report").state == "done" and baseline.is_file():
            return True
        self.dir.mkdir(parents=True, exist_ok=True)
        self._save()
        self._set("report", "running")   # also valid from blocked: a new attempt after the report was supplied
        source = self._find_report()
        if source is None:
            self._set("report", "blocked", f"DeepEval report not found: {self.report_path or self.run_dir / 'eval_report*.json'}")
            return False
        if not baseline.is_file():
            baseline.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, baseline)
        self._set("report", "done", f"baseline saved from {source.name}")
        return True

    # ---------- step 2 ----------

    def _step_triage(self) -> None:
        if self.status.step("triage").state in ("awaiting_approval", "done"):
            return
        self._set("triage", "running")
        try:
            findings = extract_findings(load_report(self.dir / "baseline" / "eval_report.json"))
            (self.dir / "findings.json").write_text(
                json.dumps([f.model_dump() for f in findings], indent=2), encoding="utf-8")
            if not findings:
                self._write_backlog(RemediationBacklog(summary="The report has no failed tests or gaps.", tasks=[]), [])
                self._set("triage", "done", "Nothing to remediate: the report has no failed tests or gaps")
                return
            context = gather_context(self.run_dir)
            triage = self._cached("triage.json", TriageResult) or self._run_triage(findings, context)
            backlog = self._cached("backlog.json", RemediationBacklog) or self._run_plan(findings, triage, context)
            backlog.limitations = sorted({*backlog.limitations, *(x[2:] for x in context["limitations"].splitlines() if x.startswith("- "))})
            self._write_backlog(backlog, findings)
            self._set("triage", "awaiting_approval",
                      f"{len(backlog.tasks)} task(s) in remediation/backlog.md. Review it, then run: remediate approve")
        except ReportFormatError as e:
            self._set("triage", "failed", str(e))
        except Exception as e:
            self._set("triage", "failed", f"{type(e).__name__}: {e}")
            raise

    def _cached(self, name: str, model):
        path = self.dir / name
        return model.model_validate_json(path.read_text(encoding="utf-8")) if path.is_file() else None

    def _run_triage(self, findings: list[Finding], context: dict[str, str]) -> TriageResult:
        triage, usage = triage_findings(self.runner, findings, context)
        self._write_json("triage.json", triage)
        self._log("triage", tokens=usage.total_tokens, model=usage.model)
        return triage

    def _run_plan(self, findings: list[Finding], triage: TriageResult, context: dict[str, str]) -> RemediationBacklog:
        backlog, usage = plan_backlog(self.runner, findings, triage, context)
        self._log("plan", tokens=usage.total_tokens, model=usage.model, tasks=len(backlog.tasks))
        return backlog

    def _write_backlog(self, backlog: RemediationBacklog, findings: list[Finding]) -> None:
        self._write_json("backlog.json", backlog)
        (self.dir / "backlog.md").write_text(backlog.to_markdown(), encoding="utf-8")

    # ---------- public ----------

    def run(self) -> RemediationStatus:
        if self._step_report():
            self._step_triage()
        return self.status

    def approve(self) -> RemediationStatus:
        if self.status.step("triage").state != "awaiting_approval":
            raise RemediationError(
                f"The backlog is not waiting for approval (triage is {self.status.step('triage').state})")
        backlog = self._cached("backlog.json", RemediationBacklog)
        for task in backlog.tasks:
            if task.status == "proposed":
                task.status = "approved"
        self._write_backlog(backlog, [])
        self._set("triage", "done", f"Approved {sum(t.status == 'approved' for t in backlog.tasks)} task(s)")
        self.status.note = "Backlog approved. The fix loop (steps 3-6) is not implemented yet; it starts here in stage 2."
        self._save()
        return self.status
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_flow.py -v`
Expected: PASS (9 passed)

- [ ] **Step 5: Run the whole remediation set and the existing suite**

Run: `cd ai_factory_fz && uv run pytest tests -q`
Expected: all previous tests plus the new ones pass.

- [ ] **Step 6: Commit**

```bash
git add ai_factory_fz/src/agentic_sdlc/remediation/flow.py ai_factory_fz/tests/test_remediation_flow.py
git commit -m "feat(remediation): flow for report, triage, backlog and approval gate"
```

---

### Task 7: `remediate` CLI

**Files:**
- Create: `ai_factory_fz/src/agentic_sdlc/remediation/cli.py`
- Modify: `ai_factory_fz/pyproject.toml` (`[project.scripts]`: add `remediate = "agentic_sdlc.remediation.cli:main"`)
- Test: `ai_factory_fz/tests/test_remediation_cli.py`

**Interfaces:**
- Consumes: `RemediationFlow`, `RemediationStatus`, `RemediationError` (Tasks 3, 6).
- Produces: `main(argv: list[str] | None = None, runner_factory=None) -> int` with subcommands:
  - `remediate run (--run-dir DIR | --run-id ID) [--report FILE]`
  - `remediate approve (--run-dir DIR | --run-id ID)`
  - `remediate status (--run-dir DIR | --run-id ID)`
  - `remediate resume ...` (same as `run`)
  - `build_runner(run_dir) -> TaskRunner` reads `profile` and `pipeline` from `state.json` when present, else defaults (`flutter_nestjs_ecommerce`, `pipeline`).
- Exit codes: 0 ok / waiting for approval, 1 failed or blocked, 2 usage or refused approval.

- [ ] **Step 1: Write the failing tests**

`ai_factory_fz/tests/test_remediation_cli.py`:

```python
import json

from remediation_helpers import FakeRunner, make_task, make_validated, sample_report

from agentic_sdlc.remediation.cli import main
from agentic_sdlc.remediation.findings import extract_findings
from agentic_sdlc.remediation.schemas import RemediationBacklog, TriageResult


def factory(tmp_path):
    ids = [f.id for f in extract_findings(sample_report())]
    runner = FakeRunner({
        "analyze_eval_report": TriageResult(findings=[make_validated(i) for i in ids]),
        "plan_remediation": RemediationBacklog(summary="s", tasks=[make_task(finding_ids=ids)]),
    })
    return lambda run_dir: runner


def report(tmp_path):
    p = tmp_path / "eval_report_flow.json"
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
    monkeypatch.setattr("agentic_sdlc.remediation.cli.RUNS_DIR", tmp_path)
    (tmp_path / "myrun").mkdir()
    assert main(["status", "--run-id", "myrun"], factory(tmp_path)) == 0
    assert main(["status", "--run-id", "nope"], factory(tmp_path)) == 2


def test_run_dir_with_spaces_works(tmp_path):
    run = tmp_path / "my run"
    run.mkdir()
    rp = run / "eval_report_flow.json"
    rp.write_text(json.dumps(sample_report()), encoding="utf-8")
    assert main(["run", "--run-dir", str(run), "--report", str(rp)], factory(tmp_path)) == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: ... remediation.cli`

- [ ] **Step 3: Implement**

`ai_factory_fz/src/agentic_sdlc/remediation/cli.py`:

```python
"""remediate: run, approve, resume or show the status of a DeepEval remediation cycle.

  uv run remediate run     --run-dir runs/<id> --report runs/<id>/eval_report_flow.json
  uv run remediate approve --run-id <id>
  uv run remediate status  --run-id <id>
"""

import argparse
import json
from pathlib import Path

from agentic_sdlc.remediation.flow import RemediationError, RemediationFlow
from agentic_sdlc.remediation.status import RemediationStatus
from agentic_sdlc.settings import RUNS_DIR

DEFAULT_PROFILE = "flutter_nestjs_ecommerce"
DEFAULT_PIPELINE = "pipeline"


def build_runner(run_dir: Path):
    """A TaskRunner for the Project Manager. Uses the run's own profile and pipeline when it has a state.json."""
    from agentic_sdlc.crews.base import TaskRunner
    from agentic_sdlc.registry.agents import AgentRegistry
    from agentic_sdlc.registry.profiles import Profile
    from agentic_sdlc.settings import load_config

    profile, pipeline = DEFAULT_PROFILE, DEFAULT_PIPELINE
    state = Path(run_dir) / "state.json"
    if state.is_file():
        data = json.loads(state.read_text(encoding="utf-8"))
        profile, pipeline = data.get("profile") or profile, data.get("pipeline") or pipeline
    agents = AgentRegistry.from_config(Profile.load(profile), None, load_config(pipeline).get("models"))
    return TaskRunner(agents)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="remediate", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("run", "resume", "approve", "status"):
        s = sub.add_parser(name)
        where = s.add_mutually_exclusive_group(required=True)
        where.add_argument("--run-dir", type=Path, help="Path to the run folder")
        where.add_argument("--run-id", help="Run id inside the runs folder")
        if name in ("run", "resume"):
            s.add_argument("--report", type=Path, help="eval_report*.json to start from (default: newest in the run)")
    return p


def _print_status(status: RemediationStatus) -> None:
    print("\n".join(status.lines()))
    if status.note:
        print(f"\n{status.note}")


def main(argv: list[str] | None = None, runner_factory=None) -> int:
    args = _parser().parse_args(argv)
    run_dir = (args.run_dir or RUNS_DIR / args.run_id).resolve()
    if not run_dir.is_dir():
        print(f"Run folder not found: {run_dir}")
        return 2
    if args.command == "status":
        _print_status(RemediationStatus.load(run_dir / "remediation" / "status.json"))
        return 0
    runner = (runner_factory or build_runner)(run_dir) if args.command != "approve" else None
    flow = RemediationFlow(run_dir, runner, getattr(args, "report", None))
    if args.command == "approve":
        try:
            status = flow.approve()
        except RemediationError as e:
            print(str(e))
            return 2
        _print_status(status)
        return 0
    status = flow.run()
    _print_status(status)
    return 1 if any(s.state in ("failed", "blocked") for s in status.steps) else 0
```

Add to `[project.scripts]` in `ai_factory_fz/pyproject.toml`:

```toml
remediate = "agentic_sdlc.remediation.cli:main"
```

Note: a console script calls `main()` and uses its return value as the exit code, which is what we want.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ai_factory_fz && uv run pytest tests/test_remediation_cli.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Smoke-test the installed script**

Run: `cd ai_factory_fz && uv run remediate status --run-dir runs/sample-manual`
Expected: six lines, all `PENDING`, exit code 0 (no model call).

- [ ] **Step 6: Commit**

```bash
git add ai_factory_fz/src/agentic_sdlc/remediation/cli.py ai_factory_fz/pyproject.toml ai_factory_fz/tests/test_remediation_cli.py
git commit -m "feat(remediation): remediate CLI (run, approve, resume, status)"
```

---

### Task 8: DeepEval side: HTML report, status markers, trigger

**Files:**
- Create: `ai_factory_fz/deepeval/eval_report_html.py`
- Create: `ai_factory_fz/deepeval/remediation_trigger.py`
- Modify: `ai_factory_fz/deepeval/eval_report.py` (add the status markers to `to_markdown`, a `write` that also writes `.html`)
- Modify: `ai_factory_fz/deepeval/conftest.py` (only count the two test folders, call the trigger)
- Create: `ai_factory_fz/deepeval/unit_tests/test_report_html.py`, `ai_factory_fz/deepeval/unit_tests/test_trigger.py`, `ai_factory_fz/deepeval/unit_tests/test_report_status_block.py`

**Interfaces:**
- Consumes: the report dict from `eval_report.build` (keys as in Task 2).
- Produces:
  - `eval_report_html.to_html(report: dict) -> str` (self-contained HTML, escaped, with the status markers)
  - `eval_report.STATUS_PLACEHOLDER_MD` / `_HTML` constants containing the markers and the text `Remediation not started`
  - `eval_report.write(r, folder, name)` now also writes `<name>.html` and returns three paths
  - `remediation_trigger.maybe_start(run_dir: Path, report_json: Path) -> Path | None` (returns the log path when started)
- The marker strings MUST be identical to `agentic_sdlc.remediation.status.STATUS_START/END`: `<!-- remediation-status:start -->` / `<!-- remediation-status:end -->`.

- [ ] **Step 1: Write the failing tests**

`ai_factory_fz/deepeval/unit_tests/test_report_html.py`:

```python
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
```

`ai_factory_fz/deepeval/unit_tests/test_trigger.py`:

```python
import remediation_trigger as t


def test_does_nothing_unless_enabled(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(t.subprocess, "Popen", lambda *a, **k: calls.append((a, k)))
    monkeypatch.delenv("DEEPEVAL_REMEDIATE", raising=False)
    assert t.maybe_start(tmp_path, tmp_path / "eval_report_flow.json") is None
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "0")
    assert t.maybe_start(tmp_path, tmp_path / "eval_report_flow.json") is None
    assert calls == []


def test_starts_remediate_with_absolute_paths_when_enabled(tmp_path, monkeypatch):
    calls = []

    class FakeProc:
        pass

    monkeypatch.setattr(t.subprocess, "Popen", lambda *a, **k: calls.append((a, k)) or FakeProc())
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "1")
    run = tmp_path / "my run"
    run.mkdir()
    log = t.maybe_start(run, run / "eval_report_flow.json")
    (cmd,), kwargs = calls[0]
    assert cmd[:3] == ["uv", "run", "remediate"] and "run" in cmd
    assert str(run.resolve()) in cmd and str((run / "eval_report_flow.json").resolve()) in cmd
    assert kwargs["cwd"] == t.FZ_ROOT and log == run / "remediation" / "trigger.log" and log.parent.is_dir()


def test_a_failing_launch_never_raises(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise OSError("uv not found")

    monkeypatch.setattr(t.subprocess, "Popen", boom)
    monkeypatch.setenv("DEEPEVAL_REMEDIATE", "1")
    assert t.maybe_start(tmp_path, tmp_path / "x.json") is None
```

`ai_factory_fz/deepeval/unit_tests/test_report_status_block.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ai_factory_fz/deepeval && uv run pytest unit_tests -v`
Expected: FAIL with `ModuleNotFoundError: eval_report_html` / `remediation_trigger`

- [ ] **Step 3: Make the unit tests importable**

Create `ai_factory_fz/deepeval/unit_tests/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

- [ ] **Step 4: Implement the HTML report**

`ai_factory_fz/deepeval/eval_report_html.py`:

```python
"""Self-contained HTML version of the DeepEval report (same data as eval_report.json). All text is escaped."""

from html import escape as e

STATUS_START = "<!-- remediation-status:start -->"
STATUS_END = "<!-- remediation-status:end -->"
STATUS_PLACEHOLDER_HTML = f"{STATUS_START}<p class=\"remediation-status\">Remediation not started.</p>{STATUS_END}"

CSS = """
body{font-family:system-ui,sans-serif;margin:2rem auto;max-width:960px;padding:0 1rem;color:#1f2328;background:#fff}
table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #d0d7de;padding:.4rem .6rem;text-align:left}
th{background:#f6f8fa}.HIGH{color:#1a7f37;font-weight:600}.MEDIUM{color:#9a6700;font-weight:600}.LOW,.FAIL{color:#cf222e;font-weight:600}
.PASS{color:#1a7f37;font-weight:600}details{margin:1rem 0;border:1px solid #d0d7de;border-radius:6px;padding:.5rem 1rem}
.remediation-status{background:#f6f8fa;padding:.75rem 1.5rem;border-radius:6px}
@media(prefers-color-scheme:dark){body{background:#0d1117;color:#e6edf3}th{background:#161b22}th,td,details{border-color:#30363d}
.remediation-status{background:#161b22}.HIGH,.PASS{color:#3fb950}.MEDIUM{color:#d29922}.LOW,.FAIL{color:#ff7b72}}
"""


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.2f}"


def _ul(items) -> str:
    return "<ul>" + "".join(f"<li>{e(str(i))}</li>" for i in items) + "</ul>" if items else "<p>None noted.</p>"


def _agent(a: dict) -> str:
    an = a.get("analysis") or {}
    parts = [f"<details><summary><b>{e(a['agent'])}</b>: <span class=\"{e(a['verdict'].replace(' ', ''))}\">{e(a['verdict'])}</span>, "
             f"confidence {_fmt(a.get('confidence'))} (<span class=\"{e(a['confidence_level'])}\">{e(a['confidence_level'])}</span>)</summary>"]
    if a.get("level_reasoning"):
        parts.append(f"<p><b>Why this level:</b> {e(a['level_reasoning'])}</p>")
    if an and not an.get("error"):
        parts += [f"<p><b>Why this score:</b> {e(an.get('why_score', ''))}</p>",
                  f"<p><b>Level justification:</b> {e(an.get('level_justification', ''))}</p>",
                  "<p><b>Strengths</b></p>" + _ul(an.get("strengths")),
                  "<p><b>Gaps</b></p>" + _ul(an.get("gaps")),
                  "<p><b>What can be improved</b></p>" + _ul(an.get("improvements"))]
    parts.append("<p><b>Judge's reasons per test</b></p><ul>")
    for t in a.get("tests", []):
        parts.append(f"<li><code>{e(t['file'])}::{e(t['test'])}</code>: {e(t['outcome'].upper())}, score {_fmt(t.get('score'))} "
                     f"({e(str(t.get('level')))})<br><i>Criteria:</i> {e(t.get('criteria', ''))}<br>"
                     f"<i>Judge's reason:</i> {e(t.get('reason', ''))}</li>")
    parts.append("</ul></details>")
    return "".join(parts)


def to_html(r: dict) -> str:
    o = r["overall"]
    rows = "".join(
        f"<tr><td>{e(a['agent'])}</td><td class=\"{e(a['verdict'].replace(' ', ''))}\">{e(a['verdict'])}</td>"
        f"<td>{_fmt(a.get('confidence'))}</td><td class=\"{e(a['confidence_level'])}\">{e(a['confidence_level'])}</td>"
        f"<td>{_fmt(a.get('lowest_score'))}</td><td>{a['passed']}/{a['failed']}/{a['skipped']}</td></tr>"
        for a in r["agents"]
    )
    levels = "".join(f"<li><b>{e(k)}</b>: {e(str(v))}</li>" for k, v in r.get("level_meaning", {}).items())
    return (
        f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>DeepEval report {e(r['run'])}</title><style>{CSS}</style></head><body>"
        f"<h1>DeepEval report: {e(r['run'])}</h1><p>Generated {e(r['generated'])}. Judge scores run from 0 to 1; "
        f"a test passes at {r['pass_threshold']} or above.</p>"
        f"<p><b>Overall: <span class=\"{e(o['verdict'].replace(' ', ''))}\">{e(o['verdict'])}</span></b> | confidence {_fmt(o.get('confidence'))} "
        f"({e(o['confidence_level'])}) | {o['passed']} passed, {o['failed']} failed, {o['skipped']} skipped</p>"
        f"{STATUS_PLACEHOLDER_HTML}<h2>Confidence levels</h2><ul>{levels}</ul>"
        f"<h2>Summary</h2><table><tr><th>Agent</th><th>Verdict</th><th>Confidence</th><th>Level</th><th>Lowest</th>"
        f"<th>Pass/Fail/Skip</th></tr>{rows}</table><h2>Details per agent</h2>{''.join(_agent(a) for a in r['agents'])}"
        f"</body></html>"
    )
```

- [ ] **Step 5: Implement the trigger**

`ai_factory_fz/deepeval/remediation_trigger.py`:

```python
"""Start the remediation process when a DeepEval report has been written (opt-in: DEEPEVAL_REMEDIATE=1)."""

import os
import subprocess
from pathlib import Path

FZ_ROOT = Path(__file__).resolve().parent.parent


def maybe_start(run_dir: Path, report_json: Path) -> Path | None:
    """Launch `uv run remediate run` detached. Returns the log path, or None when disabled or the launch failed."""
    if os.environ.get("DEEPEVAL_REMEDIATE") != "1":
        return None
    run_dir = Path(run_dir).resolve()
    log = run_dir / "remediation" / "trigger.log"
    cmd = ["uv", "run", "remediate", "run", "--run-dir", str(run_dir), "--report", str(Path(report_json).resolve())]
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS) if os.name == "nt" else 0
        with log.open("ab") as out:
            subprocess.Popen(cmd, cwd=FZ_ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             creationflags=flags, start_new_session=(os.name != "nt"))
    except OSError:
        return None
    return log
```

- [ ] **Step 6: Wire the report and the conftest**

In `ai_factory_fz/deepeval/eval_report.py`:

1. Add near the top (after the imports): `from eval_report_html import STATUS_PLACEHOLDER_HTML, STATUS_START, STATUS_END, to_html`
2. Add the constant `STATUS_PLACEHOLDER_MD = f"{STATUS_START}\nRemediation not started. Set DEEPEVAL_REMEDIATE=1 to start it after the report.\n{STATUS_END}"`
3. In `to_markdown`, right after the `**Overall: ...**` line plus its blank line, append `STATUS_PLACEHOLDER_MD, ""` to `lines`.
4. Replace `write` with:

```python
def write(r: dict, folder: Path, name: str = "eval_report") -> list[Path]:
    paths = [folder / f"{name}.json", folder / f"{name}.md", folder / f"{name}.html"]
    paths[0].write_text(json.dumps(r, indent=2), encoding="utf-8")
    paths[1].write_text(to_markdown(r), encoding="utf-8")
    paths[2].write_text(to_html(r), encoding="utf-8")
    return paths
```

In `ai_factory_fz/deepeval/conftest.py` replace the body so that only tests in the two evaluation folders are counted and the trigger runs after the files are written:

```python
"""Collects every test outcome and, at the end of the session, writes the pass/fail report.

Writes eval_report*.md/.json/.html into the run folder being evaluated, prints a per-agent confidence table, and
starts the remediation process when DEEPEVAL_REMEDIATE=1. See eval_report.py and remediation_trigger.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_report  # noqa: E402
import remediation_trigger  # noqa: E402
from common import find_run_dir  # noqa: E402

OUTCOMES: dict[tuple[str, str], str] = {}
EVALUATION_DIRS = ("agent_test_writeup/", "flow_test_writeup/")


def pytest_runtest_logreport(report):
    """Keep one outcome per evaluation test: the call result, or the setup result if setup did not pass."""
    nodeid = report.nodeid.replace("\\", "/")
    if not any(nodeid.startswith(d) for d in EVALUATION_DIRS):
        return
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        file, _, name = nodeid.rpartition("/")[2].partition("::")
        OUTCOMES[(file, name.split("[")[0])] = report.outcome


def pytest_terminal_summary(terminalreporter):
    if not OUTCOMES:
        return
    run = find_run_dir()
    result = eval_report.build(OUTCOMES, run.name if run else "(no run folder)")
    terminalreporter.section("DeepEval report")
    for line in eval_report.to_terminal(result):
        terminalreporter.write_line(line)
    if run is None:
        return
    try:
        paths = eval_report.write(result, run, eval_report.report_name(OUTCOMES))
    except OSError as exc:
        terminalreporter.write_line(f"Could not write the report: {exc}")
        return
    terminalreporter.write_line("")
    for p in paths:
        terminalreporter.write_line(f"Report: {p}")
    log = remediation_trigger.maybe_start(run, paths[0])
    if log:
        terminalreporter.write_line(f"Remediation started: follow {log}")
```

Important: nodeids are relative to the rootdir only when pytest is run from `ai_factory_fz/deepeval`. If `agent_test_writeup/` prefixes do not match when run from elsewhere, compare with `"agent_test_writeup/" in nodeid` instead (adjust the condition and keep the test in Step 7).

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cd ai_factory_fz/deepeval && uv run pytest unit_tests -v`
Expected: PASS (all). Also run `cd ai_factory_fz/deepeval && uv run pytest unit_tests -v` and confirm no `eval_report*` file is written anywhere (the unit tests are outside the evaluation folders, so the hook must ignore them).

- [ ] **Step 8: Commit**

```bash
git add ai_factory_fz/deepeval
git commit -m "feat(deepeval): html report, remediation status markers and opt-in trigger"
```

---

### Task 9: End-to-end check on the sample run, Planner decision, docs

**Files:**
- Modify: `ai_factory_fz/deepeval/README.md` (document `eval_report_*.html`, `DEEPEVAL_REMEDIATE`, `remediate` commands, the six-step status)
- Create: `docs/superpowers/specs/2026-10-02-deepeval-remediation-stage1-results.md` (test results and the Remediation Planner decision)

**Interfaces:** consumes everything above. This task uses real model calls (Project Manager on the pipeline's configured tier). **Ask the user for a go-ahead before Step 2** because it spends tokens.

- [ ] **Step 1: Run the full automated suites**

Run: `cd ai_factory_fz && uv run pytest tests -q` and `cd ai_factory_fz/deepeval && uv run pytest unit_tests -q`
Expected: all green.

- [ ] **Step 2: Dry check, then a real run on the sample report (needs user go-ahead)**

Run (from `ai_factory_fz`):

```bash
uv run remediate run --run-dir runs/sample-manual --report runs/sample-manual/eval_report_agents.json
uv run remediate status --run-dir runs/sample-manual
```

Expected: `1. DeepEval report: DONE`, `2. Project Manager triage and backlog: AWAITING APPROVAL (N task(s) ...)`, steps 3-6 `PENDING`. Files exist under `runs/sample-manual/remediation/`.

- [ ] **Step 3: Check the backlog quality against the spec (manual)**

Open `runs/sample-manual/remediation/backlog.md` and `triage.json`. Verify, and record each answer in the results doc:
- Every failed test in `eval_report_agents.json` (4 of them) maps to a task or a disposition.
- No `verified_defect` has an empty `evidence_checked`; the file paths in it exist in the run.
- Findings with the same root cause were grouped into one task.
- Owners follow the dependency order (customer, spec_writer, architect before developers).
- Tasks touching business rules, architecture or security are flagged `needs_human_approval`.
- No invented work item, file or requirement ids.

- [ ] **Step 4: Planner decision**

Record in the results doc whether the Project Manager reliably did the two tasks. If the guardrail rejected the output repeatedly, the classifications were unsupported, or ids were invented, recommend adding a `remediation_planner` agent (same two tasks, `balanced` model tier) as a follow-up; otherwise state that the Project Manager is sufficient. Also note the cost: tokens and duration from `remediation/history.jsonl`.

- [ ] **Step 5: Check the trigger end to end (needs user go-ahead, small cost)**

Run: `cd ai_factory_fz/deepeval && set DEEPEVAL_REMEDIATE=1` (PowerShell: `$env:DEEPEVAL_REMEDIATE=1`), then run one cheap evaluation file, for example `uv run pytest agent_test_writeup/test_architect.py -q` with `DEEPEVAL_RUN_DIR=../runs/sample-manual`. Expected: the report is written, "Remediation started: follow ...trigger.log" is printed, and `runs/sample-manual/remediation/status.json` appears; `eval_report_agents.md` shows the live status block.

- [ ] **Step 6: Update the README and commit**

Add a "Remediation" section to `ai_factory_fz/deepeval/README.md` covering the HTML report, the opt-in variable, the six steps, `remediate run|approve|status|resume`, and that stage 1 stops at the approval gate (fix loop comes in stage 2).

```bash
git add ai_factory_fz/deepeval/README.md docs/superpowers/specs/2026-10-02-deepeval-remediation-stage1-results.md
git commit -m "docs(remediation): stage 1 results, planner decision and README"
```

---

## Self-review

**Spec coverage:** trigger (Task 8), `findings.py` (2), `schemas.py` (1), triage and planner tasks (5), `status.py` and six-step status in reports (3, 8), `flow.py` with approval gate (6), CLI incl. `approve|status|resume` (7), baseline copy and append-only history (6), HTML report (8), limits for missing inputs (4, 6), guardrails against invented ids and unknown agents (1, 5), Planner decision (9). Not in this stage by design: steps 3-6, `compare.py`, `remediation_rounds` limit, token budget (stages 2-3).

**Placeholders:** none; every code step has code. Task 8 Step 6 describes edits to an existing file by exact instruction because the file is long; the replacement `write` and `conftest.py` are given in full.

**Type consistency:** `Finding`, `ValidatedFinding`, `TriageResult`, `RemediationTask`, `RemediationBacklog`, `Disposition` (Task 1) are used with the same field names in Tasks 2, 5, 6. `RemediationStatus.set/step/load/save/lines/block_md/block_html` (Task 3) are used in 6 and 7. `FakeRunner.run` matches `TaskRunner.run`. Marker strings match between `status.py` and `eval_report_html.py`.

**Known assumption to verify in Task 5 Step 5:** `artifact_guardrail` returns `(True, output)` for valid output and `(False, message)` otherwise, as in `crews/base.py`.
