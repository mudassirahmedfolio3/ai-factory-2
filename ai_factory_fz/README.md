# Agentic SDLC

A CrewAI Flow where specialized AI agents take a product brief through the software lifecycle.
The first target app type is a Flutter e-commerce app with a NestJS + PostgreSQL backend.

## Status

| Milestone | Scope | State |
|---|---|---|
| M0 Foundation | model/agent/profile registries, run workspace, file + sandbox tools, checkpoints | done |
| M1 Discovery | Customer ⇄ Spec writer clarification loop, PRD, **Gate 1** | done |
| M2 Planning & design | Backlog, architecture + OpenAPI + Prisma, **Gate 2**, design system | done |
| M3 Build loop | Scaffold, Backend/Frontend devs per work item with build+test checks, QA fix loop per milestone | done |
| M4 Release | Staging deploy, contract check, Integration pass, Smoke tester, **Gate 3**, production packaging/deploy | done |

## Quick demo

A tiny app (product list, product detail, cart) through every phase, in one sitting:

```bash
uv run kickoff --brief briefs/demo_mini.md --pipeline pipeline.demo
```

`config/pipeline.demo.yaml` caps the scope (4 stories, 6 work items, 2 milestones, 6 API operations,
3 screens) and runs every phase with every gate: it stops for your approval of the PRD, the
architecture and the release. Any pipeline file can set the same `scope:` limits.

## Setup

```bash
uv sync
cp .env.example .env
```

Then choose how the agents call Claude with `CLAUDE_CODE_ENABLE` in `.env`:

| `CLAUDE_CODE_ENABLE` | Path | Needs |
|---|---|---|
| `true` | Headless Claude Code (`claude -p`) on your Claude subscription | `CLAUDE_CODE_OAUTH_TOKEN` (create with `claude setup-token`) |
| `false` or unset | Claude API | `ANTHROPIC_API_KEY` |

The run checks the credential before any agent starts, and stops with a clear message if it is missing.
`config/models.yaml` lists `anthropic/...` models once; the switch decides how they are called.
Other providers (`openai/...`, `gemini/...`) are not affected.

On the Claude Code path each call is isolated: no Claude Code tools, settings, hooks, MCP servers or
CLAUDE.md, and nothing saved. CrewAI still runs the agent loop and tools. Subscription usage limits
apply, and this path is for your own use; if the system ever serves other people, use the API path.

## Running

```bash
uv run kickoff                                   # default brief: briefs/ecommerce_mvp.md
uv run resume <run_id> --milestones M1,M2        # (re)build selected milestones of a run
uv run kickoff --brief briefs/my_app.md --profile flutter_nestjs_ecommerce
uv run resume <run_id>                           # continue a stopped or crashed run
uv run plot                                      # open the flow graph in a browser
SDLC_GATE_MODE=auto uv run kickoff               # approve every gate without asking
crewai run                                       # same as `uv run kickoff`
```

At each gate the run pauses and lists the documents to review. Answer `y` to go on, or `n` with feedback.
The agent then rewrites the artifact using your feedback.

Each run writes to `runs/<run_id>/` (its own git repo, one commit per step):

```
docs/       product_brief, clarifications, prd, backlog, architecture (.md + .json),
            openapi.yaml, schema.prisma, design_system
reports/    run_summary.md  (gate decisions, token usage per agent/model)
state.json  checkpoint used by `resume`
server/ app/  generated code (build phase)
reports/qa_<milestone>_round<n>.md, scaffold_<component>.log
```

## Build phase

For each selected milestone (`build.milestones` in `config/pipeline.yaml`, or `--milestones`):

1. **Scaffold** each component once, with no AI: `nest new`, Prisma setup, `flutter create`, and the
   Dart API client generated from `docs/openapi.yaml`. Steps are in the profile's `components`.
2. **Implement** each work item in dependency order with the component's agent. Then the
   component's **checks** run (backend: `npm run build`, `npm test`; app: `flutter analyze`,
   `flutter test`). If they fail, the output goes back to the agent (`check_fix_attempts` times).
   A passing item is committed to the run's git repo.
3. **QA** each milestone against its acceptance criteria and the API contract. Blocker/major bugs
   go back to the developers; after `qa_fix_rounds` rounds the run stops for you to look.

Items are marked **blocked** (not failed) when their toolchain is missing, the agent needs
something only a human can provide (e.g. an email provider account), or a dependency is blocked.
They are listed with the reason in `reports/run_summary.md`; fix the cause and resume.

