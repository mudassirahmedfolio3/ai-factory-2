# DeepEval for agentic_sdlc

Evaluations that check the pipeline's output against the client brief (`../briefs/`).
This folder is its own `uv` project, so it does not touch the main project's dependencies.

**Status:** DeepEval 4.2.7 is installed. There is one `test_<agent>.py` per agent (11 agent files, 33 tests) plus one end-to-end flow file (12 tests). They skip until a pipeline run exists, so they have not been run against real output yet.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10-3.13 (3.12 is pinned in `.python-version`).

```bash
cd ai_factory_fz/deepeval
uv sync
uv run deepeval --version        # prints the installed version
```

## Judge model credentials

DeepEval metrics use an LLM as the judge. By default that is OpenAI, so create `.env` here
(it is git-ignored):

```env
OPENAI_API_KEY=sk-...
```

To judge with Claude or another provider, set it with `uv run deepeval set-<provider>` or
pass a custom model class to each metric. See https://deepeval.com/docs/metrics-introduction.

## Running evaluations

Per-agent tests are in `agent_test_writeup/`; the end-to-end flow test is in `flow_test_writeup/`:

```bash
uv run deepeval test run agent_test_writeup/test_<agent>.py     # one agent
uv run deepeval test run agent_test_writeup/                    # all agents
uv run deepeval test run flow_test_writeup/test_end_to_end_flow.py  # whole flow
```

Results print in the terminal. Run `uv run deepeval login` if you want them in Confident AI.

## Input: a pipeline run

The pipeline writes its artifacts to `../runs/<run_id>/docs/` (PRD, backlog, architecture,
OpenAPI). Produce a run first, for example:

```bash
cd ..
uv run kickoff --brief briefs/demo_mini.md --pipeline pipeline.demo
```

Or let the scripts in `run/` create the run and score it in one command (see `run/README.md`):

```bash
uv run python run/run_from_briefs.py --brief demo_mini
```

## Tests per agent

| File | Judges |
|---|---|
| `test_customer.py` | `docs/clarifications.md` vs the brief |
| `test_spec_writer.py` | `docs/prd.md` vs the brief |
| `test_project_manager.py` | `docs/backlog.md` vs the PRD |
| `test_architect.py` | architecture, OpenAPI, Prisma vs the PRD |
| `test_ui_ux_designer.py` | `docs/design_system.md` vs the PRD |
| `test_backend_developer.py` | `server/src` vs the OpenAPI contract |
| `test_frontend_developer.py` | `app/lib` vs design system and contract |
| `test_qa_engineer.py` | `reports/qa_*.md` vs the PRD |
| `test_deployment_engineer.py` | Dockerfile, compose, CI vs the architecture |
| `test_integration_pass.py` | `reports/release_round*.md` vs the contract |
| `test_smoke_tester.py` | smoke / journey tests vs the PRD |
| `test_end_to_end_flow.py` | whole run, anchored on the spec writer's PRD: PRD vs the original brief, then every other agent's output vs the PRD, in pipeline order |

The files in the table are in `agent_test_writeup/` except the last one, which is in `flow_test_writeup/`. `common.py` (in this folder) finds the run (`DEEPEVAL_RUN_DIR=runs/<run_id>`, default: newest in `../runs`) and holds the
LLM-judge helper. Each metric is a DeepEval `GEval` with a threshold of 0.6.

## Next steps

- Decide what to evaluate (documents vs. code vs. per-agent behaviour).
- Add test files and metrics in `agent_test_writeup/` or `flow_test_writeup/`. Each folder needs its own `conftest.py`.
