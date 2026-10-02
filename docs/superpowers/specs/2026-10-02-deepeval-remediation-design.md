# DeepEval remediation loop: design

Date: 2026-10-02. Status: draft for review.

## 1. Purpose

When DeepEval finishes and writes its report for a pipeline run, a Project Manager process starts. It validates the
findings, writes a prioritised remediation backlog, and (after human approval) coordinates the existing agents to fix
the source of each problem, verifies the result, and re-runs DeepEval to compare against the original baseline.

What the user asked for (their words, summarised): a six-step status for the DeepEval process: (1) DeepEval report,
(2) Project Manager / Remediation Planner, (3) fix the source of the problem (Customer, Spec Writer, Architect,
Developers, QA and deployment), (4) Integration Pass, (5) QA Engineer and Smoke Tester, (6) re-evaluate with DeepEval.
The Project Manager is the workflow orchestrator. Existing agents are reused; a dedicated Remediation Planner is added
only if the Project Manager cannot do the planning reliably. The sequence is dependency-driven, not strictly linear.

Decisions made in discussion:
- **Scope:** the whole flow, delivered in three stages (section 9).
- **Approach:** a separate `RemediationFlow` over an existing run folder, not a new phase inside `SDLCFlow`.
- **Human gate:** always pause after the backlog is written and wait for explicit approval (gate "A").
- **Report format:** keep `eval_report.json` as the machine input; add an HTML report for people (stage 1).

Assumptions to confirm during review: the trigger is opt-in (`DEEPEVAL_REMEDIATE=1`); the loop is only exercised end to
end against a pipeline-generated run, because `runs/sample-manual` is hand-written and has no `state.json`
(`ProjectState`).

## 2. Non-goals

- No change to the DeepEval criteria, thresholds or tests to make results pass.
- No automatic waiving of failed gates, no automatic acceptance of false positives, no production deployment.
- No new specialist agents beyond a possible Remediation Planner (section 4).
- No change to the existing `SDLCFlow` phase chain.

## 3. Components

New package `ai_factory_fz/src/agentic_sdlc/remediation/`, plus a hook in `ai_factory_fz/deepeval/`.

| Unit | Responsibility | Depends on |
|---|---|---|
| `findings.py` | Read `eval_report.json`; produce normalized `Finding` objects | report schema |
| `schemas.py` | Pydantic models: `Finding`, `ValidatedFinding`, `RemediationTask`, `RemediationBacklog`, `StepStatus`, `Comparison` | none |
| `triage.py` | Project Manager task `analyze_eval_report`: classify findings against run artifacts | `TaskRunner`, workspace |
| `planner.py` | Project Manager task `plan_remediation`: group by root cause, write the backlog | `TaskRunner` |
| `status.py` | Read/write `status.json`, enforce legal step transitions | schemas |
| `flow.py` | `RemediationFlow`: runs the six steps, checkpoints, resumes | all of the above |
| `compare.py` | Before/after comparison of two reports (stage 3) | schemas |
| CLI | `remediate <run_id>`, `remediate approve|status|resume <run_id>` | flow |
| `deepeval/conftest.py` hook | After the report is written, start `remediate` when `DEEPEVAL_REMEDIATE=1` | `eval_report` |

`RemediationFlow` follows the pattern of `SDLCFlow`: each step is idempotent, skips work whose artifact exists, and
checkpoints after finishing. Agents run through the existing `TaskRunner.run(phase, task_key, inputs, output_model, ...)`.
New task prompts go in `config/tasks.yaml` (`analyze_eval_report`, `plan_remediation`).

## 4. Project Manager vs. a Remediation Planner

The Project Manager agent currently has two tasks (`plan_backlog`, `reconcile_estimates`). Stage 1 adds the two new
tasks to it. If the stage 1 integration test shows it cannot reliably classify findings against evidence or keep the
backlog traceable, a Remediation Planner agent is added in `config/agents.yaml` and the same two tasks move to it. The
decision is recorded in the stage 1 test results, not assumed now.

## 5. Data model

**Finding** (from the report): `id` (F-001...), `source_test` (file::test), `agent`, `score`, `level`, `original_text`
(verbatim judge reason, gap or improvement), `evidence` (criteria text and the quoted reason), `affected` (agent output
files, requirement or work-item IDs only if present in the run).

**ValidatedFinding**: Finding plus `classification` (one of `verified_defect`, `specification_gap`, `unverified`,
`false_positive_or_exception`), `classification_reason`, `evidence_checked` (files actually read), `root_cause`,
`root_cause_status` (`confirmed` or `hypothesis`), `severity`, `evidence_confidence`, `verification_method`.
A finding is never `verified_defect` only because the test failed.

**RemediationTask**: `id` (R-001...), `title`, `problem`, `finding_ids`, `validation_status`, `root_cause`,
`affected_requirements`, `affected_components`, `owners` (existing agent keys), `inputs`, `depends_on`, `steps`,
`acceptance_criteria`, `verification` (method and expected evidence), `priority` (P0..P3), `priority_rationale`,
`status`, `needs_human_approval` and `approval_reason`. IDs of work items, files or requirements are copied from the run,
never invented; missing evidence produces an investigation task.

**Priority:** P0 critical blocker, P1 high impact, P2 normal functional or integration gap, P3 low-risk improvement,
each with a written rationale, no numeric scores.

## 6. Status model

`runs/<id>/remediation/status.json` has the six steps with a state each: `pending`, `running`, `awaiting_approval`,
`done`, `failed`, `blocked`, plus `updated`, `reason` and `round`.

