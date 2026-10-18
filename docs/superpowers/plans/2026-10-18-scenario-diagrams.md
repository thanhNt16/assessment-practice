# Interactive Scenario Flowcharts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the linear `:::glide` chip-steppers on all 17 section pages with `:::scenario` blocks rendered as hand-drawn interactive branching flowcharts (SVG turbulence filter + Excalifont), walkable by clicking choice buttons.

**Architecture:** `build.py` parses a `:::scenario` DSL in each `research/*.md` into an embedded JSON payload; a runtime SVG engine in the shared JS block lays out the DAG (topological ranks → rows), draws wobbled nodes/edges, and drives interaction (click choice → light next node, lit trail, Reset/Reveal-all). Spec: `docs/superpowers/specs/2026-10-18-scenario-diagrams-design.md`.

**Tech Stack:** Python `build.py` static generator, vanilla JS + SVG, `feTurbulence` filter, Excalifont woff2 (copied from `.agents/skills/excalidraw-diagram/references/fonts/Excalifont/`).

## Global Constraints

- No new build tooling or CDN deps; everything stays in `build.py` + served static files.
- Excalifont ships as local `fonts/Excalifont.woff2` (copy largest single-range file: `Excalifont-Regular-a88b72a24fb54c9f94e3b5fdaa7481c9.woff2`, ~25KB).
- Node kinds palette: default `#dbeafe`/`#1e3a5f`, decision `@choice` `#fef3c7`/`#b45309`, start `#fed7aa`/`#c2410c`, terminal success `#a7f3d0`/`#047857`, terminal fail `#fee2e2`/`#dc2626`.
- DSL (from spec, verbatim): `@id Label :: caption` node; `-> label => @target` unconditional edge; `? choice => @target |kind` choice edge, kind ∈ `success`/`fail`/unset; `|loop` suffix on node = dashed back-edge excluded from ranking. First declared node is start.
- Captions single-line, ≤120 chars. Every scenario needs ≥1 `?` choice and 6–12 nodes.
- Every task ends with `python3 build.py` passing + browser check where the changed surface is visible.
- Site conventions: `html.dark` class toggles theme; pages served at `http://127.0.0.1:5001/`; browser verify via `browser.open` eval tool (relay 127.0.0.1:9224).

---

### Task 1: Font asset + CSS skeleton

**Files:**
- Create: `fonts/Excalifont.woff2` (copy from `.agents/skills/excalidraw-diagram/references/fonts/Excalifont/Excalifont-Regular-a88b72a24fb54c9f94e3b5fdaa7481c9.woff2`)
- Modify: `build.py` CSS block (`.dg-png img{cursor:zoom-in}` region, ~line 570)

**Interfaces:**
- Produces: `@font-face` family `Excalifont`; CSS classes `.scenario`, `.sc-svg`, `.sc-panel`, `.sc-cap`, `.sc-choices`, `.sc-btn` (choice buttons), `.sc-bar` (Reset/Reveal row) — consumed by Tasks 2+3.

- [ ] **Step 1: Copy the font**

```bash
mkdir -p fonts
cp .agents/skills/excalidraw-diagram/references/fonts/Excalifont/Excalifont-Regular-a88b72a24fb54c9f94e3b5fdaa7481c9.woff2 fonts/Excalifont.woff2
ls -la fonts/
```

- [ ] **Step 2: Add CSS to `build.py` CSS raw string (after `.dg-png img{cursor:zoom-in}` line)**

