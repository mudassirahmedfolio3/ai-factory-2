# DeepEval for agentic_sdlc

Evaluations that check the pipeline's output against the client brief (`../briefs/`).
This folder is its own `uv` project, so it does not touch the main project's dependencies.

**Status:** DeepEval 4.2.7 is installed. There is one `test_<agent>.py` per agent (11 agent files, 33 tests) plus one end-to-end flow file (12 tests), 45 tests in total. They have been run end to end only against the hand-written sample run `../runs/sample-manual` (see [Trying the tests without a pipeline run](#trying-the-tests-without-a-pipeline-run)), not yet against real pipeline output. Each test skips when the files it needs are missing.

## Quick start (Windows PowerShell)

```powershell
cd ai_factory_fz\deepeval
uv sync                                   # once
$env:PYTHONUTF8=1                         # stops the Windows console crashing on emoji

# Which run to score. Without it, the newest folder in ..\runs is used.
$env:DEEPEVAL_RUN_DIR="..\samples\20261002-120919"

uv run pytest flow_test_writeup/test_end_to_end_flow.py -v    # the whole flow: 12 tests, about 2 minutes
uv run pytest agent_test_writeup -v                           # every agent: 33 tests, about 5 minutes
uv run pytest agent_test_writeup/test_architect.py -v         # one agent
```

- Every test is one judge call (Claude if `ANTHROPIC_API_KEY` is in `.env`), so a run costs tokens. A test passes at a score of 0.6 or above.
- The run folder needs the files the tests read (see [Input: a pipeline run](#input-a-pipeline-run)). A test whose files are missing is **skipped**, not failed. The sample folder above has only `docs/`, so about 20 of the 45 tests run.
- Each run prints a pass/fail table with a confidence per agent and writes `eval_report_flow.*`, `eval_report_agents.*` or `eval_report.*` (`.md`, `.json`, `.html`) into the run folder.
- To start the Project Manager process after the report, set `$env:DEEPEVAL_REMEDIATE=1` first (see [Remediation](#remediation-project-manager)).
- `uv run deepeval test run <path>` works too, but on Windows it can crash on emoji output; plain `pytest` is the verified way.
- Test the evaluation code itself (no model calls, no tokens): `uv run pytest remediation/tests unit_tests`.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10-3.13 (3.12 is pinned in `.python-version`).

```bash
cd ai_factory_fz/deepeval
uv sync
uv run deepeval --version        # prints the installed version
```

## Judge model credentials

Every test is one LLM-judge call. Create `.env` in this folder (it is git-ignored) with **one** of:

```env
# Option A: OpenAI as the judge (DeepEval's default)
OPENAI_API_KEY=sk-...

# Option B: Claude as the judge (used automatically when OPENAI_API_KEY is not set)
ANTHROPIC_API_KEY=sk-ant-...
```

`common.py` picks the judge in `judge_model()`: OpenAI if `OPENAI_API_KEY` is set, otherwise Claude
if `ANTHROPIC_API_KEY` is set. Set `DEEPEVAL_JUDGE_MODEL` to change the Claude model
(default `claude-sonnet-5-5`). Claude is called without a `temperature` because current models reject it.

Other providers: `uv run deepeval set-<provider>`, see https://deepeval.com/docs/metrics-introduction.

## Input: a pipeline run

The tests read one run folder, `../runs/<run_id>/`. Besides `docs/`, they use these files:

| Path in the run | Used by |
|---|---|
| `state.json` (holds the original `brief`) | customer, end-to-end flow |
| `docs/product_brief.md`, `docs/clarifications.md` | customer, spec writer, flow |
| `docs/prd.md`, `docs/backlog.md` | spec writer, project manager, most others |
| `docs/architecture.md`, `docs/openapi.yaml`, `docs/schema.prisma` | architect, backend, deployment, integration |
| `docs/design_system.md` | UI/UX designer, frontend |
| `server/src/**/*.ts`, `server/Dockerfile` | backend, deployment |
| `app/lib/**/*.dart`, `app/test/**/*.dart` | frontend |
| `reports/qa_*.md`, `reports/release_round*.md` | QA, integration pass |
| `infra/docker-compose.staging.yml`, `infra/staging.env`, `infra/README.md`, `.github/workflows/ci.yml` | deployment |
| `server/smoke/**`, `server/test-smoke/**`, `server/test/**/*smoke*`, `app/integration_test/**/*.dart` | smoke tester |

Choose the run with `DEEPEVAL_RUN_DIR` (a path, for example `../runs/<run_id>` when you run from this folder).
Without it, the newest folder in `../runs` is used. `SDLC_RUNS_DIR` moves the whole runs folder.

To create a run, `ai_factory_fz/.env` needs a Claude credential (`ANTHROPIC_API_KEY`, or
`CLAUDE_CODE_ENABLE=true` + `CLAUDE_CODE_OAUTH_TOKEN`). Then:

```bash
cd ..
uv run kickoff --brief briefs/demo_mini.md --pipeline pipeline.demo
```

Or let the scripts in `run/` create the run and score it in one command (see `run/README.md`):

```bash
uv run python run/run_from_briefs.py --brief demo_mini
```

**Cost:** a full `pipeline.demo` run is capped at 1.5M uncached tokens, and scoring adds about 45 judge calls.
Add `--dry-run` to the `run/` scripts to see the commands without spending anything.

## Running evaluations

Per-agent tests are in `agent_test_writeup/`; the end-to-end flow test is in `flow_test_writeup/`:

```bash
uv run deepeval test run agent_test_writeup/test_<agent>.py     # one agent
uv run deepeval test run agent_test_writeup/                    # all agents
uv run deepeval test run flow_test_writeup/test_end_to_end_flow.py  # whole flow
```

Results print in the terminal. Run `uv run deepeval login` if you want them in Confident AI.

### Windows notes

- `deepeval test run` can crash while printing an emoji (`UnicodeEncodeError`). Set `PYTHONUTF8=1`
  (PowerShell: `$env:PYTHONUTF8=1`) or run the tests with plain pytest, which is what has been verified:
  ```powershell
  $env:PYTHONUTF8=1; $env:DEEPEVAL_RUN_DIR="..\runs\<run_id>"
  uv run pytest agent_test_writeup/test_architect.py -v
  ```
- `portalocker` is a dependency so DeepEval can lock its cache file. Without it you get a "Shared locks on Windows" warning.

## Trying the tests without a pipeline run

`../runs/sample-manual/` is a hand-written run for a small shop app ("ShopEase Mini"). Every file in it starts with
`SAMPLE FILE: ... NOT output of the pipeline`. It is git-ignored with the rest of `runs/`. Use it to check that the
tests and the judge work, and delete it once you have a real run. Passing or failing on it says nothing about the real agents.

## Tests per agent

| File | Judges |
|---|---|
| `test_customer.py` | `docs/product_brief.md` vs the original brief; `docs/clarifications.md` vs the product brief |
| `test_spec_writer.py` | `docs/prd.md` vs `docs/product_brief.md` |
| `test_project_manager.py` | `docs/backlog.md` vs the PRD |
| `test_architect.py` | architecture, OpenAPI, Prisma vs the PRD |
| `test_ui_ux_designer.py` | `docs/design_system.md` vs the PRD |
| `test_backend_developer.py` | `server/src` vs the OpenAPI contract and architecture |
| `test_frontend_developer.py` | `app/lib` (and `app/test`) vs design system and contract |
| `test_qa_engineer.py` | `reports/qa_*.md` vs the PRD |
| `test_deployment_engineer.py` | Dockerfile, compose, CI, runbook vs the architecture |
| `test_integration_pass.py` | `reports/release_round*.md` vs the contract |
| `test_smoke_tester.py` | smoke / journey tests vs the PRD |
| `test_end_to_end_flow.py` | whole run, anchored on the spec writer's PRD: PRD vs the original brief, then every other agent's output vs the PRD, in pipeline order |

The files in the table are in `agent_test_writeup/` except the last one, which is in `flow_test_writeup/`.
`common.py` (in this folder) finds the run and holds the LLM-judge helper. Each metric is a DeepEval `GEval` with a threshold of 0.6.

## Skips and failures

- A test **skips** when a file it reads is missing, for example the deployment tests on a run that has no release phase.
- `test_every_agent_left_output` in the flow file **fails** if any agent produced nothing.
- A test **fails** when the judge scores below 0.6; the failure message contains the judge's reason.

## Reports

Every run writes its report into the run folder: `eval_report_agents.*` (agent tests only), `eval_report_flow.*`
(end-to-end flow only), or `eval_report.*` (both), each as `.md`, `.json` and a self-contained `.html`. They hold the
pass/fail result, a confidence per agent, the judge's reasons, and a written analysis (why the score, strengths,
gaps, what to improve). Each report starts with a six-step remediation status block.

## Remediation (Project Manager)

When the report is written, a Project Manager process can validate the findings and plan the fixes. It is **opt-in**:

```powershell
$env:DEEPEVAL_REMEDIATE=1      # then run the tests as usual; the report triggers the process
```

or by hand, from `ai_factory_fz` (the Project Manager needs the pipeline environment, so use that project's `uv`):

```powershell
uv run python deepeval/remediate.py run     --run-dir runs/<id> --report runs/<id>/eval_report_flow.json
uv run python deepeval/remediate.py status  --run-id <id>
uv run python deepeval/remediate.py approve --run-id <id>
```

Stage 1 covers steps 1-2 of the six: **1** DeepEval report, **2** Project Manager triage and backlog. The Project
Manager classifies every finding against the run's own files (a failed test is not proof of a defect), groups findings
by root cause, and writes a prioritised backlog (P0-P3) with owners from the existing agents. It **always stops for
your approval** (`awaiting approval`): read `runs/<id>/remediation/backlog.md`, edit `backlog.json` if you want
(reject a task by setting its `status` to `rejected` and giving its findings a disposition), then run `approve`.
Steps 3-6 (fixes, integration pass, QA and smoke tests, re-evaluation with a before/after comparison) are not built yet.

Everything is saved under `runs/<id>/remediation/`: `status.json`, `baseline/eval_report.json` (the first report, never
overwritten), `findings.json`, `triage.json`, `backlog.json` / `backlog.md`, and an append-only `history.jsonl`. A re-run
resumes where it stopped and makes no model call for work that is already saved.

All code is in `remediation/` (plus `remediate.py`, `remediation_trigger.py`, `eval_report_html.py`). The two prompts are
`remediation/prompts/tasks.yaml` and are merged in memory, so the pipeline's own `config/tasks.yaml` is untouched.
Tests: `uv run pytest remediation/tests unit_tests` (no model calls, no CrewAI needed).

## Adding tests

Add test files and metrics in `agent_test_writeup/` or `flow_test_writeup/`. Each folder needs its own `conftest.py`
that puts this folder on `sys.path` so `from common import ...` works. Use `judge(name, criteria, input_text, output_text)`
from `common.py` so the judge choice stays in one place.
