# AI Factory (React Frontend)

Figma-designed intake and nine-stage dashboard, wired to the live AI Factory backend on `release-1.0.0`.

## Run (live mode)

Requires Node 18+, pnpm (or npm), and the FastAPI backend running on port 8000.

**All-in-one (recommended)**

```powershell
cd ai_factory_ui
.\scripts\start-console.ps1
```

**Or manually**

Terminal 1 — API:

```powershell
cd ai_factory_ui\api
..\..\ai_factory\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Terminal 2 — this frontend:

```sh
cd AI-Factory-React
pnpm install
pnpm dev
```

Open **http://127.0.0.1:5173**. Vite proxies `/api` → `http://127.0.0.1:8000`.

Production: `pnpm build`, then `pnpm preview`. Tests: `pnpm test`.

## Live workflow

1. Enter requirements or use **Random brief**
2. Pick run complexity (Basic / Basic+ / Standard / Full)
3. **Start AI Factory** — triggers a real CrewAI run via `POST /api/runs`
4. Dashboard updates live via SSE (`/api/runs/{run_id}/events`)
5. Nine UI stages map to backend pipeline steps (discovery → browser)
6. **Project brief** modal loads real PRD from artifacts when available
7. **Delivery** shows the built browser preview in the phone frame when ready

## Key files

| File | Role |
|------|------|
| `src/api.js` | REST + SSE client for FastAPI backend |
| `src/phaseMap.js` | Maps 9 UI stages ↔ backend `pipeline_steps` |
| `src/runSync.js` | SSE connection helper |
| `src/App.jsx` | Intake + dashboard |
| `src/Phone.jsx` | Mobile frame with optional `previewUrl` iframe |
| `src/engine.js` | File validation only |

## Notes

- File attachments are listed in the brief text; binary upload is not yet supported by the API.
- UAT approval is read-only — the pipeline handles simulated client gates.
- Ensure `CURSOR_API_KEY` (or other LLM provider) is set in `ai_factory/.env`.
