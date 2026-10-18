"""Diagrams s01-s04: assessment-loop, sql-pipeline, spark-runtime, quorum-replication."""
import sys
sys.path.insert(0, '/Users/harry/Desktop/system-design/diagrams/exc')
import exc
from exc import (BLUE_S, BLUE_F, BLUE2_S, BLUE2_F, GREEN_S, GREEN_F,
                 AMBER_S, AMBER_F, RED, ORANGE, GRAY, INK, HDR, WHITE)
ORANGE_F = "#fed7aa"


def s01():
    d = exc.new_doc(); E = exc.B()
    d['elements'] += [
        E.title(60, 40, "EPAM Internal Assessment — Nomination to Matrix Verdict"),
        E.sub(60, 74, "Not a hiring loop: a narrative defense of real delivered work, scored against the competency matrix"),
        E.sect(60, 126, "The assessment flow"),
        # row 1
        E.rect(60, 162, 240, 80, BLUE_S, BLUE_F, "1 · Pick target grade\nA3 confirmation vs\nA3→A4 leadership delta", lsize=13),
        E.rect(350, 162, 240, 80, AMBER_S, AMBER_F, "2 · Manager sponsorship\nstated gate — without it\nassessments stall", lsize=13),
        E.rect(640, 162, 240, 80, BLUE_S, BLUE_F, "3 · Apply year-round\n+ annual promotion-\neligibility review", lsize=13),
        E.rect(930, 162, 240, 80, BLUE_S, BLUE_F, "4 · Assemble evidence\none real project —\ndecisions owned, not tasks", lsize=13),
        E.arrow(300, 202, [[0, 0], [50, 0]]),
        E.arrow(590, 202, [[0, 0], [50, 0]]),
        E.arrow(880, 202, [[0, 0], [50, 0]]),
        # row 2 (right to left)
        E.rect(930, 330, 240, 80, BLUE2_S, BLUE2_F, "5 · Committee defense\npeer/expert panel probes\none level deeper than deck", lsize=13),
        E.rect(640, 330, 240, 80, BLUE_S, "#3b82f6", "6 · Matrix verdict\ndimensions scored\nagainst the grade line", lsize=13, lcolor=WHITE),
        E.rect(350, 330, 240, 80, GREEN_S, GREEN_F, "PASS — grade confirmed\npromotion follows", lsize=13),
        E.rect(60, 330, 240, 80, RED, WHITE, "Feedback — targeted gaps\n(e.g. mentoring < A4 line)\nreapply when mature", dashed=True, lsize=13, lcolor=RED),
        E.arrow(1050, 242, [[0, 0], [0, 88]]),
        E.arrow(930, 370, [[0, 0], [-50, 0]]),
        E.arrow(640, 370, [[0, 0], [-50, 0]]),
        E.text(600, 340, 40, 18, "pass", 12, GREEN_S),
        E.arrow(760, 410, [[0, 0], [0, 35], [-520, 35], [-520, -35]], color=RED, dashed=True),
        E.text(672, 418, 84, 18, "no — gaps", 12, RED),
        # feedback loop back to apply
        E.arrow(180, 330, [[0, 0], [0, -45], [580, -45], [580, -85]], color=RED, dashed=True,
                label="reapply when evidence matures"),
        # competency matrix
        E.sect(60, 480, "Competency matrix — what the committee scores"),
        E.rect(60, 515, 520, 50, BLUE_S, BLUE_F, "Engineering depth\nA3: owns component internals · A4: sets standards others follow", lsize=12),
        E.rect(60, 573, 520, 50, BLUE_S, BLUE_F, "Architecture\nA3: ≥2 options per decision · A4: workstream direction", lsize=12),
        E.rect(60, 631, 520, 50, BLUE_S, BLUE_F, "Delivery impact\nA3: component metrics quantified · A4: team/workstream outcomes", lsize=12),
        E.rect(60, 689, 520, 50, BLUE_S, BLUE_F, "Soft skills & mentoring\nA3: reviews code, grows juniors · A4: leads, sets standards", lsize=12),
        E.rect(60, 747, 520, 50, AMBER_S, AMBER_F, "English B2+ — gates client staffing\nfluent spoken defense; rehearse aloud, timed", lsize=12),
        # I vs We
        E.sect(640, 480, "Evidence theme: I vs We"),
        E.rect(640, 515, 255, 120, BLUE_S, BLUE_F, "I — A3 confirmation\n~1 yr of delivery evidence:\nowned components end-to-end,\nreliable client-facing work", lsize=13),
        E.rect(915, 515, 255, 120, GREEN_S, GREEN_F, "We — A3→A4 delta\nleadership evidence:\nmentoring, review leadership,\nworkstream direction", lsize=13),
        E.text(640, 652, 520, 18, "Failure mode: A3-grade evidence with an A4 label", 13, RED),
        E.text(640, 680, 540, 40, "Committee probes one level deeper than the deck —\nSpark execution model · Delta MERGE · SQL windows, from your war stories", 12, GRAY),
        E.text(60, 830, 1000, 18, "Sponsorship opens the door · the matrix scores the story · A4 needs a leadership delta, not more of the same evidence", 13, INK),
    ]
    exc.save(d, '/Users/harry/Desktop/system-design/diagrams/exc/assessment-loop.excalidraw')