| # | Step | Owner |
|---|---|---|
| 1 | DeepEval report | DeepEval |
| 2 | Project Manager triage and backlog | Project Manager |
| 3 | Fix the source of the problem | Customer, Spec Writer, Architect, UI/UX, Backend, Frontend, Deployment |
| 4 | Integration Pass | Integration Pass |
| 5 | QA and smoke tests | QA Engineer, Smoke Tester |
| 6 | Re-evaluate with DeepEval | DeepEval |

Step 2 always ends in `awaiting_approval`. `remediate approve <run_id>` moves it to `done` and starts step 3.
`remediate status <run_id>` prints the six lines; the same block is written at the top of `eval_report.md` and the HTML
report. Legal transitions are enforced in `status.py` (for example a step cannot start while an earlier one is not
`done`).

## 7. Flow

**Trigger.** `deepeval/conftest.py` writes the report as today. If `DEEPEVAL_REMEDIATE=1`, it then starts
`uv run remediate <run_id> --report <path>` in `ai_factory_fz` as a separate process and records step 1 as `done`. The
trigger never blocks the test session and never runs when the variable is unset.

**Step 2.** Copy the report to `remediation/baseline/` (never modified). Extract findings. Run `analyze_eval_report`
with the findings plus the run's PRD, architecture, OpenAPI, relevant source and reports. Run `plan_remediation` on the
validated findings. Write `findings.json`, `backlog.json`, `backlog.md`. Mark `awaiting_approval`. The reviewer may edit
or reject tasks in `backlog.json` before approving; rejected tasks get a documented disposition.

**Step 3 (after approval).** Tasks run in dependency order, independent tasks in parallel:
1. Customer then Spec Writer then Architect for specification and contract tasks. The Customer separates confirmed
   requirements, interpretations needing confirmation, open questions and assumptions; assumptions never become
   requirements. Spec Writer updates PRD and acceptance criteria; Architect reconciles API, data, auth, errors, UI states,
   security and deployment.
2. Backend and Frontend Developers in parallel only after the contract is approved, using the existing `fix_work_item`
   job (edits in place). Each reports changes, findings addressed, tests run and results, remaining limits, new
   dependencies or defects.
3. UI/UX and Deployment in parallel when inputs are ready; Deployment must show execution evidence (build, startup,
   migrations).

A task is `done` only with evidence for its acceptance criteria. Each task is committed separately in the run's git
history so it can be reverted.

**Step 4.** The existing integration review runs across the changed components. A failure becomes a new backlog task
for the responsible agent with the evidence attached, and only the affected checks are re-run.

**Step 5.** QA verifies approved acceptance criteria and regressions; the Smoke Tester runs real journeys. Each check
records test, expected, actual, pass/fail and evidence. Only behaviour in the approved spec is tested; a conflict
between a test and the PRD is investigated, not resolved by widening scope.

**Step 6.** Re-run DeepEval with the copied baseline settings (same tests, criteria, threshold, judge model).
`compare.py` writes `comparison.md/json`: verdicts, counts, per-test and per-metric changes, fixed tests, regressed
tests, unresolved and new findings, confidence and coverage changes, and any configuration difference that limits
comparability. Improvement is judged per gate and critical finding, never by the average score. If gates still fail,
the new findings return to step 2 for another round.

## 8. Limits, safety and errors

- `limits.remediation_rounds` (default 3) and a token budget shared with the run's existing budget stop the loop with
  `blocked` and a summary for the reviewer.
- Missing input (`eval_report.json`, PRD, `state.json`) marks the step `blocked` with the reason; nothing is invented.
- A failed task is retried through the existing model fallbacks, then marked `failed`; dependents are `blocked`;
  independent tasks continue.
- Edits stay inside the run workspace (the existing `resolve` path check applies). The baseline report, task history
  and evaluation settings are append-only.
- Human approval is required (flagged per task) for ambiguous business requirements, material architecture changes,
  security-sensitive behaviour, destructive data operations, scope expansion and release exceptions. Final release
  approval is always human; no production deployment is triggered.
- `remediate resume <run_id>` continues from the last checkpoint after a crash.

## 9. Delivery stages

Each stage gets its own implementation plan and is usable on its own.

1. **Trigger, triage and backlog** (steps 1-2, approval gate, status, HTML report). Tested cheaply against the
   `sample-manual` report.
2. **Fix loop** (steps 3-5).
3. **Re-evaluation and comparison** (step 6, repeat rounds, final outputs).

Final outputs after stage 3: evaluation summary, validated findings, remediation backlog, execution plan, verification
report, before/after comparison, outstanding risks, release recommendation (satisfied, not satisfied, or blocked by
insufficient evidence; a human gives the final approval).

## 10. Testing

- **Unit (no model calls):** finding extraction, status transitions including `awaiting_approval` and resume, backlog
  schema validation, grouping with preserved finding links, comparison logic.
- **Stage 1 integration:** run steps 1-2 on the `sample-manual` report; every failed test maps to a task or a recorded
  disposition; no invented IDs; gate stops at `awaiting_approval`.
- **Stage 2 and 3:** one end-to-end run on a pipeline-generated run, only after the user approves the token cost.
- Existing `ai_factory_fz/tests` and the DeepEval suite stay green.

## 11. Open points

- Confirm opt-in trigger (`DEEPEVAL_REMEDIATE=1`) rather than always-on.
- Default `remediation_rounds` of 3 and the budget share.
- Remediation Planner agent: decided by the stage 1 test result (section 4).
