"""Bottom-up estimation: developers re-estimate the items they will build; the PM reconciles."""

from pydantic import BaseModel, Field

from agentic_sdlc.artifacts.backlog import Level


class ItemEstimate(BaseModel):
    item_id: str
    points: int = Field(ge=1, le=8)
    complexity: Level
    risk: Level
    confidence: Level
    rationale: str = Field(description="What drives the size, from the builder's point of view")
    concerns: str = Field(default="", description="Anything the plan misses or underestimates for this item")


class EstimateReview(BaseModel):
    estimates: list[ItemEstimate]


class Decision(BaseModel):
    item_id: str
    final_points: int = Field(ge=1, le=8)
    reason: str = Field(description="Why this number, given both estimates")


class Reconciliation(BaseModel):
    decisions: list[Decision]
