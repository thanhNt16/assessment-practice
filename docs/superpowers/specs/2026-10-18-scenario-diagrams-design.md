# Interactive Scenario Flowcharts — Design

Date: 2026-10-18
Status: approved (architecture)
Replaces: `:::glide` step-strip blocks on all 17 section pages

## Problem

`:::glide` renders a linear chip-stepper + caption + static quiz pairs — a slideshow, not interactive learning. The site's hand-drawn Excalidraw diagrams are static PNGs. We want branching decision scenarios rendered as hand-drawn interactive flowcharts: the learner walks a decision graph, chooses branches, sees consequences.

## Approach (chosen: B)

Custom SVG flowchart engine inside `build.py`'s JS bundle — no mermaid, no excalidraw runtime. Hand-drawn look achieved with `feTurbulence`+`feDisplacementMap` SVG filter on strokes and **Excalifont** webfont (woff2 already bundled in the excalidraw-diagram skill; copy ~25KB into `fonts/`).

## DSL

`:::scenario <Title>` blocks in `research/*.md`, lines:

| Form | Meaning |
|---|---|
| `@id Label :: caption` | node; `@id` is the handle, `::` splits label/caption |
| `-> label => @target` | unconditional edge from nearest declared node |
| `? choice => @target \|kind` | choice edge from nearest declared node; `kind` ∈ `success`, `fail`, or unset (neutral) |
| `-> label => @already-declared` | loop back-edge — auto-detected (dst already declared), drawn dashed, excluded from layout ranking |

First declared node = start. Nodes may carry multi-line captions (`\n` via `|` inside caption? — no: captions are single-line; keep ≤120 chars).

### Replaces `:::glide`
Every `:::glide` block converts to `:::scenario` with a real decision graph. `?`-quiz lines inside glide are dropped — assessment now lives in the branches themselves. Sections where the glide is inherently linear (s14 study-path, s15 answer-framework) get scenario trees built from the section's actual decision content (e.g. s15: "assessor asks X → answer A vs B").

## Renderer (JS, ~120 lines)

Data embedded as `<script type="application/json" class="sc-json">` inside a `.scenario` div emitted by `preprocess()`.

- **Layout:** topological ranks → rows (y), per-row sibling spread → x. Node width from `ctx.measureText` (Excalifont loaded via `FontFace`). Curved `C` connectors with arrowhead marker; `success`/`fail` edges in green/red; `loop` edges dashed, routed on the canvas right margin.
- **Sketchiness:** `<filter id="sk">` feTurbulence 0.02 / feDisplacementMap scale 3 applied to node rects + edge paths. Nodes = hand-rounded rects; decision nodes = amber fill, start = orange, terminal outcome nodes = green/red.
- **Interaction:** start lit. Panel under SVG shows active node's caption + choice buttons (labels from `?` edges). Click a choice → next node lights, edge trail stays lit, caption panel updates. Terminal nodes show outcome caption tinted. Buttons: **Reset**, **Reveal all** (lights full graph). Back-edges allowed — path can revisit.
- **Mobile:** `viewBox` + `preserveAspectRatio="xMidYMin meet"`; horizontal scroll if >viewport; min font 12px.

## CSS

`.sc-*` classes; palette reuses site vars (`--vp-c-bg-elv` card, brand accent) + the excalidraw semantic hexes for node kinds (blue `#dbeafe`/#1e3a5f, amber `#fef3c7`/#b45309, green `#a7f3d0`/#047857, red `#fee2e2`/`#dc2626`, orange `#fed7aa`/`#c2410c`).

## Fonts

Copy `Excalifont-Regular-*.woff2` (largest single file covers full latin) → `fonts/Excalifont.woff2`; `@font-face` in CSS block, used by both scenario SVG text and future diagram labels.

## Build changes

- `CONTAINER_OPEN_RE` add `scenario`; `preprocess()` branch emits `<div class="scenario"><svg>` placeholder + JSON payload
- `JS` block gains scenario engine (fetch FontFace once, build per block)
- `exc.py`/render pipeline unchanged — PNG diagrams stay static; scenarios are the interactive counterpart

## Content authoring

17 sections → 17 decision trees, mined from each `research/*.md`'s existing glide steps + body (canonical sources already on disk). Assigned in 4 parallel batches. Each tree: 6–12 nodes, ≥1 branch, ≥1 failure-colored edge where the section teaches failure modes.

## Verification

- Prototype s11 (skew-diagnosis — most naturally branched) before mass-conversion; if free-DAG layout fails, fall back to fixed two-column grid layout
- Geometric collision check in build (warn on overlapping node rects)
- Browser verify: click-through one scenario light+dark, mobile 390px no overflow

## Non-goals

- Editing scenarios in-browser
- Pan/zoom inside the SVG (the existing PNG lightbox already covers zoom)
- Sound/animation, timers, scoring

## Risks

- Font loading race → `document.fonts.load('14px Excalifont')` before layout
- DAG cycles → loop edges (auto-detected re-entry) escape ranking; malformed graphs fall back to linear listing with console warn
