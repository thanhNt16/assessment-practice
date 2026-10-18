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

