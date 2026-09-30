"""Architecture artifact, including the OpenAPI contract and Prisma schema."""

import yaml
from openapi_spec_validator import validate
from pydantic import BaseModel, Field


class Component(BaseModel):
    name: str
    responsibility: str
    technology: str


class BackendModule(BaseModel):
    name: str
    responsibility: str
    entities: list[str]
    endpoints: list[str] = Field(description="e.g. 'GET /api/v1/products'")


class AppFeature(BaseModel):
    name: str
    screens: list[str]
    state_management: str


class ADR(BaseModel):
    id: str = Field(description="ADR-001, ...")
    title: str
    context: str
    decision: str
    consequences: str


class ArchitectureDoc(BaseModel):
    overview: str
    components: list[Component]
    backend_modules: list[BackendModule]
    app_features: list[AppFeature]
    data_model_notes: str
    security: list[str]
    adrs: list[ADR]
    openapi_yaml: str = Field(description="Complete OpenAPI 3.1 document as YAML")
    prisma_schema: str = Field(description="Complete Prisma schema for PostgreSQL")

    def openapi_errors(self) -> list[str]:
        """Parse and validate the OpenAPI document; also require operationIds."""
        try:
            spec = yaml.safe_load(self.openapi_yaml)
        except yaml.YAMLError as e:
            return [f"openapi_yaml is not valid YAML: {e}"]
        if not isinstance(spec, dict):
            return ["openapi_yaml must be a YAML mapping"]
        try:
            validate(spec)
        except Exception as e:  # validator raises several exception types
            return [f"OpenAPI validation failed: {str(e).splitlines()[0]}"]
        errors = []
        for path, ops in (spec.get("paths") or {}).items():
            for method, op in ops.items():
                if method in {"get", "post", "put", "patch", "delete"} and not op.get("operationId"):
                    errors.append(f"{method.upper()} {path} has no operationId")
        if not spec.get("paths"):
            errors.append("OpenAPI document has no paths")
        return errors

    def prisma_errors(self) -> list[str]:
        s = self.prisma_schema
        errors = []
        if "datasource" not in s or "postgresql" not in s:
            errors.append("Prisma schema needs a postgresql datasource")
        if "model " not in s:
            errors.append("Prisma schema defines no models")
        return errors

    def app_features_summary(self) -> str:
        return "\n".join(
            f"- {f.name}: screens {', '.join(f.screens)} (state: {f.state_management})"
            for f in self.app_features
        )

    def to_markdown(self) -> str:
        lines = ["# Architecture", "", self.overview, "", "## Components"]
        lines += [f"- **{c.name}** ({c.technology}): {c.responsibility}" for c in self.components]
        lines += ["", "## Backend modules"]
        for m in self.backend_modules:
            lines += [f"### {m.name}", m.responsibility, f"Entities: {', '.join(m.entities)}", ""]
            lines += [f"- `{e}`" for e in m.endpoints]
            lines.append("")
        lines += ["## Mobile app features", self.app_features_summary(), ""]
        lines += ["## Data model", self.data_model_notes, "", "## Security"]
        lines += [f"- {s}" for s in self.security]
        lines += ["", "## Architecture decisions"]
        for a in self.adrs:
            lines += [
                f"### {a.id}: {a.title}",
                f"**Context:** {a.context}",
                "",
                f"**Decision:** {a.decision}",
                "",
                f"**Consequences:** {a.consequences}",
                "",
            ]
        lines.append("The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.")
        return "\n".join(lines)
