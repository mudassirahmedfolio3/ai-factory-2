"""Architect guardrails: a compliant design passes all 14; each rule catches its own violation."""

import pytest

from agentic_sdlc.artifacts.architecture import ADR, AppFeature, ArchitectureDoc, BackendModule, Component
from agentic_sdlc.guardrails import architecture as g
from agentic_sdlc.registry.profiles import Profile

OPENAPI = """
openapi: 3.1.0
info: {title: Shop, version: '1'}
servers: [{url: 'http://localhost:3000/api/v1'}]
paths:
  /health:
    get: {operationId: getHealth, security: [], responses: {'200': {description: ok, content: {application/json: {schema: {type: object}}}}}}
  /products:
    get:
      operationId: listProducts
      security: []
      responses:
        '200': {description: ok, content: {application/json: {schema: {$ref: '#/components/schemas/ProductPage'}}}}
        '400': {$ref: '#/components/responses/BadRequest'}
  /cart:
    post:
      operationId: createCart
      security: [{bearerAuth: []}]
      responses:
        '201': {description: created, content: {application/json: {schema: {type: object}}}}
        '401': {description: no, content: {application/json: {schema: {$ref: '#/components/schemas/Error'}}}}
components:
  securitySchemes: {bearerAuth: {type: http, scheme: bearer}}
  responses:
    BadRequest: {description: bad, content: {application/json: {schema: {$ref: '#/components/schemas/Error'}}}}
  schemas:
    Error: {type: object}
    ProductPage: {type: object}
"""

PRISMA = """
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
model Product {
  id         String   @id @default(uuid())
  name       String
  priceCents Int
  createdAt  DateTime @default(now())
  updatedAt  DateTime @updatedAt
}
model Cart {
  id        String   @id
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
"""

LONG = "A sufficiently detailed explanation of this point."


def good() -> ArchitectureDoc:
    return ArchitectureDoc(
        overview="A Flutter mobile app talking to a NestJS API.",
        components=[Component(name="App", responsibility="r", technology="Flutter 3, Riverpod"),
                    Component(name="API", responsibility="r", technology="NestJS, Prisma"),
                    Component(name="DB", responsibility="r", technology="PostgreSQL 16"),
                    Component(name="Images", responsibility="r", technology="Static files served by the API")],
        backend_modules=[
            BackendModule(name="health", responsibility="r", entities=[], endpoints=["GET /api/v1/health"]),
            BackendModule(name="catalog", responsibility="r", entities=["Product (read-only)"], endpoints=["GET /api/v1/products"]),
            BackendModule(name="cart", responsibility="r", entities=["Cart"], endpoints=["POST /api/v1/cart"]),
        ],
        app_features=[AppFeature(name="catalog", screens=["ProductList"], state_management="Riverpod")],
        data_model_notes="n",
        security=["JWT bearer authentication", "Input validation with class-validator",
                  "Secrets only from environment variables"],
        adrs=[ADR(id=f"ADR-00{i}", title="t", context=LONG, decision=LONG, consequences=LONG) for i in (1, 2, 3)],
        openapi_yaml=OPENAPI, prisma_schema=PRISMA,
    )


@pytest.fixture
def profile():
    return Profile.load("flutter_nestjs_ecommerce")


def rule_hits(arch, profile, rule):
    return g.check(arch, profile, [rule])


def test_compliant_design_passes_all_rules(profile):
    assert g.check(good(), profile, g.ALL_RULES) == []


def test_a1_forbidden_and_required_stack(profile):
    a = good()
    a.components.append(Component(name="Admin", responsibility="r", technology="React 18 SPA"))
    a.components = [c for c in a.components if c.name != "DB"]
    hits = rule_hits(a, profile, "A1")
    assert any("uses react" in h for h in hits) and any("does not use postgresql" in h for h in hits)


def test_a1_allows_sdks_like_analytics(profile):
    a = good()
    a.components[0].technology += ", Firebase Analytics SDK"
    assert rule_hits(a, profile, "A1") == []


def test_a2_mobile_platform(profile):
    a = good()
    a.overview += " Plus an admin web app."
    assert any("web app" in h for h in rule_hits(a, profile, "A2"))
    a2 = good()
    a2.app_features = []
    assert any("no app features" in h for h in rule_hits(a2, profile, "A2"))


def test_b1_prose_must_match_contract(profile):
    a = good()
    a.backend_modules[1].endpoints.append("DELETE /api/v1/products/{productId}")
    a.backend_modules[2].endpoints = []
    hits = rule_hits(a, profile, "B1")
    assert "B1: module endpoint DELETE /products/{} is not in openapi.yaml" in hits
    assert "B1: openapi.yaml operation POST /cart is not listed under any backend module" in hits


