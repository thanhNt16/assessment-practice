--- /tmp/build-t1.py	2026-10-18 11:14:12.941516000 +0700
+++ build.py	2026-10-18 11:15:06.919058674 +0700
@@ -527,6 +527,29 @@
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
@@ -610,6 +633,25 @@
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
