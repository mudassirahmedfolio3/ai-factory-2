# AI Factory

CrewAI Flow that orchestrates the **full SDLC plus Harness-style software delivery** for e-commerce Flutter mobile apps: discovery, design, build, code review, security scanning, QA, governed deployment, SRE verification, and client approval loops.

## Prerequisites

- Python 3.10–3.13 (via `uv python install 3.12`)
- [uv](https://docs.astral.sh/uv/) and CrewAI CLI (`uv tool install crewai`)
- API key in `.env` (never commit real keys) — OpenAI, Groq, or Cursor via proxy

## Setup

```powershell
cd ai_factory
crewai install
copy .env.example .env   # then edit .env
```

## LLM providers (switch via `.env`)

| Provider | When to use | Required |
|----------|-------------|----------|
| `openai` | Production (default later) | `OPENAI_API_KEY=sk-...` |
| `groq` | Free interim | `GROQ_API_KEY` from [console.groq.com](https://console.groq.com) |
| `cursor_proxy` | Temporary Cursor subscription | `CURSOR_API_KEY` + local proxy |

### Temporary: Cursor key (until OpenAI arrives)

Cursor `crsr_...` keys are **not** OpenAI-compatible directly. CrewAI talks to them through a local proxy:

**One-time** — authenticate Cursor CLI (if not done):

```powershell
agent login
# Or ensure CURSOR_API_KEY is set in .env (already configured)
```

**Terminal 1** — start proxy (keep running):

```powershell
cd ai_factory
.\scripts\start-cursor-proxy.ps1
```

If the proxy health check fails, run `agent login` and restart the script.

**Terminal 2** — run factory:

```powershell
cd ai_factory
crewai run
```

`.env` for Cursor proxy:

```env
LLM_PROVIDER=cursor_proxy
CURSOR_API_KEY=crsr_your-key-here
CURSOR_PROXY_BASE_URL=http://localhost:4646/v1
CURSOR_PROXY_MODEL=auto
```

### Switch back to OpenAI later

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
LLM_STRONG_MODEL=gpt-4o
LLM_FAST_MODEL=gpt-4o-mini
```

No code changes needed — all crews read from `llm_config.py`.

## Run

```powershell
crewai run
```

Generated artifacts are written to `artifacts/`; runnable Flutter apps land in `apps/{run_id}/`.

### Browser preview (instead of cloud deploy)

No Flutter or emulator required. The **Browser** step generates a mobile-style HTML demo under `apps/{run_id}/` and opens it in your default browser.

Re-open the latest preview:

```powershell
cd ai_factory
.\scripts\run-preview.ps1
```

## Flow overview

### Product SDLC (left side)
1. **Discovery** — PM + E-commerce Advisor produce PRD
2. **Simulated Client** — PRD approval gate
3. **Design** — Architect + Flutter Engineer
4. **Sprint planning** — Scope and task breakdown per release

### Delivery pipeline (Harness-style, right side)
5. **Build** — Flutter implementation
6. **Code Review Worker Agent** — PR-style quality/security review
7. **AppSec Worker Agent** — SCA, SAST, secrets, mobile OWASP
8. **QA** — Test plan and release readiness
9. **Release** — Changelog and release notes
10. **Governance gate** — L1/L2/L3 risk-based autonomy before deploy
11. **Browser preview** — mobile-style HTML demo at `apps/{run_id}/`, opens in your browser
12. **Simulated Client** — Release demo approval
13. **Change requests** — Minor → sprint; major → discovery

## Risk-based autonomy (Harness-style)

| Level | Behavior |
|-------|----------|
| **L1** | Agents prepare only; deploy always requires explicit approval |
| **L2** | Default — simulated ops approver gates deploy (human-in-the-loop) |
| **L3** | Auto-deploy when security, QA, and code review all pass |

Set via kickoff inputs or trigger payload:

```json
{
  "autonomy_level": "L2",
  "deploy_environment": "staging"
}
```

## Software Delivery Knowledge Graph

A lightweight knowledge graph accumulates project context across phases (services, releases, artifacts, reviews, scans, pipelines). Written to `artifacts/knowledge_graph.json` and injected into worker agent prompts.

## Audit trail

Governance events are appended to `artifacts/audit/` (JSONL) — approvals, scan results, deploy decisions.

## Checkpointing

```powershell
crewai checkpoint list .checkpoints
crewai checkpoint
```

## Agents (11 roles)

| Agent | Role |
|-------|------|
| Product Manager | Discovery, Sprint Planning, Release, Change Request |
| E-commerce Domain Advisor | Discovery, Change Request |
| Technical Architect | Design, Build |
| Flutter Mobile Engineer | Design, Sprint Planning, Build |
| Code Review Worker Agent | Autonomous PR review |
| AppSec Worker Agent | Security scanning + remediation |
| QA Engineer | QA |
| Release Engineer | Release prep |
| DevOps Engineer | CI/CD pipeline + deploy runbook |
| SRE Engineer | Post-deploy verification |
| Simulated Client / Ops | PRD, deploy, and release approval gates |

## Knowledge playbooks

`src/ai_factory/knowledge/`:

- `ecommerce_patterns.md`
- `flutter_conventions.md`
- `release_checklist.md`
- `ci_cd_pipelines.md`
- `security_scanning.md`
- `governance_policies.md`

## Project layout

```
src/ai_factory/
├── main.py                 # Master SDLC + delivery Flow
├── models.py               # State, approvals, governance
├── knowledge_graph.py      # Delivery knowledge graph
├── governance.py           # L1/L2/L3 policy gate
├── utils.py                # Artifacts, audit, graph sync
├── knowledge/
└── crews/
    ├── discovery_crew/
    ├── design_crew/
    ├── sprint_planning_crew/
    ├── build_crew/
    ├── code_review_crew/   # NEW
    ├── security_crew/      # NEW
    ├── qa_crew/
    ├── release_crew/
    ├── deployment_crew/    # NEW
    └── change_request_crew/
```
