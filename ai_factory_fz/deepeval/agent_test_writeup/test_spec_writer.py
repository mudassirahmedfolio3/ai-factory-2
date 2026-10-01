"""DeepEval checks for the `spec_writer` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_prd_covers_brief_without_scope_creep():
    judge(
        "prd_covers_brief_without_scope_creep",
        criteria='The PRD must cover every capability in the input product brief and the clarifications, add no major scope they do not imply, keep the first release focused on what is needed to sell and fulfil an order, and not design the architecture.',
        input_text=brief(),
        output_text=read("docs/prd.md"),
    )


def test_stories_have_gwt_acceptance_criteria():
    judge(
        "stories_have_gwt_acceptance_criteria",
        criteria='Story ids follow US-001, US-002, ... Every user story has at least two acceptance criteria in Given/When/Then form that a QA engineer can test directly, and every story has a priority of must, should or could.',
        input_text=brief(),
        output_text=read("docs/prd.md"),
    )


def test_nfr_and_out_of_scope():
    judge(
        "nfr_and_out_of_scope",
        criteria='The PRD includes non-functional requirements (performance, security, privacy, accessibility, supported platforms) and an explicit out-of-scope list.',
        input_text=brief(),
        output_text=read("docs/prd.md"),
    )


def test_clarifications_reflected_in_prd():
    judge(
        "clarifications_reflected_in_prd",
        criteria='The PRD (output) reflects the decisions made in the clarifications (input): answered questions on scope, business rules, payments, delivery or returns show up as requirements or as out-of-scope items, and nothing contradicts them.',
        input_text=read("docs/clarifications.md"),
        output_text=read("docs/prd.md"),
    )
