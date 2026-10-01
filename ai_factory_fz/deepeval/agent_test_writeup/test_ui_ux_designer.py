"""DeepEval checks for the `ui_ux_designer` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_every_must_story_has_screen():
    judge(
        "every_must_story_has_screen",
        criteria='Every screen has an id (SCR-01, ...), a go_router path, the components it uses, and the user stories it serves. Every must-have user story in the PRD is served by at least one screen.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/design_system.md"),
    )


def test_screen_states_covered():
    judge(
        "screen_states_covered",
        criteria='Each screen specifies its loading, empty and error states.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/design_system.md"),
    )


def test_design_tokens_and_accessibility():
    judge(
        "design_tokens_and_accessibility",
        criteria='Colors are hex values with light and dark theme variants, the design system defines reusable components and navigation, the minimum touch target is 48dp, and text contrast is at least WCAG AA.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/design_system.md"),
    )