**Who writes the code** follows `CLAUDE_CODE_ENABLE`:
- `true`: each job goes to Claude Code with its file tools, confined to the component folder
  (`docs/` is read-only), plus only the allow-listed commands. It runs in `dontAsk` mode, so anything
  else is denied.
- `false`: a CrewAI agent with the `fs_read`/`fs_write`/`fs_list`/`sandbox_exec` tools.

**Where commands run** (`build.sandbox`, or `SDLC_SANDBOX`):
- `docker` (recommended): each command runs in a throwaway container of the runtime image. Your
  user must be able to use Docker: `sudo usermod -aG docker $USER`, then log out and in.
  Missing images are pulled automatically when the build phase starts (first time: a few minutes).
  Claude Code agents cannot run commands in this mode; the checks run for them after each job.
- `local`: commands run on this machine inside the run folder. The toolchains (`npm`, `flutter`,
  `java` for the client generator) must be installed. Code written by the agents, such as tests,
  then runs with your user's rights.

## Release phase

Enable with `phases.release: true` in `config/pipeline.yaml`; it runs after the build phase.

1. **Deployment engineer** writes `server/Dockerfile`, `infra/docker-compose.staging.yml`,
   `infra/staging.env` (test values only), `.github/workflows/ci.yml` and `infra/README.md`, and makes
   sure the API serves its health endpoint and OpenAPI JSON.
2. **Smoke tester** writes a smoke suite (`npm run test:smoke`) for the journeys that are built.
3. **Staging round**: start staging, then run three checks. It then stops staging.
   - **Contract check:** the API's served OpenAPI is compared with `docs/openapi.yaml`, for the built scope.
   - **Integration pass:** the agent reviews config and wiring, fixes glue, and reports bugs.
   - **Smoke suite:** runs against staging.
   Problems go to the Backend developer, then another round, up to `release.fix_rounds`.
4. **Gate 3**: you approve the release. Rejecting it sends your feedback to the developer and
   staging is verified again.
5. **Production**: build the release, write `reports/release_notes.md`, and tag the run repo
   `release-<timestamp>`. If `release.production_command` is set, it is run too (your deploy script).

Staging runs with Docker Compose in `docker` sandbox mode. In `local` mode the API runs as a local
process against the database in `SDLC_STAGING_DATABASE_URL` (use an empty database; migrations are
applied to it).

## Configuration

| File | What it controls |
|---|---|
| `config/models.yaml` | Which model each agent uses, plus fallbacks (any `provider/model` that `crewai.LLM` supports) |
| `config/agents.yaml` | Role, goal, backstory and tools of each agent |
| `config/tasks.yaml` | Task prompts for each phase |
| `config/pipeline.yaml` | Phases on/off, gates on/off, gate mode, loop limits, token budget |
| `profiles/<name>/` | App type: stack, domain entities, conventions per agent, sandbox images and allowed commands |

To support a new app type, copy `profiles/flutter_nestjs_ecommerce/`, change it, and pass `--profile <name>`.

## Layout

```
src/agentic_sdlc/
  flow.py            SDLCFlow: phases, gates (routers), revision loops, checkpoints
  state.py           ProjectState (artifacts, gate history, token usage)
  artifacts/         Pydantic contracts between agents (PRD, Backlog, ArchitectureDoc, DesignSystem)
  crews/             one module per phase; base.py runs a task with structured output + model fallback
  registry/          models.yaml -> LLM, agents.yaml + profile -> Agent, profile loader
  llms/backend.py    CLAUDE_CODE_ENABLE switch and credential checks
  llms/claude_code.py  CrewAI LLM that runs each call through `claude -p`
  build/             scaffold.py (deterministic setup), coders.py (Claude Code / CrewAI workers), loop.py (build + QA loop)
  release/           staging.py (compose or local API process), contract.py (OpenAPI diff), releaser.py
  tools/             path-jailed file tools, sandbox exec in Docker or locally (allow-listed commands)
  gates/human.py     console / auto approval
  workspace.py       runs/<run_id>/ layout, git commits, state save
```

## Tests

```bash
uv run pytest
```

The tests make no LLM calls. They cover flow routing (approve, reject, rejection limit, budget stop, resume),
the real Crew path with a scripted fake LLM (structured output, guardrail retry, model fallback),
artifact validation, registries, the path jail and the sandbox allow-list.

## Debugging runs

Use CrewAI traces to see every agent decision, LLM call and token count: `crewai traces enable`, then run.