```css
@font-face{font-family:Excalifont;src:url(fonts/Excalifont.woff2) format('woff2');font-display:swap}
.scenario{margin:18px 0;border:1px solid var(--vp-c-divider);border-radius:12px;background:var(--vp-c-bg-elv);overflow:hidden}
.sc-head{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid var(--vp-c-divider);font-weight:600;font-size:14px}
.sc-head .sc-ic{margin-right:6px}
.sc-body{overflow-x:auto;padding:14px}
.sc-svg{display:block;margin:0 auto;font-family:Excalifont,cursive}
.sc-svg .sc-node{cursor:pointer}
.sc-svg text{font-family:Excalifont,cursive}
.sc-panel{border-top:1px solid var(--vp-c-divider);padding:12px 14px;min-height:52px}
.sc-cap{font-size:14px;color:var(--vp-c-text-2);line-height:1.55}
.sc-choices{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.sc-btn{border:1.5px solid var(--vp-c-divider);border-radius:9px;background:var(--vp-c-bg);color:var(--vp-c-text-1);font-family:Excalifont,cursive;font-size:15px;padding:6px 14px;cursor:pointer}
.sc-btn:hover{border-color:var(--vp-c-brand-1);color:var(--vp-c-brand-1)}
.sc-btn.ok{border-color:#047857;color:#047857}
.sc-btn.bad{border-color:#dc2626;color:#dc2626}
.sc-bar{display:flex;gap:8px;margin-top:10px}
.sc-bar button{border:1px solid var(--vp-c-divider);border-radius:7px;background:transparent;color:var(--vp-c-text-3);font-size:12px;padding:4px 10px;cursor:pointer;font-family:var(--font-body)}
.sc-bar button:hover{color:var(--vp-c-brand-1);border-color:var(--vp-c-brand-1)}
html.dark .sc-btn{background:var(--vp-c-bg)}
```

- [ ] **Step 3: Build + font serves**

Run: `python3 build.py && curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5001/fonts/Excalifont.woff2`
Expected: `Done — index.html + 13 section pages`, `200`

- [ ] **Step 4: Commit**

```bash
git add fonts/Excalifont.woff2 build.py
git commit -m "feat: Excalifont asset + scenario CSS skeleton"
```

---

### Task 2: DSL parser + payload emitter in `preprocess()`

**Files:**
- Modify: `build.py` — `CONTAINER_OPEN_RE` (line ~105), `preprocess()` (lines ~108–166), add `scenario_parse()` next to `glide_html()` (line ~168)

**Interfaces:**
- Consumes: `:::scenario <Title>` blocks from `research/*.md`
- Produces:
  - `scenario_parse(lines) -> {"title": str, "nodes": [{"id","label","cap","loop"}], "edges": [{"src"|None,"label","dst","kind"|None,"choice":bool}]}`. Choice edges carry `"src"` resolved to the most recently declared `@node` when written as `?`.
  - `preprocess()` returns `(src, mer, glides, scenarios)` — update the TWO call sites that unpack it (`render_page`, ~line 190) to accept the 4-tuple.
  - Emitted HTML: `<div class="scenario" data-sc="N"><div class="sc-head">…title…</div><div class="sc-body"></div><div class="sc-panel"><div class="sc-cap"></div><div class="sc-choices"></div><div class="sc-bar"><button data-a="reset">↺ Reset</button><button data-a="reveal">Reveal all</button></div></div><script type="application/json" class="sc-json">PAYLOAD</script></div>` with placeholder `SCENARIOPLOT{N}X` swapped post-render like mermaid.

- [ ] **Step 1: Write the parser**

Add after `GLIDE_QUIZ_RE`:

```python
SC_NODE_RE  = re.compile(r'^@(\w+)\s+(.*?)\s*::\s*(.+?)(\s*\|loop)?$')
SC_EDGE_RE  = re.compile(r'^(->|\?)\s*(.*?)\s*=>\s*@(\w+)(\s*\|\s*(success|fail))?$')
SC_TITLE_RE = None  # title comes from container header
```

And the function:

