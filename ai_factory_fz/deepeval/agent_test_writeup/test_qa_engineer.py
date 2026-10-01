"""DeepEval checks for the `qa_engineer` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_criteria_mapped_to_tests():
    judge(
        "criteria_mapped_to_tests",
        criteria='The QA report verifies the milestone against its acceptance criteria: each criterion covered by built items is mapped to code and tests that prove it, and it checks endpoints against openapi.yaml and looks for security problems.',
        input_text=read("docs/prd.md"),
        output_text=read_glob("reports/qa_*.md"),
    )


def test_bugs_precise_and_reproducible():
    judge(
        "bugs_precise_and_reproducible",
        criteria='Every bug names the work item it belongs to and has steps, expected and actual results. Severity follows the rules: blocker for breaking the milestone goal or security, major for an unmet acceptance criterion, minor otherwise.',
        input_text=read("docs/prd.md"),
        output_text=read_glob("reports/qa_*.md"),
    )


def test_pass_flag_consistent():
    judge(
        "pass_flag_consistent",
        criteria="The report's passed flag is true only when there are no blocker or major bugs, and bugs are not reported for work items that were not built.",
        input_text=read("docs/prd.md"),
        output_text=read_glob("reports/qa_*.md"),
    )
