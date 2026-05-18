# Real-timeish Analytics with DuckDB + Micro-batches

A lightweight, Kafka-free near-real-time analytics pipeline for e-commerce event streams. Built to answer:

- **Orders per minute** — rolling count of `checkout` events
- **Revenue in the last 15 minutes** — sum of `price` on checkout events
- **Top SKUs right now** — ranked by checkout volume in a sliding window

Updated every 10 seconds. Zero Kafka. Zero Flink. Just files, DuckDB, and a couple of Python scripts.

---

## Architecture

```
event_generator.py          micro-batch-writer.py           DuckDB rollups
─────────────────           ─────────────────────           ──────────────
Emits JSONL events    →     Reads inbox_events/       →     recompute_window_pattern.sql
to inbox_events/            Writes Parquet to               rolls up last 5 min
every 10 seconds            lake/events/dt=YYYY-MM-DD/      every 10 seconds
                            HH/MM/ every 2 seconds
                                                            query_lake.sql
                                                            serves last 15 min
                                                            for the API layer
```

### Key Design Choices

| Concern | Choice | Why |
|---|---|---|
| Transport | Local folder / object storage | No broker to operate |
| Ingest format | JSONL → Parquet | Columnar, efficient for aggregation |
| Partitioning | `dt=YYYY-MM-DD/HH/MM/` | Prunes old partitions cheaply |
| State tracking | DuckDB `ingest_checkpoint` table | Idempotent re-runs, no duplicate ingestion |
| Rollup window | Last 5 minutes, recomputed from Parquet | Idempotent, no streaming state |
| Query latency | ~2 s end-to-end | Enough for a commerce dashboard |

---

## Project Structure

```
.
├── event_generator.py            # Simulates the app: emits JSONL events to inbox_events/
├── micro-batch-writer.py         # Polls inbox_events/, converts JSONL → Parquet in lake/
├── recompute_window_pattern.sql  # Recomputes last-5-min rollups into rollup_minute table
├── query_lake.sql                # Ad-hoc query: last-15-min event counts from raw Parquet
├── metrics.duckdb                # Persistent DuckDB file (checkpoint + rollup tables)
├── inbox_events/                 # Landing zone — JSONL files dropped here by the generator
└── lake/
    └── events/
        └── dt=YYYY-MM-DD/HH/MM/ # Minute-partitioned Parquet files
```

---

## Scripts

### `event_generator.py`

Simulates an e-commerce application emitting events. Every 10 seconds it generates 50–500
random events and writes them as a `.jsonl` file into `inbox_events/`.

**Event schema:**

| Field | Type | Description |
|---|---|---|
| `user_id` | UUID string | Anonymous session identifier |
| `event` | string | `page_view` (70%), `add_to_cart` (20%), `checkout` (10%) |
| `ts` | ISO 8601 with timezone | Event timestamp |
| `sku` | string | Product SKU (`SKU-001` … `SKU-020`) |
| `price` | float | Revenue amount — non-zero only for `checkout` events |

```bash
python event_generator.py
```

---

### `micro-batch-writer.py`

Polls `inbox_events/` every 2 seconds. For each new `.jsonl` file it:

1. Reads it with DuckDB's `read_json_auto()`
2. Casts all fields (including timezone-aware `ts::TIMESTAMPTZ`)
3. Writes a Parquet file to the correct minute partition under `lake/events/`
4. Records the filename in `ingest_checkpoint` to avoid reprocessing

Console output per micro-batch:

```
[2026-05-19T03:30:00Z] Found 2 new file(s): ['events_20260519_033000.jsonl', ...]
  → Ingesting events_20260519_033000.jsonl  →  lake/events/dt=2026-05-19/03/30/events_20260519_033000.parquet
     ✓ 312 rows written
  → Ingesting events_20260519_033010.jsonl  →  lake/events/dt=2026-05-19/03/30/events_20260519_033010.parquet
     ✓ 178 rows written
[2026-05-19T03:30:01Z] Batch done — 2 file(s), 490 rows in 0.43s. Sleeping 2s...
```

```bash
python micro-batch-writer.py
```

---

### `recompute_window_pattern.sql`

Recomputes the last 5 minutes of rollups into the `rollup_minute` table. Designed to be run
on a schedule (e.g., every 10 seconds via a cron job or a loop):

```sql
-- Idempotent: deletes and re-inserts the last 5 minutes
DELETE FROM rollup_minute WHERE minute >= date_trunc('minute', now() - INTERVAL 5 MINUTE);

INSERT INTO rollup_minute
SELECT date_trunc('minute', ts) AS minute, event, count(*) AS cnt
FROM read_parquet('lake/events/**/*.parquet')
WHERE ts >= now() - INTERVAL 5 MINUTE
GROUP BY 1, 2;
```

---

### `query_lake.sql`

Ad-hoc query to get the last 15 minutes of event counts directly from Parquet — useful for
revenue calculations and top-SKU analysis without needing the rollup table:

```sql
SELECT date_trunc('minute', ts) AS minute, event, count(*) AS cnt
FROM read_parquet('lake/events/**/*.parquet')
WHERE ts >= now() - INTERVAL 15 MINUTE
GROUP BY 1, 2
ORDER BY 1, 2;
```

---

## Quickstart

### 1. Install dependencies

```bash
# Using uv (recommended)
uv sync

# Or pip
pip install duckdb>=1.5.2
```

### 2. Start the event generator

```bash
# In terminal 1
python event_generator.py
```

### 3. Start the micro-batch writer

```bash
# In terminal 2
python micro-batch-writer.py
```

### 4. Query the lake

```bash
# Ad-hoc: last 15 minutes of events
duckdb metrics.duckdb < query_lake.sql

# Or interactively
duckdb metrics.duckdb
SELECT event, sum(price) AS revenue
FROM read_parquet('lake/events/**/*.parquet')
WHERE ts >= now() - INTERVAL 15 MINUTE
  AND event = 'checkout'
GROUP BY 1;
```

---

## Why Not Kafka + Flink?

| | Kafka + Flink | This stack |
|---|---|---|
| Infra to operate | Kafka cluster, Flink cluster, ZooKeeper | Zero — just a folder |
| Latency | Sub-second | 2–10 seconds |
| Cost | $$$  | $ (object storage) |
| Complexity | High | One Python file per concern |
| Good enough for | Millions of events/sec | Thousands of events/sec |

For a small commerce team that needs answers updated every 10 seconds, a micro-batch approach
over object storage (or a local folder) is dramatically simpler to build, deploy, and debug.

---

## Python Version

Requires Python ≥ 3.13 (see `.python-version`).
