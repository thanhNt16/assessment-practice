# Glide Blocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an interactive `:::glide` container — a numbered step-through of each section's key design + flip-to-answer quiz cards — rendered at the top of every section page (s01–s17).

**Architecture:** Extend the existing `:::type` preprocessor in `build.py` with a `glide` type that parses `n) label :: caption` and `? q :: a` lines into a payload, emitted as DOM markup. A single shared JS block (appended to the existing `JS` string) animates all `.glide` instances; CSS goes into the existing `CSS` string. Content is authored inside each `research/NN-*.md` after the hook paragraph.

**Tech Stack:** Python (markdown-it-py), vanilla JS, CSS — all inside `build.py`; no new runtime deps.

## Global Constraints

- Section file contract: `## Title` line 1, `###` subsections, `:::info|tip|warning|glide` containers only.
- `:::` must never appear inside a glide line (parser constraint — enforce with raise).
- Every glide claim must come from that section's own text — no new facts.
- Malformed glide line → `raise ValueError` in build (loud failure).
- Budget per glide: 5–9 steps + 2–4 quiz items.
- No placeholders in plans/deliverables; TDD where feasible.

---

### Task 1: Glide preprocessor + markup renderer in build.py

**Files:**
- Modify: `build.py` — `CONTAINER_OPEN_RE` (~line 105), `preprocess()` (~line 107-129), plus new `GLIDE` emission in `render_page`'s flush path.
- Test: `tests/test_glide.py` (create `tests/` dir; plain `python3 -m pytest` or a `python3 -c` harness — repo has no test suite, so use a small `unittest` file runnable by `python3 -m unittest`).

**Interfaces:**
- Produces: `preprocess(src)` returns `(src_out, mermaids, glides)` — **signature change**: was `(src, mer)`. Update `render_page` call site. `render_page` gains glide payloads rendered via `glide_html(payload)` → HTML string spliced in place of the container.
- `glide_html(payload: {"title":str,"steps":[{"n","label","caption"}],"quiz":[{"q","a"}]}) -> str`

- [ ] **Step 1: Write failing tests**

Create `tests/test_glide.py`:

```python
import unittest, sys, pathlib, importlib.util, re
spec = importlib.util.spec_from_file_location("build", pathlib.Path(__file__).parent.parent / "build.py")

def load_build():
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class GlideTest(unittest.TestCase):
    def test_parse(self):
        b = load_build()
        src = "## T\n\n:::glide My Flow\n1) A :: first\n2) B :: second\n? Q :: A\n:::\n\n### s\n"
        out, mer, glides = b.preprocess(src)
        self.assertEqual(len(glides), 1)
        g = glides[0]
        self.assertEqual(g["title"], "My Flow")
        self.assertEqual(g["steps"], [{"n":1,"label":"A","caption":"first"},{"n":2,"label":"B","caption":"second"}])
        self.assertEqual(g["quiz"], [{"q":"Q","a":"A"}])
    def test_html_shape(self):
        b = load_build()
        h = b.glide_html({"title":"T","steps":[{"n":1,"label":"L","caption":"C"}],"quiz":[{"q":"Q","a":"A"}]})
        for needle in ['class="glide"','glide-chip','glide-cap','qflip','◀','▶','1/1']:
            self.assertIn(needle, h)
    def test_bad_line_raises(self):
        b = load_build()
        with self.assertRaises(ValueError):
            b.preprocess("## T\n\n:::glide X\n1) missing sep\n:::\n")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify fail** — `python3 -m unittest tests.test_glide -v` → ImportError/AttributeError.

- [ ] **Step 3: Implement**

In `build.py`:

```python
CONTAINER_OPEN_RE = re.compile(r'^:::\s*(info|tip|warning|glide)\s*(.*)$')
GLIDE_STEP_RE = re.compile(r'^(\d+)\)\s+(.*?)\s*::\s*(.+)$')
GLIDE_QUIZ_RE = re.compile(r'^\?\s+(.*?)\s*::\s*(.+)$')
```

Rework `preprocess`:

```python
def preprocess(src):
    """Extract mermaid fences; convert :::containers (incl. glide) to placeholders."""
    mer, glides = [], []
    def stash(m):
        mer.append(m.group(1).strip()); return f"\nMERMAIDPLOT{len(mer)-1}X\n"
    src = MERMAID_FENCE_RE.sub(stash, src)
    out, in_c, glide_lines = [], False, []
    for line in src.split("\n"):
        s = line.strip()
        mo = CONTAINER_OPEN_RE.match(s)
        if mo and not in_c:
            typ, title = mo.group(1), mo.group(2).strip()
            if typ == "glide":
                in_c, glide_lines, glide_title = "glide", [], title
                continue
            t = f'<div class="ct-title">{html.escape(title)}</div>' if title else ""
            out += [f'<div class="ct ct-{typ}">', t, ""]
            in_c = True; continue
        if s == ":::" and in_c:
            if in_c == "glide":
                payload = {"title": glide_title, "steps": [], "quiz": []}
                for gl in glide_lines:
                    if not gl.strip(): continue
                    ms, mq = GLIDE_STEP_RE.match(gl.strip()), GLIDE_QUIZ_RE.match(gl.strip())
                    if ms:
                        payload["steps"].append({"n": int(ms.group(1)),
                            "label": md.renderInline(ms.group(2)), "caption": md.renderInline(ms.group(3))})
                    elif mq:
                        payload["quiz"].append({"q": md.renderInline(mq.group(1)),
                            "a": md.renderInline(mq.group(2))})
                    else:
                        raise ValueError(f"Malformed glide line: {gl!r}")
                glides.append(payload)
                out.append(f"\nGLIDEPLOT{len(glides)-1}X\n")
            else:
                out += ["", "</div>"]
            in_c = False; continue
        out.append(line)
    return "\n".join(out), mer, glides
