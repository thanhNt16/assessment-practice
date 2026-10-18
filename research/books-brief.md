# Books Brief — DDIA 2nd Edition & Current DE Reading (verified 2026-10-17)

## 1. DDIA 2nd Edition — Status
- **Published March 2026**, O'Reilly. Authors: **Martin Kleppmann + Chris Riccomini** (new co-author).
  - [Kleppmann's pub page](https://martin.kleppmann.com/2026/03/24/designing-data-intensive-applications-2e.html) — 670 pp (vs 616 in 1e/2017); ISBN 9781098119065 (print), 9781098119027 (ebook).
  - O'Reilly catalog: [learning.oreilly.com/library/view/designing-data-intensive-applications/9781098119058](https://learning.oreilly.com/library/view/designing-data-intensive-applications/9781098119058) (bot-blocked 403 for scrapers; fine in browser).
- **What's new vs 1e (2017):** [ScyllaDB interview](https://www.scylladb.com/2026/03/26/rethinking-designing-data-intensive-applications/), [3-chapter excerpt page](https://lp.scylladb.com/designing-data-intensive-apps-book-offer):
  - Two new opening chapters (ch1 trade-offs: operational vs analytical, cloud vs self-hosted, single-node vs distributed; ch2 nonfunctional requirements — replaces old ch1).
  - Cloud services woven throughout; **object storage as first-class building block**; control/data/compute-plane split as the default DB architecture.
  - Postgres-ecosystem/embedded-to-cloud trend (DuckDB/MotherDuck, pgvector), **vector search / embeddings / AI-era storage formats** discussed (LanceDB, Arrow, multimodal).
  - "Partitioning" renamed **"Sharding"**; new ch13 "A Philosophy of Streaming Systems"; ethics material split into ch14 "Doing the Right Thing".
  - Official per-chapter literature refs: [github.com/ept/ddia2-references](https://github.com/ept/ddia2-references) (14 chapters, CC BY-NC 4.0).

## 2. Chapter List (2nd edition, 14 chapters)
Titles cross-checked against O'Reilly pages (ch01/07/09/12/13 verified via O'Reilly URLs) + [study guide repo](https://github.com/sofien6/Designing-Data-Intensive-Applications-2nd-edition); ch1/2/9 also confirmed by the official ScyllaDB excerpt.
| Ch | Title (2e) | vs 1e |
|---|---|---|
| 1 | Trade-Offs in Data Systems Architecture | NEW |
| 2 | Defining Nonfunctional Requirements | rework of 1e ch1 |
| 3 | Data Models and Query Languages | same |
| 4 | Storage and Retrieval | same |
| 5 | Encoding and Evolution | same |
| 6 | Replication | same |
| 7 | Sharding | 1e "Partitioning" |
| 8 | Transactions | same |
| 9 | The Trouble with Distributed Systems | same |
| 10 | Consistency and Consensus | same |
| 11 | Batch Processing | same |
| 12 | Stream Processing | same |
| 13 | A Philosophy of Streaming Systems | NEW |
| 14 | Doing the Right Thing | NEW (grew out of 1e ch12 ethics section; 1e "Future of Data Systems" ch12 gone) |

Chapter URL pattern: `https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/chNN.html`

## 3. Free Access — ground truth (⚠ assumption in task corrected)
- **dataintensive.net is still the 1st-edition site** (footer © 2014-2019; TOC link → 1e ISBN). No free full chapters there.
- Free 2e content that exists:
  - **ScyllaDB free excerpt (~150 pp: ch1 + ch2 + ch9), email-gated:** [lp.scylladb.com/designing-data-intensive-apps-book-offer](https://lp.scylladb.com/designing-data-intensive-apps-book-offer); blog excerpts e.g. [scalability excerpt (ch2)](https://www.scylladb.com/2026/08/04/ddia-2nd-edition-excerpt-on-scalability).
  - **Official references repo** (all 14 chapters' further-reading links, free): [github.com/ept/ddia2-references](https://github.com/ept/ddia2-references).
  - O'Reilly 10-day trial / subscription for full text; 1e remains readable via older free summaries.
  - Unofficial 2e study summaries: [sofien6.github.io/Designing-Data-Intensive-Applications-2nd-edition](https://sofien6.github.io/Designing-Data-Intensive-Applications-2nd-edition/).

## 4. DDIA 2e → Course Section Mapping
| Course section | DDIA 2e chapters | Notes |
|---|---|---|
| s04 Distributed Systems Fundamentals | 6, 7, 8, 9, 10 | core: replication, sharding, transactions, failure modes, consistency/consensus |
| s06 Batch vs Streaming | 11, 12, 13 | 13 is new 2e material — strongest "why streaming" argumentation (unbundling, lambda critique) |
| s12 Kafka & Streaming Backbones | 11, 12 (+ ch13 refs: Kreps "The Log") | log abstraction, delivery semantics |
| s05 Data Platform Architecture | 1, 2 | new ch1's cloud-vs-self-hosted & op-vs-analytical trade-offs = assessment-ready framing |
| s07 Lakehouse / s09 Table Formats | 4, 5 + interview-level cloud/object-store themes | full lakehouse/table-format treatment lives in dedicated books below; [INFERENCE] 2e covers object-store-native DBs but no dedicated table-format chapter seen in TOC |
| s10 Spark vs Flink | 12 | engine-agnostic; pair with Learning Spark 2e |
| s13 Pipeline Reliability | 2, 9 | nonfunctionals + failure taxonomy |
| EPAM A3 topic → chapter: distributed fundamentals→9,10; replication→6; partitioning→7; consistency→10; batch vs stream→11,12,13 | | |

## 5. Other Current Books (verified editions)
| Book | Authors | Latest edition | Status |
|---|---|---|---|
| DDIA 2e | Kleppmann, Riccomini | Mar 2026 | current — primary reference |
| Fundamentals of Data Engineering | Reis, Housley | 1e, Jun 2022 ([O'Reilly](https://www.oreilly.com/library/view/fundamentals-of-data/9781098108298)) | still latest; no 2e found |
| Streaming Systems | Akidau, Chernyak, Lax | 1e, 2018 ([O'Reilly](https://www.oreilly.com/library/view/streaming-systems/9781491983867)) | still latest; no 2e found — DDIA 2e ch12-13 now cover streaming theory more freshly |
| Learning Spark, 2e | Damji, Wenig, Das, Lee | Jul 2020 ([O'Reilly](https://www.oreilly.com/library/view/learning-spark-2nd/9781492050032)) | still latest Spark intro; free PDF from Databricks |
| Spark: The Definitive Guide | Chambers, Zaharia | 1e, Feb 2018 | no English 2e found; skip in favor of Learning Spark 2e + HPS 2e |
| High Performance Spark, 2e | (1e: Karau, Warren) | 2026, new edition listed ([O'Reilly](https://www.oreilly.com/library/view/high-performance-spark/9781098145842)) | new — check author lineup when citing |
| Apache Iceberg: The Definitive Guide | Shiran, Hughes, Merced | May 2024 ([O'Reilly](https://www.oreilly.com/library/view/apache-iceberg-the/9781098148614)) | current; maps to s09 |
| Delta Lake: The Definitive Guide | Lee, Wentling, Haines, Babu | Oct 2024 ([O'Reilly](https://www.oreilly.com/library/view/delta-lake-the/9781098151935)) | current; maps to s09 |
| Designing Machine Learning Systems | Huyen | 1e, 2022 | still 1e; superseded in practice by her AI Engineering |
| AI Engineering | Huyen | Jan 2025 ([O'Reilly](https://www.oreilly.com/library/view/ai-engineering/9781098166298)) | current for ML/AI-adjacent platform work |

## 6. Action for Content Integration
- Update any "1e/2017" references to 2e/Mar-2026; chapter numbers shift by +1 from ch2 onward vs 1e, and "Partitioning" → "Sharding".
- Cite O'Reilly chapter URLs (pattern above) per course section; use ddia2-references for further-reading blocks; ScyllaDB excerpt as the free reading link.
- Flag in s06/s12: ch13 "A Philosophy of Streaming Systems" is new-in-2e content not present in most older summaries/notes circulating online.
