"""DeepEval checks for the `smoke_tester` agent, judged on the artifacts it produces in a pipeline run.

Criteria come from the agent's task rules in config/tasks.yaml and its goal in config/agents.yaml."""

from common import brief, judge, original_brief, read, read_glob  # noqa: F401


def test_smoke_suite_covers_built_journeys():
    judge(
        "smoke_suite_covers_built_journeys",
        criteria='The smoke suite uses plain HTTP requests against SMOKE_BASE_URL (SMOKE_BASE_URL plus the contract path) without importing application code, covers a handful of built journeys end to end (health, sign up, sign in, browse, add to cart) with unique test data per run, and has clear failure messages.',
        input_text=read("docs/prd.md"),
        output_text=read_glob("server/test/**/*smoke*", "server/smoke/**/*", "server/test-smoke/**/*"),
    )


def test_device_tests_drive_real_app():
    judge(
        "device_tests_drive_real_app",
        criteria="The on-device tests use Flutter's integration_test package to drive the real app like a user (open the product list, open a product, add it to the cart, open the cart, change a quantity and check the total), do not mock the network, wait with pumpAndSettle or timeouts, and keep each test independent of the others.",
        input_text=read("docs/prd.md"),
        output_text=read_glob("app/integration_test/**/*.dart"),
    )
