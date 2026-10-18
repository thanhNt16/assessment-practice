
===== research/01-epam-assessment.md =====
:::glide Glide — From Nomination to Matrix Verdict
1) Pick the target grade :: **A3 confirmation** (defend with ~1 year of delivery evidence) vs **A3→A4** (leadership delta: mentoring, review leadership, workstream direction) — different evidence, same process.
2) Secure manager sponsorship :: Advocacy is a **stated gate** — assessments stall regardless of skill; start the conversation quarters before applying.
3) Apply year-round :: Applications accepted **any time**; many roles add an **annual promotion-eligibility review** on top.
4) Assemble one real project :: Progression narrative anchored to **real delivered work** — decisions owned, not tasks done; resume adjectives read junior.
5) Map to the competency matrix :: Cover every dimension: **engineering depth, architecture (≥2 options per decision), delivery impact, mentoring, English B2+**.
6) Build the defense deck :: Context → Architecture → Impact → Growth → Mentoring; each bullet = one dimension, **one artifact, one number**.
7) Face the committee :: Peer/expert panel probes **one level deeper than your deck** — Spark execution model, Delta MERGE, window functions from your own war stories.
8) Matrix-anchored verdict :: Pass confirms the grade; gaps (e.g. mentoring below the A4 line) loop you back to reapply when evidence matures.
? Why does sponsorship matter when skill already clears the bar? :: Skill clears the bar; **sponsorship and project visibility open the door** — if your manager cannot narrate your impact, the committee never sees your best evidence.
? What is the classic A3→A4 failure mode? :: **A3-grade evidence with an A4 label** — the promotion needs a leadership delta (formal mentoring, review leadership, workstream direction), not more of the same component-level evidence.
? There is no Codility in an internal Assessment — what is judged instead? :: **Actual delivered work**: impact metrics, owned decisions with trade-offs and alternatives, mentored people, progression over time — scored against the matrix from real project examples.
? Why rehearse the deck spoken and timed? :: English **B2+ is scored and gates client staffing**; the defense itself is an English delivery test, so rehearse the hardest follow-ups aloud, not just the slides.
:::
===== research/02-sql-deep-dive.md =====
:::glide Glide — SQL Execution & Window Playbook
1) FROM and JOIN :: base rows enter; duplicate join keys fan out and silently double sums
2) WHERE :: filters **rows only** — keep it SARGable so partition pruning works
3) GROUP BY and HAVING :: groups form; WHERE can't hold aggregates, HAVING filters groups
4) SELECT + window functions :: one window pass — every row survives, unlike GROUP BY
5) Dedup with ROW_NUMBER :: `PARTITION BY customer_id ORDER BY order_ts DESC, id DESC`, keep `rn = 1` — one scan, deterministic ties, no duplicates
6) QUALIFY variant :: Snowflake and Databricks SQL filter windows natively; OSS Spark needs the subquery
7) Sessionize with LAG :: flag rows where the gap exceeds 30 minutes, running SUM becomes the session id
8) ORDER BY and LIMIT :: aliases and windows finally visible; windows ran *before* this
? Why pick the windowed dedup over the correlated-subquery self-join? :: The self-join re-scans the table per row and returns duplicates on ties; the window does a single scan plus one sort, breaks ties deterministically with `id DESC`, and yields exactly one row per key.
? On scores 100, 100, 90 — what do RANK and DENSE_RANK return? :: RANK gives `1,1,3` (gaps after ties); DENSE_RANK gives `1,1,2` (no gaps) — pick per whether ties should consume ranks.
? A LEFT JOIN plus WHERE on the right table's column returns more rows than the left table — what happened? :: The WHERE silently converted it to an INNER JOIN, and duplicate join keys caused row fan-out; move the condition into ON.
? Why does `WHERE CAST(dt AS STRING) = '2024-01-01'` full-scan? :: Wrapping the filtered column in a function breaks SARGability, so the engine can't prune partitions — compare `dt = DATE '2024-01-01'`.
:::
===== research/03-python-pyspark.md =====
:::glide Glide — Where the Job Dies
1) Driver plans, executors run :: pandas is one eager process; Spark builds a **lazy DAG** on the driver and runs tasks on partitions across executor JVMs.
2) Nothing big crosses to the driver :: `collect()`, `toPandas()`, `take(10**9)` land full results in driver RAM — the classic **driver OOM**.
3) Executor OOM is data shape :: one giant partition (**skew**), `repartition(1)` before a heavy stage, or `cache()` without `MEMORY_AND_DISK`.
4) Climb the UDF ladder last :: native functions ride Tungsten at 1×; pandas UDFs amortize per **Arrow batch** (~2–5×); row-wise Python UDFs pay serialization into CPython every row (~10×+).
5) Windows carry the screens :: `row_number`/`dense_rank` over `partitionBy` solve **latest per key**, **top-k per group**, and **sessionize** in one API.
6) Diagnose skew before fixing it :: `groupBy(col).count().orderBy(desc("count"))` or the Spark UI — 199 tasks in 2 min, one straggler in 38 min = hot key.
7) Salt the hot key, re-aggregate :: random salt splits 400 M rows into 16 sub-groups; stage 2 sums only 16 partials per key, so all tasks finish together.
8) Cheap knobs first :: `repartition(n, col)` shuffles and balances; `coalesce(n)` skips shuffle but can leave skew; cache only when reused ≥2×, then `unpersist()`.
? Why is a row-wise Python UDF so much slower than a native function? :: Every row pays JVM → serialized bytes → CPython process → back, single-threaded; pandas UDFs amortize that crossing per Arrow batch.
? Interviewer says "the file won't fit in memory" in plain Python — expected answer? :: **Yield, don't return**: a generator streams at O(1) RAM while dicts/sets are O(n).
? Why salt a skewed `groupBy` instead of just repartitioning? :: The hot key's partition must hold 400 M partial aggregates in one task; salting splits it into N sub-groups so tasks finish together — `coalesce`-style merging can leave skew, and AQE's skew-join split (`spark.sql.adaptive.skewJoin.enabled`) only helps joins automatically.
? "pandas code works but Spark gives wrong results" — what broke? :: Row order isn't guaranteed across partitions: window frames need explicit `orderBy`, and nondeterministic UDFs break re-execution.
:::
===== research/04-distributed-fundamentals.md =====
:::glide Glide — The Quorum Decision
1) A partition occurs :: CAP only forces a choice under partition — before that, CA is coherent
2) Pick C or A :: CP blocks or rejects rather than serve stale; AP answers with possibly stale data
3) Apply the quorum rule :: `R + W > N` forces read and write sets to overlap, so every read sees the newest value
4) Guard against split-brain :: `W > N/2` prevents two write quorums from forming
5) Size the quorum :: W=3/R=3 on N=5 gives 99.1% availability on both paths; W=1/R=5 gives ~99.999% writes but 59.0% reads
6) Accept retries :: retries are mandatory, so delivery is at-least-once and duplicates are guaranteed, not exceptional
7) Make replays harmless :: idempotency keys, dedup tables, upserts, and transactional offsets turn duplicate delivery into no-ops
8) Order with event time :: wall clocks lie across machines, so windows close deterministically only via event time + watermarks
? Why is Kafka's W=3/R=3-style `acks=all` + `min.insync.replicas=2` treated as CP-leaning? :: It approximates a write quorum over the ISR: `unclean.leader.election.enable` is the explicit switch that decides whether the cluster refuses stale leaders (CP) or keeps serving (AP).
? Why does W=1/R=5 only suit rarely-read telemetry? :: Any single node accepts writes (~99.999% write availability, lowest latency), but reads need all 5 nodes — only 59.0% read availability, tolerable only when a failed read can simply be retried.
? What does "exactly-once" actually guarantee? :: Effectively-once end-to-end: at-least-once delivery plus idempotent, transactional sinks — Kafka EOS (PID + per-partition sequence numbers) only works if the sink commits transactionally; no system executes a side effect literally once.
? When does quorum sizing still lose data? :: It doesn't prevent LWW-style loss — last-write-wins silently discards concurrent updates, which is why causal ordering (vector clocks) and event time matter alongside replication.
:::
===== research/05-platform-architecture.md =====
:::glide Glide — Source to Gold
1) Sources → ingestion :: Move data with **no business logic** — batch extract, CDC stream, or queue; first decisions are pull vs push, full vs incremental.
2) Bronze lands raw :: Immutable append-only copy plus ingest metadata is your **replay insurance** — never edited downstream.
3) Silver validates :: Deduplicated, typed, conformed; the quality gate sends failures to **quarantine** so bad data never poisons gold.
4) Gold serves :: Dimensional models and aggregates for BI/ML — warehouse tables, dashboards, features, reverse-ETL.
5) Declare the grain :: "One row per order line" — model the *business process*, not the source system; grain is the #1 modeling question.
6) Pin facts with SCD2 :: The surrogate FK pins each fact to the dimension version true at event time — without it there is **no as-of join**.
7) Contract the interface :: Versioned, machine-enforceable producer→consumer agreements catch renames at **producer build time**, not as NULLs in gold weeks later.
8) Run the spine :: Orchestration, catalog, observability, security cut across every layer — mention them **unprompted**.
? Why log-based CDC over polling `updated_at`? :: Polling misses hard deletes and untouched rows; log-based (binlog/WAL → Debezium → Kafka) has minimal source overhead, captures deletes, seconds latency. Triggers slow every write inline — legacy-only red flag.
? When do you skip a medallion layer? :: Where no trust boundary exists — teams making all three copies of every dataset get blank tables and tripled storage.
? Why does SCD2 need a surrogate key, not just valid dates? :: The fact's FK pins the row to the version true at event time; re-keying facts later is a full rewrite — the MERGE must run in one transaction or a crash leaves no current row.
? Star, Data Vault, or OBT? :: Star for BI aggregations by conformed dimensions; Data Vault for regulated multi-source integration with full attribute history; OBT for one consumer scanning whole rows where joins dominate latency.
:::
===== research/06-batch-vs-streaming.md =====
:::glide Glide — From Bounded Batch to Exactly-Once
1) Pick the domain :: **Batch** = what is true given all data up to now over bounded input; **streaming** = what is true right now over unbounded input — the real trade is latency vs reprocessing cost, not throughput.
2) Reason in event time :: Only **event time** (when the event occurred) is reproducible; processing time is for lag monitoring, ingestion time is rarely correct — windows, billing, analytics all hang off it.
3) Trust the watermark :: `W = maxObservedEventTime − allowedLateness` (typically 20 s–5 min) is a monotonic promise "no event ≤ W arrives later"; it is the engine's permission slip to close a window.
4) Emit when W passes the end :: Window `[10:00,10:05)` fires once W ≥ 10:05; in parallel pipelines W = **min across partitions**, so one idle source stalls all progress.
5) Handle the stragglers :: A late event **within allowedLateness** re-accumulates and re-fires (retraction/upsert); **beyond** it goes to a side output or dead-letter — too tight drops data, too loose delays results and grows state.
6) Bound your state :: Window contents, join buffers, dedup keys live keyed in RocksDB/heap — they grow **forever without TTL**.
7) Make exactly-once end-to-end :: Three layers must align: replayable source (offsets in the checkpoint), exactly-once state (Flink snapshot/restore), exactly-once sink (Kafka transactions or idempotent upsert) — otherwise settle for at-least-once plus dedupe.
8) Escalate by SLA :: Batch → micro-batch (~500 ms floor) → true streaming (10–100 ms) — every step up is a permanent tax of state ops, checkpoints, and watermark tuning; fraud SLA < 5 s demands streaming, an hourly dashboard gets cheap batch.
? Why does one idle parallel source freeze the whole pipeline? :: Because W = **min across partitions** — a stalled partition pins the min-watermark, so no window can emit anywhere.
? A batch job double-counts on retry — why, and the fix? :: Non-idempotent `INSERT INTO` + retry silently appends twice; rerun safely with `INSERT OVERWRITE` on the partition or a keyed `MERGE`.
? Why does "exactly-once" fail into a plain non-transactional HTTP sink? :: Layer 3 is missing — no transactional or idempotent sink means the best possible is at-least-once delivery with dedupe downstream.
? When does the watermark dial break in each direction? :: Too tight → events beyond allowedLateness are dropped to side outputs; too loose → results are delayed and state grows longer.
:::
===== research/07-warehouse-lakehouse.md =====
:::glide Glide — Four Generations, Four Failure Modes
1) **EDW** couples storage with compute :: $/TB too high; can't hold logs, JSON, images, ML assets — raw data has nowhere cheap to live
2) **Lake** lands anything, schema-on-read :: the writer checks nothing — a renamed column silently poisons every downstream job
3) **Lake breaks structurally** :: no atomic commits, no enforcement, no stats/compaction, no governance → the equilibrium is a data swamp
4) **Fix one: cloud DW** decouples compute :: micro-partitions (~16 MB) + min/max pruning, isolated virtual warehouses, auto-suspend bills $0 while idle
5) **Cloud DW breaks** :: proprietary formats → lake + warehouse = two synced copies of data, lock-in
6) **Fix two: lakehouse** adds an open ACID table format :: Parquet + table format + object storage + catalog + any engine — the format + catalog *is* the platform
7) **ELT displaces ETL** :: decoupled storage made landing raw cheap, elastic compute made in-warehouse transforms cheap — ETL survives only at trust boundaries (PII masking, cross-region compliance)
8) **Choose by workload** :: utilization <30% → per-second auto-suspend; >60% sustained → always-on/reserved; workload mix, team size, and lock-in tolerance pick warehouse vs lakehouse vs OLAP serving tier
? Why is blaming "bad engineers" the junior answer for lake failure? :: The platform made hygiene expensive and sloppiness free — no atomic commits (concurrent writers corrupted partitions), no schema enforcement, no compaction (millions of small files), no governance (duplicate contradictory datasets) — so at scale the equilibrium is a swamp.
? What does the lakehouse add that finally fixes the swamp? :: A transactional table format over open Parquet: ACID commits, time travel, schema-on-write with late binding (enforce on commit, evolve without rewriting files), stats for pruning — with the catalog as the platform and any engine (Spark, Trino, Flink, DuckDB) on top.
? When does an always-on cluster beat auto-suspend? :: When utilization is sustained >60%. The 2h-nightly workload runs at ~17% utilization and pays ~6× compute for idle; flipped to steady 24/7 BI, always-on ≈ $2.3k vs auto-suspend Large ≈ $11.7k — a 5× win the other way.
:::
===== research/08-snowflake-vs-databricks.md =====
:::glide Glide — Who Owns the Storage
1) Converging origins :: Snowflake grew a SQL warehouse outward into the lakehouse; Databricks grew a Spark lakehouse inward into SQL/BI — compare mechanisms, not feature checklists
2) Storage ownership :: **Snowflake abstracts storage away** (micro-partitions, ~16 MB, bundled bill); **Databricks makes your lake the source of truth** (your S3 + Delta ACID log) — this one choice explains pricing, governance, and lock-in
3) Compute model :: Warehouses XS→6XL auto-suspend to zero vs Spark + **Photon** clusters — why BI defaults to Snowflake and code-heavy pipelines to Databricks
4) Billing shape :: **Credits bundle IaaS**; **DBUs stack on the VM bill** — never compare list rates; the ~15% Databricks edge in the worked example is entirely assumption-driven
5) Workload verdicts :: SQL/BI → Snowflake; ML/GPU/code-first pipelines and continuous streaming → Databricks; governance is capability parity but openness favors Unity Catalog
6) Lock-in asymmetry :: Snowflake locks in **data gravity** (exit = unload proprietary native tables to Iceberg); Databricks locks in **workflows** (exit = re-platform notebooks/jobs, data stays in your bucket)
7) The neutral layer :: **Iceberg + one REST catalog** (Open Catalog/Polaris or UC) lets both engines read shared data — no efficient cross-read of Snowflake native tables otherwise
8) The exit :: Iceberg support is table stakes on both sides now; catalog ownership is the live differentiator — design the exit before you need it
? Why is Databricks ~15% cheaper in the worked example, and why not trust that number? :: It is entirely assumption-driven — swap the credit price ($2–4 by cloud/region), warehouse sizes, or the analyst/ETL mix and either side wins; model 3-year all-in TCO on your workload, never list rates.
? Where does each platform's lock-in actually bite? :: **Snowflake locks in data gravity**: native tables are proprietary, so exiting means re-platforming storage by unloading to Iceberg. **Databricks locks in workflows**: exiting means re-platforming notebooks/jobs, but data stays in your cloud account.
? Why can't the two platforms just share data naively? :: Snowflake native tables are proprietary and Spark can't scan them efficiently — the neutral pattern is Iceberg in S3 with a REST catalog (Open Catalog/Polaris or UC) both engines read, at the cost of two contracts, two governance models, two teams.
? Why discount vendor benchmarks like TPC-DS 2023 or TPC-DI 2025? :: Claims contradict each other year over year (~3× DBX, then ~5× for DBX SQL Serverless, Snowflake's Gen2 rebuttal, consultancies reporting the reverse on pure BI) — workload shape dominates, so run a 2-week PoC with your schemas, query mix, and concurrency profile.
:::
===== research/09-table-formats.md =====
:::glide Glide — Log, Tree, Timeline
1) Parquet alone is not a table :: a **file format** says nothing about the collection — no atomicity, no updates/deletes, and planning is O(all files)
2) Delta = one log :: commits append `_delta_log` JSONs (`add`/`remove`/`metaData`/`txn`); a **checkpoint every 10th commit** keeps replay short
3) Delta commit = create file N+1 :: **optimistic concurrency**; conditional put arbitrates, losers re-validate against new state and retry
4) Iceberg = a metadata tree :: catalog pointer → `metadata.json` → manifest-list → manifests → data files, with partition and min/max pruning at every level
5) Iceberg commit = **catalog pointer swap** :: arbitration lives in the catalog (CAS), not on storage; REST catalog decouples engines and vendors short-lived credentials
6) Hudi = a timeline over file groups :: instants (`commit`/`delta-commit`/`compaction`) are the WAL; **CoW** rewrites bases, **MoR** appends logs until background compaction folds them
7) Deletes are a cost ladder :: CoW rewrite → Iceberg v2 position deletes → DV bitmaps (Delta 2.x/Iceberg v3) → Hudi MoR log records — write cost falls, read cost rises
8) Time travel is replay :: old log / old snapshot / old slices resurrect the rows; only `VACUUM` / `expire_snapshots` / `clean` truly delete
9) Pick by estate, not benchmark :: multi-engine → Iceberg REST; Databricks/Spark → Delta + UniForm; keyed CDC upsert-heavy → Hudi — and every published benchmark is vendor-shaped

