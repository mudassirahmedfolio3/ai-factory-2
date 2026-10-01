"""DeepEval checks for the `backend_developer` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_endpoints_match_contract():
    judge(
        "endpoints_match_contract",
        criteria='The NestJS code implements the OpenAPI contract: paths, HTTP methods, status codes and request/response shapes match exactly, and implemented endpoints are not invented beyond the contract.',
        input_text=read("docs/openapi.yaml"),
        output_text=read_glob("server/src/**/*.ts"),
    )


def test_complete_with_tests():
    judge(
        "complete_with_tests",
        criteria='The implementation is complete with no placeholders or TODOs for core behaviour, follows the module structure in the architecture, and ships focused unit tests for the behaviour it adds.',
        input_text=read("docs/architecture.md"),
        output_text=read_glob("server/src/**/*.ts"),
    )


def test_no_secrets_in_code():
    judge(
        "no_secrets_in_code",
        criteria='No secrets, keys or passwords are hard-coded; configuration is read from environment variables, and input is validated.',
        input_text=read("docs/architecture.md"),
        output_text=read_glob("server/src/**/*.ts"),
    )
