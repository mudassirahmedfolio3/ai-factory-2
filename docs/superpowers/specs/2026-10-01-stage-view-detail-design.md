# Stage View Detail Panel — Design

**Date:** 2026-10-01  
**Status:** Approved in conversation (Approach 1 + Sections 1–3)  
**Scope:** `AI-Factory-React` dashboard only (no fz pipeline changes)

## Goal

Move the stage info that currently sits with the phone (info-cards) into the left **View detail** expand panel. Support navigating past/future stages via the stepper. When a stage was visited more than once (pipeline revisits), show each visit as an iteration block.

## Decisions

| Topic | Choice |
|---|---|
| Layout approach | Approach 1 — remove right-side info-cards; full detail only in View detail |
| Iteration meaning | A — pipeline revisits of the same UI stage |
| Auto-open View detail | No — user toggles; content refreshes if already open when stage changes |
| Iteration order | Oldest → newest |
| Single pass | Still show `Iteration 1` for consistency |
| Backend changes | None for this feature |

## Layout

### Right column (`application-studio`)

**Keep**

- Studio heading (project name, usage, stage blurb, status)
- Phone / preview frame
- Stage actions (gate review, emulator, etc.)
- Stage progress bar

**Remove**

- The two `info-cards` articles (document card + feature checklist)

### Left bottom (`agent-context` / View detail)

**Collapsed (unchanged)**

- Agent line + status
- Compact context grid (working on / input / output)
- `View detail` / `Hide detail` toggle

**Expanded — for the selected stage**

1. Existing stage summary (description, task, checklist chips, maturity)
2. Content formerly in info-cards:
   - Artifact / document row (still opens the brief/PRD modal on click)
   - Feature / checklist lines with progress ticks
   - Delivery-stage copy via existing `deliveryCopy` when on last stage
3. Iteration blocks (see below)

## Navigation

| Selection | View detail content |
|---|---|
| Live stage (default) | Live fields + artifact/feature content + iteration blocks for this stage |
| Past stage (stepper click) | That stage’s static/live-derived fields + its iteration history (read-only) |
| Future stage | Static copy from `data.js`; iterations empty or muted “Not started” |

- Stepper click behavior stays: `review(i)` sets `view` / clears for live.
- `Return to live stage` remains in the footer when reviewing.
- Changing `stageIndex` while detail is open updates panel content; do not force-close; reset detail scroll.

## Iteration blocks

### Definition

An **iteration** is one contiguous visit to a UI stage. A new iteration starts when the pipeline returns to that stage after having left it (e.g. QA fail → developer fix → back on Backend/Frontend).

### Data source

Frontend-only:

- Existing audit SSE / `auditEvents`
- Existing `buildProjectJourney` mapping (extend or add a helper to group events by UI stage index)

Map audit events → UI stage index via `phaseMap` / journey stage labels. Events that re-enter a completed stage (e.g. `developer_fix` after QA) open a new iteration block for that stage.

If audit data is sparse for a stage that only ran once, still render **Iteration 1** with status/progress from `runState` / stage aggregate.

### Presentation

Stacked under stage summary, oldest → newest:

```
Iteration 1 · first pass
  status · timestamp · short summary

Iteration 2 · revisit after QA
  status · timestamp · short summary
```

**Rules**

- Multiple visits → one block per visit; label `Iteration N` + reason when known
- Live stage mid-pass → latest block marked `In progress`
- Future stage → no blocks, or one muted “Not started”
- Prefer compact blocks (not cards) inside the existing detail scroll area; may raise `max-height` slightly so multi-iteration history remains readable

## Out of scope

- fz / agentic_sdlc changes
- Changing gate review UI
- Changing stepper visuals beyond existing live/completed styles
- Auto-opening View detail on stage change

## Acceptance criteria

1. Info-cards no longer appear next to/below the phone.
2. Expanding View detail shows former info-card content for the selected stage.
3. Document row still opens the existing brief/release modal.
4. Clicking past/future stages updates View detail to that stage.
5. Stages with revisits show multiple numbered iteration blocks.
6. Stages with a single pass show `Iteration 1`.
7. Live run continues to update live-stage detail without breaking History / gates / emulator.

## Implementation notes (non-binding)

- Likely touch: `App.jsx` (move markup, wire iterations), `styles.css` (iteration block styles, detail max-height), optionally `journeyMap.js` or a small `stageIterations.js` helper.
- Reuse `deliveryCopy`, `stage.card1` / `card2`, and existing modal handlers.
