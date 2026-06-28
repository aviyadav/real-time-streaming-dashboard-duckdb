Write-Host "Stopping docker compose (if running)..." -ForegroundColor Yellow
docker compose -f docker\compose.yml down | Out-Null

Write-Host "Cleaning local data..." -ForegroundColor Yellow
if (Test-Path ".\data\parquet") { Remove-Item -Recurse -Force ".\data\parquet\*" }
if (Test-Path ".\data\duckdb\crypto.duckdb") { Remove-Item -Force ".\data\duckdb\crypto.duckdb" }

Write-Host "✅ Clean complete." -ForegroundColor Green