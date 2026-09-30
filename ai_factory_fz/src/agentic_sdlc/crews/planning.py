"""Planning phase: Project manager builds the backlog, Architect designs the system and API contract."""

from agentic_sdlc.artifacts.architecture import ArchitectureDoc
from agentic_sdlc.artifacts.backlog import Backlog
from agentic_sdlc.artifacts.prd import PRD
from agentic_sdlc.crews.base import TaskResult, TaskRunner, artifact_guardrail
from agentic_sdlc.scope import Scope

PHASE = "planning"


def plan_backlog(runner: TaskRunner, prd: PRD, stack: str, scope: Scope | None = None) -> TaskResult[Backlog]:
    scope = scope or Scope()
    must_haves = prd.must_have_ids()
    return runner.run(
        PHASE,
        "plan_backlog",
        {"prd": prd.to_markdown(), "stack": stack, "scope_rules": scope.rules_text()},
        Backlog,
        guardrail=artifact_guardrail(Backlog, lambda b: b.validation_errors(must_haves) + scope.backlog_errors(b)),
    )


def design_architecture(
    runner: TaskRunner,
    prd: PRD,
    backlog: Backlog,
    stack: str,
    domain_entities: list[str],
    revision_notes: str,
    scope: Scope | None = None,
) -> TaskResult[ArchitectureDoc]:
    scope = scope or Scope()
    return runner.run(
        PHASE,
        "design_architecture",
        {
            "prd": prd.to_markdown(),
            "backlog": backlog.to_markdown(),
            "stack": stack,
            "domain_entities": ", ".join(domain_entities),
            "revision_notes": revision_notes or "(none)",
            "scope_rules": scope.rules_text(),
        },
        ArchitectureDoc,
        guardrail=artifact_guardrail(
            ArchitectureDoc, lambda a: a.openapi_errors() + a.prisma_errors() + scope.architecture_errors(a)
        ),
    )
