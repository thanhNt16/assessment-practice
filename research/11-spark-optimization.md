## Spark Performance: Catalyst, AQE & Tuning


:::tldr
- Catalyst: rule-based logical optimization (pushdown, pruning, folding) + cost-based physical planning; without `ANALYZE TABLE`, `sizeInBytes` defaults huge so auto-broadcast never fires at compile time.
- AQE re-plans at each shuffle boundary from actual map-output stats — default since 3.2: coalesce toward ~64 MB, skew-join split, SMJ→BHJ/SHJ switch; useless without an Exchange.
- AQE skew-join split fires only above BOTH thresholds: > 5× median partition AND > 256 MB — joins only; groupBy skew needs salting.
- Join choice = one threshold + honest stats: broadcast ≤ 10 MB (misestimate → driver OOM), SHJ on hint, SMJ the robust default.
- Size partitions ≈ shuffle bytes ÷ 128–256 MB — the 200 default is wrong in both directions; over-provision and let AQE coalesce (it cannot split ordinary oversized partitions).
- Unified memory (fraction 0.6): storage evicts, execution spills; G1GC for ≥4–8 GB heaps; GC > 10–15% of task time = allocation churn.
- Diagnose from the UI: max ≫ p50 → skew; spill counters → memory; fix data shape before knobs.
:::

Catalyst compiles your query into fused machine code, AQE repairs bad plans mid-flight using runtime stats, and nearly every production Spark incident reduces to one UI metric: shuffle size, skew, spill, or GC.

:::scenario Scenario — Skew Diagnosis
@start Hot stage in the UI :: one stage's max task time dwarfs the rest — name the metric before touching any config
-> compare task times => @p50
@p50 p50 vs max fork :: median healthy, max huge → skew; every task slow → sizing, not hot keys
? max far above p50 => @operator |success
? all tasks uniformly slow => @uniform |fail
@uniform Right-size partitions :: spill and GC, not skew — 500 GB ÷ 200 = 2.5 GB tasks; size ≈ shuffle bytes ÷ 128 MB, AQE coalesces down
-> re-check the stage => @verify
@operator Join or groupBy? :: AQE de-skews joins only; aggregation skew needs salting — name the operator before choosing a fix
? skewed join => @bytes |success
? skewed groupBy => @salt |fail
@bytes Measure partition bytes :: AQE splits only above skewedPartitionFactor (5× median) AND skewedPartitionThresholdInBytes (256 MB)
? both thresholds met => @aeskew |success
? under one threshold => @manual |fail
@manual Threshold miss :: below either knob AQE never fires — find a broadcastable side or salt the key yourself
? small side ≤ 10 MB => @broadcast |success
? big-big join => @salt |fail
@aeskew AQE skew split :: skewJoin splits the fat side toward advisory 64 MB subtasks; SMJ/SHJ only — confirm in the AQE plan
-> re-check the stage => @verify
@broadcast Broadcast the dim :: honest stats ≤ autoBroadcastJoinThreshold (10 MB) remove the skew-prone shuffle; misestimate → driver OOM
-> re-check the stage => @verify
@salt Salt the hot key :: random prefix, partial agg, then final agg — the only fix that de-skews groupBy; AQE split does not
-> re-check the stage => @verify
@verify Confirm the repair :: max ≈ p50 again, no spill, plan shows split/broadcast (isFinalPlan=true) — else diagnose again
-> diagnose again => @p50
:::
::::diagram skew-diagnosis.png
::::
:::

### Catalyst: The Query Optimizer

- Four phases: parse → analyze (resolve names/types against the catalog) → optimize the logical plan (rules) → pick a physical plan (cost) → whole-stage codegen per stage:

:::steps Catalyst, phase by phase
```mermaid
flowchart LR
  Q[[SQL or DataFrame]] --> U[Unresolved Logical Plan]
  AN --> |analyzer resolves catalog| AN[Analyzed Logical Plan]
  AN --> |rule batches to fixed point| OPT[Optimized Logical Plan]
  OPT --> |cost based JoinSelection| PH[Physical Plan]
  PH --> AQE[AdaptiveSparkPlan]
  AQE --> |whole-stage codegen| EX[Executed stages]
  EX -. completed shuffle stats .-> AQE
```
SQL or DataFrame code parses into an unresolved logical plan — names not yet bound. :: Q,U
The analyzer resolves references against the catalog to an analyzed logical plan. :: AN
Rule batches run to a fixed point — predicate pushdown, column pruning, constant folding — no statistics needed. :: OPT
Cost-based JoinSelection picks physical strategies from catalog stats (sizeInBytes, rowCount); without ANALYZE TABLE auto-broadcast never fires at compile time. :: PH
AdaptiveSparkPlan re-plans at runtime from completed shuffle stage statistics — isFinalPlan=true in explain output. :: AQE
Whole-stage codegen fuses each stage into one Java function — no per-row virtual dispatch. :: EX
:::

