# Glide blocks — interactive step-through per section

**Date:** 2026-10-18 · **Status:** approved design

## Goal
Each section page (s01–s17) opens with an interactive "Glide" block: a numbered step-through of the section's key design/flow, followed by flip-to-answer quiz cards — so a reader can absorb key design + takeaways in ~60s before/instead of reading the page.

## Syntax (authoring)

Extends the existing `:::type` container convention in `research/*.md`:

```markdown
:::glide <Title>
n) <step label> :: <caption — why it matters>
? <question> :: <answer>
:::
```

- `n)` = a diagram step; number sets order; label is the node text; `::` separates label from caption.
- `?` = quiz card; `::` separates question from answer.
- Captions/answers pass through `md.renderInline` — bold, code, links allowed. `:::` cannot appear inside any line (parser constraint).
- Placement: immediately after the `##` H1 + hook paragraph, before the first `###`.
- Content contract: 5–9 steps + 2–4 quiz items per section; every claim comes from that section's existing text — no new facts.

## Renderer changes (`build.py`)

1. `CONTAINER_OPEN_RE` extended to accept `glide`; glide containers bypass the generic `ct-*` div path — the preprocessor collects their body lines and parses into `{"steps":[{n,label,caption}],"quiz":[{q,a}]}`.
2. Parsed payload emitted as markup:
   - `<div class="glide">` card: header (🧩 icon, title, `n/m` counter), `<ol>` of step chips (numbered, `.lit` for current ≤ n), caption `<div>`, then quiz cards (`<button class="qflip">` front/back), `◀ ▶` buttons.
   - Quiz answers hidden via `<details>`-like state toggled in JS (accessible: `aria-expanded`, real buttons).
3. Malformed glide line (no `::` separator, bad number) → `raise` in build — loud failure, no silent drop.

## Styling + behavior

- ~60 lines CSS into existing `CSS` string: `.glide` card on `--vp-c-bg-elv`, chips in `--vp-c-bg-alt`, lit chip `--vp-c-brand-1`; flip animation = simple `.show` class swap (no CSS 3D — keeps it robust).
- ~80 lines JS appended to existing `JS` string: per-`.glide` state `{i}`; `prev/next` clamp; chips `≤i` lit; caption swap; quiz `click` toggles `.show` + `aria-expanded`; ←/→ when block has focus (`tabindex=0`). All elements are real DOM (no innerHTML re-render per step) — mobile-safe.
- Dark theme free via existing CSS vars.

## Error handling
- Zero `:::`-in-caption enforcement at parse time; unknown container names still error as today.
- JS guards: `document.querySelectorAll('.glide')` empty → no-op (index page unaffected).

## Testing
- Browser pass on s01 + s16: steps advance, captions swap, chips light in order, quiz flips, ←/→ keys, 390px viewport zero horizontal overflow.
- Programmatic check: all 17 section pages contain exactly one `.glide`; all quiz cards have answers.
- No regression: existing `:::info/tip/warning` and ```mermaid fences unchanged; `s17` build identical except the glide addition.

## Out of scope
- Index-page glide, branching diagrams, persistence of quiz state.
