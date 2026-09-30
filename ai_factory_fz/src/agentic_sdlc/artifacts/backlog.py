"""Planning artifact: epics, work items and milestones."""

from typing import Literal

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class Epic(BaseModel):
    id: str = Field(description="E-01, E-02, ...")
    title: str
    story_ids: list[str]


Level = Literal["low", "medium", "high"]


class WorkItem(BaseModel):
    id: str = Field(description="WI-001, WI-002, ...")
    title: str
    description: str
    epic_id: str
    feature: str = Field(default="", description="Feature within the epic, e.g. 'Cart API' or 'Cart screen'")
    component: Literal["backend", "frontend", "infra", "shared"]
    story_ids: list[str]
    depends_on: list[str] = Field(default_factory=list)
    # Links to the solution this item builds (from the architecture and design).
    modules: list[str] = Field(default_factory=list, description="Backend module names it builds or changes")
    api_operations: list[str] = Field(default_factory=list, description="OpenAPI operationIds it implements (backend) or calls (app)")
    data_models: list[str] = Field(default_factory=list, description="Prisma model names it creates or changes")
    screens: list[str] = Field(default_factory=list, description="Screen ids (SCR-..) it builds")
    # Estimate and its reasoning.
    estimate_points: int = Field(ge=1, le=8)
    complexity: Level = "medium"
    risk: Level = "medium"
    confidence: Level = "medium"
    estimate_rationale: str = Field(default="", description="One line: what drives the size")
    status: Literal["todo", "in_progress", "done", "blocked"] = "todo"
    # Filled in by the estimation review (not part of what the Project manager writes).
    pm_points: SkipJsonSchema[int | None] = None        # the PM's draft estimate
    dev_points: SkipJsonSchema[int | None] = None       # the builder's estimate
    estimated_by: SkipJsonSchema[str] = ""              # agent that re-estimated it
    estimate_notes: SkipJsonSchema[str] = ""            # outcome: adopted / reconciled, and why

    @property
    def disagreement(self) -> bool:
        return "reconciled" in self.estimate_notes


class Milestone(BaseModel):
    id: str = Field(description="M1, M2, ...")
    name: str
    goal: str
    work_item_ids: list[str]


class Backlog(BaseModel):
    epics: list[Epic]
    work_items: list[WorkItem]
    milestones: list[Milestone]
    estimation_reviewed: SkipJsonSchema[bool] = False   # set by the estimation review

    def total_points(self) -> int:
        return sum(w.estimate_points for w in self.work_items)

    def critical_path(self) -> list[str]:
        """Longest chain of dependencies by points (the shortest possible delivery sequence)."""
        items = {w.id: w for w in self.work_items}
        memo: dict[str, tuple[int, list[str]]] = {}

        def longest(wid: str, seen: frozenset) -> tuple[int, list[str]]:
            if wid in memo:
                return memo[wid]
            best = (0, [])
            for d in items[wid].depends_on:
                if d in items and d not in seen:
                    cand = longest(d, seen | {d})
                    if cand[0] > best[0]:
                        best = cand
            memo[wid] = (best[0] + items[wid].estimate_points, [*best[1], wid])
            return memo[wid]

        return max((longest(w, frozenset({w})) for w in items), default=(0, []))[1]

    def coverage_errors(self, operations: dict[str, str], data_models: list[str], screen_ids: list[str]) -> list[str]:
        """The plan must cover the solution: every API operation has a backend item, every data
        model and screen an item; links point at things that exist; app items depend on the
        backend items that provide the operations they call."""
        errors: list[str] = []
        items = {w.id: w for w in self.work_items}
        providers: dict[str, set[str]] = {}
        for w in self.work_items:
            for op in w.api_operations:
                if op not in operations:
                    errors.append(f"{w.id} links unknown API operation '{op}'")
                elif w.component == "backend":
                    providers.setdefault(op, set()).add(w.id)
            errors += [f"{w.id} links unknown data model '{m}'" for m in w.data_models if data_models and m not in data_models]
            errors += [f"{w.id} links unknown screen '{sc}'" for sc in w.screens if screen_ids and sc not in screen_ids]
        for op, route in operations.items():
            if op not in providers:
                errors.append(f"No backend work item implements API operation {op} ({route})")
        covered_models = {m for w in self.work_items for m in w.data_models}
        errors += [f"No work item covers data model {m}" for m in data_models if m not in covered_models]
        covered_screens = {sc for w in self.work_items for sc in w.screens}
        errors += [f"No work item builds screen {sc}" for sc in screen_ids if sc not in covered_screens]

        def ancestors(wid: str) -> set[str]:
            out, stack = set(), list(items[wid].depends_on)
            while stack:
                d = stack.pop()
                if d in items and d not in out:
                    out.add(d)
                    stack += items[d].depends_on
            return out

        for w in self.work_items:
            if w.component == "backend":
                continue
            deps = ancestors(w.id)
            for op in w.api_operations:
                if op in providers and not providers[op] & deps:
                    errors.append(f"{w.id} calls {op} but does not depend on the item that implements it "
                                  f"({', '.join(sorted(providers[op]))})")
        return errors

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
        cp = self.critical_path()
        lines = ["# Delivery plan (work breakdown)", "",
                 f"Total: {len(self.work_items)} work items, {self.total_points()} points. "
                 f"Critical path ({sum(items[w].estimate_points for w in cp)} points): {' → '.join(cp) or '-'}", "",
                 "## Epics"]
        lines += [f"- **{e.id}** {e.title} (stories: {', '.join(e.story_ids)})" for e in self.epics]
        lines.append("")
        if self.estimation_reviewed:
            changed = [w for w in self.work_items if w.pm_points is not None and w.pm_points != w.estimate_points]
            disputed = [w for w in self.work_items if w.disagreement]
            lines += ["## Estimation review",
                      f"Developers re-estimated every item: {len(changed)} changed from the PM's draft, "
                      f"{len(disputed)} big disagreements reconciled by the PM (highest estimate risk)."]
            lines += [f"- **{w.id}** PM {w.pm_points} / {w.estimated_by} {w.dev_points} → **{w.estimate_points}**: {w.estimate_notes}"
                      for w in disputed]
            lines.append("")
        for m in self.milestones:
            pts = sum(items[w].estimate_points for w in m.work_item_ids if w in items)
            lines += [f"## {m.id}: {m.name} ({pts} pts)", m.goal, "",
                      "| Item | Feature | Component | Pts | Risk/Conf. | Builds | Depends on | Why this size |",
                      "|---|---|---|---|---|---|---|---|"]
            for wid in m.work_item_ids:
                w = items.get(wid)
                if w:
                    builds = "; ".join(x for x in (", ".join(w.api_operations), ", ".join(w.data_models),
                                                   ", ".join(w.screens)) if x) or "-"
                    pts = (f"{w.estimate_points} (PM {w.pm_points}, dev {w.dev_points})"
                           if w.dev_points is not None else str(w.estimate_points))
                    lines.append(
                        f"| {w.id} {w.title} | {w.feature or '-'} | {w.component} | {pts} | "
                        f"{w.risk}/{w.confidence} | {builds} | {', '.join(w.depends_on) or '-'} | {w.estimate_rationale or '-'} |"
                    )
            lines.append("")
        return "\n".join(lines)
