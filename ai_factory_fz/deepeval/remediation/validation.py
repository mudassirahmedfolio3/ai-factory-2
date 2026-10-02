"""Checks on model output (used as task guardrails): a list of error strings, empty when valid."""

from pathlib import Path

from remediation.schemas import AGENT_KEYS, Finding, RemediationBacklog, TriageResult


def _is_run_file(rel: str, run_dir: Path) -> bool:
    try:
        root = run_dir.resolve()
        path = (root / rel).resolve()
        path.relative_to(root)
        return path.is_file()
    except (ValueError, OSError, RuntimeError):
        return False


def check_triage(triage: TriageResult, findings: list[Finding], run_dir: Path | None = None) -> list[str]:
    known = {f.id for f in findings}
    errors, seen = [], set()
    for v in triage.findings:
        if v.finding_id in seen:
            errors.append(f"duplicate triage entry for {v.finding_id}")
        seen.add(v.finding_id)
        if v.finding_id not in known:
            errors.append(f"{v.finding_id} is not a finding in the report")
        if run_dir is not None:
            for rel in (e.strip() for e in v.evidence_checked):
                if rel and not _is_run_file(rel, Path(run_dir)):
                    errors.append(f"{v.finding_id} evidence_checked '{rel}' is not a file in the run: do not invent paths")
        if v.classification == "verified_defect":
            stripped = [e.strip() for e in v.evidence_checked if e.strip()]
            if not stripped:
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
    errors, task_ids, covered, disp_ids = [], set(), set(), set()

    # Validate tasks
    for t in backlog.tasks:
        if t.id in task_ids:
            errors.append(f"duplicate task id {t.id}")
        task_ids.add(t.id)
        if not t.finding_ids:
            errors.append(f"{t.id} cites no finding")

        # Validate task validation_status matches cited findings' classifications
        cited_classes = {classes.get(fid) for fid in t.finding_ids if fid in classes}
        if t.validation_status not in cited_classes:
            errors.append(f"{t.id} validation_status '{t.validation_status}' does not match any cited finding's classification")
        if t.validation_status == "verified_defect" and "verified_defect" not in cited_classes:
            errors.append(f"{t.id} validation_status is verified_defect but no cited finding is classified verified_defect")

        for fid in t.finding_ids:
            if t.status != "rejected":   # a rejected task covers nothing: its findings need a disposition
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

    # Validate dispositions
    for d in backlog.dispositions:
        if d.finding_id in disp_ids:
            errors.append(f"duplicate disposition for {d.finding_id}")
        disp_ids.add(d.finding_id)
        if d.finding_id not in known:
            errors.append(f"disposition cites unknown finding {d.finding_id}")
        elif d.finding_id in covered:
            errors.append(f"{d.finding_id} is covered by both a task and a disposition")
        if d.disposition == "no_action_false_positive" and classes.get(d.finding_id) != "false_positive_or_exception":
            errors.append(f"disposition 'no_action_false_positive' for {d.finding_id} requires false_positive_or_exception classification")

    for t in backlog.tasks:
        for dep in t.depends_on:
            if dep not in task_ids:
                errors.append(f"{t.id} depends on unknown task {dep}")
    if _has_cycle({t.id: list(t.depends_on) for t in backlog.tasks}):
        errors.append("task dependencies contain a cycle")
    covered |= disp_ids
    for fid in sorted(known - covered):
        errors.append(f"{fid} has neither a task nor a disposition")
    return errors
