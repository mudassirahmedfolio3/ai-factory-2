from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

GRAPH_PATH = Path("artifacts/knowledge_graph.json")


class KnowledgeEntity(BaseModel):
    id: str
    type: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class KnowledgeRelationship(BaseModel):
    source_id: str
    relationship: str
    target_id: str


class DeliveryKnowledgeGraph(BaseModel):
    """Lightweight Software Delivery Knowledge Graph (Harness-style shared context)."""

    entities: list[KnowledgeEntity] = Field(default_factory=list)
    relationships: list[KnowledgeRelationship] = Field(default_factory=list)

    def upsert(self, entity_id: str, entity_type: str, **attributes: Any) -> None:
        for entity in self.entities:
            if entity.id == entity_id:
                entity.attributes.update(attributes)
                return
        self.entities.append(
            KnowledgeEntity(id=entity_id, type=entity_type, attributes=attributes)
        )

    def link(self, source_id: str, relationship: str, target_id: str) -> None:
        rel = KnowledgeRelationship(
            source_id=source_id, relationship=relationship, target_id=target_id
        )
        if rel not in self.relationships:
            self.relationships.append(rel)

    def context_for_agents(self, max_chars: int = 4000) -> str:
        lines = ["# Software Delivery Knowledge Graph Context", ""]
        by_type: dict[str, list[KnowledgeEntity]] = {}
        for entity in self.entities:
            by_type.setdefault(entity.type, []).append(entity)

        for entity_type, items in sorted(by_type.items()):
            lines.append(f"## {entity_type}")
            for item in items:
                attrs = ", ".join(f"{k}={v}" for k, v in item.attributes.items())
                lines.append(f"- **{item.id}**: {attrs}")
            lines.append("")

        if self.relationships:
            lines.append("## Relationships")
            for rel in self.relationships[-20:]:
                lines.append(
                    f"- {rel.source_id} --[{rel.relationship}]--> {rel.target_id}"
                )

        text = "\n".join(lines)
        if len(text) > max_chars:
            return text[:max_chars] + "\n...(truncated)"
        return text

    def save(self) -> Path:
        GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
        GRAPH_PATH.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return GRAPH_PATH

    @classmethod
    def load(cls) -> DeliveryKnowledgeGraph:
        if GRAPH_PATH.exists():
            return cls.model_validate_json(GRAPH_PATH.read_text(encoding="utf-8"))
        return cls()
