# Study Layer & Site Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the 17-page reading site into a 26-page interactive study system: spaced-repetition flashcards with Review hub and mastery rings, TL;DR + Cram page, diagram stepper, two interactive labs, glossary tooltips + Graph page, study-focused layout polish.

**Architecture:** All content stays in `research/*.md` (new `:::tldr`, `:::cards`, `:::steps` blocks + `research/glossary.md`). `build.py` compiles everything at build time into `study.json` and inlines per-section data into pages. Runtime is vanilla JS + `localStorage`; no backend, no dependencies. Spec: `docs/superpowers/specs/2026-10-18-study-layer-design.md`.

**Tech Stack:** Python 3 stdlib + `markdown-it-py` (installed), vanilla JS, SVG, mermaid (CDN, already wired).

## Global Constraints

- Static site; runtime state only in `localStorage`; no new npm/pip dependencies.
- Never hand-edit `s*.html` / `index.html` — edit sources, run `python3 build.py`. Server `learn-server` is already serving `:5001`; rebuilt pages appear on reload.
- Theme: use existing CSS vars (`--vp-c-brand-1`, `--vp-c-bg`, `--vp-c-divider`, `--font-body`, `--font-head`, `--font-mono`) and the existing green success tokens (`#22a55b` / `#1d914e` / dark `#4ccb7f`). Both light and dark mode must work.
- Existing page contract preserved: H2 title line 1, `###` subs, ends `### Key Takeaways` + `### Interview Lens`.
- localStorage keys (exact): `study-sched`, `tldr-collapsed`, `cram-reviewed`, existing `ldp-visited`, `vp-theme`.
- `study.json` schema (exact, `sec` is 1-based):
  `{"cards":[{"id":"s12-1","sec":12,"q":"...","a":"..."}], "terms":[{"t":"Watermark","def":"..."}], "edges":[{"a":"Watermark","b":"Kafka","why":"..."}], "termRefs":{"Watermark":[6,12]}, "tldr":{"12":["bullet ..."]}}`
- JS runtime API (exact names, defined once in `JS`): `schedAll()`, `schedGrade(id, grade)` with `grade ∈ {'again','hard','good','easy'}`, `dueList(allCards)`, `mastery(secNo) -> {studied,total,mature,pct}`, `initFlipcards(rootEl)`.
- Keyboard: space flips, 1/2/3/4 grade again/hard/good/easy (only when a card is flipped).
- Card count targets: ≥4 cards and 5–7 TL;DR bullets per section; ~120 terms; ~60 edges.
- Commits after every task; message style matches `git log` (`feat:`, `docs:`, `fix:`).

---

### Task 1: Promote s18–s26 + fold surveys + 9 scenario trees

**Files:**
- Modify: `build.py:14-62` (FILES, NODES, MODULES), `build.py:1016` (hero tagline)
- Modify: `research/16-genai-design.md`, `research/17-ml-design.md` (fold-ins)
- Create: nothing new — s18–s26 sources already exist in `research/`
- Modify (content only): the 9 new topic files for scenario blocks

**Interfaces:**
- Produces: 26-entry `FILES`, `NODES`, `MODULES` (later tasks rely on `len(FILES)==26`, `module_of`, `page_url`).
- Consumes: existing `scenario_parse` DSL — `@id Title :: body`, `-> @target`, `-> label => @target | success`, `? label => @target`.

**Steps:**

- [ ] **Step 1: Fold `16-genai-overview.md` into `16-genai-design.md`** — in the overview file delete its `## ` title line, demote every `### ` to `#### `, then splice the remainder into `16-genai-design.md` just before its final `### Key Takeaways`. Delete `research/16-genai-overview.md`. Same for `17-smart-compose.md` → `17-ml-design.md` (spliced before `### Key Takeaways`). If a folded subsection duplicates existing content in the target, keep the more concrete version and drop the other — no duplicated claims.

- [ ] **Step 2: Extend registries** in `build.py`:

```python
FILES = [
    # ... existing 17 entries unchanged through "17-ml-design.md",
    "18-machine-translation.md",
    "19-chatbot-assistant.md",
    "20-image-captioning.md",
    "21-rag.md",
    "22-face-generation.md",
    "23-high-resolution-image-synthesis.md",
    "24-text-to-image.md",
    "25-headshot-personalization.md",
    "26-text-to-video.md",
]

# append to NODES (order = FILES order):
    {"icon": "🌍", "short": "Translation", "blurb": "NMT pipeline: tokenization, attention, beam vs sampling, evaluation."},
    {"icon": "💬", "short": "Chatbot",     "blurb": "Intent, dialogue state, retrieval+generation hybrid, guardrails."},
    {"icon": "🖼️", "short": "Captioning",  "blurb": "CNN encoder + transformer decoder, beam search, BLEU/CIDEr."},
    {"icon": "🔍", "short": "RAG",         "blurb": "Chunking, embeddings, vector search, rerank, freshness + eval."},
    {"icon": "🎭", "short": "Face Gen",    "blurb": "GAN/StyleGAN latent space, ethics + provenance."},
    {"icon": "✨", "short": "Hi-Res Synth", "blurb": "Progressive growing, super-resolution cascade, compute budget."},
    {"icon": "🎨", "short": "Text→Image",  "blurb": "Diffusion, CLIP conditioning, guidance scale, serving latency."},
    {"icon": "👤", "short": "Headshots",   "blurb": "Personalization tuning, privacy, dedup at scale."},
    {"icon": "🎬", "short": "Text→Video",  "blurb": "Temporal consistency, frame sampling, cost + moderation."},
]

# replace the last MODULES tuple and extend:
    ("🤖 GenAI & ML Design", 15, 26),  # 16–26
```

