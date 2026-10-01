# Run the eval pipelines

Each pipeline does two steps: **(1)** create an SDLC run with `uv run kickoff` in `ai_factory_fz`,
then **(2)** score that run with the DeepEval tests. Gates are auto-approved (`SDLC_GATE_MODE=auto`).

| Pipeline | Script | Brief comes from | SDLC config used |
|---|---|---|---|
| 1. Briefs | `run_from_briefs.py` | a file in `ai_factory_fz/briefs/` | `pipeline.demo` (full: build + release, Docker + emulator) |
| 2. Text | `run_from_text.py` | text passed in (React app later) | `pipeline.ui` (discovery to build, local sandbox, no release) |

Change the SDLC config with `--pipeline <name>` (any file in `ai_factory_fz/config/`, without `.yaml`).

## Before you start

- `ai_factory_fz/.env` has a Claude credential (`ANTHROPIC_API_KEY`, or `CLAUDE_CODE_ENABLE=true` + `CLAUDE_CODE_OAUTH_TOKEN`).
- `deepeval/.env` has `OPENAI_API_KEY` (the judge).
- Run every command below from `ai_factory_fz\deepeval` (this folder's parent).

Add `--dry-run` to any command to print what it would run without spending anything.

## Pipeline 1: from the briefs folder

```powershell
uv run python run/run_from_briefs.py --list                       # show available briefs
uv run python run/run_from_briefs.py --brief demo_mini            # run + score everything
uv run python run/run_from_briefs.py --brief ecommerce_mvp --pipeline pipeline
```

## Pipeline 2: from text

```powershell
uv run python run/run_from_text.py --text "A mobile shop where users browse and buy shoes."
uv run python run/run_from_text.py --file C:\path\to\my_brief.md
```

For the React app (later): post one JSON object to stdin.

```powershell
'{"brief": "A bakery ordering app", "name": "bakery"}' | uv run python run/run_from_text.py --stdin-json
```

The text is saved to `run/inputs/<run_id>.md` (git-ignored) and passed to the same kickoff as pipeline 1.

## Options (both pipelines)

| Option | Effect |
|---|---|
| `--agent <name>` | Score only one agent: `customer`, `spec_writer`, `project_manager`, `architect`, `ui_ux_designer`, `backend_developer`, `frontend_developer`, `qa_engineer`, `deployment_engineer`, `integration_pass`, `smoke_tester` |
| `--flow-only` | Score only the end-to-end flow test |
| `--no-tests` | Create the run, skip scoring |
| `--skip-run <run_id>` | Do not create a run; score an existing one in `ai_factory_fz\runs\` |
| `--profile <name>` | SDLC profile (default: the project's default) |
| `--dry-run` | Print the commands only |

Examples:

```powershell
uv run python run/run_from_briefs.py --brief demo_mini --agent spec_writer
uv run python run/run_from_briefs.py --skip-run 20261001-120000-eval-demo-mini --flow-only
uv run python run/run_from_text.py --text "..." --no-tests
```

## Notes

- Tests for agents whose phase did not run are skipped, not failed. `pipeline.ui` has no release phase, so
  the deployment, integration and smoke tests skip.
- If the SDLC run stops early, the script warns and still scores what exists. Continue it with
  `uv run resume <run_id>` in `ai_factory_fz`, then `--skip-run <run_id>`.
- A full run uses many tokens (`pipeline.demo` caps at 1.5M uncached tokens; `pipeline.ui` has no cap).
- You can still run the test files directly; see `../README.md`.
