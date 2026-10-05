# AI Factory FZ — Run Stall & Failure Playbook

**Scope:** Flutter + NestJS client-demo runs (e.g. `20261004-043044` lighting-retail-mvp, `20261003-044724` ShopEase)  
**Updated:** 2026-10-04  

This document lists reasons factory runs **stop, fail, or appear stuck**, based on observed runs under `ai_factory_fz/runs/`.

---

## A. Real blockers (work stops or is discarded)

### 1. `server/` vs `apps/api/` + DV3 guardrails (lighting M2)

- **Profile** scopes backend work to **`server/`** (`flutter_nestjs_ecommerce`).
- **WI-001 / architect** often places NestJS at **`apps/api/`**.
- Agents edit `apps/api/...` → **DV3: outside component (server/)** → changes **discarded** after ~3 attempts.
- A **`server` → `apps/api` junction** made every path show as `apps/api/...`, so “fix in server/” could not pass guardrails.
- **Signal:** WI-007 **failed**; WI-008–012 **blocked**; run **completed** with M2 **partial**.
- **Mitigation (repo):** `workspace_layout.py` resolves backend to `apps/api` when appropriate; contract copies include `apps/api/` paths (commit `6bb017a`).

### 2. Backend scaffold on missing/empty `server/`

- Scaffold step: `npx @nestjs/cli new server` when `server/package.json` is missing.
- API already lives under **`apps/api/`** → long-running or hung **`npx`/`cmd`** child.
- **Signal:** Worker alive, high CPU, no new transcript lines.

### 3. Dependency cascade

- Build is **sequential**. One **failed** or **blocked** WI blocks dependents (e.g. WI-007 failed → WI-008–012 blocked).
- **Signal:** Run finished but milestone incomplete; not necessarily a hung worker.

### 4. Guardrail / check retry budget exhausted

- Loop: agent → DV1/DV2/DV3 → component checks (`npm test`, `flutter test`, etc.).
- After **~3 attempts**, **`discard_changes`** and WI marked **failed**.
- **Signal:** `still failing after N attempt(s); changes discarded` in `state.json` / `reports/run_summary.md`.

### 5. DV3 contract copy drift

- `server/prisma/schema.prisma` or OpenAPI copies must match **`docs/schema.prisma`** / **`docs/openapi.yaml`**.
- **Signal:** `DV3: … must stay identical to the approved docs/…`.

### 6. Build/test failures (non-guardrail)

- Flutter analyze/test, Jest, Prisma, codegen failures after agent work.
- Example: run `20261002-123506` — WI-002 failed on api_client type errors.

### 7. Agent-reported blocked

- Agent marks WI **blocked** (e.g. business style approval). Entire chain can stall from WI-001.
- Example: run `20260930-112938`.

### 8. Worker gone, state stale

- Sleep, kill, crash → no **`fz_worker`**; UI may show **running** until reconcile.
- **Signal:** `is_live: false` with running status, or orphaned **stopped**.

### 9. Invalid `state.json` after manual edit

- UTF-8 **BOM** or corrupt JSON → **500 on POST /resume**.
- **Signal:** `Invalid JSON: expected value at line 1 column 1`.

### 10. Multiple workers on one run

- Stacked **POST /resume** while worker live → git/state **race**.

---

## B. Environment / operations

| # | Cause | Notes |
|---|--------|--------|
| 11 | **Laptop sleep/hibernate** | Kills worker and agent children; lid/OEM can override “never sleep”. |
| 12 | **API down (port 8001)** | Need `FACTORY_ENGINE=fz` uvicorn for resume/status. |
| 13 | **Heavy robocopy** | Copying `apps/api` → `server` **with node_modules** — very slow/aborted. |

---

## C. “Looks stuck” but often is not

| # | Cause | Notes |
|---|--------|--------|
| 14 | **Long cursor-agent turns** | M2 backend WIs: **5–15+ minutes** with **no new transcript line** until step completes. |
| 15 | **Heartbeat-only updates** | `updated_at` / “Worker active” without WI status change. |
| 16 | **M1 QA fix loops** | Multiple QA rounds + fix WIs (e.g. filter reset bugs). |
| 17 | **Gap after M1 QA before M2** | Worker idle or scaffold hang before first M2 WI logs. |

---

## D. Layout / planning mismatches (recurring)

| # | Issue |
|---|--------|
| 18 | Architect **monorepo** (`apps/api`, `app/`) vs profile **scaffold** (`nest new server`, `workdir: server`). |
| 19 | Transcript **workdir: server** vs prompt **working directory apps/api**. |
| 20 | **Duplicate git trees** for `server/` and `apps/api/` (junction era). |

---

## E. Other runs in this repo (same patterns)

- **ShopEase `20261003-044724`:** `server/` backend, DV3 fix loops, M2/M3 QA.
- **`20261002-123506`:** WI-002 failed (api_client) → downstream blocked.
- **`20260930-112938`:** WI-001 blocked (approval) → full chain blocked.

---

## Quick diagnosis checklist

1. **Child `npx` / `nest` / cursor-agent?** → #2 or long agent (#14).
2. **WI failed + “discarded”?** → #1, #4, #5, #6.
3. **One failed, rest blocked?** → #3.
4. **No worker after sleep?** → #11, #8.
5. **Resume 500?** → #9.
6. **Transcript quiet &lt;30 min, CPU on agent?** → #14 (wait).

---

## Resume rules (lighting / FZ)

- **One worker** per run; do not stack resumes.
- Resume only if **`is_live: false`** or **no progress 15–45+ min** with flat CPU.
- Keep machine **awake** (plugged in, lid open, presentation mode optional).
- **`state.json`** is gitignored — fix BOM/JSON with UTF-8 **without** BOM before resume.

---

*Generated for local ops reference. Does not modify any run workspace.*
