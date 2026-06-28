import duckdb
from pathlib import Path

DB_PATH = Path("data/duckdb/crypto.duckdb")
INIT_SQL = Path("warehouse/duckdb/init.sql")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH))

print("Running init.sql against:", DB_PATH)
con.execute(INIT_SQL.read_text(encoding="utf-8"))

tables = con.execute("""
    SELECT table_schema, table_name, table_type
    FROM information_schema.tables
    WHERE table_schema = 'ext'
""").fetchall()

print("Objects in schema 'ext':")
for row in tables:
    print(row)

con.close()
print("✅ DuckDB initialized successfully")