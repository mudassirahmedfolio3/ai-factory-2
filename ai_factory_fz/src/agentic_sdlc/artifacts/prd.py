"""Discovery artifacts: product brief, clarifications and the PRD."""

from typing import Literal

from pydantic import BaseModel, Field


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) or "- (none)"


class ProductBrief(BaseModel):
    product_name: str
    vision: str
    target_users: list[str]
    business_goals: list[str]
    key_features: list[str]
    constraints: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        return (
            f"# Product brief: {self.product_name}\n\n{self.vision}\n\n"
            f"## Target users\n{_bullets(self.target_users)}\n\n"
            f"## Business goals\n{_bullets(self.business_goals)}\n\n"
            f"## Key features\n{_bullets(self.key_features)}\n\n"
            f"## Constraints\n{_bullets(self.constraints)}\n\n"
            f"## Open questions\n{_bullets(self.open_questions)}\n"
        )


class SpecQuestions(BaseModel):
    questions: list[str] = Field(description="Open questions for the customer; empty if none")
    ready: bool = Field(description="True when there is enough information to write the PRD")


class QAPair(BaseModel):
    question: str
    answer: str


class CustomerAnswers(BaseModel):
    answers: list[QAPair]


class AcceptanceCriterion(BaseModel):
    given: str
    when: str
    then: str


class UserStory(BaseModel):
    id: str = Field(description="US-001, US-002, ...")
    title: str
    as_a: str
    i_want: str
    so_that: str
    priority: Literal["must", "should", "could"]
    acceptance_criteria: list[AcceptanceCriterion]


class Persona(BaseModel):
    name: str
    description: str
    goals: list[str]


class PRD(BaseModel):
    title: str
    summary: str
    personas: list[Persona]
    user_stories: list[UserStory]
    non_functional_requirements: list[str]
    out_of_scope: list[str]
    assumptions: list[str] = Field(default_factory=list)

    def must_have_ids(self) -> list[str]:
        return [s.id for s in self.user_stories if s.priority == "must"]

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", self.summary, "", "## Personas"]
        for p in self.personas:
            lines += [f"### {p.name}", p.description, _bullets(p.goals), ""]
        lines.append("## User stories")
        for s in self.user_stories:
            lines += [
                f"### {s.id} {s.title} ({s.priority})",
                f"As a {s.as_a}, I want {s.i_want}, so that {s.so_that}.",
                "",
            ]
            lines += [
                f"- **Given** {c.given} **when** {c.when} **then** {c.then}"
                for c in s.acceptance_criteria
            ]
            lines.append("")
        lines += [
            "## Non-functional requirements", _bullets(self.non_functional_requirements), "",
            "## Out of scope", _bullets(self.out_of_scope), "",
            "## Assumptions", _bullets(self.assumptions), "",
        ]
        return "\n".join(lines)
