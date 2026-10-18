--- /tmp/build-base.py	2026-10-18 11:08:43.468254000 +0700
+++ build.py	2026-10-18 11:11:47.177692450 +0700
@@ -102,35 +102,78 @@
 md.enable("table")
 
 MERMAID_FENCE_RE = re.compile(r'```mermaid\n(.*?)```', re.S)
-CONTAINER_OPEN_RE = re.compile(r'^:::\s*(info|tip|warning)\s*(.*)$')
-
+CONTAINER_OPEN_RE = re.compile(r'^:::\s*(info|tip|warning|glide)\s*(.*)$')
+GLIDE_STEP_RE = re.compile(r'^(\d+)\)\s+(.*?)\s*::\s*(.+)$')
+GLIDE_QUIZ_RE = re.compile(r'^\?\s+(.*?)\s*::\s*(.+)$')
 def preprocess(src):
-    """Extract mermaid fences to placeholders; convert :::containers to div blocks."""
-    mer = []
+    """Extract mermaid fences; convert :::containers (incl. glide) to placeholders."""
+    mer, glides = [], []
     def stash(m):
         mer.append(m.group(1).strip())
         return f"\nMERMAIDPLOT{len(mer)-1}X\n"
     src = MERMAID_FENCE_RE.sub(stash, src)
-    out, in_c = [], False
+    out, in_c, glide_lines = [], False, []
     for line in src.split("\n"):
         s = line.strip()
         mo = CONTAINER_OPEN_RE.match(s)
         if mo and not in_c:
             typ, title = mo.group(1), mo.group(2).strip()
+            if typ == "glide":
+                in_c, glide_lines, glide_title = "glide", [], title
+                continue
             t = f'<div class="ct-title">{html.escape(title)}</div>' if title else ""
             out += [f'<div class="ct ct-{typ}">', t, ""]
             in_c = True
             continue
         if s == ":::" and in_c:
-            out += ["", "</div>"]
+            if in_c == "glide":
+                payload = {"title": glide_title, "steps": [], "quiz": []}
+                for gl in glide_lines:
+                    if not gl.strip(): continue
+                    ms, mq = GLIDE_STEP_RE.match(gl.strip()), GLIDE_QUIZ_RE.match(gl.strip())
+                    if ms:
+                        payload["steps"].append({"n": int(ms.group(1)),
+                            "label": md.renderInline(ms.group(2)), "caption": md.renderInline(ms.group(3))})
+                    elif mq:
+                        payload["quiz"].append({"q": md.renderInline(mq.group(1)),
+                            "a": md.renderInline(mq.group(2))})
+                    else:
+                        raise ValueError(f"Malformed glide line: {gl!r}")
+                glides.append(payload)
+                out.append(f"\nGLIDEPLOT{len(glides)-1}X\n")
+            else:
+                out += ["", "</div>"]
             in_c = False
             continue
+        if in_c == "glide":
+            glide_lines.append(line)
+            continue
         out.append(line)
-    return "\n".join(out), mer
+    return "\n".join(out), mer, glides
+
+def glide_html(g):
+    chips = "".join(
+        f'<li class="glide-chip" data-i="{s["n"]-1}"><b>{s["n"]}</b>{s["label"]}</li>'
+        for s in g["steps"])
+    caps = "".join(f'<div class="glide-cap" data-i="{i}">{s["caption"]}</div>'
+                   for i, s in enumerate(g["steps"]))
+    quiz = "".join(
+        f'<button class="qflip" type="button" aria-expanded="false">'
+        f'<span class="qf">? {q["q"]}</span><span class="qa">{q["a"]}</span></button>'
+        for q in g["quiz"])
+    return (f'<div class="glide" tabindex="0">'
+            f'<div class="glide-h"><span class="glide-ic">🧩</span>'
+            f'<b>Glide · {html.escape(g["title"])}</b>'
+            f'<span class="glide-ct">1/{len(g["steps"])}</span></div>'
+            f'<ol class="glide-steps">{chips}</ol>'
+            f'<div class="glide-caps">{caps}</div>'
+            f'<div class="glide-ctl"><button class="gprev" type="button">◀</button>'
+            f'<button class="gnext" type="button">▶</button></div>'
+            f'<div class="glide-quiz">{quiz}</div></div>')
 
 def render_page(src, sec_no):
     """Render a section file: ## → h1, ### → h2 with anchors."""
-    src, mer = preprocess(src)
+    src, mer, glides = preprocess(src)
     lines = src.split("\n")
     subs = []
     h1_title = None
@@ -168,6 +211,8 @@
     out = "\n".join(parts)
     for i, m in enumerate(mer):
         out = out.replace(f"MERMAIDPLOT{i}X", f'<div class="mermaid">\n{m}\n</div>')
+    for i, g in enumerate(glides):
+        out = out.replace(f"GLIDEPLOT{i}X", glide_html(g))
     return out, h1_title, subs
 
 # ---------------- collect sections ----------------
