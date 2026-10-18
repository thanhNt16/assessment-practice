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
