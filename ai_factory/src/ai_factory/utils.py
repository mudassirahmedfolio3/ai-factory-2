from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ai_factory.complexity import get_profile
from ai_factory.knowledge_graph import DeliveryKnowledgeGraph
from ai_factory.usage_tracker import get_usage_tracker

if TYPE_CHECKING:
    from ai_factory.models import AIFactoryState

ARTIFACTS_DIR = Path("artifacts")
AUDIT_DIR = ARTIFACTS_DIR / "audit"
RUNS_DIR = ARTIFACTS_DIR / "runs"
RUN_STATE_PATH = ARTIFACTS_DIR / "run_state.json"


def _estimated_minutes(complexity: str) -> int:
    return get_profile(complexity).estimated_minutes

# UI pipeline stepper (internal phases map to each display step)
PIPELINE_STEPS: list[dict[str, Any]] = [
    {"id": "discovery", "label": "Discovery", "phases": ["kickoff", "discovery", "prd_review"]},
    {"id": "design", "label": "Design", "phases": ["design"]},
    {"id": "sprint", "label": "Sprint", "phases": ["sprint_planning", "change_request"]},
    {"id": "build", "label": "Build", "phases": ["build"]},
    {"id": "code_review", "label": "Code Review", "phases": ["code_review"]},
    {"id": "security", "label": "Security", "phases": ["security"]},
    {"id": "qa", "label": "QA", "phases": ["qa"]},
    {"id": "release", "label": "Release", "phases": ["release", "governance", "deploy_approval"]},
    {"id": "browser", "label": "Browser", "phases": ["browser", "emulator", "deployment"]},
    {"id": "client_review", "label": "Client Review", "phases": ["release_review"]},
]


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _step_status(current_phase: str, step_phases: list[str], run_status: str) -> str:
    if run_status == "completed":
        return "completed"
    if run_status == "failed" and current_phase in step_phases:
        return "failed"
    if current_phase in step_phases:
        return "active"
    current_idx = next(
        (i for i, s in enumerate(PIPELINE_STEPS) if current_phase in s["phases"]),
        -1,
    )
    step_idx = next(
        (i for i, s in enumerate(PIPELINE_STEPS) if s["phases"] == step_phases),
        -1,
    )
    if current_idx >= 0 and step_idx >= 0 and step_idx < current_idx:
        return "completed"
    return "pending"


def publish_run_state(state: "AIFactoryState", status: str | None = None) -> Path:
    """Write live run snapshot for the presentation layer."""
    if status:
        state.run_status = status
    if not state.run_id:
        state.run_id = new_run_id()

    steps = [
        {
            "id": step["id"],
            "label": step["label"],
            "status": _step_status(state.phase, step["phases"], state.run_status),
        }
        for step in PIPELINE_STEPS
    ]

    payload = {
        "run_id": state.run_id,
        "project_name": state.project_name,
        "phase": state.phase,
        "status": state.run_status,
        "release_number": state.release_number,
        "complexity": state.complexity,
        "estimated_minutes": _estimated_minutes(state.complexity),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_steps": steps,
        "flutter_project_dir": state.flutter_project_dir or None,
        "checks": {
            "code_review_passed": state.code_review_passed,
            "security_passed": state.security_passed,
            "qa_passed": state.qa_passed,
            "post_deploy_passed": state.post_deploy_passed,
            "deploy_approved": state.deploy_approved,
            "flutter_artifacts_ready": bool(state.flutter_project_dir),
        },
        "approvals": {
            "prd": state.prd_approval.decision if state.prd_approval else None,
            "release": state.release_approval.decision if state.release_approval else None,
            "deploy": state.deploy_approval.decision if state.deploy_approval else None,
        },
        "artifacts_index": list_artifacts(),
        "usage": {
            **get_usage_tracker().snapshot().to_dict(),
            "budget_warning": get_usage_tracker().budget_warning(),
        },
    }
    RUN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return RUN_STATE_PATH


def list_artifacts() -> list[dict[str, str]]:
    """Return relative artifact paths for the UI file browser."""
    if not ARTIFACTS_DIR.exists():
        return []
    skip = {"runs", "audit"}
    items: list[dict[str, str]] = []
    for path in sorted(ARTIFACTS_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ARTIFACTS_DIR).as_posix()
        top = rel.split("/")[0]
        if top in skip or rel in ("run_state.json", "knowledge_graph.json"):
            continue
        items.append({"path": rel, "category": top})
    return items


def archive_run(state: "AIFactoryState") -> Path:
    """Snapshot completed run for historical review."""
    if not state.run_id:
        state.run_id = new_run_id()
    dest = RUNS_DIR / state.run_id
    dest.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "run_id": state.run_id,
        "project_name": state.project_name,
        "phase": state.phase,
        "status": state.run_status,
        "release_number": state.release_number,
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "code_review_passed": state.code_review_passed,
            "security_passed": state.security_passed,
            "qa_passed": state.qa_passed,
            "post_deploy_passed": state.post_deploy_passed,
        },
    }
    (dest / "snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    if RUN_STATE_PATH.exists():
        shutil.copy2(RUN_STATE_PATH, dest / "run_state.json")

    audit_src = AUDIT_DIR
    if audit_src.exists():
        audit_dest = dest / "audit"
        audit_dest.mkdir(exist_ok=True)
        for audit_file in audit_src.glob("*.jsonl"):
            shutil.copy2(audit_file, audit_dest / audit_file.name)

    for item in list_artifacts():
        src = ARTIFACTS_DIR / item["path"]
        if src.exists():
            target = dest / "artifacts" / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)

    return dest


