# Glossary — single source for terms + graph edges

## Format
- Term lines: `TERM :: one-sentence definition` (TERM is matched case-insensitively at word boundaries).
- Edge lines: `TERM_A > TERM_B :: why they're connected` (both must be defined).
- `##` headers are ignored (organization only).

## Terms
Watermark :: Event-time progress marker; windows close and late data is judged against it.
Idempotency :: An operation safe to retry — same input, same final state, no duplicate effects.
Exactly-once :: Effect semantics built from at-least-once delivery + idempotent writes or transactional commits.
Medallion :: Bronze (raw) → silver (validated) → gold (business-ready) layering of lakehouse data.
RAG :: Retrieval-augmented generation — ground an LLM answer in retrieved documents.
Embedding :: Dense vector representation of text/image such that semantic similarity ≈ vector distance.
AQE :: Adaptive Query Execution — Spark re-plans joins/partitions at shuffle boundaries using runtime stats.
ISR :: In-sync replicas — Kafka followers caught up enough to acknowledge writes.
Parquet :: Columnar file format with per-column encoding and nested-type support.
CDC :: Change data capture — stream of row-level changes from an OLTP log.
SCD Type 2 :: Slowly changing dimension keeping history as new versioned rows.
Backfill :: Reprocessing historical data with new logic into the same destination.
Lambda architecture :: Batch + speed layers serving merged views; Kappa collapses both onto one stream.
Shuffle :: Redistributing data across partitions between stages; the dominant Spark cost.
Skew :: Uneven key distribution making one partition dominate stage time.
Checkpoint :: Durable snapshot of Flink state enabling exactly-once recovery.
Compaction :: Merging small files into fewer large ones to restore read performance.
Z-ordering :: Multi-column clustering of lakehouse files to prune scans on any column.
Distributed join strategy :: Broadcast vs sort-merge vs shuffle-hash — picked by size + skew stats.
Feature store :: Versioned repository of point-in-time-correct features for training and serving.

## Edges
Checkpoint > Exactly-once :: exactly-once recovery replays from durable state snapshots.
Idempotency > exactly-once :: exactly-once is engineered from idempotent writes.
Medallion > Parquet :: lakehouse layers are stored in open columnar formats.
RAG > Embedding :: retrieval quality depends on embedding similarity.
AQE > Skew :: AQE detects and rewrites skewed joins at runtime.
Shuffle > Skew :: skew only matters where a shuffle redistributes keys.
