from agentic_sdlc.scope import Scope
from agentic_sdlc.settings import load_config


def test_no_limits_by_default(prd, backlog, architecture, design_system):
    s = Scope.from_pipeline({})
    assert s.rules_text() == "(no extra scope limits)"
    assert s.prd_errors(prd) == s.backlog_errors(backlog) == s.architecture_errors(architecture) == s.design_errors(design_system) == []


def test_limits_are_enforced(prd, backlog, architecture, design_system):
    s = Scope(max_user_stories=1, max_work_items=1, max_milestones=1, max_api_operations=0, max_screens=0)
    assert s.prd_errors(prd) == ["Too many user stories: 2 (limit 1). Cut scope."]
    assert s.backlog_errors(backlog) == ["Too many work items: 2 (limit 1). Cut scope."]
    assert s.architecture_errors(architecture) == []  # 0 means "no limit"
    s.max_api_operations = s.max_screens = 1
    assert s.architecture_errors(architecture) == []
    assert s.design_errors(design_system) == []


def test_demo_pipeline_is_small_and_complete():
    p = load_config("pipeline.demo")
    s = Scope.from_pipeline(p)
    assert s.max_work_items <= 6 and s.max_milestones <= 2
    assert all(p["phases"].values())
    assert p["gates"] == {"prd": True, "architecture": True, "release": True}
    assert p["gate_mode"] == "console"
    text = s.rules_text()
    assert "at most 4 user stories" in text
    assert "no payments" in text


def test_infra_endpoints_do_not_count_toward_the_api_limit(architecture):
    architecture.openapi_yaml += "  /health:\n    get:\n      operationId: health\n      responses:\n        '200': {description: ok}\n"
    assert Scope(max_api_operations=1).architecture_errors(architecture) == ["Too many API operations: 2 (limit 1). Cut scope."]
    s = Scope(max_api_operations=1, infra_paths=("/health",))
    assert s.architecture_errors(architecture) == []
    assert "do not count toward the API operation limit" in s.rules_text()
