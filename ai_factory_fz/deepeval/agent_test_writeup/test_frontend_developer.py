"""DeepEval checks for the `frontend_developer` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_uses_generated_api_client():
    judge(
        "uses_generated_api_client",
        criteria='The Flutter code uses the generated API client for backend calls instead of hand-written HTTP calls, and calls match the operations in the OpenAPI contract.',
        input_text=read("docs/openapi.yaml"),
        output_text=read_glob("app/lib/**/*.dart"),
    )


def test_screens_match_design_spec():
    judge(
        "screens_match_design_spec",
        criteria='The Flutter code implements the screens, routes, components and design tokens defined in the design system, including loading, empty and error states.',
        input_text=read("docs/design_system.md"),
        output_text=read_glob("app/lib/**/*.dart"),
    )


def test_widget_tests_and_no_placeholders():
    judge(
        "widget_tests_and_no_placeholders",
        criteria='The implementation is complete with no placeholders or TODOs for core behaviour, and widget tests accompany the features.',
        input_text=read("docs/design_system.md"),
        output_text=read_glob("app/lib/**/*.dart", "app/test/**/*.dart"),
    )
