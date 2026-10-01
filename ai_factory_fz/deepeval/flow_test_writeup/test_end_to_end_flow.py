"""End-to-end check of one pipeline run, anchored on the spec writer's PRD.

The PRD is the contract every later agent builds on. This file first validates the PRD against the
client brief, then validates what each downstream agent produced against that PRD, in pipeline order.
A weak PRD shows up in the first test; a drifting downstream agent shows up in its own test.
"""

from common import brief, judge, original_brief, read, read_glob, run_dir

ALL_AGENTS = [
    "customer", "spec_writer", "project_manager", "architect", "ui_ux_designer",
    "backend_developer", "frontend_developer", "qa_engineer", "deployment_engineer",
    "integration_pass", "smoke_tester",
]

# Where each agent leaves its work in runs/<run_id>/ (any one match counts).
AGENT_OUTPUTS = {
    "customer": ["docs/product_brief.md", "docs/clarifications.md"],
    "spec_writer": ["docs/prd.md"],
    "project_manager": ["docs/backlog.md"],
    "architect": ["docs/architecture.md", "docs/openapi.yaml", "docs/schema.prisma"],
    "ui_ux_designer": ["docs/design_system.md"],
    "backend_developer": ["server/src"],
    "frontend_developer": ["app/lib"],
    "qa_engineer": ["reports/qa_*.md"],
    "deployment_engineer": ["server/Dockerfile", "infra/docker-compose.staging.yml"],
    "integration_pass": ["reports/release_round*.md"],
    "smoke_tester": ["server/test", "server/smoke", "app/integration_test"],
}


def prd() -> str:
    return read("docs/prd.md")


def test_every_agent_left_output():
    """No LLM: each of the 11 agents produced something in this run. Lists the ones that did not."""
    root = run_dir()
    missing = [a for a in ALL_AGENTS if not any(any(root.glob(p)) for p in AGENT_OUTPUTS[a])]
    assert not missing, f"No output found for: {missing} (run: {root.name})"


def test_01_spec_writer_prd_satisfies_client_brief():
    judge(
        "prd_satisfies_client_brief",
        criteria="The PRD must cover every capability the original client brief asks for, add no major "
                 "scope the brief does not imply, have Given/When/Then acceptance criteria on every "
                 "story, and include non-functional requirements and an out-of-scope list.",
        input_text=original_brief(),
        output_text=prd(),
    )


def test_02_customer_brief_and_answers_match_prd():
    judge(
        "prd_reflects_customer_decisions",
        criteria="The PRD (output) reflects the product brief and the customer's clarification answers "
                 "(input): decisions on scope, business rules, payments, delivery and returns appear as "
                 "requirements or out-of-scope items, and nothing contradicts them.",
        input_text=read("docs/product_brief.md", "docs/clarifications.md"),
        output_text=prd(),
    )


def test_03_project_manager_backlog_traces_to_prd():
    judge(
        "backlog_traces_to_prd",
        criteria="The backlog covers every must-have PRD story with at least one work item, each work "
                 "item names the stories it serves, and no work item serves a story missing from the PRD.",
        input_text=prd(),
        output_text=read("docs/backlog.md"),
    )


def test_04_architect_design_supports_prd():
    judge(
        "architecture_supports_prd",
        criteria="The architecture, OpenAPI contract and Prisma schema support every must-have PRD "
                 "story: each story's data and actions have an endpoint and stored entity, and nothing "
                 "important in the PRD is left without a design.",
        input_text=prd(),
        output_text=read("docs/architecture.md", "docs/openapi.yaml", "docs/schema.prisma"),
    )


def test_05_ui_ux_designer_screens_serve_prd_stories():
    judge(
        "screens_serve_prd_stories",
        criteria="Every must-have PRD story is served by at least one screen in the design system, and "
                 "the screens specify their loading, empty and error states.",
        input_text=prd(),
        output_text=read("docs/design_system.md"),
    )


def test_06_backend_developer_code_matches_contract_from_prd():
    judge(
        "backend_code_matches_contract",
        criteria="The backend code implements the API contract derived from the PRD: matching paths, "
                 "methods, status codes and shapes, with no secrets in code.",
        input_text=read("docs/openapi.yaml"),
        output_text=read_glob("server/src/**/*.ts"),
    )


def test_07_frontend_developer_app_matches_design_from_prd():
    judge(
        "app_matches_design",
        criteria="The Flutter app implements the screens and design tokens from the design system and "
                 "calls the API through the generated client, matching the contract.",
        input_text=read("docs/design_system.md", "docs/openapi.yaml"),
        output_text=read_glob("app/lib/**/*.dart"),
    )


def test_08_qa_engineer_verifies_prd_acceptance_criteria():
    judge(
        "qa_verifies_acceptance_criteria",
        criteria="The QA reports check the PRD's acceptance criteria for the built items, report "
                 "reproducible bugs with correct severity, and set passed only when no blocker or major "
                 "bug remains.",
        input_text=prd(),
        output_text=read_glob("reports/qa_*.md"),
    )


def test_09_deployment_engineer_ships_what_architecture_describes():
    judge(
        "deployment_matches_architecture",
        criteria="The Dockerfile and compose file run the system the architecture describes (API plus "
                 "PostgreSQL, migrations on start, PORT), and contain no real secrets.",
        input_text=read("docs/architecture.md"),
        output_text=read("server/Dockerfile", "infra/docker-compose.staging.yml", "infra/staging.env"),
    )


def test_10_integration_pass_confirms_contract_on_staging():
    judge(
        "integration_confirms_contract",
        criteria="The release verification report states whether the served API matches the contract "
                 "and what integration problems were found, with correct severity.",
        input_text=read("docs/openapi.yaml"),
        output_text=read_glob("reports/release_round*.md"),
    )


def test_11_smoke_tester_covers_prd_journeys():
    judge(
        "smoke_covers_prd_journeys",
        criteria="The smoke and on-device tests exercise the key PRD user journeys that were built end "
                 "to end, assert real outcomes, and are independent of each other.",
        input_text=prd(),
        output_text=read_glob(
            "server/test/**/*smoke*", "server/smoke/**/*", "server/test-smoke/**/*",
            "app/integration_test/**/*.dart",
        ),
    )
