"""DeepEval checks for the `project_manager` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_every_must_story_covered():
    judge(
        "every_must_story_covered",
        criteria='The backlog (input is the PRD) covers every must-have user story with at least one work item, and each work item names the user stories it serves. No work item serves a story that is not in the PRD.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/backlog.md"),
    )


def test_work_items_small_and_well_formed():
    judge(
        "work_items_small_and_well_formed",
        criteria='Ids follow E-01, WI-001 and M1 patterns. Each work item belongs to exactly one component (backend, frontend, infra or shared), is small (1 to 5 points), and lists depends_on only with work item ids and without cycles.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/backlog.md"),
    )


def test_milestones_ordered_testable():
    judge(
        "milestones_ordered_testable",
        criteria='Milestones are ordered so each ends in a testable slice (for example auth, then catalog, then cart, then checkout, then orders) and backend work items come before the frontend items that call them.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/backlog.md"),
    )
