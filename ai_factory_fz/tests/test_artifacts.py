from agentic_sdlc.artifacts.backlog import WorkItem
from agentic_sdlc.crews.base import fill_template
from agentic_sdlc.crews.discovery import prd_errors


def test_markdown_renders_for_every_artifact(product_brief, prd, backlog, architecture, design_system):
    for artifact in (product_brief, prd, backlog, architecture, design_system):
        assert artifact.to_markdown().startswith("# ")


def test_valid_backlog_has_no_errors(backlog, prd):
    assert backlog.validation_errors(prd.must_have_ids()) == []


def test_backlog_detects_bad_refs_cycles_and_uncovered_stories(backlog):
    backlog.work_items[0].depends_on = ["WI-002"]  # WI-002 already depends on WI-001
    backlog.work_items.append(
        WorkItem(id="WI-003", title="t", description="d", epic_id="E-99", component="infra", story_ids=[], depends_on=["WI-404"], estimate_points=1)
    )
    errors = backlog.validation_errors(["US-001", "US-777"])
    joined = "\n".join(errors)
    assert "cycle" in joined
    assert "unknown epic E-99" in joined
    assert "unknown work item WI-404" in joined
    assert "WI-003 is not in any milestone" in joined
    assert "US-777" in joined


def test_openapi_and_prisma_checks(architecture):
    assert architecture.openapi_errors() == []
    assert architecture.prisma_errors() == []
    architecture.openapi_yaml = architecture.openapi_yaml.replace("operationId: listProducts", "summary: x")
    assert any("operationId" in e for e in architecture.openapi_errors())
    architecture.openapi_yaml = "openapi: [broken"
    assert architecture.openapi_errors()
    architecture.prisma_schema = "nothing here"
    assert len(architecture.prisma_errors()) == 2


def test_prd_checks(prd):
    assert prd_errors(prd) == []
    prd.user_stories[1].id = "US-001"
    prd.user_stories[0].acceptance_criteria = prd.user_stories[0].acceptance_criteria[:1]
    errors = prd_errors(prd)
    assert "unique" in errors[0]
    assert any("two acceptance criteria" in e for e in errors)


def test_design_coverage(design_system):
    assert design_system.uncovered_stories(["US-001", "US-005"]) == ["US-005"]


def test_fill_template_leaves_braces_in_values_alone():
    out = fill_template("A {x} B {y}", {"x": "{json: 1}", "y": 2})
    assert out == "A {json: 1} B 2"


def test_plan_covers_the_solution(backlog, architecture, design_system):
    ops, models, screens = architecture.operations(), architecture.data_models(), [x.id for x in design_system.screens]
    assert ops == {"listProducts": "GET /api/v1/products"}
    assert models == ["Product"]
    assert backlog.coverage_errors(ops, models, screens) == []


def test_coverage_finds_gaps_bad_links_and_missing_dependencies(backlog, architecture):
    ops = {**architecture.operations(), "createCart": "POST /carts"}
    backlog.work_items[1].depends_on = []                      # the screen no longer depends on the API item
    backlog.work_items[1].screens = ["SCR-99"]
    backlog.work_items[0].data_models = ["Product", "Ghost"]
    errors = "\n".join(backlog.coverage_errors(ops, ["Product", "Cart"], ["SCR-01"]))
    assert "No backend work item implements API operation createCart" in errors
    assert "No work item covers data model Cart" in errors
    assert "No work item builds screen SCR-01" in errors
    assert "WI-002 links unknown screen 'SCR-99'" in errors
    assert "WI-001 links unknown data model 'Ghost'" in errors
    assert "WI-002 calls listProducts but does not depend on the item that implements it (WI-001)" in errors


def test_critical_path_and_markdown(backlog):
    assert backlog.critical_path() == ["WI-001", "WI-002"]
    md = backlog.to_markdown()
    assert "Critical path (6 points): WI-001 → WI-002" in md
    assert "one paginated endpoint" in md and "listProducts" in md


def test_old_backlogs_without_links_still_load():
    from agentic_sdlc.artifacts.backlog import WorkItem
    w = WorkItem.model_validate({"id": "WI-001", "title": "t", "description": "d", "epic_id": "E-01",
                                 "component": "backend", "story_ids": [], "estimate_points": 2})
    assert w.api_operations == [] and w.risk == "medium"
