## SQL Deep Dive: The Problems EPAM Actually Asks


:::tldr
- Window functions compute per-row values over a frame without collapsing rows — the core difference from GROUP BY.
- Canonical dedup: `ROW_NUMBER() OVER (PARTITION BY key ORDER BY ts DESC, id DESC)`, keep rn=1 — one scan, deterministic ties.
- Logical order: FROM/JOIN → WHERE → GROUP BY/HAVING → windows → ORDER BY; WHERE filters rows, HAVING filters groups.
- SARGable predicates only: `CAST(dt AS STRING)` full-scans; `dt = DATE '2024-01-01'` prunes partitions.
- LEFT JOIN plus WHERE on the right table's column silently becomes an INNER JOIN — move it into ON.
- Duplicate join keys fan out rows: a 1.1x key duplication silently doubles summed revenue.
- CTEs get inlined and recomputed — Snowflake: `AS MATERIALIZED`; Spark: `CACHE TABLE`.
:::

EPAM senior DE screens live in SQL mechanics — windows, dedup, grouping traps — and in whether you know how the engine logically executes a query.

:::scenario Scenario — SQL Execution & Window Playbook
@start FROM and JOIN :: Base rows enter first; duplicate join keys fan out and silently double sums — check row counts at FROM/JOIN.
? Join keys duplicated => @dedup |success
? Rows come back clean => @where |fail
@dedup Dedup with ROW_NUMBER :: `PARTITION BY customer_id ORDER BY order_ts DESC, id DESC`, keep rn=1 — one scan, deterministic ties, one row per key.
-> deduplicated => @where
@where WHERE :: Filters **rows only** — keep predicates SARGable so the engine can prune partitions.
? Predicate SARGable => @group |success
? Column wrapped in a function => @sarg |fail
@sarg Fix the SARGability break :: `WHERE CAST(dt AS STRING)=...` full-scans; compare `dt = DATE '2024-01-01'` and let partition pruning work.
-> unwrapped and pruning => @group
@group GROUP BY and HAVING :: Groups form after WHERE; HAVING filters groups. Need a value on **every row** instead? Windows run here.
? Need per-row values over a frame => @window |success
-> collapse and filter groups => @limit
@window SELECT + window functions :: One pass, every row survives — unlike GROUP BY. RANK 1,1,3 vs DENSE_RANK 1,1,2: should ties consume ranks?
? Engine has QUALIFY => @qualify |success
? OSS Spark, no QUALIFY => @limit |fail
@qualify QUALIFY variant :: Snowflake and Databricks SQL filter windows natively; the rn=1 subquery collapses into a single clause.
-> native window filter => @limit
@limit ORDER BY and LIMIT :: Aliases and windows finally visible — windows already ran. Re-explain the plan: pushdown, pruning, shuffle size.
-> keep tuning => @start
:::
::::diagram sql-pipeline.png
:::

### Window Functions

