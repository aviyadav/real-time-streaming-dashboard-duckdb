$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$LogDir = ".\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("dbt_tests_" + (Get-Date -Format "yyyyMMdd") + ".log")

function Log($msg) {
  $line = ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg)
  $line | Tee-Object -FilePath $LogFile -Append | Out-Host
}

try {
  Log "Starting dbt_nightly_tests"
  $env:DUCKDB_PATH = (Resolve-Path .\data\duckdb\crypto.duckdb).Path
  Log "DUCKDB_PATH=$env:DUCKDB_PATH"

  python .\scripts\init_duckdb.py 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Host

  dbt test --project-dir .\warehouse\dbt\crypto_dbt --profiles-dir .\warehouse\dbt --select stg_trades fct_trades_1m fct_candles_1m fct_orderflow_1m 2>&1 |
    Tee-Object -FilePath $LogFile -Append | Out-Host

  Log "dbt_nightly_tests completed OK"
  exit 0
}
catch {
  Log ("dbt_nightly_tests failed: " + $_.Exception.Message)
  exit 1
}