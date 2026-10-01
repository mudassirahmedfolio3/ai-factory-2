"""DeepEval checks for the `architect` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_architecture_supports_prd():
    judge(
        "architecture_supports_prd",
        criteria='The architecture document describes components and responsibilities, backend modules with their entities and endpoints, and mobile app features with screens and state management. Together they support every must-have story in the PRD, using simple proven technology.',
        input_text=read("docs/prd.md", "docs/backlog.md"),
        output_text=read("docs/architecture.md"),
    )


def test_openapi_complete_and_usable():
    judge(
        "openapi_complete_and_usable",
        criteria='The OpenAPI 3.1 document covers every endpoint the must-have stories need, with request and response schemas, bearer auth, pagination and a shared error schema. Every operation has an operationId.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/openapi.yaml"),
    )


def test_prisma_schema_matches_api():
    judge(
        "prisma_schema_matches_api",
        criteria='The Prisma schema for PostgreSQL stores every resource the OpenAPI document exposes, with sensible relations, keys and field types.',
        input_text=read("docs/openapi.yaml"),
        output_text=read("docs/schema.prisma"),
    )


def test_security_design_and_adrs():
    judge(
        "security_design_and_adrs",
        criteria='The architecture includes a security design and at least three ADRs that each record a key decision, its context and its consequences.',
        input_text=read("docs/prd.md"),
        output_text=read("docs/architecture.md"),
    )
