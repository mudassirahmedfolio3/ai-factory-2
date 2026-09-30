"""Planning artifact: epics, work items and milestones."""

from typing import Literal

from pydantic import BaseModel, Field


class Epic(BaseModel):
    id: str = Field(description="E-01, E-02, ...")
    title: str
    story_ids: list[str]


class WorkItem(BaseModel):
    id: str = Field(description="WI-001, WI-002, ...")
    title: str
    description: str
    epic_id: str
    component: Literal["backend", "frontend", "infra", "shared"]
    story_ids: list[str]
    depends_on: list[str] = Field(default_factory=list)
    estimate_points: int = Field(ge=1, le=8)
    status: Literal["todo", "in_progress", "done", "blocked"] = "todo"


class Milestone(BaseModel):
    id: str = Field(description="M1, M2, ...")
    name: str
    goal: str
    work_item_ids: list[str]


class Backlog(BaseModel):
    epics: list[Epic]
    work_items: list[WorkItem]
    milestones: list[Milestone]

    def validation_errors(self, must_have_story_ids: list[str] | None = None) -> list[str]:
        """Structural checks: unknown references, cycles, uncovered must-have stories."""
        errors: list[str] = []
        items = {w.id: w for w in self.work_items}
        epic_ids = {e.id for e in self.epics}
        for w in self.work_items:
            if w.epic_id not in epic_ids:
                errors.append(f"{w.id} references unknown epic {w.epic_id}")
            for dep in w.depends_on:
                if dep not in items:
                    errors.append(f"{w.id} depends on unknown work item {dep}")
        for m in self.milestones:
            for wid in m.work_item_ids:
                if wid not in items:
                    errors.append(f"Milestone {m.id} lists unknown work item {wid}")
        scheduled = {wid for m in self.milestones for wid in m.work_item_ids}
        for wid in items.keys() - scheduled:
            errors.append(f"{wid} is not in any milestone")
        if self._has_cycle(items):
            errors.append("Work item dependencies contain a cycle")
        if must_have_story_ids:
            covered = {sid for w in self.work_items for sid in w.story_ids}
            for sid in must_have_story_ids:
                if sid not in covered:
                    errors.append(f"Must-have story {sid} has no work item")
        return errors

    @staticmethod
    def _has_cycle(items: dict[str, WorkItem]) -> bool:
        visiting, done = set(), set()

        def visit(wid: str) -> bool:
            if wid in done:
                return False
            if wid in visiting:
                return True
            visiting.add(wid)
            if any(visit(d) for d in items[wid].depends_on if d in items):
                return True
            visiting.discard(wid)
            done.add(wid)
            return False

        return any(visit(wid) for wid in items)

    def to_markdown(self) -> str:
        items = {w.id: w for w in self.work_items}
        lines = ["# Delivery backlog", "", "## Epics"]
        lines += [f"- **{e.id}** {e.title} (stories: {', '.join(e.story_ids)})" for e in self.epics]
        lines.append("")
        for m in self.milestones:
            lines += [f"## {m.id}: {m.name}", m.goal, "", "| Item | Component | Pts | Depends on | Stories |", "|---|---|---|---|---|"]
            for wid in m.work_item_ids:
                w = items.get(wid)
                if w:
                    lines.append(
                        f"| {w.id} {w.title} | {w.component} | {w.estimate_points} | "
                        f"{', '.join(w.depends_on) or '-'} | {', '.join(w.story_ids)} |"
                    )
            lines.append("")
        return "\n".join(lines)
