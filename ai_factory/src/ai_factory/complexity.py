"""Run complexity profiles — scope, releases, and UI time estimates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ComplexityLevel = Literal["basic", "basic_plus", "standard", "full"]


@dataclass(frozen=True)
class ComplexityProfile:
    id: ComplexityLevel
    label: str
    description: str
    estimated_minutes: int
    max_releases: int
    llm_calls_approx: int


PROFILES: dict[ComplexityLevel, ComplexityProfile] = {
    "basic": ComplexityProfile(
        id="basic",
        label="Basic",
        description="Mini PRD + lightweight Flutter sketch. Auto-pass review, QA, and deploy gates.",
        estimated_minutes=10,
        max_releases=1,
        llm_calls_approx=2,
    ),
    "basic_plus": ComplexityProfile(
        id="basic_plus",
        label="Basic+",
        description=(
            "Full discovery crew + client PRD review, design/build/QA agents, "
            "richer browser preview. Skips full security/deploy crews."
        ),
        estimated_minutes=25,
        max_releases=1,
        llm_calls_approx=10,
    ),
    "standard": ComplexityProfile(
        id="standard",
        label="Standard",
        description="Full SDLC pipeline with all crews, one release, simulated client approvals.",
        estimated_minutes=60,
        max_releases=1,
        llm_calls_approx=24,
    ),
    "full": ComplexityProfile(
        id="full",
        label="Full",
        description="Complete pipeline with multiple releases and change-request loops.",
        estimated_minutes=120,
        max_releases=2,
        llm_calls_approx=40,
    ),
}


def get_profile(level: str) -> ComplexityProfile:
    normalized = (level or "standard").strip().lower()
    if normalized not in PROFILES:
        return PROFILES["standard"]
    return PROFILES[normalized]  # type: ignore[index]


def list_profiles() -> list[dict[str, object]]:
    return [
        {
            "id": p.id,
            "label": p.label,
            "description": p.description,
            "estimated_minutes": p.estimated_minutes,
            "max_releases": p.max_releases,
        }
        for p in PROFILES.values()
    ]
