# AI Factory

React implementation of the AI Factory Figma intake screen and nine-stage dashboard. React, React DOM and Vite only; native CSS handles transitions and skeleton animations. Inter is loaded from Google Fonts.

## Run

Requires Node 22.12+ (Node 24 recommended) and pnpm.

```sh
pnpm install
pnpm dev
```

Production: `pnpm build`, then `pnpm preview`. Tests: `pnpm test`.

## Demo workflow

Enter requirements, use an example prompt or attach files. Start begins Requirement → Business Analyst → UX → UI → Architect → Developer → QA → UAT → Delivery. A normal run takes about two minutes. Speed controls offer 2× and 4×, plus pause/resume. Stage navigation reviews a stage without skipping or corrupting the running process; “Return to live stage” resumes following it.

UAT automatically approves in the demo so an unattended run finishes. During UAT, Approve release proceeds immediately. Request changes pauses the demo and collects feedback; submitting reruns Developer, QA and UAT. Closing that dialog leaves the run paused so the reviewer can decide when to resume.

Delivery reveals a working NOVA sample: create an item, save/unsave items and navigate tabs. View application opens a larger review dialog. Project journey lists all outputs. Download handover exports a JSON demo report, not generated application source.

## Integration points

- `src/styles.css`: shared Figma color, spacing, radius and animation variables.
- `src/data.js`, `src/stages.json`: stage content and original local artwork.
- `src/engine.js`: deterministic workflow state machine, independent of the UI.
- `src/Phone.jsx`: `MobileFrame` exposes a `children` slot and optional `previewUrl` iframe. Its content viewport stays contained inside the phone. The iframe intentionally allows scripts/forms but isolates the embedded origin; extend only for a trusted integration.
- `src/App.jsx`: intake, dashboard, review dialogs and handover.

This is a frontend simulation. Files remain in memory in the current browser tab; no AI backend receives or parses them. Refresh resets the session. The NOVA sample is dummy data, not generated from the brief. A backend can later replace timer events and provide a built app through the mobile slot.

Accepted files: PDF, DOC/DOCX, TXT, MD, PNG, JPG, WebP. Maximum 20 MB each, 8 files. Empty/unsupported files are rejected. Drag-and-drop, remove attachment and Ctrl/Cmd+Enter submit are supported.

Responsive layout stacks the factory floor and studio below 900px; the nine-stage navigation scrolls horizontally. Keyboard focus, dialog Escape handling, semantic progress indicators and reduced-motion support are included.
