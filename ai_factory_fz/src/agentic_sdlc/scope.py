"""Scope limits: keep a run small (e.g. a demo) by capping what the planning agents produce.

Configured under `scope:` in the pipeline file. The limits go into the Spec writer, Project
manager, Architect and UI/UX prompts, and the output checks reject anything over them, so the
agent has to cut scope instead of the limit being a suggestion.
"""

from dataclasses import dataclass
from typing import Any

import yaml

from agentic_sdlc.artifacts.architecture import ArchitectureDoc
from agentic_sdlc.artifacts.backlog import Backlog
from agentic_sdlc.artifacts.design import DesignSystem
from agentic_sdlc.artifacts.prd import PRD

_METHODS = {"get", "post", "put", "patch", "delete"}


@dataclass
class Scope:
    max_user_stories: int | None = None
    max_work_items: int | None = None
    max_milestones: int | None = None
    max_api_operations: int | None = None
    max_screens: int | None = None
    guidance: str = ""   # free text for the agents, e.g. "demo: no accounts or payments"
    # Infrastructure endpoints (health check, API docs) never count toward max_api_operations.
    # Paths relative to the API base, e.g. /health. Set from the profile by the flow.
    infra_paths: tuple[str, ...] = ()

    @classmethod
    def from_pipeline(cls, pipeline: dict[str, Any], infra_paths: tuple[str, ...] = ()) -> "Scope":
        s = pipeline.get("scope") or {}
        fields = {k: s[k] for k in cls.__dataclass_fields__ if k in s and k != "infra_paths"}
        return cls(**fields, infra_paths=infra_paths)

    def rules_text(self) -> str:
        rules = []
        if self.guidance:
            rules.append(self.guidance.strip())
        limits = {
            "user stories": self.max_user_stories, "work items": self.max_work_items,
            "milestones": self.max_milestones, "API operations": self.max_api_operations,
            "app screens": self.max_screens,
        }
        caps = [f"at most {n} {what}" for what, n in limits.items() if n]
        if caps:
            rules.append("Hard scope limits for this run: " + ", ".join(caps) + ". Cut scope to fit; "
                         "keep only what the core journey needs.")
        if self.max_api_operations and self.infra_paths:
            rules.append("Infrastructure endpoints (" + ", ".join(self.infra_paths) + ") do not count toward "
                         "the API operation limit; include the health check in the contract.")
        if rules:
            rules.append("These scope rules take priority over any other rule about what to include.")
        return "\n".join(rules) or "(no extra scope limits)"

    # ---------- checks (used as output guardrails) ----------

    @staticmethod
    def _over(what: str, count: int, limit: int | None) -> list[str]:
        return [f"Too many {what}: {count} (limit {limit}). Cut scope."] if limit and count > limit else []

    def prd_errors(self, prd: PRD) -> list[str]:
        return self._over("user stories", len(prd.user_stories), self.max_user_stories)

    def backlog_errors(self, backlog: Backlog) -> list[str]:
        return (self._over("work items", len(backlog.work_items), self.max_work_items)
                + self._over("milestones", len(backlog.milestones), self.max_milestones))

    def architecture_errors(self, arch: ArchitectureDoc) -> list[str]:
        try:
            spec = yaml.safe_load(arch.openapi_yaml) or {}
        except yaml.YAMLError:
            return []  # reported by the OpenAPI check
        infra = {p.rstrip("/") for p in self.infra_paths}
        ops = sum(1 for path, item in (spec.get("paths") or {}).items() if path.rstrip("/") not in infra
                  for m in (item or {}) if m in _METHODS)
        return self._over("API operations", ops, self.max_api_operations)

    def design_errors(self, design: DesignSystem) -> list[str]:
        return self._over("screens", len(design.screens), self.max_screens)
