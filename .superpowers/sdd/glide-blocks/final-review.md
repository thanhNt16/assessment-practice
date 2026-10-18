--- /tmp/build-base.py	2026-10-18 11:08:43.468254000 +0700
+++ build.py	2026-10-18 11:15:06.919058674 +0700
@@ -102,35 +102,80 @@
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
+    if in_c == "glide":
+        raise ValueError("Unclosed :::glide block")
+    return "\n".join(out), mer, glides
 
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
+
 def render_page(src, sec_no):
     """Render a section file: ## → h1, ### → h2 with anchors."""
-    src, mer = preprocess(src)
+    src, mer, glides = preprocess(src)
     lines = src.split("\n")
     subs = []
     h1_title = None
@@ -168,6 +213,8 @@
     out = "\n".join(parts)
     for i, m in enumerate(mer):
         out = out.replace(f"MERMAIDPLOT{i}X", f'<div class="mermaid">\n{m}\n</div>')
+    for i, g in enumerate(glides):
+        out = out.replace(f"GLIDEPLOT{i}X", glide_html(g))
     return out, h1_title, subs
 
 # ---------------- collect sections ----------------
@@ -480,6 +527,29 @@
   .vm-svg{width:min(300px,85vw)}
 }
 @media(max-width:420px){.features{grid-template-columns:1fr}}
+.glide{margin:18px 0 26px;border:1px solid var(--vp-c-divider);border-radius:12px;background:var(--vp-c-bg-elv);padding:14px 16px}
+.glide:focus{outline:2px solid var(--vp-c-brand-1);outline-offset:2px}
+.glide-h{display:flex;align-items:center;gap:8px;font-weight:600}
+.glide-h b{flex:1}
+.glide-ic{font-size:18px}
+.glide-ct{font-family:var(--vp-font-family-mono);font-size:12px;color:var(--vp-c-text-3)}
+.glide-steps{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:10px 0;margin:0}
+.glide-chip{flex:1 1 auto;min-width:70px;text-align:center;padding:8px 10px;border-radius:8px;background:var(--vp-c-bg-alt);color:var(--vp-c-text-2);font-size:13px;line-height:1.3;transition:all .2s;border:1px solid transparent}
+.glide-chip b{display:block;font-family:var(--vp-font-family-mono);font-size:11px;color:var(--vp-c-text-3)}
+.glide-chip.lit{background:rgba(217,92,65,.12);border-color:var(--vp-c-brand-1);color:var(--vp-c-text-1)}
+.glide-chip.lit b{color:var(--vp-c-brand-1)}
+.glide-caps{position:relative;min-height:44px}
+.glide-cap{display:none;font-size:14px;color:var(--vp-c-text-2);padding:6px 0}
+.glide-cap.on{display:block}
+.glide-ctl{display:flex;gap:6px;margin-top:4px}
+.gprev,.gnext{width:34px;height:30px;border-radius:8px;border:1px solid var(--vp-c-divider);background:var(--vp-c-bg-alt);color:var(--vp-c-text-1);cursor:pointer;font-size:13px}
+.gprev:hover,.gnext:hover{border-color:var(--vp-c-brand-1);color:var(--vp-c-brand-1)}
+.glide-quiz{margin-top:10px;display:flex;flex-direction:column;gap:6px}
+.qflip{text-align:left;width:100%;border:1px dashed var(--vp-c-divider);border-radius:8px;background:transparent;padding:8px 10px;cursor:pointer;font:inherit;color:var(--vp-c-text-1)}
+.qflip .qa{display:none;margin-top:6px;padding-top:6px;border-top:1px solid var(--vp-c-divider);color:var(--vp-c-text-2)}
+.qflip.show .qa{display:block}
+.qflip.show{border-style:solid;border-color:var(--vp-c-brand-1)}
+@media (max-width:640px){.glide-chip{min-width:56px;font-size:12px;padding:6px}}
 """
 
 JS = r"""
@@ -563,6 +633,25 @@
   });
 });
 document.addEventListener('click',e=>{if(!e.target.closest('.vm-node'))vmNodes.forEach(n=>n.classList.remove('open'))});
+document.querySelectorAll('.glide').forEach(gl=>{
+  const chips=[...gl.querySelectorAll('.glide-chip')];
+  const caps=[...gl.querySelectorAll('.glide-cap')];
+  const ct=gl.querySelector('.glide-ct');
+  let i=0;const n=caps.length;
+  const show=k=>{i=Math.max(0,Math.min(n-1,k));
+    chips.forEach((c,j)=>c.classList.toggle('lit',j<=i));
+    caps.forEach((c,j)=>c.classList.toggle('on',j===i));
+    if(ct)ct.textContent=(i+1)+'/'+n;};
+  gl.querySelector('.gprev').onclick=()=>show(i-1);
+  gl.querySelector('.gnext').onclick=()=>show(i+1);
+  gl.addEventListener('keydown',e=>{
+    if(e.key==='ArrowLeft'){e.preventDefault();show(i-1)}
+    if(e.key==='ArrowRight'){e.preventDefault();show(i+1)}});
+  chips.forEach((c,j)=>{c.style.cursor='pointer';c.onclick=()=>show(j)});
+  show(0);
+});
+document.querySelectorAll('.qflip').forEach(q=>q.onclick=()=>{
+  q.classList.toggle('show');q.setAttribute('aria-expanded',q.classList.contains('show'))});
 """
 
 MERMAID_JS = r"""