```python
def scenario_parse(title, lines):
    nodes, edges, order, last = [], [], [], None
    for ln in lines:
        ln = ln.strip()
        if not ln: continue
        m = SC_NODE_RE.match(ln)
        if m:
            nid, label, cap = m.group(1), m.group(2), m.group(3)
            nodes.append({"id": nid, "label": label, "cap": cap,
                          "loop": bool(m.group(4))})
            order.append(nid); last = nid
            continue
        m = SC_EDGE_RE.match(ln)
        if m:
            tok, label, dst = m.group(1), m.group(2), m.group(3)
            kind = m.group(5)
            if tok == "?":
                if last is None: raise ValueError(f"?-edge before any node in {title!r}: {ln!r}")
                edges.append({"src": last, "label": label, "dst": dst,
                              "kind": kind, "choice": True})
            else:
                src = last if "=>" not in ln.split("->")[0] else last
                edges.append({"src": last, "label": label, "dst": dst,
                              "kind": kind, "choice": False})
            continue
        raise ValueError(f"Malformed scenario line in {title!r}: {ln!r}")
    ids = {n["id"] for n in nodes}
    for e in edges:
        if e["dst"] not in ids:
            raise ValueError(f"Scenario {title!r}: edge to unknown node @{e['dst']}")
    return {"title": title, "nodes": nodes, "edges": edges, "start": order[0] if order else None}
```

Note: `->` edges also bind `src` to the preceding node (last declared) — explicit `@a -> @b` pairs aren't in the DSL; keep it simple per spec.

- [ ] **Step 2: Wire into preprocess()**

In `CONTAINER_OPEN_RE` add `scenario` to the alternation. In `preprocess()`:

```python
out, in_c, glide_lines = [], False, []
scenarios = []          # add
sc_title = None         # add
```

Extend the `if mo and not in_c:` branch:

```python
            if typ == "scenario":
                in_c, glide_lines, sc_title = "scenario", [], title
                continue
```

In the close branch (`if re.match(r'^:{3,}$', s) and in_c:`), add before the glide check:

```python
            if in_c == "scenario":
                scenarios.append(scenario_parse(sc_title, glide_lines))
                out.append(f"\nSCENARIOPLOT{len(scenarios)-1}X\n")
                in_c = False
```

(Inside the block, `glide_lines` is reused as the raw-line accumulator; the `if in_c == "glide"` accumulator branch at line ~160 must also fire for `"scenario"` — change it to `if in_c in ("glide","scenario")`.)

Return signature: `return "\n".join(out), mer, glides, scenarios`. Update call site: `src, mer, glides, scenarios = preprocess(src)` and thread `scenarios` into `render_page`.

- [ ] **Step 3: Emit HTML**

In `render_page`, next to the `GLIDEPLOT` substitution add a `SCENARIOPLOT` substitution calling:

```python
def scenario_html(g, idx):
    return (f'<div class="scenario" data-sc="{idx}">'
            f'<div class="sc-head"><span><span class="sc-ic">🧭</span><b>Scenario · {html.escape(g["title"])}</b></span></div>'
            f'<div class="sc-body"></div>'
            f'<div class="sc-panel"><div class="sc-cap"></div><div class="sc-choices"></div>'
            f'<div class="sc-bar"><button data-a="reset">↺ Reset</button><button data-a="reveal">Reveal all</button></div></div>'
            f'<script type="application/json" class="sc-json">{html.escape(json.dumps(g, ensure_ascii=False))}</script></div>')
```

- [ ] **Step 4: Smoke parse — add one test block**

Temporarily append to `research/11-spark-optimization.md` before `### Key Takeaways`... actually: replace its `:::glide` block contents later in Task 4. For now, create `/tmp/sc_test.md`:

```
:::scenario Skew test
@a Slow stage :: find the hot stage in the UI
-> p50 vs max => @b
@b p50 ≪ max? :: skew vs uniform slow
? yes — skewed key => @fix |success
? no — all tasks slow => @agg |fail
@fix Salt the key or broadcast :: small side <10MB → broadcast
@agg Aggregation skew vs join skew :: check exchange operator
|loop
```

