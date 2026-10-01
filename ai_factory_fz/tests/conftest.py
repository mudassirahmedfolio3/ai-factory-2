import pytest

from agentic_sdlc.artifacts.architecture import ADR, AppFeature, ArchitectureDoc, BackendModule, Component
from agentic_sdlc.artifacts.backlog import Backlog, Epic, Milestone, WorkItem
from agentic_sdlc.artifacts.design import ColorToken, DesignSystem, NavigationLink, ScreenSpec, SharedWidget, TypeStyle
from agentic_sdlc.artifacts.prd import (
    PRD,
    AcceptanceCriterion,
    CustomerAnswers,
    Persona,
    ProductBrief,
    QAPair,
    SpecQuestions,
    UserStory,
)

VALID_OPENAPI = """
openapi: 3.1.0
info: {title: Shop API, version: 1.0.0}
paths:
  /api/v1/products:
    get:
      operationId: listProducts
      responses:
        '200': {description: OK}
"""

VALID_PRISMA = """
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
model Product {
  id   String @id
  name String
}
"""


def _ac() -> list[AcceptanceCriterion]:
    return [AcceptanceCriterion(given="g", when="w", then="t")] * 2


@pytest.fixture
def product_brief() -> ProductBrief:
    return ProductBrief(
        product_name="ShopEase", vision="Sell clothes", target_users=["shoppers"],
        business_goals=["sales"], key_features=["catalog", "cart"],
    )


@pytest.fixture
def prd() -> PRD:
    return PRD(
        title="ShopEase PRD", summary="s",
        personas=[Persona(name="Ann", description="d", goals=["buy"])],
        user_stories=[
            UserStory(id="US-001", title="Browse", as_a="shopper", i_want="browse", so_that="find", priority="must", acceptance_criteria=_ac()),
            UserStory(id="US-002", title="Wishlist", as_a="shopper", i_want="save", so_that="later", priority="could", acceptance_criteria=_ac()),
        ],
        non_functional_requirements=["fast"], out_of_scope=["marketplace"],
    )


@pytest.fixture
def backlog() -> Backlog:
    return Backlog(
        epics=[Epic(id="E-01", title="Catalog", story_ids=["US-001"])],
        work_items=[
            WorkItem(id="WI-001", title="Products API", description="d", epic_id="E-01", component="backend", story_ids=["US-001"], estimate_points=3,
                     feature="Catalog API", modules=["catalog"], api_operations=["listProducts"], data_models=["Product"],
                     estimate_rationale="one paginated endpoint"),
            WorkItem(id="WI-002", title="Products screen", description="d", epic_id="E-01", component="frontend", story_ids=["US-001"], depends_on=["WI-001"], estimate_points=3,
                     feature="Catalog screen", api_operations=["listProducts"], screens=["SCR-01"]),
        ],
        milestones=[Milestone(id="M1", name="Catalog", goal="browse", work_item_ids=["WI-001", "WI-002"])],
    )


@pytest.fixture
def architecture() -> ArchitectureDoc:
    return ArchitectureDoc(
        overview="o",
        components=[Component(name="api", responsibility="r", technology="NestJS")],
        backend_modules=[BackendModule(name="catalog", responsibility="r", entities=["Product"], endpoints=["GET /api/v1/products"])],
        app_features=[AppFeature(name="catalog", screens=["ProductList"], state_management="Riverpod")],
        data_model_notes="n", security=["jwt"],
        adrs=[ADR(id="ADR-001", title="t", context="c", decision="d", consequences="c")],
        openapi_yaml=VALID_OPENAPI, prisma_schema=VALID_PRISMA,
    )


@pytest.fixture
def design_system() -> DesignSystem:
    return DesignSystem(
        colors=[ColorToken(name="primary", light="#000000", dark="#FFFFFF")],
        typography=[TypeStyle(name="body", size=14, weight=400, line_height=1.4)],
        spacing=[4, 8], corner_radii=[8],
        shared_widgets=[SharedWidget(name="ProductCard", description="d")],
        screens=[ScreenSpec(id="SCR-01", name="Products", route="/products", purpose="p", components=["ProductCard"], states=["loading"], story_ids=["US-001"])],
        navigation=[NavigationLink(from_screen="SCR-01", to_screen="SCR-01", trigger="tap")],
        accessibility=["48dp targets"],
    )


@pytest.fixture
def canned(product_brief, prd, backlog, architecture, design_system):
    """Artifact returned for each task key by the fake runner."""
    return {
        "customer_brief": product_brief,
        "spec_questions": SpecQuestions(questions=["Guest checkout?"], ready=False),
        "customer_answers": CustomerAnswers(answers=[QAPair(question="Guest checkout?", answer="No")]),
        "write_prd": prd,
        "plan_backlog": backlog,
        "design_architecture": architecture,
        "design_ui": design_system,
    }


@pytest.fixture(autouse=True)
def docker_reachable_directly(monkeypatch):
    """Tests must not depend on this machine's Docker setup: assume direct access."""
    from agentic_sdlc.tools import docker_access
    monkeypatch.setattr(docker_access, "access_mode", lambda: "direct")