? Why is Iceberg planning O(pruned metadata) instead of O(all files)? :: Manifest lists carry **partition-range summaries** and manifests carry per-column min/max/null counts, so data files are pruned before any I/O.
? One `UPDATE` on 10 files: why does Delta write ~KBs while Hudi CoW writes ~100 MB? :: Delta appends 1 log JSON + 10 DV bitmaps on existing `add` entries; Hudi CoW must rewrite all 10 base files as new slices.
? Why does Iceberg partition evolution need no rewrite? :: Partition transforms live in the **spec**, attached per file — old files stay queryable under their old spec, and engines never hand-write partition filters (hidden partitioning).
? The delete question is a trap ladder — name the rungs. :: CoW rewrite → position deletes (Iceberg v2) → deletion vectors → MoR logs, naming write-vs-read cost at each rung.
:::
===== research/10-spark-vs-flink.md =====
:::glide Glide — Exactly-Once, Barrier by Barrier
1) Streaming-first model :: records flow one at a time → ~10 ms floor; batch is just a bounded stream — every mechanism below follows from this choice.
2) Native watermarks :: sources emit timestamps plus a *monotonic promise*; windows/timers fire when the watermark passes, late data goes to side outputs.
3) Keyed state on a backend :: heap for small/low-latency, RocksDB for TBs, **ForSt/disaggregated** for cloud — the backend choice *is* the capacity decision.
4) Checkpoint = async barrier snapshot :: barriers flow with the data (Chandy–Lamport); processing never pauses while state is snapshotted to DFS.
5) Barrier alignment :: an operator snapshots only once barriers arrive from **all** inputs — that alignment is what makes the snapshot a consistent global cut.
6) Unaligned under backpressure :: barriers overtake in-flight buffers and snapshot those too — larger snapshots, but *steady* checkpoint duration.
7) Sink 2PC :: `TwoPhaseCommittingSink` pre-commits at checkpoint, commits on `notifyCheckpointComplete` — Kafka becomes exactly-once, not at-least-once.
8) Exactly-once assembly :: rewindable source + barrier snapshot + 2PC/idempotent sink — remove any one piece and the guarantee degrades.
9) Savepoints for surgery :: manually triggered checkpoints in canonical format enable upgrades, rescaling, migration — plain checkpoints optimize speed, not compatibility.
? Why does checkpoint interval bound deliverable latency? :: 2PC sinks commit only when a checkpoint completes, so nothing becomes visible downstream until then — checkpoint interval sets the visibility floor.
? When do unaligned checkpoints help, and what do they cost? :: Under backpressure: barriers overtake in-flight buffers and snapshot them too, giving steady checkpoint duration at the price of larger snapshots.
? Why can't a Flink 1.x savepoint be restored in 2.x? :: There is no 1.x→2.x state compatibility; plain checkpoints optimize speed, not the canonical version-stable format savepoints use.
? Why does naive HPA break stateful Flink jobs? :: Rescaling a stateful job changes key-group distribution and checkpointed state; the Flink K8s operator autoscaler (FLIP-271) reads per-vertex lag/backpressure instead.
:::
===== research/11-spark-optimization.md =====
:::glide Glide — Diagnosing the Slow Spark Join
1) Find the hot stage :: Open the stage with the **largest shuffle read** — nearly every production incident is shuffle size, skew, spill, or GC.
2) Compare task p50 vs max :: Summary metrics show **median 35 s, max 24 min** — a huge max-vs-p50 gap means skew, not slow code.
3) Read the partition bytes :: the max task (partition 113) reads **40 GB** while a median partition is 500 GB ÷ 200 = **2.5 GB** — one fat key.
4) Check the AQE skew thresholds :: 40 GB > `skewedPartitionThresholdInBytes` (256 MB) **and** > 5 × 2.5 GB = 12.5 GB — both conditions met, so the skew-join split fires (joins only).
5) Verify the split math :: 40 GB ÷ 64 MB target ≈ **625 subtasks** of ~0.6 s each — stage wall drops from 24 min to the runner-up ≈ **40 s**.
6) Aggregate skew? Salt instead :: AQE skew split does not help `groupBy` — use `pmod(hash(key, rand()), N)`, partial-aggregate salted, second pass strips the salt.
7) Check the broadcast escape hatch :: dim table is 8 GB ≫ 10 MB threshold — forcing `/*+ BROADCAST */` would collect it all on the driver and OOM.
8) No skew? Read spill and GC :: `spill (disk) > 0` → per-task memory short (partitions ↑, memory ↑); GC time > 10–15% of task time → G1GC and smaller objects.
? Why is the 200 default for `spark.sql.shuffle.partitions` wrong in both directions? :: 500 GB shuffle → 2.5 GB partitions (spill, skew); 2 GB shuffle → 200 tasks of 10 MB (scheduling overhead). Size from bytes: `partitions ≈ shuffle_bytes / (128–256 MB)` — or over-provision and let AQE coalesce.
? When can AQE not rescue a plan at runtime? :: Nothing to re-plan without an `Exchange`; coalesce skips user-forced `repartition(n)`; skew split covers joins only — aggregate skew needs salting.
? Why does execution memory spill to disk while storage memory does not? :: In the unified model storage and execution borrow from each other, but storage blocks evict under pressure while **execution never evicts — it spills**; per-task execution memory ≈ pool ÷ concurrent tasks.
? Why is forcing `/*+ BROADCAST */` on stale statistics dangerous? :: The hint overrides stats — after heavy appends the "small" side can be huge at runtime, the driver collects it all and dies. Verify `sizeInBytes` in the plan first.
:::
===== research/12-messaging-kafka.md =====
:::glide Glide — From Producer to Acknowledged Write
1) Produce to the leader :: Producer batches per partition (`linger.ms`, `batch.size`), partitioning by **murmur2 key hash** — `hash(key) % partitionCount` is where per-entity ordering lives, so changing partition count silently breaks it.
2) Followers fetch continuously :: One leader per partition; replicas current within `replica.lag.time.max.ms` (30s) form the **ISR** — the set Kafka trusts.
3) `acks=all` gates the ack :: With `min.insync.replicas=2`, the write is only acknowledged once all ISR have it; acks shrink to 1 and producers get `NOT_ENOUGH_REPLICAS` instead of silent degradation.
4) High watermark advances :: The **HW** is the highest offset replicated to all ISR — consumers read only up to it, never seeing un-replicated tail data.
5) Leader dies, controller elects :: Election picks from the ISR; `unclean.leader.election.enable=false` (default) trades availability for **zero acknowledged-data loss**.
6) Consumers own their offsets :: Committed to `__consumer_offsets`, a 50-partition log-compacted topic — replay is an offset reset, not a redeliver.
7) Exactly-once stops at Kafka's edge :: Idempotent producer + transactions give EOS *within* Kafka; across system boundaries it's at-least-once + **idempotent sinks** or the outbox.
8) The crash-in-between window :: `db.save(x); kafka.send(event(x))` dual-writes — only the outbox (event row commits with business change, CDC publishes) makes DB↔Kafka atomic.
? Why `acks=all` + RF=3 + `min.insync.replicas=2` rather than `acks=1`? :: `acks=1` only covers the leader writing locally — a leader crash before replication loses records. The canonical recipe survives `min.insync.replicas−1` broker failures.
? When does strict ordering break? :: Ordering is strict only *within a partition*; `hash(key) % partitionCount` maps a key to one partition, so **changing partition count** silently breaks the key→partition map.
? What happens when ISR shrinks to 1 with `min.insync.replicas=2`? :: Producers get `NOT_ENOUGH_REPLICAS` — an explicit failure instead of silent degradation of durability.
? Why is exactly-once "marketing" for external effects? :: EOS (idempotent producer + transactions + `read_committed`) is real *within* Kafka; across boundaries delivery is at-least-once, so side effects need idempotent sinks (DB unique key/upsert) or the outbox pattern.
:::
===== research/13-pipeline-reliability.md =====
:::glide Glide — The Incident Loop
1) Alert fires :: monitoring must catch silent bad data — quarantine rate, freshness lag, test pass rate — never wait for "when someone complains"
2) Classify the root cause :: the branch decides containment: upstream schema/source change, bad deploy, or corrupt partition
3) Contain: pause ingest, rollback, or quarantine the partition :: stop the bleeding — publish to staging and promote only when gates pass, so consumers keep last-known-good data
4) Fix and add the missing check :: every incident ends as a new automated check; that is how reliability compounds
5) Backfill idempotently :: lineage enumerates impacted tables so you reprocess only affected partitions — `DELETE + INSERT` per partition or `MERGE`, never blind append
6) Verify reconciliation and tests :: row counts per partition, `SUM(hash(...))` checksums on business keys, sampled source-vs-target diff
7) Blameless postmortem :: close the loop — the new check from step 4 is what makes the next alert fire earlier

