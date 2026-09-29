# AI Factory Console

Presentation layer for the AI Factory SDLC pipeline — live monitoring and run control.

## Structure

```
ai_factory_ui/
├── api/                    FastAPI backend (reads artifacts, starts runs, SSE events)
└── scripts/start-console.ps1

AI-Factory-React/           Primary frontend (release-1.0.0+) — Figma UI wired to api/
ai_factory_ui/web/          Legacy React console (still in repo, not started by default)
```

The factory writes `ai_factory/artifacts/run_state.json` and audit logs; the API reads them.

## Prerequisites

- Python 3.12+ with `ai_factory` dependencies installed (`cd ai_factory && crewai install`)
- Node.js 18+ and pnpm (or npm)
- Cursor CLI or API key in `ai_factory/.env` (`LLM_PROVIDER=cursor_cli`)

## Start the console

**One command (Windows)**

```powershell
cd ai_factory_ui
.\scripts\start-console.ps1
```

Starts the API on **http://127.0.0.1:8000** and **AI-Factory-React** on **http://127.0.0.1:5173**.

**Or manually — Terminal 1 — API**

```powershell
cd ai_factory_ui\api
..\..\ai_factory\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — AI-Factory-React**

```powershell
cd AI-Factory-React
pnpm install
pnpm dev
```

## Usage

1. Open **http://127.0.0.1:5173**
2. Enter a brief, pick complexity, and click **Start AI Factory**
3. Watch the nine-stage dashboard update via SSE as the CrewAI pipeline runs
4. View PRD artifacts and browser preview when the run completes

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_FACTORY_ROOT` | `../ai_factory` | Path to the CrewAI factory project |