Wait — `|loop` on `@agg` line is wrong per DSL (loop is a node flag marking a dashed back-edge... check spec: "`@id … :: caption |loop` — back-edge flag"). The loop flag belongs to an edge semantics: mark node `loop: true` when the graph *re-enters* it. Simpler: in `scenario_parse`, if the line starts `-> ... => @x` and `@x` was already declared, tag that edge `loop: True` automatically; the `|loop` suffix on nodes is redundant — drop it from parser, keep auto-detection. (Spec amendment recorded here; update spec file.)

Use this `/tmp/sc_test.md` instead:

```
:::scenario Skew test
@a Slow stage :: find the hot stage
-> p50 vs max => @b
@b p50 much less than max? :: skew vs uniform
? yes skewed key => @fix |success
? no all slow => @agg |fail
@fix Salt or broadcast :: under 10MB broadcast
@agg Agg vs join skew :: check exchange
-> back to monitoring => @a
```

The last edge auto-detects `loop` since `@a` already declared. Emit check:

Run: `python3 -c "import build; s=open('/tmp/sc_test.md').read(); print(build.scenario_parse('t', s.split('\n')[1:-1]))"` — expect dict with 4 nodes, 4 edges, last edge `loop: True`, `start: 'a'`.

- [ ] **Step 5: Commit**

```bash
git add build.py docs/superpowers/specs/2026-10-18-scenario-diagrams-design.md
git commit -m "feat: :::scenario DSL parser + JSON payload emitter"
```

---

### Task 3: SVG layout + interaction engine (JS)

**Files:**
- Modify: `build.py` JS block (append after the lightbox code, ~line 715)

**Interfaces:**
- Consumes: `.scenario` divs with `.sc-json` payloads from Task 2; `.sc-body` container; `.sc-cap`/`.sc-choices`/`.sc-bar` panel; `.sc-*` CSS from Task 1.
- Produces: runtime function `mountScenario(div, data)`; SVG node ids `scn-<idx>-<nodeId>`; lit-state classes `.lit`, `.lit-edge` on paths; no globals besides this function + the per-div mount loop.

- [ ] **Step 1: Write the engine** (~150 lines appended to `JS` raw string)

