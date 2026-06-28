$ErrorActionPreference = "Stop"

# Always run from repo root (Task Scheduler starts in System32 by default)
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Skip if DuckDB file doesn't exist yet (e.g., after cleanup)
if (-not (Test-Path ".\data\duckdb\crypto.duckdb")) {
  Log "DuckDB file missing (data\duckdb\crypto.duckdb). Skipping run."
  exit 0
}

# Skip if there is no parquet data yet
$parquetCount = (Get-ChildItem -Recurse .\data\parquet\trades -Filter *.parquet -ErrorAction SilentlyContinue | Measure-Object).Count
if ($parquetCount -eq 0) {
  Log "No parquet files found under data\parquet\trades. Skipping run."
  exit 0
}


# Logs
$LogDir = ".\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("dbt_refresh_marts_" + (Get-Date -Format "yyyyMMdd") + ".log")

function Log($msg) {
  $line = ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg)
  $line | Tee-Object -FilePath $LogFile -Append | Out-Host
}

try {
  Log "Starting dbt_refresh_marts"

  # Ensure dbt points to the right DuckDB file
  $env:DUCKDB_PATH = (Resolve-Path .\data\duckdb\crypto.duckdb).Path
  Log "DUCKDB_PATH=$env:DUCKDB_PATH"

  # Ensure DuckDB ext views exist (safe to re-run)
  Log "Running init_duckdb.py"
  python .\scripts\init_duckdb.py 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Host

  # Run staging + marts
  Log "Running dbt models"
  dbt run --project-dir .\warehouse\dbt\crypto_dbt --profiles-dir .\warehouse\dbt --select stg_trades fct_trades_1m fct_candles_1m fct_orderflow_1m fct_ingestion_latency_1m  fct_pipeline_health_5m 2>&1 |
    Tee-Object -FilePath $LogFile -Append | Out-Host

  Log "✅ dbt_refresh_marts completed OK"
  exit 0
}
catch {
  Log ("dbt_refresh_marts failed: " + $_.Exception.Message)
  exit 1
}