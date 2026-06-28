# Ensure dbt always points to the correct DuckDB file
$env:DUCKDB_PATH = (Resolve-Path .\data\duckdb\crypto.duckdb).Path

# Initialize DuckDB schemas/views (ext.trades)
python .\scripts\init_duckdb.py

# Run dbt
dbt debug --project-dir .\warehouse\dbt\crypto_dbt --profiles-dir .\warehouse\dbt
dbt run   --project-dir .\warehouse\dbt\crypto_dbt --profiles-dir .\warehouse\dbt
dbt test  --project-dir .\warehouse\dbt\crypto_dbt --profiles-dir .\warehouse\dbt