```js
// === scenario engine ===
const SC_FONT_OK=document.fonts?document.fonts.load('16px Excalifont'):Promise.resolve();
const SK_ID='scSketch';
function scLayout(d,W){
  // ranks: BFS depth from start; loop edges (dst already seen at insert) excluded
  const adj={};d.nodes.forEach(n=>adj[n.id]=[]);
  d.edges.forEach(e=>{if(!e.loop&&e.src)adj[e.src].push(e)});
  const depth={};const q=[d.start];depth[d.start]=0;
  while(q.length){const u=q.shift();(adj[u]||[]).forEach(e=>{if(depth[e.dst]===undefined){depth[e.dst]=depth[u]+1;q.push(e.dst)}})}
  d.nodes.forEach(n=>{if(depth[n.id]===undefined)depth[n.id]=Object.keys(depth).length}); // unreachable → tail
  const rows={};Object.entries(depth).forEach(([id,dp])=>{(rows[dp]=rows[dp]||[]).push(id)});
  // measure
  const cv=document.createElement('canvas').getContext('2d');
  cv.font='16px Excalifont';
  const pos={},NW=[];
  const ROWH=110,PAD=26;
  Object.keys(rows).sort((a,b)=>a-b).forEach(dp=>{
    const ids=rows[dp];const ws=ids.map(id=>Math.max(120,cv.measureText(d.nodes.find(n=>n.id===id).label).width+44));
    const total=ws.reduce((a,b)=>a+b,0)+PAD*(ids.length-1);
    let x=Math.max(PAD,(W-total)/2);
    ids.forEach((id,i)=>{pos[id]={x:x,y:60+dp*ROWH,w:ws[i],h:56};x+=ws[i]+PAD});
  });
  const maxY=60+Math.max(...Object.values(depth))*ROWH+90;
  return {pos,W:Math.max(W,...Object.values(pos).map(p=>p.x+p.w))+PAD,H:maxY};
}
function scPath(a,b){ // cubic connector bottom->top
  const x1=a.x+a.w/2,y1=a.y+a.h,x2=b.x+b.w/2,y2=b.y;
  const dy=Math.max(24,(y2-y1)*0.45);
  return `M${x1} ${y1} C${x1} ${y1+dy} ${x2} ${y2-dy} ${x2} ${y2}`;
}
const NS='http://www.w3.org/2000/svg';
function mountScenario(div,d,idx){
  const body=div.querySelector('.sc-body'),cap=div.querySelector('.sc-cap'),
        ch=div.querySelector('.sc-choices');
  const W=Math.min(1100,body.clientWidth||900);
  const L=scLayout(d,W);
  const svg=document.createElementNS(NS,'svg');
  svg.setAttribute('class','sc-svg');svg.setAttribute('viewBox',`0 0 ${L.W} ${L.H}`);
  svg.setAttribute('width',L.W);svg.setAttribute('height',L.H);
  svg.innerHTML=`<defs>
   <filter id="${SK_ID}${idx}"><feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3"/></filter>
   <marker id="scA${idx}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#1e3a5f"/></marker>
   <marker id="scAg${idx}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#047857"/></marker>
   <marker id="scAr${idx}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#dc2626"/></marker>
  </defs>`;
  const kindOf=id=>{const n=d.nodes.find(n=>n.id===id);
    const out=d.edges.filter(e=>e.src===id&&e.choice).length;
    if(id===d.start)return ['#fed7aa','#c2410c'];
    if(out>0)return ['#fef3c7','#b45309'];
    const inbound=d.edges.find(e=>e.dst===id);
    if(inbound&&inbound.kind==='success')return ['#a7f3d0','#047857'];
    if(inbound&&inbound.kind==='fail')return ['#fee2e2','#dc2626'];
    return ['#dbeafe','#1e3a5f'];};
  const el={};
  // edges first (under nodes)
  d.edges.forEach((e,i)=>{
    if(!e.src||!L.pos[e.src]||!L.pos[e.dst])return;
    const p=document.createElementNS(NS,'path');
    const a=L.pos[e.src],b=L.pos[e.dst];
    let dstr;
    if(e.loop||b.y<=a.y){ // back-edge: route right margin
      const rx=L.W-24;
      dstr=`M${a.x+a.w} ${a.y+a.h/2} C${rx} ${a.y} ${rx} ${b.y} ${b.x+b.w} ${b.y+b.h/2}`;
      p.setAttribute('stroke-dasharray','7 5');
    } else dstr=scPath(a,b);
    p.setAttribute('d',dstr);p.setAttribute('fill','none');
    const col=e.kind==='success'?'#047857':e.kind==='fail'?'#dc2626':'#1e3a5f';
    p.setAttribute('stroke',col);p.setAttribute('stroke-width','2');
    p.setAttribute('marker-end',`url(#scA${e.kind==='success'?'g':e.kind==='fail'?'r':''}${idx})`);
    p.setAttribute('filter',`url(#${SK_ID}${idx})`);
    p.classList.add('sc-edge');p.dataset.ei=i;svg.appendChild(p);
    if(e.label){const t=document.createElementNS(NS,'text');
      const mx=(a.x+a.w/2+b.x+b.w/2)/2,my=(a.y+a.h+b.y)/2-8;
      t.setAttribute('x',mx);t.setAttribute('y',my);t.setAttribute('text-anchor','middle');
      t.setAttribute('font-size','13');t.setAttribute('fill','#64748b');t.textContent=e.label;
      t.classList.add('sc-edge-lbl');t.dataset.ei=i;svg.appendChild(t);}
  });
  d.nodes.forEach(n=>{
    const p=L.pos[n.id],[fill,stroke]=kindOf(n.id);
    const g=document.createElementNS(NS,'g');g.classList.add('sc-node');g.dataset.nid=n.id;
    const r=document.createElementNS(NS,'rect');
    r.setAttribute('x',p.x);r.setAttribute('y',p.y);r.setAttribute('width',p.w);r.setAttribute('height',p.h);
    r.setAttribute('rx','10');r.setAttribute('fill',fill);r.setAttribute('stroke',stroke);
    r.setAttribute('stroke-width','2');r.setAttribute('filter',`url(#${SK_ID}${idx})`);
    const t=document.createElementNS(NS,'text');
    t.setAttribute('x',p.x+p.w/2);t.setAttribute('y',p.y+p.h/2+2);
    t.setAttribute('text-anchor','middle');t.setAttribute('font-size','16');
    t.setAttribute('fill','#374151');
    // wrap label into ≤2 tspans
    const words=n.label.split(' ');const lines=['',''];let li=0;
    words.forEach(w=>{if((lines[li]+' '+w).trim().length>Math.max(10,(p.w-24)/8.4)&&li===0)li=1;lines[li]=(lines[li]+' '+w).trim()});
    lines.forEach((ln,i)=>{if(!ln)return;const ts=document.createElementNS(NS,'tspan');
      ts.setAttribute('x',p.x+p.w/2);ts.setAttribute('dy',i===0?(lines[1]?-8:0):18);
      if(i===0)ts.setAttribute('y',p.y+p.h/2+2);ts.textContent=ln;t.appendChild(ts);});
    g.appendChild(r);g.appendChild(t);svg.appendChild(g);el[n.id]={g,r,t};
    g.addEventListener('click',()=>enter(n.id));
  });
  body.appendChild(svg);
  // interaction state
  let cur=null;const visited=new Set();
  function paint(){
    d.nodes.forEach(n=>{const c=el[n.id];
      c.g.style.opacity=visited.has(n.id)?1:(n.id===d.start?1:.45);
      c.r.setAttribute('stroke-width',n.id===cur?3.5:2);});
    svg.querySelectorAll('.sc-edge').forEach(p=>{
      const e=d.edges[+p.dataset.ei];
      const on=visited.has(e.src)&&visited.has(e.dst);
      p.style.opacity=on?1:.3;});
    svg.querySelectorAll('.sc-edge-lbl').forEach(t=>{
      const e=d.edges[+t.dataset.ei];
      t.style.opacity=(visited.has(e.src)&&visited.has(e.dst))?1:.35;});
  }
  function enter(id){
    cur=id;visited.add(id);
    const n=d.nodes.find(n=>n.id===id);
    cap.textContent=n.cap;
    ch.innerHTML='';
    d.edges.filter(e=>e.src===id&&e.choice).forEach(e=>{
      const b=document.createElement('button');b.className='sc-btn'+(e.kind==='success'?' ok':e.kind==='fail'?' bad':'');
      b.textContent='? '+e.label;b.onclick=()=>enter(e.dst);ch.appendChild(b);});
    const nx=d.edges.filter(e=>e.src===id&&!e.choice&&!e.loop);
    nx.forEach(e=>{const b=document.createElement('button');b.className='sc-btn';b.textContent='→ '+(e.label||'continue');b.onclick=()=>enter(e.dst);ch.appendChild(b);});
    if(!d.edges.some(e=>e.src===id&&!e.loop)){const s=document.createElement('div');
      s.className='sc-cap';s.style.marginTop='6px';
      const win=n.cap;s.style.color='#047857';s.textContent='◼ outcome — '+win;ch.appendChild(s);}
    paint();
  }
  div.querySelector('[data-a="reset"]').onclick=()=>{visited.clear();enter(d.start)};
  div.querySelector('[data-a="reveal"]').onclick=()=>{d.nodes.forEach(n=>visited.add(n.id));
    d.edges.forEach(e=>e.src&&visited.add(e.src));paint();};
  enter(d.start);
}
SC_FONT_OK.then(()=>{
  document.querySelectorAll('.scenario').forEach((dv,i)=>{
    const data=JSON.parse(dv.querySelector('.sc-json').textContent);
    mountScenario(dv,data,i);
  });
});
```

- [ ] **Step 2: Wire test block into s11 md**

In `research/11-spark-optimization.md` replace the `:::glide … :::` block with the `/tmp/sc_test.md` scenario content (real version authored in Task 4 — for this task use the test tree verbatim, prefix title `Scenario — `).

- [ ] **Step 3: Build + browser verify**

```bash
python3 build.py
```
Then in eval:

```python
tab = await browser.open(url="http://127.0.0.1:5001/s11.html", name="sc1")
import asyncio; await asyncio.sleep(2.5)
print(await tab.evaluate("""(()=>({
  svg: !!document.querySelector('.sc-svg'),
  nodes: document.querySelectorAll('.sc-node').length,
  edges: document.querySelectorAll('.sc-edge').length,
  choices: document.querySelectorAll('.sc-btn').length,
  cap: document.querySelector('.sc-cap').textContent.slice(0,40)
}))()"""))
```
Expected: svg true, 4 nodes, 4 edges, ≥1 choice button, non-empty cap. Then click a `.sc-btn` and confirm a second node lights (`visited` opacity change → `document.querySelectorAll('.sc-node')[X].style.opacity`).

- [ ] **Step 4: Dark check**

`localStorage.setItem('vp-theme','dark');location.reload()` via `tab.evaluate`, re-run the query — opacity/color intact (fills are fixed hexes so both themes read the same; acceptable per spec).

- [ ] **Step 5: Commit**

```bash
git add build.py research/11-spark-optimization.md
git commit -m "feat: scenario SVG engine — layout, sketch filter, walk interaction"
```

---

### Task 4: Author all 17 real scenario trees

**Files:**
- Modify: `research/01-epam-assessment.md` … `research/17-ml-design.md` — each `:::glide` block → `:::scenario` with a real decision graph

**Interfaces:**
- Consumes: existing glide step text + section body content; DSL from Task 2.
- Produces: 17 `:::scenario` blocks; each 6–12 nodes, ≥1 `?` choice, ≥1 `|success` or `|fail` edge where the section teaches failure modes; first node = entry point.

- [ ] **Step 1: Dispatch 4 subagents (parallel `task` calls), each owning sections:**
  - Agent A: 01–04 (assessment, sql, pyspark, distributed)
  - Agent B: 05–08 (platform, batch-vs-stream, lakehouse, snowflake/databricks)
  - Agent C: 09–11 + 13 (table-formats, spark-vs-flink, skew [replace test tree], incidents)
  - Agent D: 14–17 (resources, interview, genai, ml)

  Each agent instruction:
  - Read `research/NN-*.md`; mine the section's real decision points (failure modes, tradeoff forks, config gates — the `Key Takeaways`/`Interview Lens` sections are richest).
  - Replace the `:::glide`…`:::` block with `:::scenario <Title>` using DSL: `@id Label :: caption`, `-> label => @id`, `? choice => @id |success|fail`. Node ids short slugs (`@a`,`@b`… or semantic). 6–12 nodes, exactly one start (first `@`); every node reachable; caption ≤120 chars, carries the *teaching* content (numbers/thresholds from the section).
  - Constraints: no two sibling `?` labels identical; `->` edges may chain nodes linearly between choices; auto-loop edges (to an earlier-declared node) are legal for "back to monitoring" style returns.
  - Verify: `python3 build.py` exits 0 for their files only (parser raises on malformed lines — that's the gate).
  - DO NOT edit `build.py`, other sections, or `diagrams/`.

- [ ] **Step 2: Geometric/render audit**

After all four return, run build and in-browser audit per page (or batch-check all 17):

```python
for s in [f's{i:02d}' for i in range(1,18)]:
    await tab.goto(f'http://127.0.0.1:5001/{s}.html'); await asyncio.sleep(1.2)
    r = await tab.evaluate("""(()=>({
      n:document.querySelectorAll('.sc-node').length,
      e:document.querySelectorAll('.sc-edge').length,
      c:document.querySelectorAll('.sc-btn').length}))()""")
    print(s, r)
