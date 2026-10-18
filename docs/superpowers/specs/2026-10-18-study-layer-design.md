# Study Layer & Site Enhancement — Design

Date: 2026-10-18
Status: Approved (brainstorming complete)
Scope: interactive-learning program over the full 26-section site — active recall, summaries, visual explanation, knowledge linking, layout polish.

## Goals

1. **Retention**: spaced-repetition flashcards (SM-2 lite) with a Review hub, per-page self-check widgets, mastery rings on the path map.
2. **Comprehension**: diagram-stepper primitive on ~8 high-value mermaid diagrams + 2 bespoke interactive labs (skew, watermark).
3. **Connections**: glossary-term tooltips in page text, related-concept chips, one interactive Graph page.
4. **Summaries**: collapsible TL;DR at top of every page + one Cram page compiling all TL;DRs.
5. **Layout**: study-focused polish (study pager, mobile outline, wider column) — no chrome redesign.

Non-goals: backend, accounts, sync, force-directed graphs, animation frameworks, redesigning the navbar beyond three new links.

## Hard constraints

- Static site served by `python3 -m http.server`; all runtime state in `localStorage`, all compute at build time (build.py) or in vanilla JS.
- Existing conventions preserved: markdown source in `research/*.md`, `preprocess()` block routing (`:::name`), scenario DSL, scenario canvas pan/zoom code, VitePress theme variables.

## Phase 1 — Foundations: authoring + data model

### Authoring blocks (inside research/*.md)

```
:::tldr
- bullet: the claim to defend
:::

:::cards
Q: question text :: answer text
:::
```

- `:::tldr` — 5–7 bullets; placed near top of each topic file; rendered as the page TL;DR card.
- `:::cards` — one per line `Q :: A`; target ~6 cards/section → ~155 total across 26 sections.
- Blocks are stripped from page flow by `preprocess()` (like `:::scenario`) and routed to the compiler.

### Glossary + graph edges: research/glossary.md (new)

- Format: `TERM :: definition` lines, one section header per module for readability. Single authoritative glossary (~120 terms) deduped from the genAI/ML glossary drafts.
- Graph edges appended as `TERM > TERM :: why` lines (hand-authored, ~60 edges).

### Build output

- `build.py` compiles all of the above into **`study.json`** emitted next to the pages:
  - `cards: [{id, sec, q, a}]` — `id` = `s{nn}-{k}`
  - `terms: [{t, def}]`, `edges: [{a, b, why}]`
  - `termRefs: {term: [sec...]}` — pages where the term appears (build-time scan)
  - `tldr: {sec: [bullets]}`
- Section pages inline their own cards/TL;DR via placeholders (`CARDSLOT`, `TLDRSLOT`); hub/graph/cram fetch `study.json` once.

### Content promotion

- s18–s26 built from existing research files (16-genai-overview, 17-smart-compose, 18-machine-translation, 19-chatbot-assistant, 20-image-captioning, 21-rag, 22-face-generation, 23-high-resolution-image-synthesis, 24-text-to-image, 25-headshot-personalization, 26-text-to-video — final mapping fixes 26 numbered pages; leftover files fold in as extras where noted in the plan).
- New module on path map + sidebar: **GenAI & ML Design** covering s16–s26.
- 9 new scenario trees for files that lack one (same DSL, 8–12 nodes).

## Phase 2 — Study system

### Scheduling (SM-2 lite)

- `localStorage["study-sched"]`: `{cardId: {e, iv, due}}` (ease, interval days, due epoch-millis).
- Grades: **again** → iv 10 min, ease −0.15 (floor 1.3); **hard** → iv 1d, ease −0.05; **good** → iv × ease; **easy** → iv × ease × 1.3, ease +0.1 (cap 2.8). New cards: good = 1d.
- No learning-step queue beyond "again" — "again" cards re-queue at end of the current session.

### Review hub — review.html

- Top-nav "Review". Due-today queue across all sections, ordered oldest-due first, cap 40/session (rest tomorrow).
- Card UI: front = question + section chip (chip links to source page); click/space flips; four grade buttons with keyboard 1–4; after grading, next card slides in.
- Session header: `due today N`, streak, deck total; "Study ahead" button when queue empty (picks lowest-interval cards).
- Persisted session state survives reload (position restored).

