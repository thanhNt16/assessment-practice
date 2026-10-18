## Distributed Systems Fundamentals

Interviewers rarely say "CAP theorem" — they test it by asking why your Kafka topic has 3 replicas with `min.insync.replicas=2`, whether a retried Spark job double-counts, or why Snowflake loads can safely re-run.

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

::::diagram quorum-replication.png
:::
### CAP & the Consistency Spectrum

- **CAP, read correctly:** only when a network *partition* occurs must you choose — **CP** (refuse stale answers, sacrifice availability) or **AP** (serve possibly stale data, sacrifice consistency). "CA" is only coherent for non-distributed systems with no partitions ([CAP theorem](https://en.wikipedia.org/wiki/CAP_theorem)).
- "C" here means linearizability ([Gilbert–Lynch proof](https://en.wikipedia.org/wiki/CAP_theorem)); the practical spectrum from [Jepsen](https://jepsen.io/consistency) is: strong → sequential → causal → eventual.
- **Read-your-writes** is the pragmatic middle users actually need: a session sees its own writes without global coordination.
- ACID vs BASE ([Vogels, Eventually-Consistent](https://www.allthingsdistributed.com/2008/12/eventually_consistent.html)):

| Model | Core promise | Cost |
|---|---|---|
| **ACID** | Atomic, Consistent, Isolated, Durable per transaction | Locks + coordination + latency |
| **BASE** | Basically Available, Soft state, Eventually consistent | Stale reads, app-level conflict handling |

| Consistency level | Guarantee | Tools that offer it |
|---|---|---|
| Linearizable | Every read sees latest committed write | ZooKeeper, etcd, Spanner |
| Sequential | Per-partition/client order kept, no cross-client causality | Kafka per-partition ordering |
| Causal / read-your-writes | See effects of causes you observed | DynamoDB strongly consistent reads, MongoDB causal sessions |
| Eventual | Replicas converge when writes stop | Cassandra ONE (tunable), Redis replicas, DynamoDB default reads |

```mermaid
flowchart TD
    REQ[Request arrives at cluster] --> P{Network partition now}
    P -- No partition --> OK[CA is possible - serve consistent and available]
    P -- Partition --> CH{Pick one}
    CH -- Consistency --> CP[CP - block or reject rather than serve stale]
    CH -- Availability --> AP[AP - answer with possibly stale data]
    CP --> EX1[Examples - ZooKeeper - etcd - HBase - Kafka min ISR]
    AP --> EX2[Examples - Cassandra - DynamoDB - DNS]
```

### Replication & Partitioning

- **Leader–follower replication:** *sync* (follower acks before commit — no loss, higher latency) vs *async* (fast, but failover loses recent writes and lagging followers serve stale reads). Semi-sync is the middle ground.
- **Quorum rule:** `R + W > N` forces read and write sets to overlap; `W > N/2` prevents two write quorums (split-brain).

```text
Quorum: N=5 replicas, W=3 writers, R=3 readers  ->  R+W=6 > 5

  write W=3              read R=3            forced overlap
 +----+----+----+       +----+----+----+
 | R1 | R2 | R3 |       | R1 | R4 | R5 |     R1 sits in both sets,
 +----+----+----+       +----+----+----+     so the reader always
                                              sees the newest value
```

:::info Worked Example
Quorum sizing on N=5 replicas at 90% node uptime:

- **W=3, R=3:** write availability = P(≥3 of 5 up) = 10·0.9³·0.1² + 5·0.9⁴·0.1 + 0.9⁵ = **99.1%**; read availability identical. R+W=6>5 → every read sees the latest acknowledged write. Tolerates 2 failures on both paths.
- **W=1, R=5:** write availability = 1 − 0.1⁵ ≈ **99.999%** (any single node accepts, lowest latency); read availability = 0.9⁵ = **59.0%** — reads need all 5 nodes, but each read is maximally fresh.
- **Decision:** W=3/R=3 for balanced OLTP; W=1/R=5 only for write-heavy, rarely-read telemetry where a failed read can simply be retried.
:::

- **Hash vs range partitioning:** hash spreads load uniformly but kills range scans; range is scan-friendly but hot-spots on monotonically increasing keys (timestamps, IDs). Fix hot keys by salting or shard splitting.
- **Rebalancing:** `hash(key) mod N` moves nearly everything when N changes; consistent hashing or many-fixed-partitions → few assignments move (Kafka's model).
- **Consensus in one breath:** Raft/Paxos make a cluster agree on one ordered log despite crashes — the engine behind leader election and metadata ([Raft](https://raft.github.io/)): Kafka KRaft controllers, Flink HA via ZooKeeper, etcd, HDFS QJM.

### Idempotency & Exactly-Once Myths

- Retries are mandatory in distributed systems → delivery is **at-least-once** → duplicates are guaranteed, not exceptional.
- **Idempotency** makes replays harmless: same operation applied twice = same result. Mechanisms: idempotency keys, dedup tables, MERGE/upsert keyed on a natural ID, storing offsets in the same transaction as results.
- "Exactly-once" is **effectively-once end-to-end**: Kafka EOS = idempotent producer (PID + per-partition sequence numbers) + transactional offsets ([Kafka semantics](https://kafka.apache.org/documentation/#semantics)); the sink must participate — e.g., an Iceberg sink committing on Spark checkpoints.
- No system executes a side effect literally once; it guarantees the *observable effect* happens once via dedup + atomic commit.

### Time, Clocks & Event Ordering

- Wall clocks drift (NTP skew, leap seconds) — never order business events with `now()` across machines.
- **LWW dangers:** last-write-wins silently discards concurrent updates — data loss disguised as conflict resolution.
- **Vector clocks in one line:** per-node counters that detect causality and concurrency without a global clock (Dynamo, Riak).
- Hence stream processing runs on **event time** (record timestamp) + **watermarks** ("no earlier events expected") so windows close deterministically despite disorder ([Flink event time](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/)).

### Transactions, Backpressure & the Fallacies

- **2PC:** coordinator prepares, then commits all participants — atomic but **blocking**: a coordinator crash leaves locks held. Fine inside one cluster (Flink two-phase-commit sinks), poor across services.
- **Saga:** chain of local transactions, each with a compensating transaction on failure — trades atomicity for availability; the microservices default over cross-service 2PC.
- **Backpressure:** consumers slower than producers fill unbounded buffers until OOM. Flow control = bounded queues, credit-based transfer (Flink), pull-based consumption (Kafka), rate limits (Spark `maxOffsetsPerTrigger`).
- **Fallacies of distributed computing:** the network is reliable, latency is zero, bandwidth is infinite, the network is secure, topology doesn't change, there is one admin, transport cost is zero, the network is homogeneous. Every timeout, retry policy, and buffer bound exists because these are false.

### Where This Shows Up

**Use cases:**
- **CAP:** Kafka's `unclean.leader.election.enable` is an explicit CP-vs-AP switch; Iceberg commits use optimistic concurrency on the metadata pointer, serialized by catalog CAS ([Iceberg spec](https://iceberg.apache.org/spec/)).
- **Replication/quorum:** `acks=all` + `min.insync.replicas` ≈ write quorum over the ISR; read from followers trades freshness for locality.
- **Partitioning:** Kafka partition keys, Spark hash-shuffle skew, Iceberg bucket transforms + partition evolution, Snowflake clustering keys (range-style micro-partitions).
- **Idempotency:** Kafka idempotent producer; Spark `foreachBatch` + MERGE; Snowflake COPY skips already-loaded files for 64 days ([docs](https://docs.snowflake.com/en/user-guide/data-load-considerations-load)); Iceberg MERGE makes replays no-ops.
- **Event time:** Spark Structured Streaming / Flink watermarks; Kafka record timestamps (`CreateTime` vs `LogAppendTime`).
- **Consensus:** Kafka KRaft replaced ZooKeeper with a Raft quorum of controllers; Flink HA elects the JobManager via ZooKeeper.

:::tip Go Deeper — DDIA 2nd Edition (Mar 2026)
This section maps almost 1:1 to [DDIA 2e](https://martin.kleppmann.com/2026/03/24/designing-data-intensive-applications-2e.html) (Kleppmann & Riccomini): ch6 Replication, ch7 Sharding, ch8 Transactions, ch9 The Trouble with Distributed Systems, ch10 Consistency & Consensus. 2e adds cloud/object-store-native framing and renames Partitioning→Sharding. Per-chapter further-reading lists: [ept/ddia2-references](https://github.com/ept/ddia2-references). Free ch1+2+9 excerpt via [ScyllaDB](https://lp.scylladb.com/designing-data-intensive-apps-book-offer).
:::

### Key Takeaways

- Under partition you pick C or A explicitly — every distributed store answers this whether you choose or not.
- `R + W > N` is the dial trading read/write availability and latency against freshness.
- Design every consumer and sink to be safe when it runs twice — because retries guarantee it will.
- Event time + watermarks exist because wall clocks lie across machines.
- "Exactly-once" = at-least-once delivery + idempotent, transactional sinks — never a transport guarantee alone.

### Interview Lens

- Asked "is Kafka CP or AP?": answer it's tunable per topic — quote `min.insync.replicas` and unclean leader election as the two knobs.
- Volunteer the quorum math (W=3/R=3 vs W=1/R=5) when replication factor comes up — it shows reasoning, not recitation.
- Map any "what if the job crashes mid-run?" question to idempotency + checkpointing, never to "it probably won't happen".
