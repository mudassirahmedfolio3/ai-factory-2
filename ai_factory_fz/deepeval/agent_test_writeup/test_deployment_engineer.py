"""DeepEval checks for the `deployment_engineer` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_dockerfile_and_compose():
    judge(
        "dockerfile_and_compose",
        criteria='The Dockerfile is a small multi-stage production image that runs database migrations on start before the server and listens on the PORT environment variable. The compose file runs the API plus PostgreSQL 16, builds the API from its folder and reads settings from the staging env file.',
        input_text=read("docs/architecture.md"),
        output_text=read("server/Dockerfile", "infra/docker-compose.staging.yml"),
    )


def test_no_real_secrets():
    judge(
        "no_real_secrets",
        criteria='The deployment files contain only safe test values and placeholders such as sk_test_placeholder, never real keys. The staging env file says at its top that these are test values, and DATABASE_URL points at the compose database.',
        input_text=read("docs/architecture.md"),
        output_text=read("server/Dockerfile", "infra/docker-compose.staging.yml", "infra/staging.env", ".github/workflows/ci.yml", "infra/README.md"),
    )


def test_ci_and_runbook():
    judge(
        "ci_and_runbook",
        criteria='The CI workflow installs, lints, builds and tests the API on every push and pull request. The infra README explains how to run staging and which variables production needs.',
        input_text=read("docs/architecture.md"),
        output_text=read(".github/workflows/ci.yml", "infra/README.md"),
    )