? Why page on the *first* miss of a 99% daily freshness SLO? :: 30 daily runs give an error budget of (1 − 0.99) × 30 = 0.3 runs — below one run — so a single miss already yields 96.7% and breaches; otherwise reshape the SLI as 15-minute probes (≈28 late samples/month) and alert on fast burn

? Why must backfills be idempotent? :: Same input → same output is what makes retries and surgical backfills safe; blind append would duplicate partitions already loaded

? What does the circuit breaker do when a gate fails? :: Stops the swap: publish to staging and atomically promote, so consumers receive last-known-good data instead of garbage

? Why is lineage a pillar of observability, not optional? :: Metrics say *what* broke and logs *where*, but lineage answers "which dashboards and models are downstream?" — bounding the blast radius and scoping the backfill
:::
===== research/14-resources-practice.md =====
:::glide From Five Sources to One Repo
1) Diagnose the weak area :: Start from the need, not the firehose — **wiki** explains, **handbook** curates, **SDE** builds, **newsletters** keep you sharp.
2) Need a concept → Wiki :: Mid-build lookups: `Kappa Architecture`, `Idempotence` — one verified link per course section, never search blind.
3) Need a book or course → Handbook :: Read it like a **menu, not a course**: commit to the Fundamentals → DDIA 2e pair, close the tab, build.
4) Need hands-on reps → SDE :: 100+ posts with full code; each of drills 1–15 names its tutorial and the section it trains.
5) Need current signal → DET + DEC :: Community/events plus practitioner benchmarks — finish the archives in Week 6 for current tool takes.
6) Attach drills to one build spine :: `API → ingest → lake → transform+DQ → serve → ops` — one repo, layers added weekly, so reps compound.
7) Pick ONE archetype, finish it :: Batch lakehouse, streaming, CDC, DQ-gated, or LLM — a small finished repo beats three half-cloned tutorials.
8) Ship README + rehearse the walkthrough :: The drill-15 walkthrough **IS** the A3 architecture screen — rehearse until 5 minutes feels short.
? Why the 1:2 read-to-build ratio? :: Tutorial hell: a 40th Spark video compounds to zero. Every reading hour earns two hours in drills; if you cannot whiteboard failure modes — rerun, schema drift, hot key — you watched, you did not learn.
? Why start drill 9 in Week 2? :: It is the **spine** — the batch beginner project (API → S3 → warehouse → dbt) that every later drill attaches to as layers are added weekly.
? Why one finished archetype, not three repos? :: A small finished repo with a README naming tradeoffs outcompetes any certificate — and its walkthrough doubles as the architecture screen.
? Wiki or handbook — which, when? :: Wiki for **concept lookups mid-build**; handbook to **find** — the single index for books, courses, interview rounds; newsletters only to stay current.
:::
===== research/15-interview-prep.md =====
:::glide The Six-Step Answer
1) Clarify :: State back the **freshness SLA**, consumers, correctness, constraints — never skip the SLA question
2) Estimate :: ev/s → ev/day → raw → replicated → compressed; capacity math **before** architecture
3) High-level design :: Draw the happy path, **SLA named on every hop**
4) Tradeoffs :: Per arrow: alternative, why rejected, **one number** — probes land hardest here
5) Ops & failure :: Lag, DLQ, schema gates, replay, GDPR, cost — offered **unprompted**
6) Evolution :: "At 10x, bottleneck X; I change Y" — pre-computed per scenario
7) Evidence :: Close on the ledger: claim → story → artifact → metric → matrix line — "**I**", never "we"