def s02():
    d = exc.new_doc(); E = exc.B()
    stages = [
        ("1 · FROM / JOIN", "base rows enter — dup join keys fan out sums", "sees: base rows"),
        ("2 · WHERE", "filters rows only — can't see SELECT aliases", "sees: rows only"),
        ("3 · GROUP BY / HAVING", "filters groups — aggregates illegal in WHERE", "sees: groups only"),
        ("4 · SELECT + window functions", "one window pass — every row survives", "sees: aliases + window pass"),
        ("5 · DISTINCT", "dedup after SELECT + windows", "sees: projected rows"),
        ("6 · ORDER BY", "aliases + windows finally visible here", "sees: aliases + windows"),
        ("7 · LIMIT", "applies last — windows already computed", "sees: ranked rows"),
    ]
    traps = {  # stage idx -> (trap label, aligned y)
        0: "LEFT JOIN + WHERE on right-table col\nsilently becomes INNER — move it into ON",
        1: "NOT IN + NULL in subquery → zero rows\n(UNKNOWN); WHERE can't see SELECT aliases",
        2: "COUNT(col) skips NULLs — COUNT(*) counts rows\nNULL is its own group in GROUP BY",
        3: "windows run AFTER GROUP BY / HAVING —\nthe window sees groups, not raw rows",
        5: "aliases + window results visible only\nfrom ORDER BY on — never in WHERE",
    }
    els = [
        E.title(60, 40, "SQL Logical Execution Order — Where Each Trap Lives"),
        E.sub(60, 74, "Written top-down, executed in this order — SELECT aliases and window results do not exist until stage 4"),
        E.sect(340, 126, "Logical execution pipeline"),
        E.sect(820, 126, "Traps anchored to their stage"),
    ]
    y = 162
    centers = []
    for i, (name, note, sees) in enumerate(stages):
        stroke, fill = (BLUE2_S, BLUE2_F) if i == 3 else (BLUE_S, BLUE_F)
        els += [E.rect(340, y, 400, 62, stroke, fill, f"{name}\n{note}", lsize=13),
                E.text(60, y + 22, 260, 18, sees, 12, GRAY)]
        centers.append(y + 31)
        if i < 6:
            els.append(E.arrow(540, y + 62, [[0, 0], [0, 28]]))
        if i in traps:
            els += [E.rect(820, y, 380, 58, RED, WHITE, traps[i], dashed=True, lsize=12, lcolor=RED),
                    E.line(740, centers[-1], [[0, 0], [80, -2]])]
        y += 90
    els += [
        E.text(60, 790, 1000, 18, "Latest per key in one scan + one sort: ROW_NUMBER() OVER (PARTITION BY key ORDER BY ts DESC, id DESC) — keep rn = 1", 13, INK),
        E.text(60, 818, 800, 18, "QUALIFY collapses it in Snowflake/Databricks SQL; OSS Spark needs the subquery", 12, GRAY),
    ]
    d['elements'] += els
    exc.save(d, '/Users/harry/Desktop/system-design/diagrams/exc/sql-pipeline.excalidraw')