```

Add `glide_html`:

```python
def glide_html(g):
    chips = "".join(
        f'<li class="glide-chip" data-i="{s["n"]-1}"><b>{s["n"]}</b>{s["label"]}</li>'
        for s in g["steps"])
    caps = "".join(f'<div class="glide-cap" data-i="{i}">{s["caption"]}</div>'
                   for i, s in enumerate(g["steps"]))
    quiz = "".join(
        f'<button class="qflip" type="button" aria-expanded="false">'
        f'<span class="qf">? {q["q"]}</span><span class="qa">{q["a"]}</span></button>'
        for q in g["quiz"])
    return (f'<div class="glide" tabindex="0">'
            f'<div class="glide-h"><span class="glide-ic">🧩</span>'
            f'<b>Glide · {html.escape(g["title"])}</b>'
            f'<span class="glide-ct">1/{len(g["steps"])}</span></div>'
            f'<ol class="glide-steps">{chips}</ol>'
            f'<div class="glide-caps">{caps}</div>'
            f'<div class="glide-ctl"><button class="gprev" type="button">◀</button>'
            f'<button class="gnext" type="button">▶</button></div>'
            f'<div class="glide-quiz">{quiz}</div></div>')
```

In `render_page`: `src, mer, glides = preprocess(src)`; replace placeholders after `out` assembly:

```python
for i, g in enumerate(glides):
    out = out.replace(f"GLIDEPLOT{i}X", glide_html(g))
