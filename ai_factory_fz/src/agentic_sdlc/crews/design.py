"""Design phase: UI/UX designer produces the design system and screen specs."""

from agentic_sdlc.artifacts.architecture import ArchitectureDoc
from agentic_sdlc.artifacts.design import DesignSystem
from agentic_sdlc.artifacts.prd import PRD
from agentic_sdlc.crews.base import TaskResult, TaskRunner, artifact_guardrail
from agentic_sdlc.scope import Scope

PHASE = "design"


def design_ui(runner: TaskRunner, prd: PRD, architecture: ArchitectureDoc, scope: Scope | None = None) -> TaskResult[DesignSystem]:
    scope = scope or Scope()
    must_haves = prd.must_have_ids()
    return runner.run(
        PHASE,
        "design_ui",
        {"prd": prd.to_markdown(), "app_features": architecture.app_features_summary(), "scope_rules": scope.rules_text()},
        DesignSystem,
        guardrail=artifact_guardrail(
            DesignSystem,
            lambda d: [f"Must-have story {sid} is not served by any screen" for sid in d.uncovered_stories(must_haves)]
            + scope.design_errors(d),
        ),
    )