def s03():
    d = exc.new_doc(); E = exc.B()
    d['elements'] += [
        E.title(60, 40, "PySpark Runtime — Driver Plans the DAG, Executors Run Tasks"),
        E.sub(60, 74, "Nothing big crosses back to the driver; the shuffle and the JVM→CPython boundary are where jobs die"),
        # driver
        E.rect(60, 150, 320, 140, BLUE_S, "#3b82f6", "DRIVER — 1 JVM process\nbuilds lazy DAG · schedules tasks\nCatalyst: logical → physical plan\ntracks stage + task state", lsize=13, lcolor=WHITE),
        E.text(60, 300, 420, 40, "driver OOM: collect() · toPandas() · take(10**9)\nfull result set lands in driver RAM", 13, RED),
        # executors
        E.rect(460, 130, 700, 230, GRAY, "transparent", "", dashed=True),
        E.text(476, 137, 400, 18, "Executor cluster — partitions across JVMs", 13, GRAY),
        E.rect(490, 175, 190, 80, BLUE_S, BLUE_F, "Executor 1\ntasks on partitions\nshuffle · cache", lsize=13),
        E.rect(710, 175, 190, 80, BLUE_S, BLUE_F, "Executor 2\ntasks on partitions\nagg state · sorts", lsize=13),
        E.rect(930, 175, 190, 80, BLUE_S, BLUE_F, "Executor N\ntasks on partitions\nstraggler = skew", lsize=13),
        E.arrow(380, 190, [[0, 0], [80, 0]]),
        E.text(392, 162, 60, 18, "tasks", 12, GRAY),
        E.arrow(460, 240, [[0, 0], [-80, 0]], color=GRAY, dashed=True),
        E.text(392, 248, 60, 18, "status", 12, GRAY),
        E.text(460, 372, 640, 40, "executor OOM = data shape, not size:\nskew · repartition(1) before a heavy stage · cache() without MEMORY_AND_DISK", 13, RED),
        # shuffle
        E.arrow(810, 360, [[0, 0], [0, 70]]),
        E.text(826, 406, 160, 18, "shuffle write / read", 12, GRAY),
        E.rect(460, 430, 700, 70, ORANGE, ORANGE_F, "SHUFFLE — wide exchange by key (groupBy · join)\nstage boundary: hot key = one straggler task; skew lives here", lsize=13),
        # UDF ladder
        E.sect(60, 540, "UDF ladder — pay the serialization tax last"),
        E.rect(60, 575, 300, 84, GREEN_S, GREEN_F, "Native functions (F.sum, F.when)\ncolumnar Tungsten codegen — 1×", lsize=13),
        E.rect(400, 575, 300, 84, AMBER_S, AMBER_F, "pandas UDF (@pandas_udf)\nArrow-batch amortized — ~2–5×", lsize=13),
        E.rect(740, 575, 300, 84, RED, WHITE, "Python UDF (@udf) — last resort\nJVM → bytes → CPython, ~10×+", lsize=13),
        E.arrow(360, 617, [[0, 0], [40, 0]]),
        E.arrow(700, 617, [[0, 0], [40, 0]]),
        # skew story + summary
        E.text(60, 690, 1000, 40, "Skew in the wild: 1 B rows on 200 executors — 199 tasks in 2 min, one straggler 38 min, then executor OOM.\nFix: salt the hot key → two-stage agg (16 × 25 M partials), or AQE skewJoin; cache only if reused ≥2×, then unpersist()", 13, RED),
        E.text(60, 762, 1000, 18, "Diagnose before fixing: groupBy(key).count().orderBy(desc('count')) — or read the Spark UI, not vibes", 13, INK),
    ]
    exc.save(d, '/Users/harry/Desktop/system-design/diagrams/exc/spark-runtime.excalidraw')