- **Rule-based** optimizer: batches of `Rule[LogicalPlan]` applied to a fixed point — no statistics needed ([SQL docs](https://spark.apache.org/docs/latest/sql-programming-guide.html)):

| Rule | What it does | Example |
|---|---|---|
| PredicatePushdown | filters before join/exchange | `WHERE` on partition column prunes files |
| ColumnPruning | reads only referenced columns | parquet scan of 3 of 200 columns |
| ConstantFolding | folds literal math / dead branches | `WHERE 1 = 0` → empty relation |

- **Cost-based** physical planning: `JoinSelection` compares plan sizes from catalog stats (`sizeInBytes`, `rowCount`); `spark.sql.cbo.enabled` (default `false`) enables richer stats. Without `ANALYZE TABLE`, `sizeInBytes` defaults to a huge value → auto-broadcast never fires at compile time.
- **Whole-stage codegen** fuses all operators of one stage into a single Java function — no per-row virtual dispatch; falls back above `spark.sql.codegen.maxFields` (100).
- Read it in `explain("formatted")`: look for `PushedFilters`, the `ReadSchema` column list, the number of `Exchange` nodes, and the `*` codegen marker — abridged:

```text
== Physical Plan ==                     <- isFinalPlan=true means AQE re-planned
AdaptiveSparkPlan (6)
+- Sort (5)
   +- Exchange hashpartitioning(customer_id, 4096)   <- each Exchange = a stage cut
      +- Project (3)                                  <- ColumnPruning happened
         +- Filter (2)                                <- Pushdown happened
            +- Scan parquet (1)
               PushedFilters: [IsNotNull(customer_id)]
               ReadSchema: struct<customer_id:string,amount:decimal(10,2)>
```

- Tungsten carries this to hardware: `sun.misc.Unsafe` off-heap allocation, a compact binary row format (`UnsafeRow`) instead of JVM objects, and cache-aware computation ([Databricks, Project Tungsten](https://www.databricks.com/blog/2015/04/28/project-tungsten-bringing-spark-closer-to-bare-metal.html)) — GC pressure drops because data stops living as objects.

### AQE: Adaptive Query Execution

- Re-optimizes at each shuffle boundary using **actual map-output stats** from completed stages ([performance tuning docs](https://spark.apache.org/docs/latest/sql-performance-tuning.html), [Databricks AQE](https://www.databricks.com/blog/2020/05/29/adaptive-query-execution-speeding-up-spark-sql-at-runtime.html)); on by default since 3.2.0 (`spark.sql.adaptive.enabled`).

| Feature | Triggers when | Knobs |
|---|---|---|
| Coalesce partitions | many tiny post-shuffle partitions | merge toward `advisoryPartitionSizeInBytes` (64 MB); `parallelismFirst=true` keeps a floor |
| Skew-join split | partition > `skewedPartitionFactor` (5) × median **and** > `skewedPartitionThresholdInBytes` (256 MB) | splits only the fat side into target-size subtasks; joins only (SMJ/SHJ) |
| Join-strategy switch | runtime side fits `spark.sql.adaptive.autoBroadcastJoinThreshold`, or empty-partition ratio ≥ `nonEmptyPartitionRatioForBroadcastJoin` (0.2) | SMJ → broadcast hash or shuffled hash |

- Limits: nothing to re-plan without an `Exchange`; coalesce skips user-forced `repartition(n)`; skew split does not help groupBy/aggregate skew — salt those.

### Join Strategies

| Strategy | Condition | Trade-off |
|---|---|---|
| Broadcast hash (BHJ) | one side ≤ `spark.sql.autoBroadcastJoinThreshold` (10 MB default) per stats | no shuffle of the big side; driver collects + broadcasts; misestimate → driver OOM |
| Shuffled hash (SHJ) | both shuffled, build side fits hash map | no sort needed, faster; chosen only if `preferSortMergeJoin=false` or hinted |
| Sort-merge (SMJ) | default for large equi-joins | both sides sorted; spills gracefully; the robust pick |

- SMJ wins when neither side is reliably small, inputs are unsorted, or you need predictable spill behavior at 3 a.m. — SHJ needs a hint or config; BHJ needs honest stats or AQE runtime rescue.
- **Use cases:**
- Broadcast: star-schema dimensions (MBs to low GBs), enrichment joins in streaming micro-batches, repeated small-lookup joins.
- SMJ: TB-scale fact-fact joins, unknown cardinality, skewed keys (AQE splits apply); SHJ: medium build side where sorting is the bottleneck.

```python
from pyspark.sql import functions as F

dim = spark.read.table("dim_customer")          # 8 MB, stats fresh
orders = spark.read.table("fct_orders")
orders.join(F.broadcast(dim), "customer_id")    # API hint
# SQL: SELECT /*+ BROADCAST(d) */ * FROM fct_orders o JOIN dim_customer d ON ...

spark.conf.set("spark.sql.adaptive.enabled", "true")              # default since 3.2.0
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128m")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "4096")            # size from data; AQE merges down
```

### Shuffle & Partitioning

- Sort-based shuffle (default since 1.2): each map task writes **one** sorted, serialized data file plus an index; each reduce task fetches its byte range from the map task's block manager. No `shuffle.partitions` files per map task — that was the hash era.
- ≤ `spark.shuffle.sort.bypassMergeThreshold` (200) reduce partitions with no map-side combine → bypass: unsorted per-reducer files, no sort cost.
- 200 default is wrong in both directions: 500 GB shuffle → 2.5 GB partitions (spill, skew); 2 GB shuffle → 200 tasks of 10 MB (scheduling overhead). Size from data: `partitions ≈ shuffle_bytes / (128–256 MB)` — or over-provision and let AQE coalesce.
- Skew fixes, in order: AQE skew-join split (joins, zero code) → salting `pmod(hash(key, rand()), N)` for aggregates (two-phase: salted partial agg, then strip) → isolate the hot key with a separate pass.
- `repartition(n)`: full shuffle, can raise partition count — use before heavy joins/writes. `coalesce(n)`: merges without shuffle — cheap, but few fat tasks land on few cores → skew/OOM; only after a filter shrank the data or for small final outputs.

### Memory, Spill & GC

```text
Executor JVM heap, say 20 GB
+---------------------------------------------------------------+
| reserved 300 MB                                                 |
| unified = spark.memory.fraction 0.6 -> 11.8 GB                  |
|   storage 5.9 GB  <--- borrow --->  execution 5.9 GB            |
|     cache, broadcast:      sorts, aggs, joins, shuffles:        |
|     evicted under pressure           SPILL to disk              |
| user memory 0.4 -> 7.9 GB: UDF objects, your collections        |
+---------------------------------------------------------------+
```

- Unified model ([tuning guide](https://spark.apache.org/docs/latest/tuning.html)): `spark.memory.fraction` (0.6) carves the pool; storage and execution borrow from each other. Storage blocks evict; **execution never evicts — it spills**. Per-task execution memory ≈ pool ÷ concurrent tasks, so 5 cores on 12 GB → ~1.4 GB per sort/agg.
- Spill appears when a sort/hash table exceeds that share: `spill (memory)` converts to `spill (disk)` in stage metrics. Fix by target: more partitions, less per-task data, more executor memory, or reduce skew.
- GC pressure: UnsafeRow churn + fat UDF objects → GC time competes with task time. G1GC for ≥4–8 GB heaps (`-XX:+UseG1GC`), Kryo for custom-typed RDDs, avoid `collect()`-scale object graphs.
- OOM patterns: **driver** — `collect()` or broadcasting an underestimated table (fix: limit, `toLocalIterator`, honest stats). **Executor** — skewed task or over-`coalesce`d partitions (fix: AQE/salting, raise partitions). **YARN "memory overhead exceeded"** — raise `spark.executor.memoryOverhead`.

### Reading the Spark UI

| Signal (where) | Means | Action |
|---|---|---|
| Spill (disk) > 0 on sort/agg stages ([web UI](https://spark.apache.org/docs/latest/web-ui.html)) | per-task memory short | partitions ↑, memory ↑, skew ↓ |
| Task max ≫ p50 (Summary Metrics) | skew | AQE skew split or salting |
| GC Time > 10–15% of task time | allocation churn | G1GC, smaller objects, less caching |
| #Files in scan (SQL tab) ≫ data size | small-file problem | compaction, `optimizeWrite` |
| Initial vs final AQE plan differ | runtime rescue fired | verify what changed — do not assume compile-time plan runs |
| Failures concentrated on one executor (Executors tab) | bad node | exclude the node |

:::info Worked Example — Diagnosing a slow join stage
Stats: 2 TB fact join, stage shows shuffle write 500 GB, `spark.sql.shuffle.partitions=200`; summary metrics — median task 35 s, max task **24 min**; the max task (partition 113) reads **40 GB** while a median partition is 500 GB ÷ 200 = **2.5 GB**.
Decision: 40 GB > 256 MB threshold and > 5 × 2.5 GB = 12.5 GB → AQE skew-join split fires, splitting into 40 GB ÷ 64 MB ≈ **625 subtasks** of ~64 MB ≈ 0.6 s each at ~100 MB/s. Stage wall drops from 24 min to the runner-up ≈ 2.5 GB ≈ 40 s.
If it were a `groupBy`, AQE skew split does not apply → salt: `(user_id, pmod(hash(user_id, rand()), 16))`, partial-aggregate salted, second pass strips the salt — 16× parallelism on the hot key.
Broadcast escape hatch? Dim table is 8 GB ≫ 10 MB threshold — forcing `/*+ BROADCAST */` would OOM the driver. No.
:::

:::tip
Over-provision `spark.sql.shuffle.partitions` and let AQE coalesce — AQE merges small partitions but cannot split ordinary (non-skewed) oversized ones. Under-provisioning is unrecoverable at runtime.
:::

:::warning
`/*+ BROADCAST */` overrides stats. Stale statistics after heavy appends make a "small" side huge at runtime — the driver collects it all and dies. Verify `sizeInBytes` in the plan before forcing.
:::

:::cards
Q: What does AQE re-plan with, and since which release? :: Actual shuffle stats at each Exchange boundary — default since Spark 3.2.
Q: State both AQE skew-join split triggers. :: Partition above 5× the median AND above 256 MB — split toward ~64 MB subtasks.
Q: Why doesn't AQE fix skewed groupBy? :: Skew split covers joins only (SMJ/SHJ) — aggregate skew needs salting.
Q: Broadcast join condition and its failure mode? :: One side ≤ 10 MB per honest stats; stale/underestimated stats make the driver OOM collecting it.
Q: How do you size shuffle partitions? :: ≈ shuffle bytes ÷ 128–256 MB — over-provision, AQE coalesces; the 200 default is wrong both ways.
Q: Storage vs execution memory under pressure? :: Storage evicts blocks; execution never evicts — it spills to disk.
Q: What does max task time ≫ p50 in the UI mean? :: Skew; uniformly slow tasks point to sizing, spill, or GC instead.
:::

### Key Takeaways

- Catalyst = rule-based logical optimization + cost-based physical planning; Tungsten = off-heap binary rows + whole-stage codegen; `explain("formatted")` proves pushdown, pruning, codegen actually happened.
- AQE re-plans at shuffle boundaries since 3.2: coalesce to ~64 MB, split >5×-median-and->256 MB skewed join partitions, switch SMJ→BHJ/SHJ; useless without an Exchange, blind to aggregate skew.
- Join choice = one threshold (10 MB) + honest stats: broadcast when one side truly fits, SHJ when sort hurts, SMJ as the robust default.
- Shuffle is the cost center: size partitions from bytes (~128–256 MB), not the 200 default; `repartition` for width, `coalesce` only shrinking.
- The UI answers first: p50-vs-max for skew, spill counters for memory, GC time for pressure — fix data shape before knobs.

### Interview Lens

- On "why is my Spark job slow": open the stage with the largest shuffle read, compare task p50 vs max, check spill and GC — then classify into skew / partitions / memory / GC with numbers, not knob names.
- Whiteboard `SparkPlan` end to end: parsed → analyzed → optimized logical → physical (JoinSelection cost) → AQE re-plan points at each Exchange → codegen; know which optimizations need stats and which need only rules.
- Defend a threshold decision: given a dim table size, compute broadcast feasibility (10 MB rule, driver memory), expected shuffle bytes ÷ 128 MB → partition count, and when you would salt instead of trusting AQE.