def test_b2_health_and_b3_prefix(profile):
    a = good()
    a.openapi_yaml = OPENAPI.replace("  /health:\n", "  /status:\n").replace("localhost:3000/api/v1", "localhost:3000/api")
    assert rule_hits(a, profile, "B2") == ["B2: the contract has no GET /health (health check)"]
    assert rule_hits(a, profile, "B3") == ["B3: server URL 'http://localhost:3000/api' does not end with the API prefix /api/v1"]


def test_b4_error_responses_use_one_shared_schema(profile):
    a = good()
    a.openapi_yaml = OPENAPI.replace("{$ref: '#/components/schemas/Error'}}}}\n", "{type: object}}}}\n", 1)
    assert any("does not use a shared error schema" in h for h in rule_hits(a, profile, "B4"))
    b = good()
    b.openapi_yaml = OPENAPI.replace("        '400': {$ref: '#/components/responses/BadRequest'}\n", "")
    assert rule_hits(b, profile, "B4") == ["B4: GET /products declares no error response (4xx/5xx)"]


def test_b5_typed_responses(profile):
    a = good()
    a.openapi_yaml = OPENAPI.replace("'201': {description: created, content: {application/json: {schema: {type: object}}}}",
                                     "'201': {description: created}")
    assert rule_hits(a, profile, "B5") == ["B5: POST /cart 201 response has no schema"]


def test_b6_auth_decided_per_operation(profile):
    a = good()
    a.openapi_yaml = OPENAPI.replace("operationId: listProducts\n      security: []\n", "operationId: listProducts\n")
    assert rule_hits(a, profile, "B6") == [
        "B6: GET /products does not say whether it is secured (add security, or security: [] if public)"]
    b = good()
    b.openapi_yaml = a.openapi_yaml.replace("paths:", "security: [{bearerAuth: []}]\npaths:")
    assert rule_hits(b, profile, "B6") == []   # a global default is an explicit decision


def test_c1_entities_c2_money_c3_ids(profile):
    a = good()
    a.backend_modules[2].entities = ["Cart", "CartItem (lines)"]
    assert rule_hits(a, profile, "C1") == ["C1: module 'cart' uses entity 'CartItem (lines)', which is not a model in schema.prisma"]
    b = good()
    b.prisma_schema = PRISMA.replace("priceCents Int", "price      Float").replace("  updatedAt DateTime @updatedAt\n}\n", "}\n")
    assert rule_hits(b, profile, "C2") == ["C2: Product.price is Float; store money as Int (minor units, e.g. cents)"]
    assert rule_hits(b, profile, "C3") == ["C3: model Cart is missing updatedAt"]


def test_d1_adrs_d2_security_d3_secrets(profile):
    a = good()
    a.adrs = a.adrs[:2]
    a.adrs[0].consequences = "none"
    hits = rule_hits(a, profile, "D1")
    assert "D1: 2 ADRs; at least 3 are needed for the key decisions" in hits and any("ADR-001" in h for h in hits)
    b = good()
    b.security = ["HTTPS everywhere"]
    assert len(rule_hits(b, profile, "D2")) == 3
    c = good()
    c.data_model_notes = "Example: postgresql://admin:hunter2@db:5432/shop and key sk_live_ABCDEFGHIJKLMNOP"
    hits = rule_hits(c, profile, "D3")
    assert any("Stripe secret key" in h for h in hits) and any("connection string" in h for h in hits)


def test_rules_are_chosen_per_pipeline():
    assert g.enabled_rules({}) == g.ALL_RULES
    assert g.enabled_rules({"guardrails": {"architect": ["A1", "B2"]}}) == ["A1", "B2"]
    with pytest.raises(ValueError, match="Z9"):
        g.enabled_rules({"guardrails": {"architect": ["Z9"]}})


def test_failing_design_goes_back_to_the_architect(profile):
    """The guardrail is wired into the Architect's task: its problems become the retry feedback."""
    from crewai.tasks.task_output import TaskOutput

    from agentic_sdlc.crews.base import artifact_guardrail
    bad = good()
    bad.openapi_yaml = OPENAPI.replace("  /health:\n", "  /status:\n")
    guard = artifact_guardrail(ArchitectureDoc, g.checker(profile, {}))
    ok, feedback = guard(TaskOutput(description="", raw=bad.model_dump_json(), agent="architect", pydantic=bad))
    assert not ok and "B2: the contract has no GET /health" in feedback


def test_passing_guardrail_returns_canonical_json():
    from crewai.tasks.task_output import TaskOutput

    from agentic_sdlc.crews.base import artifact_guardrail
    from pydantic import BaseModel

    class M(BaseModel):
        x: int

    guard = artifact_guardrail(M, lambda m: [] if m.x else ["need x"])
    ok, payload = guard(TaskOutput(description="", raw='{"x": 1}', agent="a", pydantic=None))
    assert ok and payload == '{"x":1}'
