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

