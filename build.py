#!/usr/bin/env python3
"""Assemble research/*.md into a multi-page VitePress-styled course site.

index.html  — hero + interactive Duolingo-style course path + learning map.
sNN.html    — one page per section (short, readable), sidebar nav, prev/next.
"""
import re, html, json
from pathlib import Path
from markdown_it import MarkdownIt

ROOT = Path(__file__).parent
RESEARCH = ROOT / "research"

FILES = [
    "01-epam-assessment.md",
    "02-sql-deep-dive.md",
    "03-python-pyspark.md",
    "04-distributed-fundamentals.md",
    "05-platform-architecture.md",
    "06-batch-vs-streaming.md",
    "07-warehouse-lakehouse.md",
    "08-snowflake-vs-databricks.md",
    "09-table-formats.md",
    "10-spark-vs-flink.md",
    "11-spark-optimization.md",
    "12-messaging-kafka.md",
    "13-pipeline-reliability.md",
    "14-resources-practice.md",
    "15-interview-prep.md",
    "16-genai-design.md",
    "17-ml-design.md",
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

# Duolingo-style path metadata — order matches FILES.
NODES = [
    {"icon": "🧭", "short": "Assessment",  "blurb": "EPAM A3 ladder, 6-round loop, grading signals, prep plan."},
    {"icon": "🧮", "short": "SQL",         "blurb": "Window functions, classic problems, query optimization."},
    {"icon": "🐍", "short": "PySpark",     "blurb": "Live-coding patterns, driver/executor model, skew fixes."},
    {"icon": "🌐", "short": "Distributed", "blurb": "CAP, consistency, replication, idempotency, time."},
    {"icon": "🏗️", "short": "Architecture","blurb": "Layers, medallion, modeling, CDC, SCD, contracts."},
    {"icon": "🌊", "short": "Streaming",   "blurb": "Batch vs streaming, watermarks, Lambda vs Kappa."},
    {"icon": "🏬", "short": "Lakehouse",   "blurb": "Warehouse vs lake vs lakehouse, disaggregation, ELT."},
    {"icon": "❄️", "short": "Snow v DBX",  "blurb": "Architecture, credits vs DBUs, decision matrix, lock-in."},
    {"icon": "🧊", "short": "Formats",     "blurb": "Delta / Iceberg / Hudi internals and when each wins."},
    {"icon": "⚡", "short": "Engines",     "blurb": "Spark DAG/shuffle/Catalyst vs Flink state/checkpoints."},
    {"icon": "🔧", "short": "Spark Tuning","blurb": "Catalyst optimizer, AQE, join strategies, shuffle & memory tuning, Spark UI."},
    {"icon": "📨", "short": "Kafka",       "blurb": "Partitions, ISR, producers/consumers, outbox, sizing."},
    {"icon": "🛡️", "short": "Reliability", "blurb": "Quality dimensions, tests, SLOs, incident playbook."},
    {"icon": "📚", "short": "Practice",    "blurb": "Best sources, drills, and portfolio projects to build real skill."},
    {"icon": "🎯", "short": "Playbook",    "blurb": "Six-step framework, 3 worked scenarios, capacity math."},
    {"icon": "🤖", "short": "GenAI",      "blurb": "GenAI system design: one framework, 11 designs — RAG, LLM serving, diffusion."},
    {"icon": "🧠", "short": "ML Design",  "blurb": "ML system design: 7-step framework, retrieval→ranking, recsys/ads at scale."},
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

# Module grouping for sidebar/map narrative (index = FILE index).
MODULES = [
    ("🎯 Goal & Foundations", 0, 4),      # 01–04: assessment, SQL, PySpark, distributed
    ("🏗️ Platform Design",   4, 8),      # 05–08: architecture, streaming, lakehouse, vendors
    ("⚙️ Technology Deep-Dive", 8, 12),  # 09–12: formats, engines, tuning, kafka
    ("🏁 Production & Defense", 12, 15), # 13–15: reliability, practice, playbook
    ("🤖 GenAI & ML Design",  15, 26), # 16–26: genai + ml system design + nine deep-dive topics
]

def module_of(i):
    for name, a, b in MODULES:
        if a <= i < b: return name
    return ""

def page_url(i):
    return f"s{i+1:02d}.html"

def slugify(text):
    s = re.sub(r'<[^>]+>', '', text)
    s = re.sub(r'[*_`]', '', s).strip().lower()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    return s or "section"

# ---------------- mermaid injections ----------------
LEARNING_MAP = """graph LR
  A[Assessment<br/>EPAM A3] --> B[Core Skills<br/>SQL · PySpark ·<br/>Distributed]
  B --> C[Platform<br/>Architecture]
  C --> D1[Batch vs<br/>Streaming]
  C --> D2[Warehouse /<br/>Lakehouse]
  D1 --> E1[Snowflake vs<br/>Databricks]
  D2 --> E1
  D1 --> E2[Delta / Iceberg /<br/>Hudi]
  D1 --> E3[Spark vs<br/>Flink]
  D1 --> E4[Kafka &<br/>Queues]
  D1 --> E5[Spark<br/>Tuning]
  E1 --> F[Reliability &<br/>Playbook]
  E2 --> F
  E3 --> F
  E4 --> F
  E5 --> F
  style A fill:#e6f1fd,stroke:#5672cd,color:#1e2327
  style F fill:#e6f1fd,stroke:#5672cd,color:#1e2327"""

INJECTIONS = {}  # kept for API compat; agents embed their own mermaid

md = MarkdownIt("commonmark", {"html": True, "linkify": True, "breaks": False})
md.enable("table")

MERMAID_FENCE_RE = re.compile(r'```mermaid\n(.*?)```', re.S)
CONTAINER_OPEN_RE = re.compile(r'^:{3,}\s*(info|tip|warning|diagram|scenario|tldr|cards|lab)\s*(.*)$')
STUDY_SLOT_RE = re.compile(r'^(TLDRSLOT|CARDSLOT)\d+X$')
SC_NODE_RE  = re.compile(r'^@(\w+)\s+(.*?)\s*::\s*(.+)$')
SC_EDGE_RE  = re.compile(r'^(->|\?)\s*(?:(.*?)\s*=>\s*)?@(\w+)(\s*\|\s*(success|fail))?$')
def preprocess(src):
    """Extract mermaid fences; convert :::containers to placeholders."""
    mer, scenarios = [], []
    def stash(m):
        mer.append(m.group(1).strip())
        return f"\nMERMAIDPLOT{len(mer)-1}X\n"
    src = MERMAID_FENCE_RE.sub(stash, src)

    used_terms = set()
    def term_wrap(line):
        for t in GLOSS_TERMS:
            if t.lower() in used_terms: continue
            m = re.search(r'\b' + re.escape(t) + r's?\b', line, 0 if re.search(r'[A-Z]', t) else re.I)
            if m:
                used_terms.add(t.lower())
                return (line[:m.start()] + f'<span class="term" data-term="{html.escape(t)}">'
                        + m.group(0) + '</span>' + line[m.end():])
        return line
    tldrs, cardss = [], []
    out, in_c, lines_acc = [], False, []
    for line in src.split("\n"):
        s = line.strip()
        mo = CONTAINER_OPEN_RE.match(s)
        if mo and not in_c:
            typ, title = mo.group(1), mo.group(2).strip()
            if typ in ("tldr", "cards"):
                in_c, lines_acc, sc_title = typ, [], title
                continue
            if typ == "scenario":
                in_c, lines_acc, sc_title = "scenario", [], title
                continue
            if typ == "diagram":
                slug = title or "diagram"
                s = html.escape(slug)
                if slug.endswith(".png"):
                    dk = s[:-4] + ".dark.png"
                    out.append(f'<div class="dg-frame dg-png"><img class="dg-light" src="diagrams/exc/{s}" alt="{s} diagram" loading="lazy"><img class="dg-dark" src="diagrams/exc/{dk}" alt="{s} diagram (dark)" loading="lazy"></div>')
                else:
                    out.append(f'<div class="dg-frame"><iframe src="diagrams/{s}.html" title="{s} diagram" loading="lazy"></iframe></div>')
                in_c = "skip"
                continue
            if typ == "lab":
                if title not in ("skew", "watermark"):
                    raise ValueError(f"unknown lab {title!r}")
                out.append(f'<div class="lab" id="lab-{title}">')
                in_c, lines_acc = "lab", []
                continue
            t = f'<div class="ct-title">{html.escape(title)}</div>' if title else ""
            out += [f'<div class="ct ct-{typ}">', t, ""]
            in_c = True
            continue
        if re.match(r'^:{3,}$', s) and in_c:
            if in_c == "scenario":
                scenarios.append(scenario_parse(sc_title, lines_acc))
                out.append(f"\nSCENARIOPLOT{len(scenarios)-1}X\n")
            elif in_c == "tldr":
                tldrs.append([l.strip("- ").strip() for l in lines_acc if l.strip()])
                out.append(f"\nTLDRSLOT{len(tldrs)-1}X\n")
            elif in_c == "cards":
                cardss.append([l for l in lines_acc if l.strip()])
                out.append(f"\nCARDSLOT{len(cardss)-1}X\n")
            elif in_c == "lab":
                out += [md.render("\n".join(lines_acc)), "</div>"]
            elif in_c == "skip":
                pass
            else:
                out += ["", "</div>"]
            in_c = False
            continue
        if in_c in ("scenario", "tldr", "cards", "lab"):
            lines_acc.append(line)
            continue
        if not in_c and not s.startswith('#') and '`' not in line and '|' not in line:
            line = term_wrap(line)
        out.append(line)
    if in_c in ("scenario", "tldr", "cards", "lab"):
        raise ValueError(f"Unclosed :::{in_c} block")
    return "\n".join(out), mer, scenarios, tldrs, cardss

def scenario_parse(title, lines):
    nodes, edges, order, last = [], [], [], None
    for ln in lines:
        ln = ln.strip()
        if not ln: continue
        m = SC_NODE_RE.match(ln)
        if m:
            nid = m.group(1)
            nodes.append({"id": nid, "label": m.group(2), "cap": m.group(3)})
            order.append(nid); last = nid
            continue
        m = SC_EDGE_RE.match(ln)
        if m:
            tok, label, dst, kind = m.group(1), m.group(2), m.group(3), m.group(5)
            if last is None:
                raise ValueError(f"edge before any node in {title!r}: {ln!r}")
            edges.append({"src": last, "label": label, "dst": dst, "kind": kind,
                          "choice": tok == "?", "loop": dst in {n["id"] for n in nodes}})
            continue
        raise ValueError(f"Malformed scenario line in {title!r}: {ln!r}")
    ids = {n["id"] for n in nodes}
    for e in edges:
        if e["dst"] not in ids:
            raise ValueError(f"Scenario {title!r}: edge to unknown node @{e['dst']}")
    return {"title": title, "nodes": nodes, "edges": edges,
            "start": order[0] if order else None}

def scenario_html(g, idx):
    return (f'<div class="scenario" data-sc="{idx}">'
            f'<div class="sc-head"><span><span class="sc-ic">🧭</span><b>Scenario · {html.escape(g["title"])}</b></span></div>'
            f'<div class="sc-body"><div class="sc-bar"><button data-a="zout">−</button><button data-a="zpct" class="sc-pct">100%</button><button data-a="zin">+</button><button data-a="hl">✎</button><button data-a="reset">↺</button><button data-a="reveal">◉</button></div></div>'
            f'<div class="sc-panel"><div class="sc-cap"></div><div class="sc-choices"></div></div>'
            f'<script type="application/json" class="sc-json">{json.dumps(g, ensure_ascii=False).replace("<", "\\u003c")}</script></div>')

def render_page(src, sec_no):
    """Render a section file: ## → h1, ### → h2 with anchors."""
    src, mer, scenarios, tldrs, cardss = preprocess(src)
    lines = src.split("\n")
    subs = []
    h1_title = None
    used = set()
    def uid(base):
        i, n = base, 2
        while i in used:
            i = f"{base}-{n}"; n += 1
        used.add(i); return i
    buf = []
    def flush():
        if not buf: return ""
        return md.render("\n".join(buf))
    parts = []
    for line in lines:
        m2 = re.match(r'^(##)\s+(.*)$', line)
        m3 = re.match(r'^(###)\s+(.*)$', line)
        if m2 and not m3:
            parts.append(flush()); buf.clear()
            t = m2.group(2).strip()
            h1_title = t
            parts.append(f'<div class="kicker">Section {sec_no} of {len(FILES)}</div>'
                         f'<h1>{md.renderInline(t)}</h1>')
            continue
        if m3:
            parts.append(flush()); buf.clear()
            t = m3.group(2).strip()
            hid = uid(slugify(t))
            subs.append((t, hid))
            parts.append(f'<h2 id="{hid}" tabindex="-1">{md.renderInline(t)}'
                         f'<a class="header-anchor" href="#{hid}">&ZeroWidthSpace;</a></h2>')
            continue
        if STUDY_SLOT_RE.match(line.strip()): continue
        buf.append(line)
    parts.append(flush())
    out = "\n".join(parts)
    for i, m in enumerate(mer):
        out = out.replace(f"MERMAIDPLOT{i}X", f'<div class="mermaid">\n{m}\n</div>')
    for i, g in enumerate(scenarios):
        out = out.replace(f"SCENARIOPLOT{i}X", scenario_html(g, i))
    return out, h1_title, subs, tldrs, cardss

# ---------------- glossary (loaded before section collection for term wrapping) ----------------
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

study = {"cards": [], "terms": [], "edges": [], "termRefs": {}, "tldr": {}}
_glossary_path = RESEARCH / "glossary.md"
if _glossary_path.exists():
    study["terms"], study["edges"] = parse_glossary(_glossary_path.read_text())
GLOSS_TERMS = sorted((t["t"] for t in study["terms"]), key=len, reverse=True)

# ---------------- collect sections ----------------
sections = []
for idx, fname in enumerate(FILES):
    src = (RESEARCH / fname).read_text()
    rendered, title, subs, tldrs, cardss = render_page(src, idx + 1)
    if len(tldrs) > 1 or len(cardss) > 1:
        raise SystemExit(f"duplicate tldr/cards block in section {idx+1}")
    sections.append({"i": idx, "file": fname, "title": title, "url": page_url(idx),
                     "subs": subs, "html": rendered,
                     "tldr": tldrs[0] if tldrs else [], "cards": cardss[0] if cardss else []})

# ---------------- study.json ----------------

def parse_study(src, sec_no):
    """Extract tldr bullets + flashcards from one section's raw markdown."""
    _, _, _, tldrs, cardss = preprocess(src)
    cards = []
    for k, ln in enumerate([l for blk in cardss for l in blk], 1):
        q, _, a = ln.partition(" :: ")
        if q.startswith("Q: "): q = q[len("Q: "):]
        cards.append({"id": f"s{sec_no:02d}-{k}", "sec": sec_no, "q": q.strip(), "a": a.strip()})
    return (tldrs[0] if tldrs else []), cards

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
    for sec in range(1, len(FILES) + 1):
        cs = [c for c in study["cards"] if c["sec"] == sec]
        tl = study.get("tldr", {}).get(sec)
        if len(cs) < 4 or not tl or not (5 <= len(tl) <= 7):
            errs.append(f"section {sec} needs 4+ cards and 5-7 tldr bullets")
    if errs: raise SystemExit("study validation failed:\n  " + "\n  ".join(errs))

if "--selftest" in __import__("sys").argv:
    bad = [
        ({"cards":[{"id":"x","sec":1,"q":"","a":"a"}],"terms":[],"edges":[]}, "empty card"),
        ({"cards":[{"id":"x","sec":1,"q":"q","a":"a"},{"id":"x","sec":1,"q":"q","a":"a"}],"terms":[],"edges":[]}, "duplicate card id"),
        ({"cards":[],"terms":[{"t":"A","def":"d"},{"t":"a","def":"d"}],"edges":[]}, "duplicate term"),
        ({"cards":[],"terms":[{"t":"A","def":"d"}],"edges":[{"a":"A","b":"B","why":"w"}]}, "unknown term"),
        ({"cards":[{"id":f"s1-{k}","sec":1,"q":"q","a":"a"} for k in range(4)],
          "terms":[],"edges":[],"tldr":{1:["b"]*3}}, "section 1 needs 4+ cards and 5-7 tldr bullets"),
    ]
    for study, why in bad:
        try: validate_study(study)
        except SystemExit as ex: assert why in str(ex), why; continue
        raise SystemExit(f"selftest failed: {why} not caught")
    for probe in (":::cards\nQ: a :: b\n", ":::tldr\n- b\n"):
        try: preprocess(probe)
        except ValueError as ex: assert "Unclosed" in str(ex), probe; continue
        raise SystemExit(f"selftest failed: unclosed block not caught: {probe!r}")
    ok = {"cards":[{"id":f"s{s}-{k}","sec":s,"q":"q","a":"a"}
                   for s in range(1, len(FILES) + 1) for k in range(4)],
          "terms":[],"edges":[],"tldr":{s:["b"]*5 for s in range(1, len(FILES) + 1)}}
    validate_study(ok)
    print("selftest OK"); __import__("sys").exit(0)

for s in sections:
    if s["tldr"]: study["tldr"][s["i"] + 1] = s["tldr"]
    study["cards"] += parse_study((RESEARCH / s["file"]).read_text(), s["i"] + 1)[1]
for t in study["terms"]:
    pat = re.compile(rf'\b{re.escape(t["t"])}s?\b', 0 if re.search(r'[A-Z]', t["t"]) else re.I)
    study["termRefs"][t["t"]] = [s["i"] + 1 for s in sections
                                 if pat.search((RESEARCH / s["file"]).read_text())]
validate_study(study)
(ROOT / "study.json").write_text(json.dumps(study, ensure_ascii=False, indent=1))

# ---------------- nav pieces ----------------
def strip(t):
    return html.escape(re.sub(r"<[^>]+>", "", t))

def nav_items(active=-1):
    lis = []
    last_mod = None
    for s in sections:
        m = module_of(s["i"])
        if m != last_mod:
            lis.append(f'<li class="nav-mod">{html.escape(m)}</li>')
            last_mod = m
        cls = "sidebar-link" + (" active" if s["i"] == active else "")
        lis.append(f'<li><a class="{cls}" href="{s["url"]}"><span class="sl-num">{s["i"]+1:02d}</span>{strip(s["title"])}</a></li>')
    return "\n".join(lis)

def outline_items(sec):
    lis = [f'<li><a class="outline-link lvl2" href="#">Overview</a></li>']
    for st, sid in sec["subs"]:
        lis.append(f'<li><a class="outline-link lvl3" href="#{sid}">{strip(st)}</a></li>')
    return "\n".join(lis)

def pager(i):
    prev_s = sections[i-1] if i > 0 else None
    next_s = sections[i+1] if i < len(sections)-1 else None
    p = f'<a class="prev" href="{prev_s["url"]}"><div class="plabel">Previous</div><div class="ptitle">← {strip(prev_s["title"])}</div></a>' if prev_s else '<span></span>'
    n = f'<a class="next" href="{next_s["url"]}"><div class="plabel">Next</div><div class="ptitle">{strip(next_s["title"])} →</div></a>' if next_s else '<span></span>'
    return f'<div class="pager">{p}{n}</div>'

# ---------------- Duolingo path ----------------
NODE_X = [0, 70, 110, 70, 0, -70, -110, -70, 0, 70, 110, 70, 0]

def vmap_svg():
    W, H, cx, step = 340, 40 + 96 * len(NODES), 170, 96
    pts = [(cx + NODE_X[i % len(NODE_X)], 60 + i * step) for i in range(len(NODES))]
    d = f"M {pts[0][0]} {pts[0][1]}"
    for i in range(1, len(pts)):
        x0, y0 = pts[i-1]; x1, y1 = pts[i]
        my = (y0 + y1) / 2
        d += f" C {x0} {my}, {x1} {my}, {x1} {y1}"
    return (f'<svg class="vm-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Course path">'
            f'<path class="vm-path" d="{d}" fill="none"/></svg>')

def vmap_html():
    step = 96
    items = []
    for i, (n, s) in enumerate(zip(NODES, sections)):
        x = NODE_X[i % len(NODE_X)]
        top = 60 + i * step
        side = "l" if x > 40 else "r"
        items.append(
            f'''<div class="vm-node" data-n="{i}" data-side="{side}" style="left:calc(50% + {x - 36}px);top:{top - 30}px">
  <a class="vm-btn" href="{s["url"]}" aria-label="{html.escape(n["short"])}"><span class="vm-icon">{n["icon"]}</span><span class="vm-check">✓</span></a>
  <div class="vm-num">{i+1}</div>
  <div class="vm-card">
    <div class="vm-card-title">{i+1}. {html.escape(n["short"])}</div>
    <div class="vm-card-blurb">{html.escape(n["blurb"])}</div>
    <a class="vm-go" href="{s["url"]}">Go →</a>
  </div>
</div>''')
    mods = []
    for name, a, b in MODULES:
        top = 60 + a * step - 34
        h = (b - a) * step - 22
        mods.append(f'<div class="vm-mod" style="top:{top}px;height:{h}px"><span>{html.escape(name)}</span></div>')
    return f'''<div class="vmap" id="vmap">
  <div class="vmap-head"><span>Course Path</span><span class="vm-progress" id="vmProgress">0 / {len(NODES)}</span></div>
  <div class="vmap-body">
    {"".join(mods)}
    {vmap_svg()}
    {"".join(items)}
  </div>
</div>'''

def path_widget():
    """Compact numbered path for section pages."""
    lis = []
    for i, (n, s) in enumerate(zip(NODES, sections)):
        lis.append(f'''<li class="pw-item" data-n="{i}"><a class="pw-link" href="{s["url"]}">
  <span class="pw-ic">{n["icon"]}</span><span class="pw-name">{i+1}. {html.escape(n["short"])}</span><span class="pw-check">✓</span>
</a></li>''')
    return f'<div class="group-title">Course Path <span class="vm-progress" id="vmProgress2"></span></div><ul class="pathlist">{"".join(lis)}</ul>'

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --vp-c-brand-1:#D95C41;--vp-c-brand-2:#C14E36;--vp-c-brand-3:#A8412B;
  --vp-c-brand-soft:rgba(217,92,65,.1);
  --vp-c-bg:#FAF9F5;--vp-c-bg-alt:#F4F3EE;--vp-c-bg-elv:#FFFFFF;
  --vp-c-divider:rgba(0,0,0,.08);--vp-c-text-1:#1A1A1A;--vp-c-text-2:#4A4A4A;
  --vp-c-text-3:#757575;
  --vp-code-bg:rgba(142,150,170,.14);--vp-code-color:#1A1A1A;
  --vp-c-tip-1:#D95C41;
  --nav-h:64px;--sidebar-w:272px;--outline-w:256px;
  --font-body:"Inter",ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --font-head:"Newsreader",serif;
  --font-mono:"JetBrains Mono","Fira Code",ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
html.dark{
  --vp-c-brand-1:#E07A64;--vp-c-brand-2:#E07A64;--vp-c-brand-3:#D95C41;
  --vp-c-brand-soft:rgba(224,122,100,.15);
  --vp-c-bg:#1A1A1A;--vp-c-bg-alt:#242424;--vp-c-bg-elv:#242424;
  --vp-c-divider:rgba(255,255,255,.1);--vp-c-text-1:#E5E5E5;--vp-c-text-2:#B3B3B3;
  --vp-c-text-3:#808080;
  --vp-code-bg:rgba(101,117,133,.16);--vp-code-color:#E5E5E5;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:calc(var(--nav-h) + 24px)}
body{margin:0;font-family:var(--font-body);font-size:16px;line-height:1.7;color:var(--vp-c-text-1);background:var(--vp-c-bg);-webkit-font-smoothing:antialiased;overflow-x:clip}
a{color:var(--vp-c-brand-2);text-decoration:none}
a:hover{color:var(--vp-c-brand-1)}

/* ---------- navbar ---------- */
.nav{position:fixed;top:0;left:0;right:0;height:var(--nav-h);display:flex;align-items:center;gap:12px;padding:0 32px;border-bottom:1px solid var(--vp-c-divider);background:var(--vp-c-bg);z-index:100}
.nav .logo{display:flex;align-items:center;gap:8px;font-weight:600;font-size:16px;color:var(--vp-c-text-1);text-decoration:none}
.nav .logo svg{flex:none}
.nav .spacer{flex:1}
.nav .search-box{display:flex;align-items:center;gap:8px;border:1px solid var(--vp-c-divider);border-radius:8px;padding:6px 12px;color:var(--vp-c-text-3);font-size:13px;background:var(--vp-c-bg-alt);min-width:180px;cursor:text}
.nav .search-box kbd{margin-left:auto;border:1px solid var(--vp-c-divider);border-radius:4px;padding:0 5px;font-size:11px;font-family:var(--font-mono);background:var(--vp-c-bg)}
.nav .theme-btn{border:none;background:none;cursor:pointer;color:var(--vp-c-text-2);padding:8px;display:flex;border-radius:50%}
.nav .theme-btn:hover{background:var(--vp-c-brand-soft);color:var(--vp-c-text-1)}
.menu-toggle{display:none;border:none;background:none;color:var(--vp-c-text-2);cursor:pointer;padding:8px}
.nav .home-link{color:var(--vp-c-text-2);font-size:14px;padding:8px;border-radius:8px;text-decoration:none}
.nav .home-link:hover{color:var(--vp-c-text-1);background:var(--vp-c-brand-soft)}

/* ---------- layout ---------- */
.layout{display:flex;padding-top:var(--nav-h);overflow-x:clip}
.sidebar{position:fixed;top:var(--nav-h);bottom:0;left:0;width:var(--sidebar-w);overflow-y:auto;padding:24px 8px 96px 32px;border-right:1px solid var(--vp-c-divider);background:var(--vp-c-bg)}
.sidebar .group-title{font-weight:700;font-size:14px;padding:8px 12px 4px;display:flex;justify-content:space-between;align-items:center}
.sidebar ul{list-style:none;margin:0;padding:0}
.sidebar-link{display:flex;gap:8px;align-items:baseline;padding:5px 12px;font-size:14px;color:var(--vp-c-text-2);border-left:2px solid transparent;border-radius:0 4px 4px 0;line-height:1.4;text-decoration:none}
.sidebar-link:hover{color:var(--vp-c-text-1)}
.sidebar-link.active{color:var(--vp-c-brand-2);font-weight:600;border-left-color:var(--vp-c-brand-2);background:var(--vp-c-brand-soft)}
.sl-num{font-size:11px;color:var(--vp-c-text-3);font-family:var(--font-mono);flex:none}
.sidebar-link.active .sl-num{color:var(--vp-c-brand-2)}
.main{flex:1;min-width:0;margin-left:var(--sidebar-w)}
@media(min-width:1440px){.main{margin-right:var(--outline-w)}}
.vp-doc{max-width:784px;margin:0 auto;padding:32px 24px 96px}

/* ---------- outline ---------- */
.outline{position:fixed;top:var(--nav-h);right:0;bottom:0;width:var(--outline-w);overflow-y:auto;padding:24px 16px 96px;border-left:1px solid var(--vp-c-divider);display:none}
@media(min-width:1440px){.outline{display:block}}
.outline .outline-title{font-weight:600;font-size:14px;padding:0 12px 8px}
.outline ul{list-style:none;margin:0;padding:0;border-left:1px solid var(--vp-c-divider)}
.outline-link{display:block;padding:4px 12px;font-size:13px;color:var(--vp-c-text-3);border-left:2px solid transparent;margin-left:-1px;line-height:1.4;text-decoration:none}
.outline-link.lvl3{padding-left:26px}
.outline-link:hover{color:var(--vp-c-text-1)}
.outline-link.active{color:var(--vp-c-brand-2);border-left-color:var(--vp-c-brand-2)}

/* ---------- typography ---------- */
.vp-doc .kicker{font-size:13px;font-weight:700;color:var(--vp-c-brand-2);letter-spacing:.5px;text-transform:uppercase}
.vp-doc h1{font-family:var(--font-head);font-size:40px;font-weight:600;letter-spacing:-.02em;margin:4px 0 24px;line-height:1.1}
.vp-doc h2{font-family:var(--font-head);font-size:32px;font-weight:600;letter-spacing:-.02em;margin:48px 0 16px;padding-top:24px;border-top:1px solid var(--vp-c-divider);line-height:1.2;position:relative}
.vp-doc h3{font-family:var(--font-head);font-size:24px;font-weight:600;margin:32px 0 12px;line-height:1.25}
.vp-doc h4{font-family:var(--font-body);font-size:16px;font-weight:700;margin:20px 0 8px;color:var(--vp-c-text-1)}
.vp-doc p{margin:16px 0}
.header-anchor{position:absolute;left:-0.7em;opacity:0;color:var(--vp-c-brand-2);font-weight:500;text-decoration:none;transition:opacity .2s}
.vp-doc h2:hover .header-anchor,.header-anchor:focus{opacity:1}
.header-anchor::before{content:"#"}
.vp-doc strong{font-weight:600}
.vp-doc code{font-family:var(--font-mono);font-size:.875em;background:var(--vp-code-bg);color:var(--vp-code-color);padding:.15em .35em;border-radius:4px}
.vp-doc pre{position:relative;margin:16px 0;padding:20px 24px;border-radius:8px;background:var(--vp-code-bg);overflow-x:auto;font-size:14px;line-height:1.7}
.vp-doc pre code{background:none;padding:0;color:inherit;font-size:inherit}
.vp-doc pre .copy-btn{position:absolute;top:8px;right:8px;border:1px solid var(--vp-c-divider);border-radius:4px;background:var(--vp-c-bg);color:var(--vp-c-text-3);font-size:11px;padding:2px 8px;cursor:pointer;opacity:0;transition:opacity .2s;font-family:var(--font-body)}
.vp-doc pre:hover .copy-btn{opacity:1}
.vp-doc blockquote{margin:16px 0;padding:8px 16px;border-left:4px solid var(--vp-c-divider);color:var(--vp-c-text-2)}
.vp-doc blockquote p{margin:4px 0}
.vp-doc ul,.vp-doc ol{padding-left:1.25rem;margin:16px 0}
.vp-doc li{margin:4px 0}
.vp-doc li::marker{color:var(--vp-c-text-3)}
.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:20px 0}
.vp-doc table{border-collapse:collapse;width:100%;margin:0;font-size:14px}
.vp-doc th,.vp-doc td{border:1px solid var(--vp-c-divider);padding:8px 16px;text-align:left;line-height:1.6}
.vp-doc th{background:var(--vp-c-bg-alt);font-weight:600}
.vp-doc tr:nth-child(2n) td{background:var(--vp-c-bg-alt)}

/* tables: stacked cards on small screens */
@media (max-width:768px){
.table-wrap{overflow:visible;margin:16px 0}
.vp-doc table{display:block;border-collapse:separate;font-size:13.5px}
.vp-doc thead{display:none}
.vp-doc tbody{display:block}
.vp-doc tr{display:block;border:1px solid var(--vp-c-divider);border-radius:10px;
  background:var(--vp-c-bg-elv);margin:0 0 10px;overflow:hidden}
.vp-doc tr:nth-child(2n) td{background:transparent}
.vp-doc td{display:flex;gap:10px;border:none;border-bottom:1px solid var(--vp-c-divider);
  padding:8px 12px;align-items:baseline}
.vp-doc td:last-child{border-bottom:none}
.vp-doc td::before{content:attr(data-th);flex:0 0 38%;font-weight:600;font-size:11.5px;
  color:var(--vp-c-text-3);text-transform:uppercase;letter-spacing:.4px;line-height:1.5}
.vp-doc td>a,.vp-doc td code{font-size:inherit}
}
@media (min-width:769px){
.vp-doc table{min-width:520px}
}
.vp-doc hr{border:none;border-top:1px solid var(--vp-c-divider);margin:40px 0}
.vp-doc a{text-decoration:underline;text-underline-offset:2px}
.vp-doc a:hover{text-decoration:none}
.vp-doc a.vm-btn,.vp-doc a.pw-link,.vp-doc .pager a,.vp-doc .feature a,.vp-doc .btn,.vp-doc a.vm-go{text-decoration:none}
.vp-doc pre.ascii{font-size:12.5px;line-height:1.5}

/* hero */
.hero{padding:24px 0 8px}
.hero .kicker{font-size:14px;font-weight:600;color:var(--vp-c-brand-2);letter-spacing:.5px;text-transform:uppercase}
.hero h1{font-family:var(--font-head);font-size:56px;font-weight:600;margin:8px 0 12px;line-height:1.1;color:var(--vp-c-brand-1)}
.hero .tagline{font-size:18px;color:var(--vp-c-text-2);max-width:640px}
.hero .actions{margin-top:20px;display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;padding:10px 20px;border-radius:20px;font-weight:600;font-size:14px;border:1px solid var(--vp-c-divider)}
.btn.brand{background:#A8412B;color:#fff!important;border-color:#A8412B}
.btn.brand:hover{background:#C14E36}
.btn.alt{background:var(--vp-c-bg-alt);color:var(--vp-c-text-1)!important}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:36px 0 8px}
.feature{border:1px solid var(--vp-c-divider);border-radius:12px;padding:20px;background:var(--vp-c-bg-elv);transition:border-color .2s}
.feature:hover{border-color:var(--vp-c-brand-3)}
.feature .icon{font-size:22px}
.feature h3{margin:8px 0 6px;font-size:16px}
.feature p{margin:0;font-size:13.5px;color:var(--vp-c-text-2);line-height:1.55}
.feature a{font-size:13px;font-weight:600}

/* mermaid */
.mermaid{display:flex;justify-content:center;margin:24px 0;padding:16px;background:var(--vp-c-bg-alt);border:1px solid var(--vp-c-divider);border-radius:12px;overflow-x:auto}
.mermaid svg{max-width:100%;height:auto}

/* custom containers */
.ct{margin:18px 0;padding:14px 18px;border:1px solid var(--vp-c-divider);border-radius:10px;background:var(--vp-c-bg-elv);font-size:14.5px;line-height:1.65}
.ct p{margin:6px 0}
.ct .ct-title{font-weight:700;font-size:13px;letter-spacing:.4px;text-transform:uppercase;margin-bottom:6px}
.ct-info{border-left:4px solid var(--vp-c-brand-3)}
.ct-info .ct-title{color:var(--vp-c-brand-2)}
.ct-tip{border-left:4px solid #22a55b;background:rgba(34,165,91,.07)}
.ct-tip .ct-title{color:#1d914e}
.ct-warning{border-left:4px solid #e38407;background:rgba(227,132,7,.08)}
.ct-warning .ct-title{color:#b4690e}
html.dark .ct-tip{background:rgba(34,165,91,.12)}
html.dark .ct-tip .ct-title{color:#4ccb7f}
html.dark .ct-warning{background:rgba(227,132,7,.12)}
html.dark .ct-warning .ct-title{color:#f0b45c}

/* ---------- Duolingo path map ---------- */
.vmap{margin:28px 0 8px;border:1px solid var(--vp-c-divider);border-radius:16px;background:var(--vp-c-bg-elv);overflow:hidden}
.vmap-head{display:flex;justify-content:space-between;align-items:center;padding:10px 18px;border-bottom:1px solid var(--vp-c-divider);font-weight:700;font-size:14px}
.vm-progress{color:var(--vp-c-text-3);font-weight:600;font-size:13px}
.vmap-body{position:relative;padding:8px 0 24px}
.vm-svg{display:block;margin:0 auto;width:340px;height:auto}
.nav-mod{font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:var(--vp-c-text-3);padding:14px 12px 3px}
.vm-mod{position:absolute;left:12px;right:12px;border:1px dashed var(--vp-c-divider);border-radius:12px;pointer-events:none}
.vm-mod span{position:absolute;top:-9px;left:14px;background:var(--vp-c-bg-elv);padding:0 8px;font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--vp-c-text-3)}
.vm-path{stroke:var(--vp-c-divider);stroke-width:14;stroke-linecap:round;stroke-dasharray:0 18}
.vm-node{position:absolute;width:72px;height:64px}
.vm-btn{position:relative;width:64px;height:60px;border:none;border-radius:50%;background:var(--vp-c-bg-alt);border-bottom:5px solid var(--vp-c-divider);cursor:pointer;font-size:26px;display:flex;align-items:center;justify-content:center;transition:transform .12s,filter .2s;padding:0;color:var(--vp-c-text-1)}
.vm-btn:hover{transform:scale(1.08);filter:brightness(1.05)}
.vm-btn:active{transform:translateY(3px);border-bottom-width:2px}
.vm-check{position:absolute;right:-4px;bottom:-4px;width:22px;height:22px;border-radius:50%;background:#22a55b;color:#fff;font-size:13px;display:none;align-items:center;justify-content:center;border:2px solid var(--vp-c-bg-elv)}
.vm-node.done .vm-btn{background:#e3f5e9;border-bottom-color:#1d914e}
.vm-node.done .vm-check{display:flex}
html.dark .vm-node.done .vm-btn{background:#12351f}
.vm-node.current .vm-btn{background:var(--vp-c-brand-soft);border-bottom-color:var(--vp-c-brand-2);animation:vm-pulse 2s infinite}
@keyframes vm-pulse{0%,100%{box-shadow:0 0 0 6px var(--vp-c-brand-soft)}50%{box-shadow:0 0 0 12px var(--vp-c-brand-soft)}}
.vm-num{position:absolute;left:-26px;top:16px;font-size:12px;font-weight:700;color:var(--vp-c-text-3);width:20px;text-align:center}
.vm-card{position:absolute;min-width:180px;max-width:230px;background:var(--vp-c-bg);border:1px solid var(--vp-c-divider);border-radius:12px;padding:10px 14px;box-shadow:0 8px 24px rgba(0,0,0,.12);opacity:0;pointer-events:none;transition:opacity .15s;z-index:5;top:-18px;left:auto;right:calc(100% + 14px)}
.vm-node:hover .vm-card,.vm-node.open .vm-card{opacity:1;pointer-events:auto}
.vm-card-title{font-weight:700;font-size:14px}
.vm-card-blurb{font-size:12.5px;color:var(--vp-c-text-2);line-height:1.5;margin:4px 0 8px}
.vm-go{font-size:13px;font-weight:700}
.vm-node[data-side="r"] .vm-card{right:auto;left:calc(100% + 14px)}

/* compact path list (section pages) */
.pathlist{list-style:none;margin:0 0 8px;padding:0}
.pw-link{display:flex;align-items:center;gap:8px;padding:4px 12px;font-size:13px;color:var(--vp-c-text-2);border-radius:6px;text-decoration:none}
.pw-link:hover{background:var(--vp-c-bg-alt);color:var(--vp-c-text-1)}
.pw-ic{width:20px;flex:none}
.pw-name{flex:1}
.pw-check{color:#22a55b;font-weight:700;opacity:0}
.pw-item.done .pw-check{opacity:1}
.pw-item.done .pw-name{color:var(--vp-c-text-3);text-decoration:line-through}
.pw-item.current .pw-link{color:var(--vp-c-brand-2);font-weight:600;background:var(--vp-c-brand-soft)}

/* mark-as-read + pager */
.mark-done{display:inline-flex;align-items:center;gap:8px;margin-top:24px;padding:10px 18px;border-radius:20px;border:1px solid var(--vp-c-divider);background:var(--vp-c-bg-alt);color:var(--vp-c-text-1);font-weight:600;font-size:14px;cursor:pointer;font-family:var(--font-body)}
.mark-done:hover{border-color:#22a55b}
.mark-done.done{background:#e3f5e9;border-color:#1d914e;color:#1d914e}
html.dark .mark-done.done{background:#12351f;color:#4ccb7f;border-color:#4ccb7f}
.pager{display:flex;justify-content:space-between;gap:16px;margin-top:48px;padding-top:24px;border-top:1px solid var(--vp-c-divider)}
.pager a{flex:1;max-width:48%;border:1px solid var(--vp-c-divider);border-radius:8px;padding:12px 16px;font-size:14px}
.pager a .plabel{font-size:12px;color:var(--vp-c-text-3)}
.pager a .ptitle{font-weight:600;color:var(--vp-c-brand-2)}
.pager a.next{text-align:right;margin-left:auto}
.footer-note{text-align:center;color:var(--vp-c-text-3);font-size:13px;margin-top:48px}

@media(max-width:960px){
  .sidebar{display:none}
  .sidebar.open{display:block;position:fixed;z-index:99;top:var(--nav-h);left:0;bottom:0;background:var(--vp-c-bg);width:min(320px,85vw);box-shadow:0 8px 24px rgba(0,0,0,.15)}
  .main{margin-left:0}
  .menu-toggle{display:flex}
  .nav{padding:0 16px}
  .nav .search-box{display:none}
  .vp-doc{padding:24px 16px 96px}
  .hero h1{font-size:30px}
  .vp-doc table{table-layout:fixed}
  .vp-doc th{white-space:normal}
  .vp-doc td,.vp-doc th{overflow-wrap:anywhere}
  .vp-doc code{overflow-wrap:anywhere;word-break:break-word}
  .vp-doc pre{font-size:12.5px;padding:14px 16px}
  .vp-doc pre code{overflow-wrap:normal;word-break:normal}
  .mermaid{padding:8px}
  .vm-num{display:none}
}
@media(max-width:760px){
  .vm-card{position:fixed;top:auto;bottom:16px;left:16px!important;right:16px!important;max-width:none;z-index:200}
  .vm-node.open::after{content:"";position:fixed;inset:0;background:rgba(0,0,0,.3);z-index:150;pointer-events:none}
  .vm-node.open .vm-btn{position:relative;z-index:160}
  .vm-svg{width:min(340px,90vw)}
}
@media(max-width:640px){
  .hero h1{font-size:26px}
  .hero .tagline{font-size:16px}
  .btn{padding:9px 14px;font-size:13px}
  .features{grid-template-columns:1fr 1fr}
  .vp-doc h1{font-size:26px}
  .vp-doc h2{font-size:20px}
  .vm-svg{width:min(300px,85vw)}
}
@media(max-width:420px){.features{grid-template-columns:1fr}}
.dg-frame{margin:18px 0;border:1px solid var(--vp-c-divider);border-radius:12px;overflow:hidden;background:var(--vp-c-bg-elv)}
.dg-frame iframe{display:block;width:100%;height:640px;border:0}
.dg-png img{display:block;width:100%;height:auto}
.dg-dark{display:none}
html.dark .dg-light{display:none}
html.dark .dg-dark{display:block}
.dg-png img{cursor:zoom-in}
@font-face{font-family:Excalifont;src:url(fonts/Excalifont.woff2) format('woff2');font-display:swap}
.scenario{margin:18px 0;border:1px solid var(--vp-c-divider);border-radius:12px;background:var(--vp-c-bg-elv);overflow:hidden}
.sc-head{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid var(--vp-c-divider);font-weight:600;font-size:14px}
.sc-head .sc-ic{margin-right:6px}
.sc-body{position:relative;height:420px;overflow:hidden;padding:0;cursor:grab;overscroll-behavior:contain;touch-action:none}
.sc-body.dragging{cursor:grabbing;user-select:none}
.sc-svg{display:block;position:absolute;top:0;left:0;transform-origin:0 0;font-family:Excalifont,cursive}
.sc-svg .sc-node{cursor:pointer}
.sc-svg text{font-family:Excalifont,cursive}
.sc-svg .sc-node text{stroke:#1f2937;stroke-width:.55px;paint-order:stroke fill;letter-spacing:.2px}
.sc-svg .sc-edge-lbl{paint-order:stroke;stroke:var(--vp-c-bg-elv);stroke-width:3.5px}
html.dark .sc-svg text{fill:#e5e7eb}
html.dark .sc-svg .sc-node text{stroke:#e5e7eb;stroke-width:.55px}
html.dark .sc-node.hl text{stroke:#ffffff}
html.dark .sc-svg .sc-edge-lbl{fill:#cbd5e1}
html.dark .sc-node[data-k=def] rect{fill:#1e3a5f;stroke:#7dd3fc}
html.dark .sc-node[data-k=start] rect{fill:#7c2d12;stroke:#fdba74}
html.dark .sc-node[data-k=choice] rect{fill:#78350f;stroke:#fbbf24}
html.dark .sc-node[data-k=ok] rect{fill:#064e3b;stroke:#34d399}
html.dark .sc-node[data-k=bad] rect{fill:#7f1d1d;stroke:#f87171}
html.dark .sc-edge[data-k=def]{stroke:#7dd3fc}
html.dark .sc-edge[data-k=ok]{stroke:#34d399}
html.dark .sc-edge[data-k=bad]{stroke:#f87171}
html.dark .sc-svg marker[id^="scA"]:not([id*="g"]):not([id*="r"]) path{fill:#7dd3fc}
html.dark .sc-svg marker[id*="Ag"] path{fill:#34d399}
html.dark .sc-svg marker[id*="Ar"] path{fill:#f87171}
.sc-panel{border-top:1px solid var(--vp-c-divider);padding:12px 14px;min-height:52px}
.sc-cap{font-size:14px;color:var(--vp-c-text-2);line-height:1.55}
.sc-choices{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.sc-btn{border:1.5px solid var(--vp-c-divider);border-radius:9px;background:var(--vp-c-bg);color:var(--vp-c-text-1);font-family:Excalifont,cursive;font-size:15px;padding:6px 14px;cursor:pointer}
.sc-btn:hover{border-color:var(--vp-c-brand-1);color:var(--vp-c-brand-1)}
.sc-btn.ok{border-color:#047857;color:#047857}
.sc-btn.bad{border-color:#dc2626;color:#dc2626}
.sc-bar{position:absolute;top:8px;right:8px;left:auto;display:flex;gap:4px;justify-content:flex-end;width:auto;padding:0;z-index:5;pointer-events:none}
.sc-bar>*{pointer-events:auto}
.sc-node.hl rect{fill:#fde047 !important}
html.dark .sc-node.hl rect{fill:#92400e !important}
html.dark .sc-node.hl text{fill:#ffffff !important}
.sc-bar button.on{color:var(--vp-c-brand-1);border-color:var(--vp-c-brand-1)}
.sc-bar button{border:1px solid var(--vp-c-divider);border-radius:7px;background:var(--vp-c-bg-elv);color:var(--vp-c-text-2);font-size:13px;padding:4px 10px;cursor:pointer;font-family:var(--font-body);box-shadow:0 1px 4px rgba(0,0,0,.15)}
.sc-bar button:hover{color:var(--vp-c-brand-1);border-color:var(--vp-c-brand-1)}
.sc-pct{min-width:52px;text-align:center;font-family:var(--vp-font-family-mono);font-size:11px}
html.dark .sc-btn{background:var(--vp-c-bg)}
.lb{position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.72);display:none}
.lb.open{display:block}
.lb-vp{position:absolute;inset:0;overflow:auto;padding:64px 20px 20px;cursor:zoom-out}
.lb-img{display:block;margin:0 auto;max-width:none;background:var(--vp-c-bg-elv);border-radius:10px}
.lb-bar{position:fixed;top:12px;right:16px;display:flex;gap:8px;z-index:201;align-items:center}
.lb-bar button{border:1px solid var(--vp-c-divider);border-radius:8px;background:var(--vp-c-bg-elv);color:var(--vp-c-text-1);font-size:15px;padding:5px 12px;cursor:pointer;font-family:var(--font-body)}
.lb-bar button:hover{border-color:var(--vp-c-brand-1);color:var(--vp-c-brand-1)}
.lb-pct{color:#fff;font-family:var(--vp-font-family-mono);font-size:12px;min-width:52px;text-align:center}
@media (max-width:640px){.dg-frame iframe{height:480px}}
/* glossary terms, popups, related chips */
.term{border-bottom:1px dotted var(--vp-c-brand-1);cursor:help}
.term-pop{position:absolute;max-width:340px;background:var(--vp-c-bg-elv);border:1px solid var(--vp-c-divider);border-radius:12px;padding:12px 14px;box-shadow:0 8px 24px rgba(0,0,0,.12);font-size:13px;z-index:60;color:var(--vp-c-text-1)}
.term-pop b{font-size:14px}
.term-pop p{margin:6px 0 0;line-height:1.55}
.term-pop .tp-links{margin-top:8px;font-size:12px;color:var(--vp-c-text-3)}
.term-pop .tp-links a{color:var(--vp-c-brand-1)}
.chip-row{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}
a.chip{padding:6px 12px;border-radius:16px;border:1px solid var(--vp-c-divider);background:var(--vp-c-bg-alt);font-size:13px;color:var(--vp-c-text-1);text-decoration:none}
a.chip:hover{border-color:var(--vp-c-brand-1);color:var(--vp-c-brand-1)}

/* ---------- self-check flipcards + review hub ---------- */
.selfcheck{margin:28px 0 0;padding:20px;border:1px solid var(--vp-c-divider);border-radius:12px;background:var(--vp-c-bg-alt)}
.sc-title{font-family:var(--font-head);font-size:20px;font-weight:600;margin:0 0 14px}
.sc-deck{display:grid;gap:14px}
.flipcard{perspective:1000px;cursor:pointer}
.fc-inner{display:grid;transition:transform .35s,opacity .2s;transform-style:preserve-3d;position:relative}
.flipcard.flipped .fc-inner{transform:rotateY(180deg)}
.flipcard.gone .fc-inner{opacity:0}
.fc-front,.fc-back{grid-area:1/1;backface-visibility:hidden;-webkit-backface-visibility:hidden;border:1px solid var(--vp-c-divider);border-left:3px solid var(--vp-c-brand-1);border-radius:12px;background:var(--vp-c-bg-elv);padding:14px 18px;min-height:180px;display:flex;flex-direction:column}
.fc-back{transform:rotateY(180deg);border-left-color:#047857}
.fc-front p,.fc-back p{margin:10px 0 0;font-size:15px;line-height:1.6}
.fc-sec{display:inline-block;font-size:12px;font-weight:600;color:var(--vp-c-brand-2);background:var(--vp-c-brand-soft);border-radius:12px;padding:2px 10px;align-self:flex-start}
.fc-sec:hover{color:var(--vp-c-brand-1)}
.fc-hint{margin-top:auto;padding-top:10px;font-size:11px;color:var(--vp-c-text-3)}
.fc-grades{display:flex;gap:8px;margin-top:auto;padding-top:12px}
.grade-btn{flex:1;border:1.5px solid;border-radius:8px;background:none;font-family:var(--font-body);font-size:13px;font-weight:600;padding:7px 4px;cursor:pointer}
.g-again{color:#e5484d;border-color:#e5484d}
.g-again:hover{background:#e5484d;color:#fff}
.g-hard{color:#e38407;border-color:#e38407}
.g-hard:hover{background:#e38407;color:#fff}
.g-good{color:#047857;border-color:#047857}
.g-good:hover{background:#047857;color:#fff}
.g-easy{color:#5672cd;border-color:#5672cd}
.g-easy:hover{background:#5672cd;color:#fff}
html.dark .g-again{color:#ff6369;border-color:#ff6369}
html.dark .g-again:hover{background:#ff6369;color:#1A1A1A}
html.dark .g-hard{color:#f5a623;border-color:#f5a623}
html.dark .g-good{color:#30a46c;border-color:#30a46c}
html.dark .g-easy{color:#8aa4e8;border-color:#8aa4e8}
/* review hub */
.review-main{flex:1;min-width:0;width:100%;max-width:860px;margin:0 auto;padding:32px 24px 96px}
.review-main h1{font-family:var(--font-head);font-size:36px;font-weight:600;margin:8px 0}
.review-stats{color:var(--vp-c-text-2);font-size:15px}
.review-stats b{color:var(--vp-c-text-1)}
.review-pos{text-align:right;font-size:12.5px;color:var(--vp-c-text-3);min-height:16px;margin:-10px 0 4px}
.review-bar{height:6px;border-radius:3px;background:var(--vp-c-divider);margin:0 0 28px;overflow:hidden}
.review-bar-fill{height:100%;width:0;background:var(--vp-c-brand-1);border-radius:3px;transition:width .3s}
.review-done{text-align:center;color:var(--vp-c-text-2);padding:32px 0}
.review-done .grade-btn{flex:none;padding:8px 18px;margin-top:8px}
.lab{--lab-ok:#2F6FEB;--lab-good:#1F883D;--lab-bad:#D93025;border:1px solid var(--vp-c-divider);border-radius:14px;padding:16px;background:var(--vp-c-bg-alt);margin:20px 0}
html.dark .lab{--lab-ok:#7CA9F5;--lab-good:#57B76A;--lab-bad:#F2766B}
.lab input[type=range]{width:100%}
.lab .lab-row{display:flex;flex-wrap:wrap;gap:4px 18px;align-items:baseline;margin:6px 0}
.lab .lab-row label{flex:1 1 240px;min-width:0;display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:2px 8px;align-items:center;font-size:14px;color:var(--vp-c-text-2)}
.lab .lab-row label>b{color:var(--vp-c-text-1);font-variant-numeric:tabular-nums}
.sk-bars{display:flex;align-items:flex-end;gap:2px;height:120px;margin:12px 0 4px}
.sk-bars div{flex:1 1 0;background:var(--lab-ok);border-radius:2px 2px 0 0;min-height:2px}
.sk-bars div.sk-hot{background:var(--lab-bad)}
.lab .sk-verdict{margin:8px 0 0}
.lab .sk-verdict b.v-warn{color:var(--lab-bad)}
.lab .sk-verdict b.v-good{color:var(--lab-good)}
.lab .lab-stats{font-size:13.5px;color:var(--vp-c-text-2)}
.lab svg text{font-size:11px;fill:var(--vp-c-text-2)}
.lab svg .wm-win{fill:var(--vp-code-bg);stroke:var(--vp-c-divider)}
.lab svg .wm-emitted{fill:var(--vp-c-brand-soft)}
.lab svg .wm-axis{stroke:var(--vp-c-divider)}
.lab svg .wm-line{stroke:var(--vp-c-text-2);stroke-dasharray:4 3}
.lab .lab-verdict{margin:6px 0 0;font-size:14.5px}
"""

JS = r"""
// theme
const root=document.documentElement;
const stored=localStorage.getItem('vp-theme');
const prefersDark=matchMedia('(prefers-color-scheme: dark)').matches;
if(stored==='dark'||(!stored&&prefersDark)){root.classList.add('dark')}
document.getElementById('themeBtn').addEventListener('click',()=>{
  root.classList.toggle('dark');
  localStorage.setItem('vp-theme',root.classList.contains('dark')?'dark':'light');
  setTimeout(()=>location.reload(),60);
});
document.getElementById('menuBtn')?.addEventListener('click',()=>document.getElementById('sidebar').classList.toggle('open'));
document.querySelectorAll('.sidebar-link,.pw-link').forEach(a=>a.addEventListener('click',()=>document.getElementById('sidebar').classList.remove('open')));
// copy buttons + ascii class
document.querySelectorAll('.vp-doc pre').forEach(pre=>{
  const code=pre.querySelector('code');
  const m=/language-(\w+)/.exec(code?code.className:'');
  if(m&&m[1]==='text')pre.classList.add('ascii');
  const btn=document.createElement('button');btn.className='copy-btn';btn.textContent='Copy';
  btn.onclick=e=>{e.stopPropagation();navigator.clipboard.writeText(pre.innerText.replace(/^Copy\n/,''));btn.textContent='Copied!';setTimeout(()=>btn.textContent='Copy',1500)};
  pre.appendChild(btn);
});
// wrap tables for scroll
document.querySelectorAll('.vp-doc table').forEach(t=>{
  const heads=[...t.querySelectorAll('thead th')].map(h=>h.textContent.trim());
  t.querySelectorAll('tbody td').forEach((td,i)=>{td.dataset.th=heads[i%heads.length]||''});
  const w=document.createElement('div');w.className='table-wrap';
  t.parentNode.insertBefore(w,t);w.appendChild(t);
});
// scrollspy outline
const heads=[...document.querySelectorAll('.vp-doc h2,.vp-doc h3')];
const outLinks={};document.querySelectorAll('.outline-link').forEach(a=>outLinks[a.getAttribute('href')]=a);
function spy(){
  let cur=null;
  for(const h of heads){if(h.getBoundingClientRect().top<=100)cur=h;else break}
  for(const k in outLinks)outLinks[k].classList.remove('active');
  if(cur&&outLinks['#'+cur.id])outLinks['#'+cur.id].classList.add('active');
  else if(!cur&&outLinks['#'])outLinks['#'].classList.add('active');
}
addEventListener('scroll',spy,{passive:true});spy();
// progress tracking (localStorage set of section indices)
const PROGRESS_KEY='ldp-visited';
const visited=new Set(JSON.parse(localStorage.getItem(PROGRESS_KEY)||'[]'));
function saveVisited(){localStorage.setItem(PROGRESS_KEY,JSON.stringify([...visited]))}
function paintProgress(){
  document.querySelectorAll('.vm-node,.pw-item').forEach(n=>{
    const i=+n.dataset.n;
    n.classList.toggle('done',visited.has(i));
  });
  // current = first unvisited node (path) or explicit current page
  const cur=document.querySelector('.pw-item.current');
  if(!cur){
    for(let i=0;i<document.querySelectorAll('.vm-node').length;i++){if(!visited.has(i)){const n=document.querySelector(`.vm-node[data-n="${i}"]`);if(n)n.classList.add('current');break}}
  }
  const pct=document.getElementById('vmProgress');if(pct)pct.textContent=visited.size+' / '+document.querySelectorAll('.vm-node').length;
  const p2=document.getElementById('vmProgress2');if(p2)p2.textContent=visited.size+' / '+document.querySelectorAll('.pw-item').length;
}
// section page: auto-mark visited + mark-as-read toggle
const secIdx=document.body.dataset.section;
if(secIdx!==undefined){
  visited.add(+secIdx);saveVisited();
  const item=document.querySelector(`.pw-item[data-n="${secIdx}"]`);if(item)item.classList.add('current');
  const btn=document.getElementById('markDone');
  if(btn){
    const paint=()=>{btn.classList.toggle('done',visited.has(+secIdx));btn.textContent=visited.has(+secIdx)?'✓ Section done — nice':'Mark section as done'};
    btn.onclick=()=>{visited.has(+secIdx)?visited.delete(+secIdx):visited.add(+secIdx);saveVisited();paint();paintProgress()};
    paint();
  }
}
paintProgress();
// vmap popovers: click toggles card; Go link navigates
const vmNodes=[...document.querySelectorAll('.vm-node')];
vmNodes.forEach(n=>{
  const b=n.querySelector('.vm-btn');
  b.addEventListener('click',e=>{
    if(n.classList.contains('open'))return; // second tap follows link
    e.preventDefault();
    e.stopPropagation();
    vmNodes.forEach(m=>{if(m!==n)m.classList.remove('open')});
    n.classList.add('open');
  });
});
document.addEventListener('click',e=>{if(!e.target.closest('.vm-node'))vmNodes.forEach(n=>n.classList.remove('open'))});
// diagram zoom lightbox
const lb=document.createElement('div');lb.className='lb';
lb.innerHTML='<div class="lb-vp"><img class="lb-img" alt="diagram zoom"></div><div class="lb-bar"><span class="lb-pct">100%</span><button data-z="0.5" title="zoom out">−</button><button data-z="2" title="zoom in">+</button><button data-z="reset">1:1</button><button data-z="close">✕</button></div>';
document.body.appendChild(lb);
const lbVp=lb.querySelector('.lb-vp'),lbImg=lb.querySelector('.lb-img'),lbPct=lb.querySelector('.lb-pct');
let lbW=0,lbZoom=1;
const lbSteps=[0.25,0.5,0.75,1,1.5,2,3,4];
function lbSet(z){lbZoom=z;lbImg.style.width=(lbW*z)+'px';lbPct.textContent=Math.round(z*100)+'%'}
lbImg.onload=()=>{lbW=lbImg.naturalWidth;lbSet(Math.min(1,(lbVp.clientWidth-40)/lbW)||1)};
document.querySelectorAll('.dg-png img').forEach(img=>img.addEventListener('click',e=>{
  e.stopPropagation();
  lbImg.src=img.src;
  lb.classList.add('open');document.body.style.overflow='hidden';
  if(lbImg.complete&&lbImg.naturalWidth){lbW=lbImg.naturalWidth;lbSet(Math.min(1,(lbVp.clientWidth-40)/lbW)||1)}
}));
function lbClose(){lb.classList.remove('open');document.body.style.overflow=''}
lbVp.addEventListener('click',e=>{if(e.target===lbVp)lbClose()});
lb.querySelectorAll('.lb-bar button').forEach(b=>b.addEventListener('click',e=>{
  e.stopPropagation();const a=b.dataset.z;
  if(a==='close')return lbClose();
  if(a==='reset')return lbSet(1);
  const dz=parseFloat(a),n=lbSteps.filter(s=>dz>1?s>lbZoom+0.01:s<lbZoom-0.01);
  lbSet(dz>1?(n[0]||4):(n[n.length-1]||0.25));
}));
lbVp.addEventListener('wheel',e=>{if(!e.ctrlKey&&!e.metaKey)return;e.preventDefault();
  const n=lbSteps.filter(s=>e.deltaY<0?s>lbZoom+0.01:s<lbZoom-0.01);
  lbSet(e.deltaY<0?(n[0]||4):(n[n.length-1]||0.25));},{passive:false});
document.addEventListener('keydown',e=>{
  if(!lb.classList.contains('open'))return;
  if(e.key==='Escape')lbClose();
  if(e.key==='+'||e.key==='='){const n=lbSteps.find(s=>s>lbZoom+0.01);lbSet(n||4)}
  if(e.key==='-'){const n=lbSteps.filter(s=>s<lbZoom-0.01);lbSet(n[n.length-1]||0.25)}
  if(e.key==='0')lbSet(1);
});
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
  cv.font='18px Excalifont';
  const pos={};
  const ROWH=162,PAD=60;
  Object.keys(rows).sort((a,b)=>a-b).forEach(dp=>{
    const ids=rows[dp];const ws=ids.map(id=>Math.max(160,cv.measureText(d.nodes.find(n=>n.id===id).label).width+64));
    const total=ws.reduce((a,b)=>a+b,0)+PAD*(ids.length-1);
    let x=Math.max(PAD,(W-total)/2);
    ids.forEach((id,i)=>{pos[id]={x:x,y:64+dp*ROWH,w:ws[i],h:64};x+=ws[i]+PAD});
  });
  const maxY=64+Math.max(...Object.values(depth))*ROWH+110;
  return {pos,W:Math.max(W,...Object.values(pos).map(p=>p.x+p.w))+PAD,H:maxY};
}
function scPath(a,b){ // cubic connector bottom->top
  const x1=a.x+a.w/2,y1=a.y+a.h,x2=b.x+b.w/2,y2=b.y;
  const dy=Math.max(24,(y2-y1)*0.45);
  return `M${x1} ${y1} C${x1} ${y1+dy} ${x2} ${y2-dy} ${x2} ${y2}`;
}
const NS='http://www.w3.org/2000/svg';
function mountScenario(div,d,idx){
  if(!d.start||!d.nodes.length){console.warn('scenario: empty payload, skipping mount',idx);return;}
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
  const kindOf=id=>{
    const out=d.edges.filter(e=>e.src===id&&e.choice).length;
    if(id===d.start)return ['#fed7aa','#c2410c','start'];
    if(out>0)return ['#fef3c7','#b45309','choice'];
    const inbound=d.edges.find(e=>e.dst===id&&e.kind)||d.edges.find(e=>e.dst===id);
    if(inbound&&inbound.kind==='success')return ['#a7f3d0','#047857','ok'];
    if(inbound&&inbound.kind==='fail')return ['#fee2e2','#dc2626','bad'];
    return ['#dbeafe','#1e3a5f','def'];};
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
    const ekind=e.kind==='success'?'ok':e.kind==='fail'?'bad':'def';
    const col=e.kind==='success'?'#047857':e.kind==='fail'?'#dc2626':'#1e3a5f';
    p.setAttribute('stroke',col);p.setAttribute('stroke-width','2.5');
    p.setAttribute('data-k',ekind);
    p.setAttribute('marker-end',`url(#scA${e.kind==='success'?'g':e.kind==='fail'?'r':''}${idx})`);
    p.setAttribute('filter',`url(#${SK_ID}${idx})`);
    p.classList.add('sc-edge');p.dataset.ei=i;svg.appendChild(p);
    if(e.label){const t=document.createElementNS(NS,'text');
      const mx=a.x+a.w/2+(b.x+b.w/2-(a.x+a.w/2))*0.3,my=a.y+a.h+(b.y-a.y-a.h)*0.32-8;
      t.setAttribute('x',mx);t.setAttribute('y',my);t.setAttribute('text-anchor','middle');
      t.setAttribute('font-size','15');t.setAttribute('fill','#475569');t.textContent=e.label;
      t.classList.add('sc-edge-lbl');t.dataset.ei=i;svg.appendChild(t);}
  });
  d.nodes.forEach(n=>{
    const p=L.pos[n.id],[fill,stroke,nkind]=kindOf(n.id);
    const g=document.createElementNS(NS,'g');g.classList.add('sc-node');g.dataset.nid=n.id;g.setAttribute('data-k',nkind);
    const r=document.createElementNS(NS,'rect');
    r.setAttribute('x',p.x);r.setAttribute('y',p.y);r.setAttribute('width',p.w);r.setAttribute('height',p.h);
    r.setAttribute('rx','10');r.setAttribute('fill',fill);r.setAttribute('stroke',stroke);
    r.setAttribute('stroke-width','2');r.setAttribute('filter',`url(#${SK_ID}${idx})`);
    const t=document.createElementNS(NS,'text');
    t.setAttribute('x',p.x+p.w/2);t.setAttribute('y',p.y+p.h/2+2);
    t.setAttribute('text-anchor','middle');t.setAttribute('font-size','18');
    t.setAttribute('fill','#1f2937');
    // wrap label into ≤2 tspans
    const words=n.label.split(' ');const lines=['',''];let li=0;
    words.forEach(w=>{if((lines[li]+' '+w).trim().length>Math.max(10,(p.w-24)/8.4)&&li===0)li=1;lines[li]=(lines[li]+' '+w).trim()});
    lines.forEach((ln,i)=>{if(!ln)return;const ts=document.createElementNS(NS,'tspan');
      ts.setAttribute('x',p.x+p.w/2);ts.setAttribute('dy',i===0?(lines[1]?-8:0):18);
      if(i===0)ts.setAttribute('y',p.y+p.h/2+2);ts.textContent=ln;t.appendChild(ts);});
    g.appendChild(r);g.appendChild(t);svg.appendChild(g);el[n.id]={g,r,t};
    g.addEventListener('click',()=>{if(hlMode){hl.has(n.id)?hl.delete(n.id):hl.add(n.id);g.classList.toggle('hl',hl.has(n.id));localStorage.setItem(hlKey,JSON.stringify([...hl]));return}enter(n.id)});
  });
  body.appendChild(svg);
  // interaction state
  const hlKey='sc-hl:'+location.pathname+':'+idx;
  const hl=new Set(JSON.parse(localStorage.getItem(hlKey)||'[]'));
  let hlMode=false;
  d.nodes.forEach(n=>{if(hl.has(n.id))el[n.id].g.classList.add('hl')});
  let cur=null;const visited=new Set();
  function paint(){
    d.nodes.forEach(n=>{const c=el[n.id];
      c.g.style.opacity=visited.has(n.id)?1:(n.id===d.start?1:.45);
      c.r.setAttribute('stroke-width',n.id===cur?4:2.5);});
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
  const hlBtn=div.querySelector('[data-a="hl"]');
  hlBtn.onclick=()=>{hlMode=!hlMode;hlBtn.classList.toggle('on',hlMode);
    hlBtn.title=hlMode?'Highlight on — tap nodes':'Highlight'};
  // zoom controls
  // free-canvas pan/zoom (transform on svg inside clipped .sc-body)
  const zPct=div.querySelector('[data-a="zpct"]');
  let tx=0,ty=0,sc=1;
  const apply=()=>{svg.style.transform=`translate(${tx}px,${ty}px) scale(${sc})`;
    if(zPct)zPct.textContent=Math.round(sc*100)+'%';};
  const fit=()=>{const cw=body.clientWidth;
    sc=Math.min(cw/L.W,1);tx=(cw-L.W*sc)/2;ty=16;apply();};
  const zAt=(f,px,py)=>{const ns=Math.min(3,Math.max(.3,sc*f));
    tx=px-(px-tx)*(ns/sc);ty=py-(py-ty)*(ns/sc);sc=ns;apply();};
  const local=e=>{const r=body.getBoundingClientRect();return [e.clientX-r.left,e.clientY-r.top];};
  const zi=div.querySelector('[data-a="zin"]'),zo=div.querySelector('[data-a="zout"]');
  if(zi)zi.onclick=()=>zAt(1.3,body.clientWidth/2,body.clientHeight/2);
  if(zo)zo.onclick=()=>zAt(1/1.3,body.clientWidth/2,body.clientHeight/2);
  if(zPct)zPct.onclick=fit;
  // pointer pan + pinch
  const ptrs=new Map();let pinched=false,moved=false;
  body.addEventListener('pointerdown',e=>{
    if(e.button!==0||hlMode)return;
    ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});
    moved=false;if(ptrs.size>1)pinched=true;});
  body.addEventListener('pointermove',e=>{
    if(!ptrs.has(e.pointerId))return;
    if(ptrs.size===2){const a=[...ptrs.entries()];const [id1,p1]=a[0],[id2,p2]=a[1];
      const oldD=Math.hypot(p2.x-p1.x,p2.y-p1.y),oldM=[(p1.x+p2.x)/2,(p1.y+p2.y)/2];
      ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});
      const n1=ptrs.get(id1),n2=ptrs.get(id2);
      const newD=Math.hypot(n2.x-n1.x,n2.y-n1.y),newM=[(n1.x+n2.x)/2,(n1.y+n2.y)/2];
      const r=body.getBoundingClientRect();
      tx+=newM[0]-oldM[0];ty+=newM[1]-oldM[1];
      if(oldD)zAt(newD/oldD,newM[0]-r.left,newM[1]-r.top);
      apply();return;}
    const p=ptrs.get(e.pointerId),dx=e.clientX-p.x,dy=e.clientY-p.y;
    ptrs.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(Math.abs(dx)+Math.abs(dy)>0){tx+=dx;ty+=dy;
      if(!moved){moved=true;body.classList.add('dragging');
        try{body.setPointerCapture(e.pointerId)}catch(_){}}
      apply();}});
  const pEnd=e=>{ptrs.delete(e.pointerId);
    if(ptrs.size===0){pinched=false;
      if(moved)svg.addEventListener('click',ev=>{ev.stopPropagation();ev.preventDefault();},{capture:true,once:true});
      moved=false;body.classList.remove('dragging');}};
  body.addEventListener('pointerup',pEnd);
  body.addEventListener('pointercancel',pEnd);
  body.addEventListener('wheel',e=>{e.preventDefault();
    if(e.ctrlKey||e.metaKey){const [px,py]=local(e);zAt(Math.pow(1.0015,-e.deltaY),px,py);
    }else{tx-=e.deltaX;ty-=e.deltaY;apply();}},{passive:false});
  fit();
  enter(d.start);
}
SC_FONT_OK.then(()=>{
  document.querySelectorAll('.scenario').forEach((dv,i)=>{
    const data=JSON.parse(dv.querySelector('.sc-json').textContent);
    mountScenario(dv,data,i);
  });
});
// glossary term popups
function closeTerm(){document.querySelectorAll('.term-pop').forEach(p=>p.remove())}
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
document.addEventListener('click',e=>{const t=e.target.closest('.term'); t?showTerm(t):closeTerm()});
if(matchMedia('(hover:hover)').matches){
  document.addEventListener('mouseover',e=>{const t=e.target.closest('.term'); if(t)showTerm(t)});
}

// ---- study scheduler (SM-2 lite) ----
const SCHED_KEY='study-sched';
function schedAll(){try{const o=JSON.parse(localStorage.getItem(SCHED_KEY));return o&&typeof o==='object'?o:{}}catch(e){try{localStorage.setItem(SCHED_KEY,'{}')}catch(_){}return{}}}
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
// ---- flipcards ----
function initFlipcards(root){
  root.querySelectorAll('.flipcard').forEach(fc=>{
    fc.addEventListener('click',e=>{if(e.target.closest('.grade-btn'))return;fc.classList.toggle('flipped');});
    fc.addEventListener('graded',e=>schedGrade(fc.dataset.id,e.detail));
  });
  root.querySelectorAll('.grade-btn').forEach(b=>b.addEventListener('click',e=>{
    e.stopPropagation();
    const fc=b.closest('.flipcard');if(!fc)return;
    fc.dispatchEvent(new CustomEvent('graded',{detail:b.dataset.g,bubbles:true}));
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
initFlipcards(document);
"""

MERMAID_JS = r"""
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
const isDark=document.documentElement.classList.contains('dark');
mermaid.initialize({startOnLoad:false,theme:isDark?'dark':'neutral',flowchart:{htmlLabels:true,curve:'basis'},themeVariables:{fontFamily:'-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif',fontSize:'14px'}});
const els=document.querySelectorAll('.mermaid');
for(const el of els){try{const {svg}=await mermaid.render('m'+Math.random().toString(36).slice(2),el.textContent.trim());el.innerHTML=svg}catch(e){el.innerHTML='<pre>'+el.textContent+'</pre>'}}
"""

LAB_SKEW_JS = r"""
(function(){
  var el=document.getElementById('lab-skew');if(!el)return;
  function $(id){return el.querySelector('#'+id)}
  var p=$('sk-p'),s=$('sk-s'),r=$('sk-r');
  function fmt(B){return B>=1e9?(B/1e9).toFixed(2)+' GB':B>=1e6?(B/1e6).toFixed(1)+' MB':(B/1e3).toFixed(1)+' KB'}
  function draw(){
    var P=+p.value,sk=+s.value,rows=Math.pow(10,6+ +r.value/10),w=100;
    var hot=rows*sk*w, rest=rows*(1-sk)*w/(P-1);
    var bars=$('sk-bars'),n=Math.min(P,20),h='';
    for(var i=0;i<n;i++){
      var idx=n===P?i:Math.round(i*(P-1)/(n-1));
      var mx=Math.max(hot,rest), b=idx===0?hot:rest;
      h+='<div'+(idx===0?' class="sk-hot"':'')+' style="height:'+Math.max(2,b/mx*100).toFixed(1)+'%" title="partition '+(idx+1)+': '+fmt(b)+'"></div>';
    }
    bars.innerHTML=h;
    var avg=(hot+rest*(P-1))/P, ratio=hot/avg, secs=hot/1e8;
    $('sk-pv').textContent=P;
    $('sk-sv').textContent=Math.round(sk*100)+'%';
    $('sk-rv').textContent=rows>=1e9?(rows/1e9).toFixed(1)+'B':(rows/1e6).toFixed(0)+'M';
    $('sk-stats').innerHTML='hot '+fmt(hot)+' · median ≈ '+fmt(rest)+' · avg '+fmt(avg)+' · max/avg <b>'+ratio.toFixed(1)+'×</b> · stage time ≈ hot/100 MB/s = <b>'+(secs>=60?(secs/60).toFixed(1)+' min':secs.toFixed(0)+' s')+'</b>';
    var aqe=hot>268435456&&hot>5*rest;
    $('sk-verdict').innerHTML=aqe
      ?'<b class="v-warn">AQE skew join will split this key</b> — set <code>spark.sql.adaptive.skewJoin.enabled=true</code>'
      :'<b class="v-good">below AQE threshold</b> — increase shuffle partitions';
  }
  [p,s,r].forEach(function(x){x.addEventListener('input',draw)});
  draw();
})();
""";

LAB_WM_JS = r"""
(function(){
  var el=document.getElementById('lab-watermark');if(!el)return;
  function $(id){return el.querySelector('#'+id)}
  var EVT=[1,3,7,9,12,2,11,15,8,16], scr=$('wm-i'), late=$('wm-late'), svg=$('wm-svg');
  var X=function(t){return 20+t*28};
  function draw(){
    var k=+scr.value, lat=late.checked?2:0, i, st=[], acc=0, drop=0;
    for(i=0;i<=k;i++){
      var ms=i?Math.max.apply(null,EVT.slice(0,i)):-Infinity, W=ms-5;
      var lateEv=EVT[i]<W, dropped=lateEv&&EVT[i]<W-lat;
      if(dropped)drop++;else acc++;
      st.push({et:EVT[i],late:lateEv,dropped:dropped});
    }
    var ms=k?Math.max.apply(null,EVT.slice(0,k)):-Infinity, W=ms-5;
    var g='';
    [[0,10],[10,20]].forEach(function(wd){
      var emitted=W>=wd[1];
      g+='<rect class="wm-win'+(emitted?' wm-emitted':'')+'" x="'+X(wd[0])+'" y="14" width="'+(X(wd[1])-X(wd[0]))+'" height="34" rx="3"/>';
      g+='<text x="'+(X(wd[0])+8)+'" y="30">['+wd[0]+'s,'+wd[1]+'s)'+(emitted?' — EMITTED':'')+'</text>';
    });
    g+='<line class="wm-axis" x1="20" y1="104" x2="580" y2="104"/>';
    [0,5,10,15,20].forEach(function(t){g+='<text x="'+X(t)+'" y="118" text-anchor="middle">'+t+'s</text>'});
    if(W>-5){
      var wx=Math.max(20,X(W));
      g+='<line class="wm-line" x1="'+wx+'" y1="14" x2="'+wx+'" y2="104"/><text x="'+(wx+4)+'" y="24">W='+W+'s</text>';
    }
    for(i=0;i<=k;i++){
      var c=st[i].dropped?'var(--lab-bad)':st[i].late?'var(--lab-good)':'var(--lab-ok)';
      g+='<circle cx="'+X(st[i].et)+'" cy="70" r="5" fill="'+c+'"/>';
      if(st[i].dropped)g+='<text x="'+X(st[i].et)+'" y="60" text-anchor="middle" style="fill:var(--lab-bad)">✕</text>';
    }
    svg.innerHTML=g;
    $('wm-kv').textContent='#'+(k+1)+' · t='+EVT[k]+'s';
    $('wm-wv').textContent=(W===-Infinity?'−∞':W)+' s';
    $('wm-acc').textContent=acc;
    $('wm-drop').textContent=drop;
    var cur=st[k];
    $('wm-msg').innerHTML=cur.dropped
      ?'<span style="color:var(--lab-bad)">late beyond allowed lateness — dropped to side output</span>'
      :cur.late
        ?'<span style="color:var(--lab-good)">late within allowed lateness — accepted, window re-fires (upsert)</span>'
        :'<span style="color:var(--lab-ok)">on-time</span>';
  }
  scr.addEventListener('input',draw);
  late.addEventListener('change',draw);
  draw();
})();
""";

LAB_JS = {"skew": LAB_SKEW_JS, "watermark": LAB_WM_JS}
LAB_PAGES = {5: "watermark", 10: "skew"}
def lab_extra(i):
    slug = LAB_PAGES.get(i)
    return f"<script>{LAB_JS[slug]}</script>" if slug else ""

FEATURES = [
    ("🧭", "Assessment Map", "EPAM's 6-round loop, A3 competency matrix, and what senior signals graders score.", "s01.html"),
    ("🧮", "Core Skills", "SQL window functions, PySpark live-coding patterns, distributed-systems fundamentals.", "s02.html"),
    ("🏗️", "Platform Design", "Layered architecture, medallion, CDC, batch vs streaming, lakehouse tradeoffs.", "s05.html"),
    ("⚡", "Engines & Formats", "Spark vs Flink internals, Delta/Iceberg/Hudi mechanics, Kafka deep dive.", "s09.html"),
    ("🛡️", "Reliability", "Quality dimensions, data testing, SLOs, incident playbooks.", "s12.html"),
    ("🎯", "Interview Playbook", "Six-step framework, 3 worked scenarios, capacity math, study plan.", "s13.html"),
]

def feature_cards():
    return "\n".join(
        f'<div class="feature"><div class="icon">{i}</div><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p><a href="{h}">Read →</a></div>'
        for i, t, d, h in FEATURES)

LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#D95C41" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="24" height="24"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>"""

NAV = f"""<nav class="nav">
  <button class="menu-toggle" id="menuBtn" aria-label="Menu"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button>
  <a class="logo" href="index.html">{LOGO}<span>Learn Data Platform Engineering</span></a>
  <div class="spacer"></div>
  <div class="search-box"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>Search<kbd>⌘K</kbd></div>
  <a class="home-link" href="index.html#vmap">🗺️ Path</a>
  <a class="home-link" href="review.html">🎴 Review</a>
  <button class="theme-btn" id="themeBtn" aria-label="Toggle theme"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
</nav>"""

THEME_BOOT = "<script>if(localStorage.getItem('vp-theme')==='dark'||(!localStorage.getItem('vp-theme')&&matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.classList.add('dark')</script>"
def script_json(obj):
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e"))

def shell(title, body, section_attr="", active=-1, extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{html.escape(title)} — EPAM A3 Senior Data Engineer assessment prep.">
<title>{html.escape(title)} | Learn Data Platform Engineering</title>
<style>{CSS}</style>
{THEME_BOOT}
</head>
<body{section_attr}>
{NAV}
<div class="layout">
{body}
</div>
<script>{JS}</script>
<script type="module">{MERMAID_JS}</script>
{extra}
</body>
</html>"""

def main_with_sidebar(active, inner, outline=""):
    return f"""  <aside class="sidebar" id="sidebar">
    <div class="group-title">Course Sections</div>
    <ul>
{nav_items(active)}
    </ul>
{path_widget()}
  </aside>
  <main class="main">
    <div class="vp-doc">
{inner}
    </div>
  </main>
{outline}"""

# ---------------- index page ----------------
index_body = main_with_sidebar(-1, f"""      <div class="hero">
        <div class="kicker">A3 Senior Data Software Engineer · Assessment Prep</div>
        <h1>Learn Data Platform Engineering</h1>
        <p class="tagline">26 short sections in 5 modules — Goal &amp; Foundations → Platform Design → Technology Deep-Dive → Production &amp; Defense → GenAI &amp; ML Design — covering everything the EPAM A3 internal assessment probes.</p>
        <div class="actions">
          <a class="btn brand" href="s01.html">Start the path →</a>
          <a class="btn alt" href="#vmap">Browse the map</a>
        </div>
        <div class="features">
{feature_cards()}
        </div>
      </div>
      <h2 id="learning-map">Learning Map</h2>
      <p>Work through the five modules in order — each dashed band groups a stage of the path. Tap a node to preview it, tap again or "Go →" to open its page. Completed sections turn green — progress is saved in your browser.</p>
      {vmap_html()}
      <div class="mermaid">
{LEARNING_MAP}
      </div>
      <div class="footer-note">Compiled {__import__('datetime').date.today().isoformat()} · Synthesized from vendor docs, papers, and reported interview experience.</div>""")

(ROOT / "index.html").write_text(shell("Learn Data Platform Engineering — A3 Senior DE Assessment Prep", index_body,
    extra=f'<script>window.STUDY_ALL_CARDS={script_json(study["cards"])}</script>'))

# ---------------- section pages ----------------
def chips_for(sec_no):
    refs = study["termRefs"]
    here = {t for t, rs in refs.items() if sec_no in rs}
    seen, chips = set(), []
    for e in study["edges"]:
        if not ({e["a"], e["b"]} & here):
            continue
        for other in (e["a"], e["b"]):
            if other in here:
                continue
            for tgt in refs.get(other, []):
                if tgt == sec_no or (other.lower(), tgt) in seen:
                    continue
                seen.add((other.lower(), tgt))
                subs_ = sections[tgt - 1]["subs"]
                a = f"#{subs_[0][1]}" if subs_ else ""
                chips.append(f'<a class="chip" href="s{tgt:02d}.html{a}" title="{html.escape(e["why"])}">{html.escape(other)}</a>')
                break
            if len(chips) >= 6:
                return chips
    return chips

def study_extra(sec=None):
    terms = {t["t"]: t["def"] for t in study["terms"]}
    out = (f'<script>window.STUDY_TERMS={script_json(terms)};'
           f'window.STUDY_TERMREFS={script_json(study["termRefs"])}</script>')
    if sec is not None:
        sc = [c for c in study["cards"] if c["sec"] == sec + 1]
        out += (f'<script>window.STUDY_ALL_CARDS={script_json(sc)};'
                f'window.STUDY={script_json({"sec": sec + 1, "cards": sc})}</script>')
    return out

def md_inline(t):
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', html.escape(t))

def flipcard_html(card, i):
    sec = i + 1
    return (f'<div class="flipcard" data-id="{card["id"]}"><div class="fc-inner">'
            f'<div class="fc-front"><a class="fc-sec" href="s{sec:02d}.html">s{sec} · {NODES[i]["short"]}</a>'
            f'<p>{md_inline(card["q"])}</p><span class="fc-hint">space to flip</span></div>'
            f'<div class="fc-back"><p>{md_inline(card["a"])}</p><div class="fc-grades">'
            f'<button class="grade-btn g-again" data-g="again">Again</button>'
            f'<button class="grade-btn g-hard" data-g="hard">Hard</button>'
            f'<button class="grade-btn g-good" data-g="good">Good</button>'
            f'<button class="grade-btn g-easy" data-g="easy">Easy</button>'
            f'</div></div></div></div>')

for s in sections:
    chips = chips_for(s["i"] + 1)
    chip_row = f'<div class="chip-row">{"".join(chips)}</div>' if chips else ""
    cards = [c for c in study["cards"] if c["sec"] == s["i"] + 1]
    selfcheck = ""
    if cards:
        deck = "".join(flipcard_html(c, s["i"]) for c in cards)
        selfcheck = (f'<div class="selfcheck"><h3 class="sc-title">Self-check — {len(cards)} cards</h3>'
                     f'<div class="sc-deck">{deck}</div></div>')
    inner = f"""{s['html']}{chip_row}
{selfcheck}
      <button class="mark-done" id="markDone">Mark section as done</button>
{pager(s['i'])}
      <div class="footer-note"><a href="index.html#vmap">← Back to course path</a></div>"""
    outline = f"""  <aside class="outline">
    <div class="outline-title">On this page</div>
    <ul>
{outline_items(s)}
    </ul>
  </aside>"""
    body = main_with_sidebar(s["i"], inner, outline)
    (ROOT / s["url"]).write_text(
        shell(s["title"], body, section_attr=f' data-section="{s["i"]}"', active=s["i"],
              extra=study_extra(s["i"]) + lab_extra(s["i"])))
    print(f"  wrote {s['url']}: '{s['title']}' +{len(s['subs'])} subs")

# ---------------- review hub ----------------
REVIEW_JS = r"""
(function(){
  const q=document.getElementById('queue');if(!q)return;
  const all=window.STUDY_ALL_CARDS||[],NAMES=window.STUDY_NODE_NAMES||[];
  const $=id=>document.getElementById(id);
  let queue=[],pos=0;
  const esc=s=>s.replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
  function flipcardHtml(c){
    const name=NAMES[c.sec-1]||('Section '+c.sec);
    return '<div class="flipcard" data-id="'+c.id+'"><div class="fc-inner">'
      +'<div class="fc-front"><a class="fc-sec" href="s'+String(c.sec).padStart(2,'0')+'.html">s'+c.sec+' · '+esc(name)+'</a>'
      +'<p>'+esc(c.q)+'</p><span class="fc-hint">space to flip</span></div>'
      +'<div class="fc-back"><p>'+esc(c.a)+'</p><div class="fc-grades">'
      +['again','hard','good','easy'].map(g=>'<button class="grade-btn g-'+g+'" data-g="'+g+'">'+g[0].toUpperCase()+g.slice(1)+'</button>').join('')
      +'</div></div></div></div>';
  }
  function streak(){try{return JSON.parse(localStorage.getItem('review-streak'))||{last:'',n:0}}catch(e){return{last:'',n:0}}}
  function bumpStreak(){
    const s=streak(),today=new Date().toISOString().slice(0,10);
    if(s.last!==today){s.n=(s.last===new Date(Date.now()-864e5).toISOString().slice(0,10))?s.n+1:1;
      s.last=today;localStorage.setItem('review-streak',JSON.stringify(s));}
  }
  function paintStats(){
    const o=schedAll(),now=Date.now(),len=queue.length;
    $('rvDue').textContent=all.filter(c=>!(c.id in o)||o[c.id].due<=now).length;
    $('rvStreak').textContent=streak().n;
    $('rvBar').style.width=len?Math.round(100*Math.min(pos,len)/len)+'%':'0%';$('rvPos').textContent=len?pos+'/'+len:'';
    $('rvDone').hidden=!(pos>=len);
  }
  function render(){paintStats();q.innerHTML=pos<queue.length?flipcardHtml(queue[pos]):'';if(q.firstElementChild)initFlipcards(q);}
  function buildQueue(){
    const o=schedAll(),now=Date.now();
    queue=all.filter(c=>!(c.id in o)||o[c.id].due<=now)
      .sort((a,b)=>((o[a.id]&&o[a.id].due)||0)-((o[b.id]&&o[b.id].due)||0)).slice(0,40);
    pos=0; // queue excludes graded cards; persisted index over-advances on reload — resume at 0
    render();
  }
  q.addEventListener('graded',e=>{
    bumpStreak();
    if(e.detail==='again')queue.push(queue[pos]);
    pos+=1;sessionStorage.setItem('review-pos',JSON.stringify(pos));
    render();
  });
  $('rvAhead').addEventListener('click',()=>{
    const o=schedAll(),iv=c=>(o[c.id]&&o[c.id].iv)||0;
    queue=all.slice().sort((a,b)=>iv(a)-iv(b)).slice(0,10);
    pos=0;sessionStorage.setItem('review-pos','0');render();
  });
  buildQueue();
})();
"""
review_body = f"""  <main class="review-main">
    <h1>Review</h1>
    <div class="review-stats">Due today: <b id="rvDue">–</b> · deck: <b>{len(study["cards"])}</b> · streak: <b id="rvStreak">0</b></div>
    <div class="review-pos" id="rvPos"></div>
    <div class="review-bar"><div class="review-bar-fill" id="rvBar"></div></div>
    <div id="queue"></div>
    <div class="review-done" id="rvDone" hidden>
      <p>Queue clear — nothing due right now.</p>
      <button class="grade-btn g-easy" id="rvAhead">Study ahead (10)</button>
    </div>
  </main>"""
(ROOT / "review.html").write_text(shell("Review", review_body, extra=(
    f'<script>window.STUDY_ALL_CARDS={script_json(study["cards"])};'
    f'window.STUDY_NODE_NAMES={script_json([n["short"] for n in NODES])}</script>'
    f'<script>{REVIEW_JS}</script>')))

print(f"Done — index.html + {len(FILES)} section pages + review.html")
