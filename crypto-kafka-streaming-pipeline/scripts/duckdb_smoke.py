import duckdb
from pathlib import Path

DUCKDB_PATH = Path("data/duckdb/crypto.duckdb")
INIT_SQL_PATH = Path("warehouse/duckdb/init.sql")

DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DUCKDB_PATH))

# Initialize schemas + views
with open(INIT_SQL_PATH, "r", encoding="utf-8") as f:
    con.execute(f.read())

print("✅ DuckDB initialized:", DUCKDB_PATH)

try:
    result = con.execute("SELECT COUNT(*) FROM ext.trades").fetchone()[0]
    print("ext.trades row count =", result)

    if result > 0:
        df = con.execute("""
            SELECT pair, trade_date, hour, price, qty
            FROM ext.trades
            ORDER BY trade_ts DESC
            LIMIT 5
        """).fetchdf()
        print(df)

except Exception as e:
    print("⚠️ Query failed (likely no parquet yet):", e)

con.close()