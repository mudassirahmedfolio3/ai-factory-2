# Stage View Detail Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move info-cards into View detail, keep stepper stage selection, and show revisit iteration blocks.

**Architecture:** Pure frontend. New `stageIterations.js` groups audit events into per-UI-stage visits. `App.jsx` removes right-column info-cards and renders that content plus iterations inside the expand panel. Styles raise detail max-height and add compact iteration blocks.

**Tech Stack:** React 19, Vite, node:test

## Global Constraints

- Frontend-only (`AI-Factory-React`); no fz changes
- Do not auto-close View detail on stage change; reset scroll only
- Always show Iteration 1 when the stage has progress; oldest → newest
- Document row must still open the brief modal

---

### Task 1: Stage iterations helper + tests

**Files:**
- Create: `AI-Factory-React/src/stageIterations.js`
- Create: `AI-Factory-React/tests/stageIterations.test.js`

**Interfaces:**
- Produces: `buildStageIterations(auditEvents, stageIndex, opts)` → `Array<{ n, reason, status, timeLabel, summary, muted }>`

- [x] **Step 1:** Write failing tests for single pass, revisit after QA, future stage empty/muted, live in-progress
- [x] **Step 2:** Implement `stageIterations.js`
- [x] **Step 3:** Run tests — expect pass

### Task 2: Move info-cards into View detail + iterations UI

**Files:**
- Modify: `AI-Factory-React/src/App.jsx`
- Modify: `AI-Factory-React/src/styles.css`

- [x] **Step 1:** Remove auto-close `useEffect` on `stageIndex`; add scroll reset via ref
- [x] **Step 2:** Move document + feature content into `context-detail-body`; remove `.info-cards` from studio
- [x] **Step 3:** Render iteration blocks from `buildStageIterations`
- [x] **Step 4:** CSS for detail document/features/iterations; raise open max-height
- [x] **Step 5:** Run tests and smoke build

**Status:** Implemented 2026-10-01