? Why defend Scenario 0 first, not a green-field prompt? :: The committee scores narrative + evidence from your **real delivered work**; one "why" probe exposes architecture you didn't build, and "we" with no "I" earns no matrix credit.

? At 100k ev/s, why 48 Kafka partitions? :: Per-partition ≈ **1.04 MB/s** ≪ 10 MB/s ceiling, and 48 matches Flink parallelism — 24h Kafka footprint ≈ 13 TB → 6 brokers × 4 TB usable.

? When does exactly-once fail to be correctness? :: Checkpoints/2PC guarantee **processing semantics only** — late joins, timezone bugs, fraud are yours; answer with watermarks, dedup windows, reconciliation.

? What breaks first at 10x in the click pipeline? :: **Flink state, not Kafka throughput** — and in migration, waves order by *consumer*, not table, so no consumer ever sees wrong data.
:::
===== research/16-genai-design.md =====
:::glide Where GenAI Plugs In
1) **Clarify requirements** :: Pin freshness, latency, and confidence thresholds *before* naming any model — the Scenario-0 discipline transferred to GenAI (Interview Lens).
2) **Frame as ML task** :: Next-token prediction on a decoder-only Transformer; two-stage training — unsupervised pretraining, then finetuning on domain data (ch2, p54-55).
3) **Prepare data the GenAI way** :: Feature engineering gives way to collecting vast data, quality/safety, and storage + retrieval — Llama 3: 15T tokens ≈ 50TB; collect, clean, then data-efficiency (ch1, p14-15).
4) **Choose model by arithmetic** :: One-pass latency → GAN/VAE; ceiling quality → diffusion; resolution at scale → AR over discrete tokens; video economics → latent diffusion (Key Takeaways).
5) **Default to RAG** :: parse → chunk → embed → ANN-index; 5M pages → 40M chunks (+20%/yr); exhaust retrieval + prompts before finetuning — finetune the LLM last (ch6, p168, p171).
6) **Pick adaptation by cost** :: prompt engineering < LoRA (MBs, frozen base) < DreamBooth (GBs, best fidelity) — pick by storage and SLA, not leaderboard (ch10, p266-269).
7) **Evaluate offline + online** :: Name the instrument (BLEU, CIDEr, CLIPScore, FID/FVD, DINO) *and* the business metric (CTR, adoption, cost per user) — naming both unprompted is the scoring behavior (ch9, p250-251).
8) **Deploy + monitor as a named stage** :: Serving services and retraining loops are their own step; watch cost per user — re-rolling seeds with new prompts quietly multiplies GPU spend (ch1, p13; ch9, p251).
? Why is finetuning the wrong first move for knowledge injection? :: It can't cite sources, needs constant retraining, and is expensive and data-hungry; RAG balances cost, scalability, freshness — finetune the LLM only when retrieval is fixed and answers are still bad (ch6, p161-171).
? When does exact nearest-neighbor search break? :: Past millions of items — linear scan is O(N x D), 40M comparisons per query at 40M chunks; ANN (tree / LSH / clustering / HNSW graph) is mandatory (ch6, p173-175).
? What does each similarity metric actually measure? :: CLIP = semantics, DINO = visual detail, face-recognition models = identity — CLIP and DINO can score high on images of two different people, so identity claims need the third instrument (ch10, p274).
? Why latent diffusion for video? :: Pixel-space 5s @ 24FPS 720p lands around 7 minutes; the 8x spatial / 8x temporal VAE compression is **512x smaller**, so diffusion runs entirely in latent space (ch11, p283-284).
:::
===== research/17-ml-design.md =====
:::glide One Skeleton, Eleven Designs
1) Clarify requirements :: the panel's menu — business objective, features, data sources/labels, constraints, scale, accuracy-vs-latency (ch1, p1-2)
2) Frame as ML task :: the load-bearing move: translate business goal → trainable objective — "increase engagement" → "maximize watch time" (Table 1.1, p3)
3) Prepare data :: ETL plus feature ops — imputation, scaling, encoding; seniority lives in data engineering, the models are the easy 20%
4) Develop a model :: the ladder — popularity baseline → LR → DNN → ensemble only if needed (ch1, p14)
5) Evaluate offline + online :: reproduce the elimination chain (MRR vs recall@k vs nDCG vs mAP vs NCE) — every chapter discards candidates for stated reasons
6) Deploy and serve :: retrieve-then-rank — candidate generation → ranking → re-ranking; business rules stay in re-rank, never in the model (ch2, p47)
7) Monitor and retrain :: continual learning where freshness matters (ch7/ch8), batch-vs-online as a stated trade (ch11, p247)
? Why weight unobserved pairs with WALS in matrix factorization? :: Observed-pairs-only loss hits zero with degenerate all-ones embeddings; adding weighted unobserved pairs forces real separation (ch6, p131-132).
? Why does recall@k fail for visual search at billions of images? :: Millions of relevant items drown recall@k, and precision@k is rank-blind — the elimination chain lands on nDCG for continuous relevance (ch2, p42-46).
? Why do ad click models demand continual learning while GBDT fights it? :: A 5-minute model-update delay measurably damages performance, and GBDT cannot be fine-tuned — only retrained from scratch — so DCN/DeepFM win (ch7, p162; ch8, p171-172, p186).
:::