# Task 1 Report: Glide preprocessor + markup renderer

## Status: DONE

## What changed (build.py)
- `CONTAINER_OPEN_RE` extended to `info|tip|warning|glide`; added `GLIDE_STEP_RE`, `GLIDE_QUIZ_RE` (~lines 105–107).
- `preprocess()` reworked: returns 3-tuple `(src_out, mermaids, glides)`; `:::glide Title` blocks stashed into `glide_lines`, parsed on close into `{"title", steps:[{n,label,caption}], quiz:[{q,a}]}` payloads; emits `\nGLIDEPLOT{i}X\n` placeholder; malformed line raises `ValueError`.
- Added `glide_html(g)`: renders `.glide` card (header w/ `1/N` counter, chip `<ol>`, caption stack, prev/next buttons, flip-quiz buttons).
- `render_page` call site updated to 3-tuple unpack; after assembly replaces `GLIDEPLOT{i}X` with `glide_html(g)` (same mechanism as mermaid placeholders; `<p>` wrap by markdown-it accepted per brief).

## Deviation from brief (bug fix)
Brief's `preprocess` verbatim code never appended body lines to `glide_lines`. Fixed by adding, **after** the `s == ":::"` close check:
```python
if in_c == "glide":
    glide_lines.append(line)
    continue
```
Ordering matters: close check first, else the `:::` terminator is swallowed into `glide_lines` and blocks never close (first attempt placed the collection before the close check and test_parse failed with 0 glides).

## Verification
- `python3 -m unittest tests.test_glide -v` → **OK, 3 tests passed** (parse, html_shape, bad_line_raises; initially failing pre-implementation as required).
- `python3 build.py` → all 17 section pages + index written, identical page/sub counts to pre-change run (no regression).

## Files
- Modified: `build.py`
- Created: `tests/test_glide.py` (unittest, loads build.py via importlib)

## Concerns
- `GLIDEPLOTnX` lands inside `<p>…</p>` after markdown render (same as existing MERMAIDPLOT placeholders). No glide blocks exist in current sources, so unobservable in output today; if styling issues appear when content lands (Task 2+), switch replace needle to `f"<p>GLIDEPLOT{i}X</p>"`.
- repo is not a git repo — no commit made.