def s04():
    d = exc.new_doc(); E = exc.B()
    d['elements'] += [
        E.title(60, 40, "Replication & Quorum — N, W, R and the Partition Fork"),
        E.sub(60, 74, "R + W > N forces read/write overlap so every read sees the newest write; W > N/2 blocks split-brain"),
        # replication group
        E.rect(60, 130, 480, 330, GRAY, "transparent", "", dashed=True),
        E.text(76, 137, 420, 18, "N = 5 replicas — 1 leader + 4 followers", 13, GRAY),
        E.rect(90, 185, 180, 110, BLUE_S, "#3b82f6", "LEADER\nacks when W=3\nreplicas hold it", lsize=13, lcolor=WHITE),
        E.rect(340, 165, 180, 50, BLUE_S, BLUE_F, "R1 · sync (in W)", lsize=12),
        E.rect(340, 227, 180, 50, BLUE_S, BLUE_F, "R2 · sync (in W)", lsize=12),
        E.rect(340, 289, 180, 50, BLUE_S, BLUE_F, "R3 · sync (in W)", lsize=12),
        E.rect(340, 351, 180, 50, GRAY, WHITE, "R4 · async (lag)", lsize=12),
        E.arrow(270, 215, [[0, 0], [70, -25]]),
        E.arrow(270, 240, [[0, 0], [70, 12]]),
        E.arrow(270, 265, [[0, 0], [70, 49]]),
        E.arrow(270, 290, [[0, 0], [70, 86]], color=GRAY, dashed=True),
        # quorum math
        E.sect(600, 126, "Quorum arithmetic — R + W > N"),
        E.rect(600, 162, 265, 110, BLUE_S, BLUE_F, "Write set W=3\n{R1, R2, R3}\nacked by 3 of 5 → commit", lsize=13),
        E.rect(895, 162, 265, 110, GREEN_S, GREEN_F, "Read set R=3\n{R1, R4, R5}\nany 3 include one fresh", lsize=13),
        E.text(600, 284, 560, 18, "sets overlap at R1 — the reader always sees the newest value", 13, INK),
        E.text(600, 314, 560, 22, "W + R > N  ·  W > N/2 → no two write quorums can form", 15, HDR),
        E.sect(600, 368, "Sizing on N = 5 (90% node uptime)"),
        E.rect(600, 403, 180, 96, BLUE_S, BLUE_F, "W=3 R=3 — balanced\n99.1% writes\n99.1% reads\ntolerates 2 failures", lsize=12),
        E.rect(795, 403, 180, 96, AMBER_S, AMBER_F, "W=1 R=5 — telemetry\n99.999% writes\n59.0% reads\nany node accepts", lsize=12),
        E.rect(990, 403, 180, 96, GRAY, WHITE, "W=5 R=1 — rare\n59.0% writes\n99.999% reads\n1 down blocks writes", lsize=12),
        # partition fork
        E.sect(60, 505, "Network partition → pick C or A"),
        E.ellipse(60, 540, 190, 60, ORANGE, ORANGE_F, "network\npartition", 13),
        E.arrow(250, 570, [[0, 0], [40, 0]]),
        E.rect(290, 528, 300, 86, BLUE_S, "#3b82f6", "CP — refuse to serve stale\nblock or reject rather than\nanswer with old data", lsize=13, lcolor=WHITE),
        E.rect(620, 528, 300, 86, GREEN_S, GREEN_F, "AP — keep answering\nmay serve stale data;\nreplicas converge later", lsize=13),
        E.rect(950, 528, 240, 86, GRAY, WHITE, "CP: ZooKeeper · etcd · HBase\nKafka minISR + unclean=false\nAP: Cassandra · Dynamo · DNS", lsize=12, lcolor=GRAY),
        E.arrow(250, 585, [[0, 0], [0, 57], [520, 57], [520, -28]], color=RED, dashed=True),
        E.text(400, 620, 70, 18, "pick one", 12, RED),
        E.text(60, 622, 300, 18, "no partition → CA is coherent", 12, GRAY),
        # split-brain
        E.sect(60, 668, "Split-brain & fencing"),
        E.rect(60, 703, 555, 92, AMBER_S, AMBER_F, "Split-brain: partition → two leaders both accept writes\nFence: W > N/2 — old leader can't reach a write quorum\nEpochs / fencing tokens: stale leader writes rejected", lsize=13),
        E.rect(655, 703, 535, 92, BLUE_S, BLUE_F, "Kafka is tunable per topic:\nacks=all + min.insync.replicas=2 ≈ write quorum over ISR\nunclean.leader.election.enable=false → CP · true → AP", lsize=13),
        E.text(60, 825, 1000, 18, "Retries guarantee duplicates — idempotency keys, dedup tables, MERGE upserts and transactional offsets make replays no-ops", 13, INK),
    ]
    exc.save(d, '/Users/harry/Desktop/system-design/diagrams/exc/quorum-replication.excalidraw')


if __name__ == "__main__":
    s01(); s02(); s03(); s04()
    print("saved 4 excalidraw files")
