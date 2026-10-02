"""DeepEval checks for the `integration_pass` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_covers_integration_areas():
    judge(
        "covers_integration_areas",
        criteria='The integration report checks configuration and environment variables, the API prefix, database migrations, CORS and security headers, error format, and that implemented endpoints match the contract.',
        input_text=read("docs/openapi.yaml"),
        output_text=read_glob("reports/release_round*.md"),
    )


def test_bugs_classified_correctly():
    judge(
        "bugs_classified_correctly",
        criteria='Problems that cannot be fixed as small glue are reported as bugs with the work item they belong to (RELEASE if unclear). Severity is blocker if the system cannot serve its built journeys, major for contract mismatches, minor otherwise, and passed is true only with no blocker or major bugs.',
        input_text=read("docs/openapi.yaml"),
        output_text=read_glob("reports/release_round*.md"),
    )