```

Note: markdown-it will wrap `GLIDEPLOTnX` in `<p>` tags — acceptable (existing mermaid does the same via same mechanism; verify visually). If wrap causes issues, strip `f'<p>GLIDEPLOT{i}X</p>'` in the replace call instead.

- [ ] **Step 4: Run tests pass** — `python3 -m unittest tests.test_glide -v` → 3 PASSED.
- [ ] **Step 5: Build once to confirm no regression** — `python3 build.py | tail -3` → all 17 pages write.

---

### Task 2: CSS + JS for glide interaction

**Files:**
- Modify: `build.py` — `CSS` string (~top), `JS` string (~line 485-566).

**Interfaces:**
- Consumes: DOM from `glide_html` — classes `.glide`, `.glide-chip[data-i]`, `.glide-cap[data-i]`, `.gprev`, `.gnext`, `.glide-ct`, `.qflip`, `.qf/.qa`.
- Produces: nothing downstream; runs at page load.

- [ ] **Step 1: Write failing check** — after build, `grep -c 'glide-chip' s01.html` currently 0 (no CSS/JS yet); visual check pending until content exists — skip formal test, gate = browser check in Task 4.

- [ ] **Step 2: Append CSS** into `CSS` string:

```css
.glide{margin:18px 0 26px;border:1px solid var(--vp-c-divider);border-radius:12px;background:var(--vp-c-bg-elv);padding:14px 16px}
.glide:focus{outline:2px solid var(--vp-c-brand-1);outline-offset:2px}
.glide-h{display:flex;align-items:center;gap:8px;font-weight:600}
.glide-h b{flex:1}
.glide-ic{font-size:18px}
.glide-ct{font-family:var(--vp-font-family-mono);font-size:12px;color:var(--vp-c-text-3)}
.glide-steps{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:10px 0;margin:0}
.glide-chip{flex:1 1 auto;min-width:70px;text-align:center;padding:8px 10px;border-radius:8px;background:var(--vp-c-bg-alt);color:var(--vp-c-text-2);font-size:13px;line-height:1.3;transition:all .2s;border:1px solid transparent}
.glide-chip b{display:block;font-family:var(--vp-font-family-mono);font-size:11px;color:var(--vp-c-text-3)}
.glide-chip.lit{background:rgba(217,92,65,.12);border-color:var(--vp-c-brand-1);color:var(--vp-c-text-1)}
.glide-chip.lit b{color:var(--vp-c-brand-1)}
.glide-caps{position:relative;min-height:44px}
.glide-cap{display:none;font-size:14px;color:var(--vp-c-text-2);padding:6px 0}
.glide-cap.on{display:block}
.glide-ctl{display:flex;gap:6px;margin-top:4px}
.gprev,.gnext{width:34px;height:30px;border-radius:8px;border:1px solid var(--vp-c-divider);background:var(--vp-c-bg-alt);color:var(--vp-c-text-1);cursor:pointer;font-size:13px}
.gprev:hover,.gnext:hover{border-color:var(--vp-c-brand-1);color:var(--vp-c-brand-1)}
.glide-quiz{margin-top:10px;display:flex;flex-direction:column;gap:6px}
.qflip{text-align:left;width:100%;border:1px dashed var(--vp-c-divider);border-radius:8px;background:transparent;padding:8px 10px;cursor:pointer;font:inherit;color:var(--vp-c-text-1)}
.qflip .qa{display:none;margin-top:6px;padding-top:6px;border-top:1px solid var(--vp-c-divider);color:var(--vp-c-text-2)}
.qflip.show .qa{display:block}
.qflip.show{border-style:solid;border-color:var(--vp-c-brand-1)}
@media (max-width:640px){.glide-chip{min-width:56px;font-size:12px;padding:6px}}
```

- [ ] **Step 3: Append JS** at end of `JS` string (before closing `"""`):

```javascript
document.querySelectorAll('.glide').forEach(gl=>{
  const chips=[...gl.querySelectorAll('.glide-chip')];
  const caps=[...gl.querySelectorAll('.glide-cap')];
  const ct=gl.querySelector('.glide-ct');
  let i=0;const n=caps.length;
  const show=k=>{i=Math.max(0,Math.min(n-1,k));
    chips.forEach((c,j)=>c.classList.toggle('lit',j<=i));
    caps.forEach((c,j)=>c.classList.toggle('on',j===i));
    if(ct)ct.textContent=(i+1)+'/'+n;};
  gl.querySelector('.gprev').onclick=()=>show(i-1);
  gl.querySelector('.gnext').onclick=()=>show(i+1);
  gl.addEventListener('keydown',e=>{
    if(e.key==='ArrowLeft'){e.preventDefault();show(i-1)}
    if(e.key==='ArrowRight'){e.preventDefault();show(i+1)}});
  chips.forEach((c,j)=>{c.style.cursor='pointer';c.onclick=()=>show(j)});
  show(0);
});
document.querySelectorAll('.qflip').forEach(q=>q.onclick=()=>{
  q.classList.toggle('show');q.setAttribute('aria-expanded',q.classList.contains('show'))});
```

- [ ] **Step 4: Build** — `python3 build.py | tail -3` succeeds.

---

### Task 3: Author glide blocks in all 17 research files

**Files:**
- Modify: `research/01-epam-assessment.md` … `research/17-ml-design.md` (17 files; insert `:::glide` after the hook paragraph, before first `###`).

**Interfaces:**
- Consumes: syntax from Task 1; each file's own headings/facts.
- Produces: 17 `:::glide` blocks, each 5–9 steps + 2–4 quiz items, content drawn only from that file's existing text.

- [ ] **Step 1: Author all 17 blocks** — fan out to subagents (batches of ~4 files each, one agent each, read-only on own file) or write inline; each block must quote only its own section's facts/numbers.
- [ ] **Step 2: Build** — `python3 build.py`; loud `ValueError` if any line malformed → fix.
- [ ] **Step 3: Verify count** — `for f in s*.html; do echo "$f $(grep -o 'class="glide"' $f | wc -l)"; done` → each = 1.

---

### Task 4: Browser verification

- [ ] **Step 1:** Open `http://127.0.0.1:5001/s01.html` and `s16.html`; confirm glide card renders at top, steps advance with ▶ and ←/→ keys, chips light cumulatively, captions swap, quiz cards flip.
- [ ] **Step 2:** Mobile pass — 390px viewport, zero horizontal overflow on both pages.
- [ ] **Step 3:** Dark-mode pass — toggle theme, chips/captions readable, lit state uses coral.
- [ ] **Step 4:** Regression — `:::info` containers and mermaid diagrams on s04/s16 unchanged.

---

## Self-review notes
- Spec coverage: syntax ✓(Task 1), markup/CSS/JS ✓(Task 1/2), authoring 17 ✓(Task 3), placement/verification ✓(Task 3/4).
- Placeholders: none — code blocks contain full implementations.
- Type consistency: `preprocess` 3-tuple signature updated at the single call site in `render_page`; `glide_html` name consistent across Tasks 1–2 class names.
