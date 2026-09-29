# AI Factory Console

Presentation layer for the AI Factory SDLC pipeline — live monitoring and historical run review.

## Structure

```
ai_factory_ui/
├── api/          FastAPI backend (reads artifacts, starts runs, SSE events)
└── web/          React + Vite dashboard
```

The factory writes `ai_factory/artifacts/run_state.json` and audit logs; this UI reads them.

## Prerequisites

- Python 3.12+ with `ai_factory` dependencies installed (`cd ai_factory && crewai install`)
- Node.js 18+
- Cursor CLI installed (`agent login` or `CURSOR_API_KEY` in `ai_factory/.env` with `LLM_PROVIDER=cursor_cli`)

## Start the console

**One command (Windows)**

```powershell
cd ai_factory_ui
.\scripts\start-console.ps1
```

**Or manually — Terminal 1 — API**

```powershell
cd ai_factory_ui\api
..\..\ai_factory\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend**

```powershell
cd ai_factory_ui\web
npm install
npm run dev
```

Open **http://localhost:5173**

## Usage

1. Click **+ New Run** and pick **Basic** (~10 min), **Basic+** (~25 min), **Standard** (~60 min), or **Full** (~2 hr)
2. Watch the pipeline board update as phases complete
3. Activity feed shows code review, QA, security, and approval events
4. Artifact panel shows PRD, review reports, QA output, etc.
5. Use **Run History** dropdown to review past archived runs

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_FACTORY_ROOT` | `../ai_factory` | Path to the CrewAI factory project |
