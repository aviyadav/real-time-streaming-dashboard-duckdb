$duckdbPath = ".\data\duckdb\crypto.duckdb"
$sqlFile = ".\warehouse\duckdb\init.sql"

New-Item -ItemType Directory -Force -Path ".\data\duckdb" | Out-Null

python -c @"
import duckdb, os
db = r'$duckdbPath'
sql = open(r'$sqlFile', 'r', encoding='utf-8').read()
con = duckdb.connect(db)
con.execute(sql)
print('✅ DuckDB initialized:', db)

# smoke query
try:
    rows = con.execute("SELECT COUNT(*) AS cnt FROM ext.trades").fetchone()[0]
    print('ext.trades count =', rows)
    if rows:
        print(con.execute("SELECT pair, trade_date, hour, price, qty FROM ext.trades ORDER BY trade_ts DESC LIMIT 5").fetchdf())
except Exception as e:
    print('⚠️ Query failed (likely no parquet yet):', e)

con.close()
"@