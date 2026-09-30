# Agentic SDLC

A CrewAI Flow where specialized AI agents take a product brief through the software lifecycle.
The first target app type is a Flutter e-commerce app with a NestJS + PostgreSQL backend.

## Status

| Milestone | Scope | State |
|---|---|---|
| M0 Foundation | model/agent/profile registries, run workspace, file + sandbox tools, checkpoints | done |
| M1 Discovery | Customer ⇄ Spec writer clarification loop, PRD, **Gate 1** | done |
| M2 Solution & plan | Architect (architecture, OpenAPI, Prisma) → UI/UX (design system) → Project manager (work breakdown + estimates, checked for coverage) → **Gate 2** | done |
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

## Lifecycle order

```
Customer ⇄ Spec writer ─► Gate 1 (PRD)
  ─► Architect ─► UI/UX designer ─► Project manager (WBS + draft estimates)
  ─► Backend/Frontend/Deployment developers re-estimate their items ─► PM reconciles big gaps
  ─► Gate 2 (solution + plan)
  ─► Build: developers per work item (checks) ─► QA per milestone
  ─► Release: staging, contract check, integration pass, smoke + device tests ─► Gate 3 ─► production
```

Estimates are bottom-up: after the Project manager drafts the plan, each developer agent
re-estimates the items it will build (one call per agent, no tools). A small gap adopts the
builder's number; a big gap (`planning.big_gap_points` / `big_gap_ratio`) is reconciled by the PM,
between the two numbers, with a reason. `docs/backlog.md` shows PM, developer and final points,
and lists the disagreements as the highest estimate risk. Switch off with `planning.estimation_review: false`.

The Project manager plans the *solution*: each work item links to the API operations, data models
and screens it builds, with points, risk, confidence and a rationale. The plan is rejected (and
redone) unless every operation, model and screen is covered and app items depend on the backend
items they call. `docs/backlog.md` shows the plan with totals and the critical path. Rejecting
Gate 2 rewrites architecture, design and plan together with your feedback.

## Architect guardrails

The Architect's design is checked in code before anyone sees it; a failing design goes back to the
Architect with the list of problems (up to 2 retries, then the run stops with the reasons).

| Group | Rules |
|---|---|
| Stack and platform | A1 no technology outside the profile's stack, core stack used · A2 Flutter mobile app only |
| API contract | B1 module endpoints match `openapi.yaml` · B2 health endpoint · B3 `/api/v1` prefix · B4 one shared error schema · B5 typed responses · B6 every operation secured or explicitly public |
| Data model | C1 module entities exist in `schema.prisma` · C2 money fields are `Int` (cents) · C3 `@id`, `createdAt`, `updatedAt` |
| Decisions and security | D1 at least 3 complete ADRs · D2 authentication, input validation, secrets covered · D3 no secrets in the design |

Rules live in `src/agentic_sdlc/guardrails/architecture.py`; the facts they check against (stack,
platform, money fields) in the profile's `guardrails:` section; which rules are on in each pipeline's
`guardrails.architect` list. A new profile brings its own stack and platform rules.

## Agent guardrails

The other agents' work is checked too (code checks; a failing result goes back to the same agent):

| Rule | Agent | Checks |
|---|---|---|
| DV1 | Backend / Frontend / Deployment | no deleted test files, no fewer test cases, no newly skipped tests |
| DV2 | Backend / Frontend / Deployment | no real-looking secrets in changed files (placeholders and test values are fine) |
| DV3 | Backend / Frontend / Deployment | changes stay in the item's component folder; contract copies equal `docs/` |
| QA1 / QA2 | QA engineer, Integration pass | verdict matches the bugs; bugs name real work items with steps, expected, actual |
| DE1 | Deployment engineer | Dockerfile runs as non-root and uses the build toolchain's Node major |
| ST1 | Smoke tester | smoke suite has enough journeys, uses `SMOKE_BASE_URL`, no app imports or mocks; device suite has real tests |
| CU1 | Customer | every clarification question is answered |
| UX1 | UI/UX designer | hex colours, unique routes, `onX`/`X` text contrast at least WCAG AA (4.5:1, computed) |

A work item that still breaks a rule after its retries is failed and its changes are discarded, so
nothing rejected is ever committed. Rules are switched on in each pipeline's `guardrails.agents`.

## Machine setup (once)

```bash
uv sync
cp .env.example .env          # set CLAUDE_CODE_ENABLE=true and CLAUDE_CODE_OAUTH_TOKEN (claude setup-token)
uv run setup                  # Docker, docker group, toolchain images, Android emulator
uv run preflight --pipeline pipeline.demo   # optional: check without starting a run
```

`uv run setup` does everything itself except what needs you: your sudo password (installing Docker,
adding you to the `docker` group) and accepting the Android SDK licence. No logout is needed after
joining the `docker` group: the pipeline notices the old session and runs Docker through `sg docker`.
Every run also starts with the same preflight check and stops before any agent runs (no tokens spent)
if something is missing, with the fix to apply.

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