def list_archived_runs() -> list[dict[str, Any]]:
    if not RUNS_DIR.exists():
        return []
    runs: list[dict[str, Any]] = []
    for run_dir in sorted(RUNS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        snap_path = run_dir / "snapshot.json"
        if snap_path.exists():
            runs.append(json.loads(snap_path.read_text(encoding="utf-8")))
        else:
            runs.append({"run_id": run_dir.name, "status": "unknown"})
    return runs


def save_artifact(relative_path: str, content: str) -> Path:
    """Write generated SDLC artifacts to the artifacts/ directory."""
    path = ARTIFACTS_DIR / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def log_audit(
    event: str,
    decision: str,
    agent: str,
    details: dict | None = None,
    state: "AIFactoryState | None" = None,
) -> Path:
    """Append governance audit trail entry (Harness-style evidence)."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "decision": decision,
        "agent": agent,
        "details": details or {},
    }
    if state and state.run_id:
        entry["run_id"] = state.run_id
    path = AUDIT_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d')}_audit.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    if state is not None:
        publish_run_state(state)
    return path


def load_knowledge_graph() -> DeliveryKnowledgeGraph:
    return DeliveryKnowledgeGraph.load()


def sync_graph_from_state(state, graph: DeliveryKnowledgeGraph | None = None) -> DeliveryKnowledgeGraph:
    """Update knowledge graph entities from current flow state."""
    kg = graph or load_knowledge_graph()
    project_id = f"project:{state.project_name}"
    kg.upsert(project_id, "project", name=state.project_name, phase=state.phase)
    kg.upsert(f"service:{state.project_name}", "service", stack="flutter", domain="ecommerce")
    kg.link(project_id, "owns", f"service:{state.project_name}")

    if state.requirements_doc:
        req_id = f"requirements:{state.project_name}"
        kg.upsert(req_id, "artifact", type="prd", phase="discovery")
        kg.link(project_id, "has_artifact", req_id)

    if state.architecture_doc:
        arch_id = f"architecture:{state.project_name}"
        kg.upsert(arch_id, "artifact", type="architecture")
        kg.link(f"service:{state.project_name}", "documented_by", arch_id)

    if state.release_number:
        rel_id = f"release:{state.project_name}:r{state.release_number}"
        kg.upsert(
            rel_id,
            "release",
            number=state.release_number,
            environment=state.deploy_environment,
        )
        kg.link(f"service:{state.project_name}", "release", rel_id)

        if state.code_artifacts:
            code_id = f"code:{rel_id}"
            kg.upsert(code_id, "artifact", type="code")
            kg.link(rel_id, "contains", code_id)

        if state.code_review_report:
            finding_id = f"review:{rel_id}"
            kg.upsert(
                finding_id,
                "review",
                passed=state.code_review_passed,
            )
            kg.link(rel_id, "reviewed_by", finding_id)

        if state.security_report:
            sec_id = f"security:{rel_id}"
            kg.upsert(sec_id, "security_scan", passed=state.security_passed)
            kg.link(rel_id, "scanned_by", sec_id)

        if state.deployment_report:
            pipe_id = f"pipeline:{rel_id}"
            kg.upsert(pipe_id, "pipeline", environment=state.deploy_environment)
            kg.link(rel_id, "deployed_via", pipe_id)

    kg.save()
    state.knowledge_graph_context = kg.context_for_agents()
    publish_run_state(state)
    return kg


def crew_inputs(state, **extra) -> dict:
    """Build standard crew kickoff inputs from flow state."""
    sync_graph_from_state(state)
    base = {
        "project_name": state.project_name,
        "client_brief": state.client_brief,
        "requirements_doc": state.requirements_doc,
        "architecture_doc": state.architecture_doc,
        "sprint_backlog": state.sprint_backlog,
        "current_sprint": state.current_sprint,
        "code_artifacts": state.code_artifacts,
        "code_review_report": state.code_review_report,
        "security_report": state.security_report,
        "deployment_report": state.deployment_report,
        "post_deploy_report": state.post_deploy_report,
        "test_report": state.test_report,
        "release_notes": state.release_notes,
        "release_number": str(state.release_number),
        "deploy_environment": state.deploy_environment,
        "autonomy_level": state.autonomy_level,
        "change_requests": "\n".join(state.change_requests),
        "client_feedback": "\n".join(state.client_feedback),
        "knowledge_graph_context": state.knowledge_graph_context,
    }
    base.update(extra)
    return base


def verdict_passed(raw: str, pass_token: str, fail_token: str | None = None) -> bool:
    """Parse worker-agent PASS/FAIL verdicts from crew output."""
    upper = raw.upper()
    passed = pass_token.upper() in upper
    if fail_token and fail_token.upper() in upper:
        return False
    return passed