```
Expect every page `n>=6, c>=1`. Fix any page that fell back (parser error → missing `.scenario`).

- [ ] **Step 3: Click-through one branch on 3 pages** (s01, s11, s13) — confirm walk works end-to-end.

- [ ] **Step 4: Commit**

```bash
git add research/*.md
git commit -m "content: convert 17 glides to decision-tree scenarios"
```

---

### Task 5: Remove glide machinery + final verify

**Files:**
- Modify: `build.py` — delete `glide_html()`, glide branch in `preprocess()` (keep shared line-accumulator), `GLIDEPLOT` substitution, `.glide*` CSS rules, `.glide` JS block, `GLIDE_STEP_RE`/`GLIDE_QUIZ_RE` regexes
- Modify: `index.html`/`s*.html` — regenerated automatically

**Interfaces:**
- Consumes: everything above.
- Produces: zero `glide` references in `build.py`; all pages render scenario blocks.

- [ ] **Step 1: Grep + delete glide code paths**

```bash
grep -n 'glide\|GLIDE\|GLIDEPLOT' build.py
```
Remove each hit: CSS `.glide`, `.glide-h`, `.glide-steps`, `.glide-chip`, `.glide-cap`, `.gprev`, `.gnext`, `.gplay`, `.qflip`(keep? — quiz flips were inside glide; remove `.qflip` JS + CSS too since scenarios carry choices now), JS `document.querySelectorAll('.glide')` block + `.qflip` block, `glide_html()`, `GLIDEPLOT` regex substitution, `glides` return value (revert `preprocess` to 3-tuple `(src, mer, scenarios)` and update call site).

- [ ] **Step 2: Rebuild + zero-glide check**

```bash
python3 build.py
! grep -l 'glide' s*.html index.html
```
Expected: no matches.

- [ ] **Step 3: Full-page verification** — all 17 pages: `.scenario` present, ≥1 node lit at load, light+dark toggle keeps diagram legible, mobile 390px viewport zero horizontal overflow of `.sc-body` (scrolls inside, page doesn't).

```python
await tab.evaluate("""(()=>{const de=document.documentElement;
  return {pageW:de.scrollWidth, inner:innerWidth, overflow:de.scrollWidth>innerWidth}})()""")
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: drop glide steppers; scenario flowcharts ship"
```

## Self-Review Notes

- DSL spec amended in Task 2 Step 4: `|loop` node suffix dropped — loops auto-detected by `dst` already declared. Spec file updated in same commit.
- `?`-edge `src` binds to the most recently declared node — documented in parser docstring; spec already says "from nearest node".
- `SCENARIOPLOT` substitution mirrors existing `MERMAIDPLOT`/`GLIDEPLOT` post-render swap — implementer must place it where `GLIDEPLOT` was applied (post `md.render`).
- Types: `scenario_parse` returns `{title,nodes,edges,start}`; `mountScenario(div, data, idx)` consumes same shape; no drift.
- Coverage check against spec: DSL ✓(T2), layout engine ✓(T3), sketch filter+Excalifont ✓(T1+T3), interaction+Reset/Reveal ✓(T3), 17 authored trees ✓(T4), s11 prototype-then-mass-convert ordering ✓(T3 uses s11 first, T4-C finishes it), mobile `viewBox` ✓(T3), lightbox untouched ✓.