Also `build.py:1016` tagline → `26 short sections in 5 modules — Goal &amp; Foundations → Platform Design → Technology Deep-Dive → Production &amp; Defense → GenAI &amp; ML Design — covering everything the EPAM A3 internal assessment probes.` And `build.py:1052` print → `Done — index.html + {len(FILES)} section pages`.

- [ ] **Step 3: Add `#### ` CSS** — add to `CSS` near the other `.vp-doc` heading rules: `.vp-doc h4{font-family:var(--font-body);font-size:16px;font-weight:700;margin:20px 0 8px;color:var(--vp-c-text-1)}`.

- [ ] **Step 4: Add one `:::scenario` block to each of the 9 new files** (none have one). Place after the first mermaid diagram, 8–12 nodes, first line is the block title. Exact DSL example (this is a complete valid tree — content per file must reflect that file's design decisions):

```markdown
:::scenario Choose a translation serving stack
@start Latency target :: p95 under 300 ms per sentence?
-> Streaming decoder pipeline => @beam | success
-> Batched offline translation => @batch
@beam Beam width 5 fits budget? :: CPU cost grows linearly with beam width
-> yes => @quant
-> no => @sample | fail
@sample Sampling with temperature 0.3 :: cheaper, occasional incoherence
-> @quant
@quant INT8-quantized encoder :: 2.4x throughput at BLEU −0.3
-> @deploy
@batch Async queue + batch size 32 :: 5x cheaper per token, minutes of latency
-> @deploy
@deploy Canary 5% + BLEU regression gate :: auto-rollback on −1 BLEU
:::
```

- [ ] **Step 5: Build + verify** — Run: `python3 build.py` → expect `Done — index.html + 26 section pages`. Then in browser (Chrome, `http://127.0.0.1:5001/`): 26 nodes on `#vmap`, 5 module bands, sidebar shows `26` under last link number, s18–s26 load with scenario tree interactive (click a leaf), `s26.html` mermaid renders. Mobile: 390px viewport, each new page zero horizontal overflow (`document.documentElement.scrollWidth <= 390`).

- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: promote genAI/ML topics to pages s18-s26"`

---

### Task 2: Study compiler — `:::tldr` / `:::cards` blocks, `glossary.md`, `study.json`, build validation

**Files:**
- Modify: `build.py` (`preprocess` ~line 108, new `parse_study()` + `validate_study()` + `--selftest`, emit `study.json` near line 1033)
- Create: `research/glossary.md` (seed: 20 terms, 6 edges)
- Modify: `research/01-epam-assessment.md`, `research/16-genai-design.md` (seed TL;DR + cards)

**Interfaces:**
- Produces: `study.json` at site root (schema in Global Constraints); `parse_study(src, sec_no) -> (tldr_bullets, cards)`; `validate_study(study)` raising `SystemExit`; `build.py --selftest` exit code 0/1. Tasks 3–9 consume these.
- Consumes: Task 1's 26-section `FILES`.

**Steps:**

- [ ] **Step 1: Extend `preprocess` container routing** — in `CONTAINER_OPEN_RE` add `tldr|cards` to the alternation. In the container open branch: `if typ in ("tldr","cards"): in_c, lines_acc, sc_title = typ, [], title; continue`. In the close branch add: `elif in_c == "tldr": tldrs.append([l.strip("- ").strip() for l in lines_acc if l.strip()]); out.append(f"\nTLDRSLOT{len(tldrs)-1}X\n")` and `elif in_c == "cards": cardss.append([l for l in lines_acc if l.strip()]); out.append(f"\nCARDSLOT{len(cardss)-1}X\n")`. Initialize `tldrs, cardss = [], []` at top and return them: `return "\n".join(out), mer, scenarios, tldrs, cardss`. Update the two call sites (`render_page` signature + the collect loop at ~line 236) — `render_page` returns `out, h1_title, subs, tldrs, cardss`; sections dict gains `"tldr": tldrs[0] if tldrs else []` and `"cards": cardss[0] if cardss else []` (only one of each block per file; >1 is a validation error).

- [ ] **Step 2: Write seed content** — `research/01-epam-assessment.md`, insert after the H2 title line:

````markdown
:::tldr
- Internal committee defense of YOUR project work — not external-style puzzles.
- Bring: problem → constraints → 2–3 design options → tradeoff rationale → measured outcome.
- Competency matrix is the rubric: map every claim to a matrix line.
- Manager sponsorship + readiness review gate the attempt.
- [WARN] Process details are reported, not officially documented.
:::

:::cards
Q: What replaces coding puzzles in the internal A3 assessment? :: A committee defense of your real project work, scored against the competency matrix.
Q: Name the 5-part structure for presenting your project. :: Problem, constraints, 2–3 design options with tradeoffs, chosen design rationale, measured outcome.
Q: Who gates the assessment attempt? :: Your manager (sponsorship) plus a readiness review.
Q: What is the single biggest defense mistake? :: Describing team achievements with "we" and never owning a decision with "I".
:::
````

Same shape for `research/16-genai-design.md` (5–7 bullets + 4 cards about the GenAI framework: requirements → model choice → context/retrieval → eval/guardrails; content from that file).

- [ ] **Step 3: Create `research/glossary.md`** (seed — Task 4 expands):

```markdown
# Glossary — single source for terms + graph edges

## Format
- Term lines: `TERM :: one-sentence definition` (TERM is matched case-insensitively at word boundaries).
- Edge lines: `TERM_A > TERM_B :: why they're connected` (both must be defined).
- `##` headers are ignored (organization only).

## Terms
Watermark :: Event-time progress marker; windows close and late data is judged against it.
Idempotency :: An operation safe to retry — same input, same final state, no duplicate effects.
Exactly-once :: Effect semantics built from at-least-once delivery + idempotent writes or transactional commits.
Medallion :: Bronze (raw) → silver (validated) → gold (business-ready) layering of lakehouse data.
RAG :: Retrieval-augmented generation — ground an LLM answer in retrieved documents.
Embedding :: Dense vector representation of text/image such that semantic similarity ≈ vector distance.
AQE :: Adaptive Query Execution — Spark re-plans joins/partitions at shuffle boundaries using runtime stats.
ISR :: In-sync replicas — Kafka followers caught up enough to acknowledge writes.
Parquet :: Columnar file format with per-column encoding and nested-type support.
CDC :: Change data capture — stream of row-level changes from an OLTP log.
SCD Type 2 :: Slowly changing dimension keeping history as new versioned rows.
Backfill :: Reprocessing historical data with new logic into the same destination.
Lambda architecture :: Batch + speed layers serving merged views; Kappa collapses both onto one stream.
Shuffle :: Redistributing data across partitions between stages; the dominant Spark cost.
Skew :: Uneven key distribution making one partition dominate stage time.
Checkpoint :: Durable snapshot of Flink state enabling exactly-once recovery.
Compaction :: Merging small files into fewer large ones to restore read performance.
Z-ordering :: Multi-column clustering of lakehouse files to prune scans on any column.
Distributed join strategy :: Broadcast vs sort-merge vs shuffle-hash — picked by size + skew stats.
Feature store :: Versioned repository of point-in-time-correct features for training and serving.

## Edges
Watermark > Kafka :: stream progress drives windowing semantics downstream of a broker.
Idempotency > exactly-once :: exactly-once is engineered from idempotent writes.
Medallion > Parquet :: lakehouse layers are stored in open columnar formats.
RAG > Embedding :: retrieval quality depends on embedding similarity.
AQE > Skew :: AQE detects and rewrites skewed joins at runtime.
Shuffle > Skew :: skew only matters where a shuffle redistributes keys.
```

- [ ] **Step 4: Implement compile + validate + emit** in `build.py` (after the sections collect loop):

```python
# ---------------- study.json ----------------
def parse_glossary(text):
    terms, edges = [], []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("- "): continue
        m = re.match(r'^(.+?)\s*>\s*(.+?)\s*::\s*(.+)$', s)
        if m: edges.append({"a": m.group(1).strip(), "b": m.group(2).strip(), "why": m.group(3).strip()}); continue
        m = re.match(r'^(.+?)\s*::\s*(.+)$', s)
        if m: terms.append({"t": m.group(1).strip(), "def": m.group(2).strip()})
    return terms, edges

def validate_study(study):
    errs = []
    seen_id, seen_t = set(), set()
    for c in study["cards"]:
        if not c["q"].strip() or not c["a"].strip(): errs.append(f"empty card {c['id']}")
        if c["id"] in seen_id: errs.append(f"duplicate card id {c['id']}")
        seen_id.add(c["id"])
    for t in study["terms"]:
        if t["t"].lower() in seen_t: errs.append(f"duplicate term {t['t']}")
        seen_t.add(t["t"].lower())
    names = {t["t"].lower() for t in study["terms"]}
    for e in study["edges"]:
        for side in (e["a"], e["b"]):
            if side.lower() not in names: errs.append(f"edge references unknown term {side}")
    if errs: raise SystemExit("study validation failed:\n  " + "\n  ".join(errs))
```

In the emit path: build `cards` as `{"id": f"s{sec:02d}-{k}", "sec": sec, "q": ..., "a": ...}` by splitting each card line once on `" :: "`; build `tldr` from sections; `termRefs` via scan over each section's raw markdown text (count term presence, case-insensitive word-boundary); write `(ROOT/"study.json").write_text(json.dumps(study, ensure_ascii=False, indent=1))`. Cards missing for a section are fine now (Task 3 enforces counts).

- [ ] **Step 5: Add `--selftest`** at top of the build entry (before page emission):

```python
if "--selftest" in __import__("sys").argv:
    bad = [
        ({"cards":[{"id":"x","sec":1,"q":"","a":"a"}],"terms":[],"edges":[]}, "empty card"),
        ({"cards":[{"id":"x","sec":1,"q":"q","a":"a"},{"id":"x","sec":1,"q":"q","a":"a"}],"terms":[],"edges":[]}, "duplicate card id"),
        ({"cards":[],"terms":[{"t":"A","def":"d"},{"t":"a","def":"d"}],"edges":[]}, "duplicate term"),
        ({"cards":[],"terms":[{"t":"A","def":"d"}],"edges":[{"a":"A","b":"B","why":"w"}]}, "unknown term"),
    ]
    for study, why in bad:
        try: validate_study(study)
        except SystemExit as ex: assert why in str(ex), why; continue
        raise SystemExit(f"selftest failed: {why} not caught")
    print("selftest OK"); __import__("sys").exit(0)
```

- [ ] **Step 6: Verify + commit** — `python3 build.py --selftest` → `selftest OK`. `python3 build.py` → writes `study.json`; `python3 -c "import json;d=json.load(open('study.json'));print(len(d['cards']),len(d['terms']),len(d['edges']))"` → `8 20 6`. Fixture check: temporarily duplicate a term line in `research/glossary.md`, rebuild, expect `SystemExit` message naming it, revert. Commit `feat: study compiler — tldr/cards blocks, glossary, study.json + validation`.

---

### Task 3: Author TL;DR + cards for all 26 sections

**Files:**
- Modify: all 26 `research/*.md` in FILES (Task 1's list) except the two seeded in Task 2.

**Interfaces:**
- Consumes: Task 2 block formats (verbatim, single `Q :: A` per line, `:::tldr` bullets).
- Produces: `study.json` with ≥4 cards and 5–7 TL;DR bullets per section (~155 cards total).

**Steps:**

- [ ] **Step 1: Author content** — for each section insert `:::tldr` immediately after the H2 title line and `:::cards` immediately before `### Key Takeaways`. Rules: TL;DR = the claims you must defend + one number to remember each where applicable (e.g. "AQE skew threshold: 256 MB and 5× median partition"). Cards test recall of exactly what the TL;DR asserts — question phrased as the assessor would ask ("What…", "When…", "Why…", "Name the…"); answers ≤ 25 words, no fluff, no "as mentioned". 4–7 cards each. Content must come from that file's own material — no new claims.

- [ ] **Step 2: Harden validation** — in `validate_study` add: `for sec in range(1, len(FILES)+1): cs=[c for c in study["cards"] if c["sec"]==sec]; assert-style errs if len(cs)<4 or not study["tldr"].get(str(sec)) or not (5 <= len(study["tldr"][str(sec)]) <= 7)` → message `section {sec} needs 4+ cards and 5-7 tldr bullets`.

- [ ] **Step 3: Verify + commit** — `python3 build.py` passes with all 26 sections; totals ≈ 130–180 cards: `python3 -c "import json;d=json.load(open('study.json'));import collections;print(len(d['cards']),sorted(collections.Counter(c['sec'] for c in d['cards']).items()))"`. Spot-read 3 sections' cards for answer quality. Commit `content: tldr + flashcards for all 26 sections`.

---

### Task 4: Full glossary + term tooltips + related chips

**Files:**
- Modify: `research/glossary.md` (to ~120 terms, ~60 edges), `build.py` (`term_wrap` in `preprocess`, chips emission, `CSS`, `JS`)

**Interfaces:**
- Consumes: `study.json` terms/edges/termRefs (Task 2).
- Produces: `<span class="term" data-term="...">` in page HTML (first occurrence per page, outside code/tables/container blocks); `.chip-row` before `### Key Takeaways` on each section page; popup UI in `JS` — later tasks don't depend on internals.

**Steps:**

- [ ] **Step 1: Expand `research/glossary.md`** to ~120 terms / ~60 edges. Sources: the 26 topic files' bold/jargon vocabulary (dedupe against existing 20) + `research/generative-ai-glossary.md` and `research/machine-learning-glossary.md` (already drafted — mine, compress to one sentence each). Every edge endpoint must be a defined term (validation enforces).

- [ ] **Step 2: Build-time term wrapping** — in `build.py`, add a module-level `GLOSS_TERMS` (sorted longest-first) loaded from `parse_glossary` output, and inside `preprocess` after the mermaid stash loop, wrap in the plain-text pass (only when `not in_c` and `'|' not in line` and not inside a fenced block — fences are already stashed):

```python
used_terms = set()
def term_wrap(line):
    for t in GLOSS_TERMS:
        if t.lower() in used_terms: continue
        m = re.search(r'\b' + re.escape(t) + r'\b', line)
        if m:
            used_terms.add(t)
            return line[:m.start()] + f'<span class="term" data-term="{html.escape(t)}">' + m.group(0) + '</span>' + line[m.end():]
    return line
```

Apply `line = term_wrap(line)` in the `out.append(line)` path. Guard: skip wrapping inside inline code spans — simplest: `if '`' in line: return line` (acceptable: skips mixed lines).

- [ ] **Step 3: CSS + popup JS** — CSS: `.term{border-bottom:1px dotted var(--vp-c-brand-1);cursor:help}` + `.term-pop{position:absolute;max-width:340px;background:var(--vp-c-bg-elv);border:1px solid var(--vp-c-divider);border-radius:12px;padding:12px 14px;box-shadow:0 8px 24px rgba(0,0,0,.12);font-size:13px;z-index:60}` with `.term-pop .tp-links a{color:var(--vp-c-brand-1)}`. JS (delegated):

```js
function showTerm(el){
  closeTerm();
  const t=el.dataset.term, d=(window.STUDY_TERMS||{})[t]; if(!d) return;
  const p=document.createElement('div'); p.className='term-pop';
  const secs=(window.STUDY_TERMREFS||{})[t]||[];
  p.innerHTML=`<b>${t}</b><p>${d}</p>`+(secs.length>1?`<div class="tp-links">Seen in: ${secs.map(s=>`<a href="s${String(s).padStart(2,'0')}.html">${s}</a>`).join(' · ')}</div>`:'');
  document.body.appendChild(p);
  const r=el.getBoundingClientRect(), w=Math.min(340,innerWidth-24);
  p.style.width=w+'px';
  p.style.left=Math.max(12,Math.min(r.left,innerWidth-w-12))+scrollX+'px';
  p.style.top=(r.bottom+8+scrollY)+'px';
}
```

Wire: `document.addEventListener('click',e=>{const t=e.target.closest('.term'); t?showTerm(t):closeTerm()})` plus hover on `matchMedia('(hover:hover)')`. `STUDY_TERMS`/`STUDY_TERMREFS` are inlined into every section page via `shell(extra=...)`: `<script>window.STUDY_TERMS={...};window.STUDY_TERMREFS={...}</script>` (compact dict literals, HTML-escaped).

- [ ] **Step 4: Related chips** — in the section page emission loop, compute chips from edges where `a`/`b` is a term appearing in this section (`termRefs`), target = the *other* sections in that term's refs; take 4–6 unique, render `<div class="chip-row"><a class="chip" href="sNN.html#anchor">label</a>...</div>` just before the mark-done button. CSS: `.chip-row{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}` `.chip{padding:6px 12px;border-radius:16px;border:1px solid var(--vp-c-divider);background:var(--vp-c-bg-alt);font-size:13px;color:var(--vp-c-text-1)}` hover border brand.

- [ ] **Step 5: Verify + commit** — rebuild; in browser: dotted-underline term on s04/s06/s21 first-occurrence only (count `document.querySelectorAll('.term').length` small, e.g. ≤ #terms), no `.term` inside `<code>`/`<pre>`/tables (`![...].some(el=>el.querySelector('.term'))` false), popup shows def + "Seen in" on multi-section terms, click-away closes, chips render on 3 pages, dark mode legible. Commit `feat: glossary tooltips + related chips (120 terms, 60 edges)`.

---

### Task 5: Scheduler + Review hub + per-page self-check widget

**Files:**
- Modify: `build.py` — `JS` (scheduler + flipcards), `CSS` (flipcard + hub), section page emission (widget slot), new `review.html` emission at end.
- Create: nothing on disk outside build output.

**Interfaces:**
- Produces (in `JS`, exact): `schedAll()`, `schedGrade(id,g)`, `dueList(allCards)`, `mastery(secNo)`, `initFlipcards(rootEl)`; `window.STUDY` on section pages = `{"sec":N,"cards":[...]}`; `review.html` fetching `study.json`.
- Consumes: `study.json` cards (Task 2/3).

**Steps:**

- [ ] **Step 1: Scheduler code** (append inside `JS`):

```js
// ---- study scheduler (SM-2 lite) ----
const SCHED_KEY='study-sched';
function schedAll(){try{const o=JSON.parse(localStorage.getItem(SCHED_KEY));return o&&typeof o==='object'?o:{}}catch(e){localStorage.setItem(SCHED_KEY,'{}');return{}}}
function schedSave(o){localStorage.setItem(SCHED_KEY,JSON.stringify(o))}
function schedGrade(id,g){
  const o=schedAll(),c=o[id]||{e:2.3,iv:0};
  if(g==='again'){c.e=Math.max(1.3,c.e-0.15);c.iv=10/1440;}
  else if(g==='hard'){c.e=Math.max(1.3,c.e-0.05);c.iv=1;}
  else if(g==='easy'){c.e=Math.min(2.8,c.e+0.1);c.iv=Math.max(c.iv*c.e,1)*1.3;}
  else{c.iv=c.iv<1?1:c.iv*c.e;}
  c.due=Date.now()+c.iv*864e5;
  o[id]=c;schedSave(o);return c;
}
function dueList(all){const o=schedAll(),now=Date.now();return all.filter(c=>!(c.id in o)||o[c.id].due<=now);}
function mastery(sec){const all=window.STUDY_ALL_CARDS||[],o=schedAll();
  const mine=all.filter(c=>c.sec===sec),st=mine.filter(c=>c.id in o);
  const mat=st.filter(c=>o[c.id].iv>=4);
  return {studied:st.length,total:mine.length,mature:mat.length,pct:mine.length?Math.round(100*mat.length/mine.length):0};}
```

On section pages inline `<script>window.STUDY_ALL_CARDS=JSON.parse(JSON.stringify(SECTION_CARDS_FROM_BUILD));window.STUDY={sec:N,cards:SECTION_CARDS_FROM_BUILD}</script>` — actually emit directly from Python: `window.STUDY_ALL_CARDS={json.dumps(section_cards)};window.STUDY={{sec:{sec},cards:{json.dumps(section_cards)}}}`. On index/hub/graph/cram pages inline the FULL cards array as `window.STUDY_ALL_CARDS` (needed for rings/hub; ~40 KB, acceptable) — review.html additionally fetches nothing then; simplify: hub uses the inlined array, drop the fetch. Spec's "fetch study.json once" is satisfied by inlining everywhere instead — same data, fewer moving parts. `study.json` remains on disk for Task 9's graph/cram pages and as the compiled artifact.

- [ ] **Step 2: Flipcard component** — markup + CSS + `initFlipcards`:

```js
function initFlipcards(root){
  root.querySelectorAll('.flipcard').forEach(fc=>{
    fc.addEventListener('click',e=>{if(e.target.closest('.grade-btn'))return;fc.classList.toggle('flipped');});
  });
  root.querySelectorAll('.grade-btn').forEach(b=>b.addEventListener('click',e=>{
    e.stopPropagation();
    const fc=b.closest('.flipcard');fc.dispatchEvent(new CustomEvent('graded',{detail:b.dataset.g,bubbles:true}));
    fc.classList.add('gone');setTimeout(()=>fc.remove(),200);
  }));
}
document.addEventListener('keydown',e=>{
  if(!/^[1-4]$/.test(e.key)&&e.key!==' ')return;
  const fc=document.querySelector('.flipcard.flipped');if(!fc)return;
  e.preventDefault();
  if(e.key===' ')fc.classList.remove('flipped');
  else fc.querySelector(`.grade-btn[data-g="${{1:'again',2:'hard',3:'good',4:'easy'}[e.key]}"]`)?.click();
});
```

Python helper `flipcard_html(card)` emits `<div class="flipcard"><div class="fc-inner"><div class="fc-front"><span class="fc-sec">s12 · Kafka</span><p>Q…</p><span class="fc-hint">space to flip</span></div><div class="fc-back"><p>A…</p><div class="fc-grades"><button class="grade-btn g-again" data-g="again">Again</button>… Good/Easy</div></div></div></div>`. CSS: `.flipcard{perspective:1000px;cursor:pointer}` `.fc-inner{transition:transform .35s;transform-style:preserve-3d;position:relative}` `.flipcard.flipped .fc-inner{transform:rotateY(180deg)}` front/back `backface-visibility:hidden`, back `transform:rotateY(180deg)`; both min-height 180px, brand-tinted borders; `.g-again` red `--vp-c-danger`-ish (`#e5484d` light/`#ff6369` dark), `.g-hard` amber `#e38407`, `.g-good` green `#22a55b`, `.g-easy` blue `#5672cd`. Grade handler calls `schedGrade(card.id, g)` — pass card id via `data-id` on `.flipcard`.

- [ ] **Step 3: Per-page widget** — section emission inserts after `### Interview Lens` content, before mark-done: `<div class="selfcheck"><h3 class="sc-title">Self-check — {n} cards</h3><div class="sc-deck">{flipcard_html per card}</div></div>` + `initFlipcards` call. Grade dispatch: on `graded` event → `schedGrade(fc.dataset.id, detail)`.

- [ ] **Step 4: Review hub `review.html`** — emitted via `shell("Review", ...)`, full-width (no sidebar): header `Due today: N · deck: M · streak: S`; `<div id="queue">` renders due cards (oldest-due first, cap 40) one at a time with a progress bar `x/N`; "Study ahead" button (visible when queue empty) loads 10 lowest-`iv` cards from `STUDY_ALL_CARDS`; session position in `sessionStorage['review-pos']`; grading a card advances and records `review- streak` in `localStorage['review-streak']` (increment when ≥1 card graded today vs last date). Section chip on card front links to `sNN.html`. Corrupt `study-sched` → caught in `schedAll` (already resets).

- [ ] **Step 5: Nav link** — add `<a class="home-link" href="review.html">🎴 Review</a>` to `NAV` before the theme button.

- [ ] **Step 6: Verify + commit** — browser: on review.html grade 10 cards across the 4 buttons; then `JSON.parse(localStorage['study-sched'])` — assert intervals: again → `iv≈0.0069` and due ≈ now+10min; hard → 1d; good(new) → 1d; easy(new) → `iv≈2.99` (2.4×1.3 ≈ wait: new e after easy = 2.4, iv = max(0×2.4,1)×1.3 = 1.3 — assert 1.3); reload → due-today count decreased by graded-not-again count, again-cards requeued; keyboard 1–4 and space work; widget on s12 grades into same store (check an s12 id appears); dark mode check. Commit `feat: SM-2 scheduler, review hub, per-page self-check`.

---

### Task 6: Mastery rings + study pager + layout polish

**Files:**
- Modify: `build.py` — `vmap_svg`/`vmap_html` (rings), `pager()` (study pager), `CSS` (mobile outline dropdown, column width, touch copy), `JS` (outline dropdown, ring refresh).

**Interfaces:**
- Consumes: `mastery(secNo)` (Task 5), `STUDY_ALL_CARDS` inlined on index (Task 5).
- Produces: ring overlay `<circle class="ring">` per `.vm-node`; `.study-pager` bottom bar; no downstream deps.

**Steps:**

- [ ] **Step 1: Rings** — in `vmap_svg`'s per-node markup add `<circle class="mring" data-sec="{i}" r="{R+5}" fill="none" stroke-width="3.5" stroke-dasharray="{pct*arc} {arc}" transform="rotate(-90 x y)"/>` placeholder circle (pct filled at runtime). JS after load: for each `.mring`, `const m=mastery(i+1)` → `stroke` = none if `m.studied===0` else (`m.pct>=70 ? '#22a55b' : '#5672cd'`), `stroke-dasharray` accordingly (dark mode uses `#4ccb7f`). Node popover adds line `12/18 studied · 7 mature` from same object.

- [ ] **Step 2: Study pager** — replace `pager(i)` output: `<div class="study-pager"><a class="sp-prev" href=...>‹ {title}</a><div class="sp-mid"><span>{progress}% mature</span><div class="sp-bar"><i style="width:{pct}%"></i></div></div><a class="sp-next" href=...>{title} ›</a></div>`; progress computed client-side on load (build-time value would be stale). CSS: sticky bottom (`position:sticky;bottom:0;background:var(--vp-c-bg-elv);border-top:1px solid var(--vp-c-divider);display:flex;justify-content:space-between;gap:12px;padding:10px 16px;z-index:40;border-radius:12px 12px 0 0`); prev/next ellipsize.

- [ ] **Step 3: Mobile outline** — `<select id="outlineJump">` with `subs` options, injected in section emission, hidden ≥1080px; on change `location.hash=value`. Desktop `.outline` unchanged.

- [ ] **Step 4: Column + copy** — `.main{max-width:880px}` at `@media(min-width:1280px)` (verify tables still pass 390px — no regression); code block copy button: add CSS `@media(hover:none){.code-wrap .copy-btn{opacity:1;position:static}}` adapting to existing copy implementation (read `JS` copy code first; keep the same button, just always-visible on touch).

- [ ] **Step 5: Verify + commit** — browser: ring colors change after grading cards for a section (grade s02 cards → blue ring → simulate `iv>=4` by hand-editing `localStorage` → green, reload, ring green + popover counts); pager sticky + %-correct; 390px no overflow on 3 pages; outline select works. Commit `feat: mastery rings, study pager, layout polish`.

---

### Task 7: Diagram stepper + 8 rollouts

**Files:**
- Modify: `build.py` — `preprocess` (`steps` container), `CSS`, `JS`/`MERMAID_JS` hook, validation of step node ids.
- Modify: 8 topic files (12-messaging-kafka, 11-spark-optimization, 06-batch-vs-streaming, 05-platform-architecture, 21-rag, 12 ISR/commit diagrams as applicable, 09-table-formats compaction, 13-pipeline-reliability commit protocol).

**Interfaces:**
- Consumes: existing mermaid fences (kept verbatim inside the block).
- Produces: `:::steps Title` block compiled to `<div class="steps" data-steps='[{c:"caption",n:["nodeA","nodeB"]}]'><div class="mermaid">…</div><div class="steps-ui">…</div></div>`; `window.__stepsInit()` called after mermaid render.

**Steps:**

- [ ] **Step 1: Parse `:::steps`** — add `steps` to `CONTAINER_OPEN_RE`. Steps block body: first stashed line is `MERMAIDPLOTkX` (fences are stashed before container parsing — keep block body lines raw); remaining lines `caption :: nodeA,nodeB`. Compiler: emit `<div class="steps" data-steps="{json}"><div class="mermaid">{mermaid source}</div><div class="steps-ui"><button class="step-btn prev">‹</button><div class="step-cap"></div><button class="step-btn next">›</button><div class="step-dots"></div></div></div>`. Build validation: every node id in a step must appear as `\b{id}\b` in the mermaid source text → else `SystemExit`.

- [ ] **Step 2: Stepper JS** — append to `JS` and call from `MERMAID_JS` after `await mermaid.run()`:

```js
window.__stepsInit=function(){
  document.querySelectorAll('.steps').forEach(st=>{
    const steps=JSON.parse(st.dataset.steps),svg=st.querySelector('svg');if(!svg)return;
    const nodes=[...svg.querySelectorAll('.node,.edgePath')];
    const hit=n=>nodes.filter(el=>(el.id||'').includes(n)||el.className?.baseVal?.includes?.(n));
    let i=0;
    const paint=()=>{
      const on=new Set();steps[i].n.forEach(id=>hit(id).forEach(el=>on.add(el)));
      nodes.forEach(el=>el.style.opacity=on.has(el)?1:.15);
      st.querySelector('.step-cap').textContent=steps[i].c;
      st.querySelector('.step-dots').innerHTML=steps.map((_,k)=>`<i class="${k===i?'on':''}"></i>`).join('');
    };
    st.querySelector('.next').onclick=()=>{i=Math.min(i+1,steps.length-1);paint()};
    st.querySelector('.prev').onclick=()=>{i=Math.max(i-1,0);paint()};
    paint();
  });
};
```

Adjust selector if mermaid v11 uses different node wrapping (verify in devtools; the includes-match on `id` is the stable part). CSS: `.steps .step-cap{min-height:2.6em;font-size:14px;color:var(--vp-c-text-2)}` `.step-dots i{width:8px;height:8px;border-radius:50%;background:var(--vp-c-divider);display:inline-block;margin:0 3px}` `.step-dots i.on{background:var(--vp-c-brand-1)}` `.step-btn` = `.btn alt`-styled small.

- [ ] **Step 3: Roll out to 8 diagrams** — wrap the existing fence of each target diagram (do not rewrite diagram content) + author 4–7 steps each, captions teaching-sequence ("Producer acks=1: leader-only ack, loss window on replica lag…"). Target diagrams: Kafka write path (s12), AQE phases (s11), watermark/window closing (s06), medallion layers (s05), RAG pipeline (s21), Iceberg compaction (s09), two-phase/transactional commit (s13), Spark shuffle stages (s10).

- [ ] **Step 4: Verify + commit** — rebuild; each steps page: dots count = steps, next/prev advance, non-listed nodes dim to 0.15, caption updates; non-stepper mermaid pages still render (regression: s02/s07); bad-id fixture → build fails. Commit `feat: diagram stepper + 8 guided diagrams`.

---

### Task 8: Skew lab (s11) + watermark lab (s06)

**Files:**
- Modify: `research/11-spark-optimization.md`, `research/06-batch-vs-streaming.md` (insert `:::lab` markers), `build.py` (`CSS`/`JS` lab code, `lab` container emitting `<div class="lab" id="lab-skew">` / `id="lab-wm">`).

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `:::lab skew` / `:::lab watermark` containers (single-word id after `lab`); self-contained JS bound by element id. No downstream deps.

**Steps:**

- [ ] **Step 1: Container** — add `lab` to `CONTAINER_OPEN_RE`; emit `<div class="lab" id="lab-{slug}">` … `</div>` (body lines inside are rendered markdown intro). Slug whitelist `{skew, watermark}`; anything else fails validation.

- [ ] **Step 2: Skew lab JS** (inject into these two pages only, via build dict):

```js
// inputs: #sk-p (partitions 4-200), #sk-s (skew 0-0.95 of rows in hottest), #sk-r rows (1e6-1e9 log), row width 100B
// math: hot=R*s*w; rest=R*(1-s)*w/(P-1); median≈rest; aqe = hot>256MB && hot>5*rest
// stage time ≈ hot / 100MB/s; render 20-bar histogram (hottest red), AQE verdict line, tuned advice text
```

Implement fully in the task (bars as `<div>`s with height %, verdict `<b>` colored). Advice text switches at AQE threshold: "below AQE threshold — increase shuffle partitions" vs "AQE skew join will split this key — set `spark.sql.adaptive.skewJoin.enabled=true`".

- [ ] **Step 3: Watermark lab JS** — fixed dataset `EVT=[{t:1},{t:3},{t:7},{t:9},{t:12},{t:2},{t:11},{t:15},{t:8},{t:16}]` (arrival order = array order), window `[0,10s)` + `[10,20s)` tumbling, watermark = `max_seen - 5s`. Scrubber `input[type=range]` 0..9 (arrival index): render event-time axis (SVG 600×120), events as dots (in-window blue / late-dropped red with ✕ / accepted-green), watermark vertical line, window boxes that flip to "EMITTED" when watermark passes their end, counters `accepted/late-dropped`. Allowed-lateness toggle (0s vs 2s) — late = `et < watermark` at arrival; with lateness on, dropped only if `et < watermark - 2`.

- [ ] **Step 4: CSS** — `.lab{border:1px solid var(--vp-c-divider);border-radius:14px;padding:16px;background:var(--vp-c-bg-alt);margin:20px 0}` `.lab input[type=range]{width:100%}` `.sk-bars{display:flex;align-items:flex-end;gap:2px;height:120px}` bars flex-grow 1.

- [ ] **Step 5: Verify + commit** — browser: skew lab — defaults `P=8, s=0.5, R=1e8` → hot 5 GB > 256 MB, verdict AQE-split; set `s=0.05` → below 5× median → "increase partitions" advice; watermark lab — scrub to index 5 (`t:2` arrives after max_seen 12 → watermark 7 → late) shows red ✕; index 9 (`t:8`, watermark 11) late, with lateness 2s → 8 ≥ 11−2 → still dropped, but `t:11`-class events would be accepted — assert counters consistent with rules for all 10 indices via a `console.log` sweep in devtools once. Commit `feat: skew + watermark interactive labs`.

---

### Task 9: Graph page + Cram page + final sweep

**Files:**
- Modify: `build.py` — emit `graph.html` + `cram.html`, `NAV` links, final print line.

**Interfaces:**
- Consumes: full `study.json` data inlined as `window.STUDY_TERMS/EDGES/TERMREFS/TLDR/CARDS` (Task 4/5 pattern).
- Produces: finished site; no downstream deps.

**Steps:**

- [ ] **Step 1: `graph.html`** — inline data; deterministic radial layout computed at render: 5 modules at anchor angles (spread evenly), each module's terms sorted by frequency desc placed on an arc `r = 170 + 22*(k mod 6)`, `Δangle = termAngleSpread` (clamp label collisions by alternating ±7px radial jitter derived from index parity — no randomness). SVG: nodes `r = 6 + min(10, freq*2)`, fill by module accent (`--c1`..`--c5` or brand shades), edges quadratic curves `M a Q mid b`. Pan/zoom: wheel = zoom to cursor, drag = pan via one `transform` on a `<g>` (15 lines, self-contained). Click node → neighbors stay opacity 1, others 0.15, tooltip div (def + sections, same `.term-pop` styles); background click resets. Term label `font-size 11`.

- [ ] **Step 2: `cram.html`** — TL;DRs grouped by module, each `<details class="cram-sec" open><summary>{n:02d} · {title}<span class="cram-check"><input type="checkbox"> reviewed</span></summary><ul>…bullets…</ul><a href="sNN.html">open section →</a></details>`; checkbox state to `localStorage['cram-reviewed']` (`{"s01":true}`), "Reset reviewed" button. Module jump chips at top.

- [ ] **Step 3: NAV** — add `<a class="home-link" href="graph.html">🕸 Graph</a>` and `<a class="home-link" href="cram.html">📋 Cram</a>` next to Review. Update the completion print to list all emitted files.

- [ ] **Step 4: Full verification sweep (recorded in final message)** —
  - `python3 build.py` clean; `--selftest` OK.
  - Browser: review session end-to-end (10 cards, reload, counts); widget→hub convergence; ring updates; stepper on 2 pages; both labs; tooltips 3 pages; graph pan/zoom/focus; cram checkbox persists; nav links all pages.
  - Dark mode on review/graph/cram.
  - 390px overflow zero on: index, s06, s21, review, graph, cram.
  - Regression: scenario trees walk (s01, s26), path map navigates, mermaid renders on non-stepper pages, mark-done still works.

- [ ] **Step 5: Commit** — `feat: graph + cram pages, nav links, study layer complete`.

---

## Self-Review (done at plan time)

- **Spec coverage:** promotion→T1; compiler/JSON/validation→T2; TL;DR+cards counts→T3; tooltips/chips/glossary→T4; scheduler/hub/widget→T5; rings/pager/outline/column/touch-copy→T6; stepper+8 diagrams→T7; two labs→T8; graph/cram/nav→T9; error handling→T2 validation + T5 `schedAll` catch; testing→per-task browser steps + final sweep. Spec's "hub fetches study.json" refined to inline (same data, fewer failure modes) — noted in T5.
- **Type consistency:** `schedGrade(id,g)` / `mastery(sec)` / `initFlipcards(root)` names used identically in T5/T6; `study.json` keys `cards/terms/edges/termRefs/tldr` used in T4/T9; `sec` is 1-based everywhere (`mastery(secNo)` called with `i+1` in T6).
- **Placeholders:** T8 lab math is specified as formulas + exact thresholds; code sketches marked "implement fully in the task" carry complete math/spec, not vagueness.
