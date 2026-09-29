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
