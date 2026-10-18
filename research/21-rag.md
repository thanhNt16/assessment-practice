## Retrieval-Augmented Generation

RAG is the data-engineer's entry point into ML system design: it is an ingestion pipeline (parse → chunk → embed → index) glued to an LLM, and interviews probe both halves. The canonical build: a ChatPDF-style bot over ~5M internal PDF pages — same shape as any "search over our docs" system you'd defend ([Perplexity](https://www.perplexity.ai/), [ChatPDF](https://www.chatpdf.com/) are the canonical examples) (ch6 §Introduction).

### Customizing an LLM: Three Options

| Approach | Core promise | Cost / limitation |
|---|---|---|
| **Finetuning** | Weights absorb company terminology and niche topics | Expensive compute, frequent retraining, needs large high-quality datasets, **no references** back to source docs (ch6 §Finetuning) |
| **Prompt engineering** | Cheap, no retraining, instantly editable | Inconsistent with phrasing; confined to pretrained knowledge; can't scale — stuffing all external docs blows the context window (ch6 §Prompt Engineering) |
| **RAG** | Up-to-date, contextual answers via retrieval at inference; balanced setup cost + scalability | Two coupled components (retrieval + generation); answer quality is hostage to retrieval quality (ch6 §RAG) |

- Pick **RAG when the knowledge changes** (docs grow ~20%/yr here) and answers must cite sources; finetuning can't keep up — updating weights per data refresh is computationally expensive and demands frequent retraining, and a finetuned model can't provide references (ch6 §Which approach).

### Data Preparation Pipeline

```mermaid
flowchart LR
    PDF[5M PDF pages] --> P[Parsing - rule-based or AI]
    P --> C[Chunking - text + images]
    C --> E[Encoders - CLIP text + image]
    E --> I[Vector index - ANN]
    I --> R[Retrieval at query time]
    R --> G[LLM generation]
```

:::scenario ChatPDF over 5M internal pages
@start Meet ChatPDF :: Knowledge changes often and answers must cite sources — decide retrieval vs stuffing first
? Knowledge changes often, citations required => @parse | success
? Static corpus that fits the context window => @prompt | fail
@parse Rule-based or AI parsing? :: Varied single/double-column layouts break fixed-template parsers — layout detection + OCR reads boxes in order
-> @chunk
@chunk Chunk 500 chars, 200 overlap :: Whole documents lose detail and bust token limits; 1,500-char pages yield 5 text + 3 image chunks
-> 5M pages x 8 chunks => @embed
@embed One shared embedding space :: Same text encoder for chunks and queries; CLIP space (or caption-then-embed) aligns images
-> @index
@index Exact or ANN search? :: Linear scan is 40M comparisons per query — clustering/LSH/HNSW approximate search is mandatory at this scale
-> @prompt
@prompt Assemble the prompt :: Query + top-k chunks + role + citation format ("end sentences with [1]") + CoT bullets
-> retrieved chunks irrelevant => @triad | fail
-> relevant => @triad | success
@triad Score the RAG triad :: Context relevance, faithfulness, answer relevance — one aggregate score hides which half broke
-> answers still bad, context fine => @raft
-> context still weak => @parse | fail
-> triad green => @ship | success
@raft RAFT-finetune last :: Golden + distractor docs teach the LLM to ignore retrieval noise — only after retrieval is fixed
-> @triad
@ship Ship with live retrieval :: Ingestion pipeline refreshes the index as pages change; stale-index monitoring alerts when crawls fall behind
:::

- **Website-sourced KBs**: clean before ingestion — remove inappropriate content, anonymize sensitive information (ch6 §Data Preparation).
- **Document parsing** converts PDF → structured blocks. *Rule-based* parsers compute layout from fixed templates — fine for uniform docs, breaks on the varied single/double-column pages this corpus has. *AI-based* parsers (Layout-Parser, Dedoc, Google Cloud Document AI) run layout detection (object detection boxes over paragraphs/tables/figures) → OCR per box in reading order → structured output of text blocks (coordinates, text, order) + non-text blocks ([LayoutParser](https://arxiv.org/abs/2103.15348)) (ch6 §Document parsing).
- **Document chunking**: embedding a whole report captures gist but misses details, and retrieved full docs exceed model limits (e.g., GPT-4o's 128K). Options: length-based (LangChain `CharacterTextSplitter`/`RecursiveCharacterTextSplitter` with `chunk_size`/`overlap`), regex on punctuation, structure-aware (`MarkdownHeaderTextSplitter`, `HTMLHeaderTextSplitter`, `PythonCodeTextSplitter`) preserving hierarchy (ch6 §Document chunking).
- **Chunk math** (memorize the shape): 5M pages × 1,500 chars; chunk size 500 with 200 overlap → 1,500/(500−200) = 5 text chunks + 3 image chunks/page → **40M chunks**, +20%/yr (ch6 §Indexing).
- **Indexing technique choice**: keyword matching (no synonyms), full-text search (Elasticsearch — heavy scans, weak semantics), knowledge graphs (great for relationship queries, too costly to build/maintain over unstructured PDFs), **vector retrieval** (semantic match even without shared terms; scalable) → vectors win at 40M+ scale (ch6 §Indexing).

### Indexing & Retrieval Models

- **Text encoder**: encoder-only Transformer producing dense embeddings; the *same* encoder embeds queries and chunks — shared space is the contract (ch6 §Architecture).
- **Image encoder** (CNN or Transformer) must align with text embeddings. Two routes: pretrained **CLIP** shared embedding space, or **image captioning** then embed the caption with the text encoder (use when joint training is too expensive) (ch6 §Image encoder).
- **Retrieval = query embedding + nearest neighbor search** over the index (Euclidean, cosine similarity) (ch6 §Sampling).

| Search | Complexity | Trade-off |
|---|---|---|
| Exact (linear) | O(N×D) | True neighbors guaranteed; 40M comparisons per query — too slow at scale |
| **ANN** | ~O(log(N)×D) | "Close enough" neighbors; needs preprocessing/extra storage |

- **ANN families**: tree-based (k-d tree, R-tree, Annoy — space partitioning), **LSH** (similar points hash to same bucket), clustering-based (inter-cluster search against centroids, then intra-cluster within selected clusters), graph-based (**HNSW** — hierarchical navigable small-world graph, coarse-to-fine descent). Production builds ship clustering-based ANN out of the box ([FAISS](https://faiss.ai/), ScaNN, Elasticsearch) (ch6 §Approximate nearest neighbor).
- **RAFT (Retrieval-Augmented Fine-Tuning)**: label retrieved docs golden vs distractor; finetune the LLM with a loss penalizing distractor use — hardens generation against noisy retrieval, which real systems always have ([RAFT](https://arxiv.org/abs/2403.10131)) (ch6 §Training). Order of operations: fix retrieval + prompts first; finetune only when answers stay poor despite relevant retrievals.

### Prompt Engineering for Generation

- **Design principles**: start simple, iterate; split multi-part tasks; clear action verbs ("Write", "Summarize"), instructions first, delimited ("###"); be specific about format/outcome but don't pad; tune prompt length deliberately (ch6 §Prompt design principles).
- **Techniques**: **CoT** (intermediate reasoning steps for multi-hop questions across documents; extends to test-time compute scaling, o1-style), **few-shot** (input-output examples set format/tone), **role-specific** (subject-matter expert persona), **user-context** (profile/location/date personalization, "use only if relevant") (ch6 §Prompt engineering techniques).
- Query-side lever: **query expansion** rewrites the query (fix typos, broaden scope) before embedding — same technique improves retrieval ([Query2doc](https://arxiv.org/abs/2303.07678)) (ch6 §Query expansion).
- Production prompt assembly: query + retrieved context + role + citation format ("answer sentences end with `[1]`", no References section) + user context + CoT step bullets (ch6 §Putting it all together).

### Evaluation: The RAG Triad

| Aspect | Measures | Metrics / methods |
|---|---|---|
| **Context relevance** | Retrieval quality — all relevant docs ranked top | Hit rate, MRR, NDCG, Precision@k |
| **Faithfulness** | Answer grounded in context (no hallucination) | Human review, automated fact-checking ([Ragas](https://docs.ragas.io/en/stable/), [ARES](https://arxiv.org/abs/2311.09476)), consistency checks across queries |
| **Answer relevance** | Completeness, no redundancy vs the query | LLM-as-judge (compare Q&A with another model) |
| **Answer correctness** | Match to reference answer | BLEU, ROUGE, METEOR (ch3 metrics) |

Unlike classic ML, no single metric works — the final text quality is a composition of retrieval and generation, hence the triad (ch6 §Evaluation).

### End-to-End Design

```text
PDFs --> parsing+chunking --> CLIP text/image encoders --> index (text, images)
user query --> safety filter --> query expansion --> text encoder --> ANN search
      --> top-k chunks + query --> prompt assembly (role/citations/CoT) --> LLM (top-p) --> answer
```

- Pre-generation **safety filtering** screens harmful queries (ch4 patterns); indexing runs offline, retrieval+generation online with a few seconds' latency budget (ch6 §Overall ML System Design).
- Interview extension points: tabular detection in parsing ([TableNet](https://arxiv.org/abs/2001.01469)), ANN internals, user-uploaded docs, **dynamic retrieval** ([FLARE](https://arxiv.org/abs/2305.06983), [Self-RAG](https://arxiv.org/abs/2310.11511) — decide when/what to retrieve), query rewriting, test-time scaling (ch6 §Other Talking Points).

### Failure modes & anti-patterns

- **Rule-based parser on mixed layouts**: template mismatch garbles text/reading order → wrong chunks indexed; symptom: answers cite content that isn't in any doc. Use AI-based parsing when formats vary (ch6 §Document parsing).
- **Indexing whole documents as one vector**: embedding captures gist, misses details; retrieved doc also busts token limits. Chunk first (ch6 §Document chunking).
- **Naive length chunking**: splits sentences/sections mid-thought → fragmented, less meaningful chunks; use overlap or structure-aware splitters (ch6 §Document chunking).
- **Exact NN at 40M scale**: O(N×D) — 40M comparisons per query, latency/cost blowup. ANN is mandatory; accept approximate recall (ch6 §Exact nearest neighbor).
- **Trusting retrieval blindly**: irrelevant/distractor docs mislead the LLM into suboptimal answers; mitigate with RAFT-style training or better ranking (ch6 §Training).
- **Prompt engineering as the whole solution**: works until external knowledge exceeds the context window — then retrieval is non-negotiable (ch6 §Which approach).
- **Low faithfulness**: plausible answers not grounded in the retrieved context; detect via the triad, not end-to-end vibes (ch6 §Faithfulness).

### Key Takeaways

- RAG = offline pipeline (parse → chunk → embed → index) + online loop (query → embed → ANN → prompt → LLM); tune the offline half before blaming the model.
- Chunk math drives capacity planning: page count × chunks-per-page × annual growth ≈ index size — 5M pages ≈ 40M chunks here.
- Shared embedding space is the invariant: same text encoder for docs and queries; CLIP or captioning aligns images into it.
- Exact search is a correctness benchmark, never a production path — ANN (clustering/LSH/HNSW) is the default at tens of millions of vectors.
- Evaluate the triad (context relevance, faithfulness, answer relevance, correctness) — one aggregate score hides which component broke.

### Interview Lens

- Asked "why not just finetune the LLM on our docs?": finetuning teaches style/terminology but can't stay current, costs retraining cycles, and can't produce citations — the three disqualifiers for a document QA product (ch6 §Finetuning).
- Nearest-neighbor probing ("why is your search fast?") is the invitation to contrast O(N×D) exact vs O(log(N)×D) ANN, then name the four ANN families and when each fits (ch6 §Sampling).
- Volunteer the chunk arithmetic before anyone asks — 5M × (1500/(500−200) + 3) = 40M chunks sized the index, and 40M-vector scale justifies ANN + scalable vector stores.
- When the interviewer says "the bot hallucinates", decompose with the triad first: is retrieval missing the doc (context relevance) or is the LLM ignoring it (faithfulness)? The fix differs — ranking/expansion vs RAFT/prompting.