Window functions compute a value per row over a related set of rows **without collapsing them** — the core difference from GROUP BY. `PARTITION BY` defines the group, `ORDER BY` defines the frame; windows run *after* GROUP BY/HAVING, *before* ORDER BY ([Postgres tutorial](https://www.postgresql.org/docs/current/tutorial-window.html)).

- Running total: `SUM(amount) OVER (ORDER BY dt ROWS UNBOUNDED PRECEDING)` — every row survives, unlike GROUP BY.
- RANK vs DENSE_RANK on scores `100,100,90`: RANK → `1,1,3`; DENSE_RANK → `1,1,2`.

| Function | Returns | Typical use |
|---|---|---|
| `ROW_NUMBER()` | 1,2,3 — unique per partition | dedup, latest record per key |
| `RANK()` / `DENSE_RANK()` | ties share rank; gaps vs no gaps: 1,1,3 vs 1,1,2 | rankings, tiers, percentiles |
| `LAG(col)` / `LEAD(col)` | previous / next row value | deltas, session starts |

### The Classic Problems

:::info Worked Example
Dedup — latest order per customer. Naive self-join: the correlated subquery re-scans the table per row, and ties return duplicates.

```sql
SELECT o.* FROM orders o WHERE o.order_ts =
  (SELECT MAX(order_ts) FROM orders i WHERE i.customer_id = o.customer_id);
```

Windowed: one scan plus one sort, deterministic tie-break, exactly one row per key even on ties.

```sql
SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id
         ORDER BY order_ts DESC, id DESC) AS rn FROM orders) t
WHERE rn = 1;
```

The window wins because it does a single pass instead of a correlated re-scan per row, makes ties deterministic, and never duplicates rows. Snowflake and Databricks SQL collapse it further with QUALIFY (OSS Spark has no QUALIFY):

```sql
SELECT * FROM orders QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id
     ORDER BY order_ts DESC, id DESC) = 1;
```
:::

**Use cases:**

- Dedup: latest record per key from append-only sources.
- Sessionization: gap-based sessions from clickstream timestamps.
- Cumulative KPIs: running totals, month-over-month deltas via LAG.
- Top-N dashboards: top 3 products per region (`ROW_NUMBER ... WHERE rn <= N`).

```sql
-- increment a counter at every >30min gap; running sum = session id
SELECT user_id, ts,
       SUM(CASE WHEN ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) > INTERVAL 30 MINUTE THEN 1 ELSE 0 END)
         OVER (PARTITION BY user_id ORDER BY ts) AS session_id
FROM clicks;
```

GROUP BY traps:

- `WHERE` filters rows **before** grouping; `HAVING` filters groups after — aggregates are illegal in WHERE.
- `COUNT(col)` skips NULLs, `COUNT(*)` counts rows, NULL is its own group; every SELECT column must be grouped or aggregated (Spark enforces strictly; Snowflake offers `ANY_VALUE`).

Join anti-patterns:

- LEFT JOIN plus WHERE on the right table's column silently becomes an INNER JOIN — move the condition into ON.
- Duplicate join keys cause row fan-out (a 1.1x key duplication silently doubles revenue sums); non-equi and comma joins degrade to nested loops or cross joins.

CTE vs subquery vs temp table:

| Option | Materialized | Reuse scope | Use when |
|---|---|---|---|
| CTE | No — inlined | one query | readability, recursion |
| Derived table | No | one query | single-use filter or agg |
| Temp table | Yes — written to storage | session or job | heavy multi-step pipelines |

Snowflake CTEs recompute per reference unless declared `AS MATERIALIZED`; Spark inlines them and may recompute — pin big intermediates with `CACHE TABLE` ([Spark CTE docs](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-cte.html)).

### Query Optimization

```mermaid
flowchart TD
    A[FROM and JOIN] --> B[WHERE]
    B --> C[GROUP BY]
    C --> D[HAVING]
    D --> E[SELECT and window functions]
    E --> F[ORDER BY]
    F --> G[LIMIT]
```

```text
Stage                  Sees
FROM / JOIN            base rows
WHERE                  rows only
GROUP BY / HAVING      groups only
SELECT + window fns    aliases + one window pass
ORDER BY / LIMIT       aliases and windows visible
```

- SARGable predicates — never wrap the filtered column in a function:

```sql
WHERE dt = DATE '2024-01-01'              -- prunes partitions
WHERE CAST(dt AS STRING) = '2024-01-01'   -- full scan
```

- Partition pruning: filter the partition column (`dt`, `event_date`) early — Snowflake micro-partitions prune on min/max metadata ([docs](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions)).
- Pre-aggregation and join order: aggregate before the join (shuffle 1M grouped rows, not 100M facts), small side on the build side, broadcast under `spark.sql.autoBroadcastJoinThreshold` ([tuning guide](https://spark.apache.org/docs/latest/sql-performance-tuning.html)).
- Statistics: stale stats mean wrong join strategy — `ANALYZE TABLE t COMPUTE STATISTICS` in Spark ([docs](https://spark.apache.org/docs/latest/sql-ref-syntax-aux-analyze-table.html)).
- `SELECT *` hurts columnar warehouses: reads every column, defeats column pruning, and breaks when schemas evolve.

### Dialect Differences

| Feature | Snowflake | Spark SQL / Databricks |
|---|---|---|
| Filter rows by window | `QUALIFY` native ([docs](https://docs.snowflake.com/en/sql-reference/constructs/qualify)) | OSS: absent — subquery; Databricks SQL has QUALIFY |
| CTE materialization | `WITH t AS MATERIALIZED` opt-in | inlined; `CACHE TABLE` to pin |
| Temp storage | `CREATE TEMPORARY TABLE` — session data | `CREATE TEMP VIEW` — metadata only, no data |

**Practice questions (reported style):**

1. Find duplicate rows and keep only the latest per customer_id.
2. Return the top 3 products by revenue for every region.
3. Sessionize a clickstream with a 30-minute inactivity cutoff; count sessions per user per day.
4. Compute cumulative revenue by month and the change vs the prior month (LAG).
5. Why does this LEFT JOIN return more rows than the left table?

:::cards
Q: What do window functions do that GROUP BY cannot? :: Keep every row while computing a value over a related frame — no collapse.
Q: Name the canonical dedup pattern for latest record per key. :: `ROW_NUMBER() OVER (PARTITION BY key ORDER BY ts DESC, id DESC)`, keep rn=1.
Q: RANK vs DENSE_RANK on scores 100, 100, 90? :: RANK: 1,1,3 with gaps; DENSE_RANK: 1,1,2 without.
Q: Why are aggregates illegal in WHERE? :: WHERE filters rows before grouping; group-level filters belong in HAVING.
Q: What silently turns a LEFT JOIN into an INNER JOIN? :: A WHERE predicate on the right table's column — move it into ON.
Q: What does a 1.1x duplicate join key do to a revenue SUM? :: Fans out rows and silently doubles the total.
Q: How do you stop CTE recomputation? :: Snowflake: `WITH t AS MATERIALIZED`; Spark: `CACHE TABLE` to pin intermediates.
:::

### Key Takeaways

- Window functions solve dedup, top-N, running totals, and sessionization in one scan — prefer them over self-joins.
- `ROW_NUMBER` for exact dedup; `RANK`/`DENSE_RANK` when ties matter; LAG/LEAD for gaps-and-islands.
- WHERE filters rows, HAVING filters groups, windows filter via QUALIFY or a subquery — know which stage each lives in.
- SARGable predicates, early partition filters, and pre-aggregation are the levers to name when asked "why is this slow"; `SELECT *` on columnar stores is a cost, pruning, and schema-evolution smell.

### Interview Lens

- Expect a live "latest record per key" — answer with ROW_NUMBER and volunteer the QUALIFY variant unprompted.
- Tie-breaks are the trap: mention `ORDER BY ..., id DESC` before the interviewer does.
- Walk the logical execution order — pushdown, pruning, shuffle size — instead of reaching for "add an index".
