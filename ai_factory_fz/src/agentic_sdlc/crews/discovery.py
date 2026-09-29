"""Discovery phase: Customer expands the brief, Spec writer clarifies and writes the PRD."""

from agentic_sdlc.artifacts.prd import PRD, CustomerAnswers, ProductBrief, QAPair, SpecQuestions
from agentic_sdlc.crews.base import TaskResult, TaskRunner, artifact_guardrail
from agentic_sdlc.scope import Scope

PHASE = "discovery"


def prd_errors(prd: PRD) -> list[str]:
    errors = []
    ids = [s.id for s in prd.user_stories]
    if len(ids) != len(set(ids)):
        errors.append("User story ids must be unique")
    if not prd.must_have_ids():
        errors.append("At least one user story must have priority 'must'")
    for s in prd.user_stories:
        if len(s.acceptance_criteria) < 2:
            errors.append(f"{s.id} needs at least two acceptance criteria")
    return errors


def format_qa(history: list[QAPair]) -> str:
    return "\n".join(f"Q: {p.question}\nA: {p.answer}" for p in history) or "(none yet)"


def expand_brief(runner: TaskRunner, brief: str) -> TaskResult[ProductBrief]:
    return runner.run(PHASE, "customer_brief", {"brief": brief}, ProductBrief)


def clarify(
    runner: TaskRunner, product_brief: ProductBrief, history: list[QAPair], max_rounds: int
) -> tuple[list[QAPair], list[TaskResult]]:
    """Spec writer asks, Customer answers, until the spec writer is ready or rounds run out."""
    history = list(history)
    results: list[TaskResult] = []
    brief_md = product_brief.to_markdown()
    for round_no in range(1, max_rounds + 1):
        asked = runner.run(
            PHASE,
            "spec_questions",
            {"product_brief": brief_md, "qa_history": format_qa(history), "round": round_no, "max_rounds": max_rounds},
            SpecQuestions,
        )
        results.append(asked)
        questions = asked.artifact.questions
        if asked.artifact.ready or not questions:
            break
        answered = runner.run(
            PHASE,
            "customer_answers",
            {"product_brief": brief_md, "questions": "\n".join(f"- {q}" for q in questions)},
            CustomerAnswers,
        )
        results.append(answered)
        history.extend(answered.artifact.answers)
    return history, results


def write_prd(
    runner: TaskRunner, product_brief: ProductBrief, history: list[QAPair], stack: str, revision_notes: str,
    scope: Scope | None = None,
) -> TaskResult[PRD]:
    scope = scope or Scope()
    return runner.run(
        PHASE,
        "write_prd",
        {
            "product_brief": product_brief.to_markdown(),
            "qa_history": format_qa(history),
            "stack": stack,
            "revision_notes": revision_notes or "(none)",
            "scope_rules": scope.rules_text(),
        },
        PRD,
        guardrail=artifact_guardrail(PRD, lambda p: prd_errors(p) + scope.prd_errors(p)),
    )
