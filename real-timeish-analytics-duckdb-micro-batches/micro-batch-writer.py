import time, os
from datetime import datetime, timezone
import duckdb

INBOX = "inbox_events"
LAKE = "lake/events"
os.makedirs(LAKE, exist_ok=True)
os.makedirs(INBOX, exist_ok=True)

con = duckdb.connect("metrics.duckdb")
con.execute("""
CREATE TABLE IF NOT EXISTS ingest_checkpoint (
    file_name TEXT PRIMARY KEY,
    ingested_at TIMESTAMP default now()
);
""")

def list_new_files():
    files = sorted([f for f in os.listdir(INBOX) if f.endswith(".jsonl")])
    if not files:
        return []
    known = set(con.execute("SELECT file_name FROM ingest_checkpoint").fetchall())
    known = {x[0] for x in known}
    return [f for f in files if f not in known]

while True:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_files = list_new_files()
    if not new_files:
        print(f"[{now_str}] Polling... no new files in {INBOX}/")
        time.sleep(2)
        continue

    print(f"[{now_str}] Found {len(new_files)} new file(s): {new_files}")

    batch_start = time.time()
    rows_total = 0

    # Load and normalize
    for f in new_files:
        path = os.path.join(INBOX, f)

        # Write into minute partition
        minute = datetime.now(timezone.utc).strftime("%Y-%m-%d/%H/%M")
        out_dir = os.path.join(LAKE, f"dt={minute}")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f.replace(".jsonl", ".parquet"))

        print(f"  → Ingesting {f}  →  {out_path}")
        con.execute(f"""
        COPY (
          SELECT
            user_id::VARCHAR    AS user_id,
            event::VARCHAR      AS event,
            ts::TIMESTAMPTZ     AS ts,
            sku::VARCHAR        AS sku,
            price::DOUBLE       AS price
          FROM read_json_auto('{path}')
        ) TO '{out_path}' (FORMAT PARQUET);
        """)

        rows = con.execute(f"SELECT count(*) FROM read_parquet('{out_path}')").fetchone()[0]
        rows_total += rows
        print(f"     ✓ {rows:,} rows written")

        con.execute("INSERT INTO ingest_checkpoint(file_name) VALUES (?);", [f])

    elapsed = time.time() - batch_start
    done_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{done_str}] Batch done — {len(new_files)} file(s), {rows_total:,} rows in {elapsed:.2f}s. Sleeping 2s...\n")
    time.sleep(2)