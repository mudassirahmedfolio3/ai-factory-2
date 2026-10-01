"""Planning phase: the Architect designs the solution; the Project manager breaks it down.

Order: Architect (from the PRD) -> UI/UX designer (design phase) -> Project manager, so the work
breakdown and estimates are built on the actual solution: every API operation, data model and
screen must be covered by a work item, and app items depend on the backend items they call.
"""

from typing import Callable

from agentic_sdlc.artifacts.architecture import ArchitectureDoc
from agentic_sdlc.artifacts.backlog import Backlog
from agentic_sdlc.artifacts.design import DesignSystem
from agentic_sdlc.artifacts.prd import PRD
from agentic_sdlc.crews.base import TaskResult, TaskRunner, artifact_guardrail
from agentic_sdlc.scope import Scope

PHASE = "planning"


def design_architecture(
    runner: TaskRunner,
    prd: PRD,
    stack: str,
    domain_entities: list[str],
    revision_notes: str,
    scope: Scope | None = None,
    guardrails: Callable[[ArchitectureDoc], list[str]] | None = None,
) -> TaskResult[ArchitectureDoc]:
    """`guardrails`: extra checks on the design (see guardrails/architecture.py)."""
    scope = scope or Scope()
    extra = guardrails or (lambda a: [])
    return runner.run(
        PHASE,
        "design_architecture",
        {
            "prd": prd.to_markdown(),
            "stack": stack,
            "domain_entities": ", ".join(domain_entities),
            "revision_notes": revision_notes or "(none)",
            "scope_rules": scope.rules_text(),
        },
        ArchitectureDoc,
        guardrail=artifact_guardrail(
            ArchitectureDoc,
            lambda a: a.openapi_errors() + a.prisma_errors() + scope.architecture_errors(a) + extra(a),
        ),
    )


def screens_summary(design: DesignSystem | None) -> str:
    if design is None:
        return "(no screen specs: the design phase is disabled)"
    return "\n".join(f"- {s.id} {s.name} ({s.route}): stories {', '.join(s.story_ids)}" for s in design.screens)


def plan_work(
    runner: TaskRunner,
    prd: PRD,
    architecture: ArchitectureDoc,
    design: DesignSystem | None,
    stack: str,
    revision_notes: str = "",
    scope: Scope | None = None,
) -> TaskResult[Backlog]:
    scope = scope or Scope()
    must_haves = prd.must_have_ids()
    operations = architecture.operations()
    models = architecture.data_models()
    screen_ids = [s.id for s in design.screens] if design else []

    def check(b: Backlog) -> list[str]:
        return (b.validation_errors(must_haves) + b.coverage_errors(operations, models, screen_ids)
                + scope.backlog_errors(b))

    return runner.run(
        PHASE,
        "plan_backlog",
        {
            "prd": prd.to_markdown(),
            "solution": architecture.solution_summary(),
            "screens": screens_summary(design),
            "stack": stack,
            "revision_notes": revision_notes or "(none)",
            "scope_rules": scope.rules_text(),
        },
        Backlog,
        guardrail=artifact_guardrail(Backlog, check),
    )
