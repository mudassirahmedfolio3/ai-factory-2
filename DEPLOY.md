# Deploy AI Factory (free tier)

The factory is two parts: a React UI (static) and a Python FastAPI backend (always-on). Netlify alone cannot run the backend.

## Recommended stack

| Part | Host |
|------|------|
| Frontend (`AI-Factory-React`) | Netlify or Cloudflare Pages |
| Backend (`ai_factory_ui/api`) | Render (free tier) |

## Backend (Render)

1. Connect this repo on Render.
2. Use root `render.yaml` or `Dockerfile`.
3. Environment variables:
   - `LLM_PROVIDER=openai` (or `groq` — not `cursor_cli` on cloud)
   - `CORS_ORIGINS=https://your-site.netlify.app`
   - Optional server fallback: `OPENAI_API_KEY` / `GROQ_API_KEY`

Health check: `GET /health`

## Frontend (Netlify)

1. New site from Git (uses `netlify.toml`).
2. Set `VITE_API_URL=https://your-api.onrender.com` (no trailing slash).
3. Optional: `BACKEND_URL` same value for `/api/*` redirects.

Local dev: leave `VITE_API_URL` unset — Vite proxies `/api` to `localhost:8000`.

## API keys

Set keys in `ai_factory/.env` (see `.env.example`) — e.g. `CURSOR_API_KEY`, `OPENAI_API_KEY`, or `GROQ_API_KEY` depending on `LLM_PROVIDER`.

## Token usage

The dashboard footer shows live LLM call count and estimated tokens during a run.