### Per-page self-check widget

- Bottom of each section page (before Interview Lens): that section's cards in the same flip/grade component (shared JS), writing to the same scheduler.

### Mastery rings

- Path-map nodes gain an SVG arc: fraction of the section's cards with `iv ≥ 4d` ("mature").
- States: no ring (nothing studied) → blue arc (learning) → green arc (≥70% mature). Node tooltip: `12/18 studied · 7 mature`.

## Phase 3 — Comprehension layer

### Diagram stepper

- `:::steps` block wraps an existing mermaid fence + numbered step lines: `caption :: nodeA,nodeB` (node IDs from the mermaid source).
- JS renders the mermaid once, then per step dims all nodes/edges not listed and highlights the listed ones (scenario-engine palette, dark-mode aware). Prev/next + progress dots; auto-scrolls long captions.
- Rollout: ~8 diagrams — Kafka write path, AQE phases, watermark/windows, medallion, RAG pipeline, ISR flow, iceberg compaction, commit protocol.
- All other mermaid stays static; stepper is strictly opt-in per diagram.

### Bespoke labs (2)

1. **Skew lab** (s11): sliders for partition count and skew ratio, inputs for rows/small-table size; computes shuffle bytes + AQE threshold crossing (256 MB / 5× median); renders a mini bar viz of partition sizes; caption narrates the tuning decision.
2. **Watermark lab** (s06): event-time scrubber over a fixed 10-event stream (some late); shows window emit moment, watermark line moving, late events dropped vs allowed-lateness effect. Pure DOM/SVG, deterministic dataset.

## Phase 4 — Knowledge links + summaries + polish

### Term tooltips

- Build-time: first occurrence of each glossary term per page, outside code blocks and tables, wrapped as `<span class="term" data-term="...">` (dotted underline).
- Hover (desktop) / tap (mobile) → popup: definition, "seen in N sections" with links, link to Graph page node.

### Related chips

- End of each section: 4–6 chips from authored edges touching that section's terms; chip → target page anchor.

### Graph page — graph.html

- Top-nav "Graph". Deterministic radial layout: modules on concentric arcs, terms positioned by module with simple angle spread; curved edges; node radius = term frequency; color = module accent.
- Pan/zoom reuses the scenario-canvas transform code (copy into shared helper).
- Click node → tooltip (definition + sections) + neighbors stay lit, rest dim (focus mode). Back to overview on background click.

### TL;DR + Cram

- TL;DR card under each page H1: collapsible, open by default, collapse state in `localStorage`.
- `cram.html`: all 26 TL;DRs grouped by module, jump links, per-TL;DR "reviewed" checkbox (persisted, reset button).

### Layout polish

- Sticky bottom study pager on section pages: ‹ prev · section progress % (from card maturity) · next ›.
- Mobile: right outline collapses into a dropdown bar under H1.
- Content column 820→880px at ≥1280px viewport.
- Code blocks: copy button always visible on touch devices (no hover dependency).

## Error handling & validation (build time)

`build.py` fails the build on:
- card with empty Q or A; duplicate card id;
- glossary term defined twice; edge referencing an unknown term;
- `:::steps` referencing mermaid node IDs that don't exist;
- page in FILES missing from disk or vice versa (17→26 mapping integrity).

Runtime guards: missing `study.json` → hub/graph/cram show an inline error card, not a blank page; scheduler JSON corrupt → reset to empty with a toast.

## Testing

- Unit-ish: build validation rules above (intentional-bad-input fixtures in a throwaway run).
- Smoke (real browser, as established): full review session — grade 10 cards across grades, reload, assert due counts and intervals match the formula; widget grades flow into the global queue; tooltip present on 3 pages; graph page pan/zoom + focus; stepper advances and highlights; both labs recompute on input; 390px zero horizontal overflow on new pages; dark mode on hub/graph/cram.
- Regression: existing scenario trees still walk; path map still navigates; mermaid still renders (stepper must not break non-stepper diagrams).

## Sequencing

Phase 1 → 4 in order; each phase ends committed, built, and browser-verified. Estimated plan tasks: ~6 (foundations, hub+widget, rings, stepper, labs, links+cram+polish).
