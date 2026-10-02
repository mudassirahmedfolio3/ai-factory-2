# Run history page — design

## Goal

Let users browse recent AI Factory runs and open any run in the full dashboard (stages, preview, journey).

## Navigation

- App view state: `intake` | `history` | `dashboard` (no React Router).
- **History** button in intake and dashboard headers.
- History header: Brand + **New project** (→ intake).
- Row action **View details** → dashboard for that `run_id`.

## History page

- Title: “Run history”; subtitle about recent runs.
- Newest-first list from `GET /runs` via existing `listRuns()`.
- Each row: project name, run id, status badge (`running` / `completed` / `failed` / `stale` + live), phase, timestamp (`archived_at` or `updated_at`), complexity if present, **View details**.
- Empty / error / retry states.
- Out of scope v1: search, filters, delete, pagination.

## Implementation

- `src/History.jsx` — page component.
- `src/App.jsx` — view switching; wire History into Intake/Dashboard headers.
- `src/styles.css` — history list styles.
- Reuse `projectFromRunState` + existing `Dashboard` for full detail.
