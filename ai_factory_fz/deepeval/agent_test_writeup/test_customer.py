"""DeepEval checks for the `customer` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_expanded_brief_faithful():
    judge(
        "expanded_brief_faithful",
        criteria="The output is a structured product brief written from the business owner's point of view. It must expand the input brief without contradicting it, fill gaps with realistic, plainly stated business decisions, and list the questions that are still undecided.",
        input_text=original_brief(),
        output_text=read("docs/product_brief.md"),
    )


def test_answers_direct_and_consistent():
    judge(
        "answers_direct_and_consistent",
        criteria="The clarifications contain questions and the customer's answers (input is the product brief). Every question must have a direct answer, and the answers must stay consistent with the brief and with a realistic first release.",
        input_text=brief(),
        output_text=read("docs/clarifications.md"),
    )


def test_non_technical_owner_voice():
    judge(
        "non_technical_owner_voice",
        criteria="The customer's answers speak as a non-technical business owner: they state business needs and decisions, not implementation or technology choices.",
        input_text=brief(),
        output_text=read("docs/clarifications.md"),
    )
