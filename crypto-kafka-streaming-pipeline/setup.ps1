# Setup virtual environment and install dependencies
# Run from project root: .\setup.ps1
# Requires: uv (https://docs.astral.sh/uv) — install with:
#   winget install astral-sh.uv
#   or: powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"

$ErrorActionPreference = "Stop"

Write-Host "=== Crypto Kafka Streaming Pipeline - Setup ===" -ForegroundColor Cyan

# 1. Check for uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: uv is not installed. Install it first:" -ForegroundColor Red
    Write-Host "  winget install astral-sh.uv" -ForegroundColor Yellow
    Write-Host "  or: powershell -ExecutionPolicy Bypass -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Yellow
    exit 1
}
Write-Host "uv detected." -ForegroundColor Green

# 2. Create virtual environment with Python 3.11
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment with Python 3.11 via uv..." -ForegroundColor Yellow
    uv venv .venv --python 3.11
} else {
    Write-Host ".venv already exists." -ForegroundColor Green
}

# 3. Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
uv pip install -r requirements.txt --python .venv\Scripts\python.exe

# 4. Install the crypto_pipeline package in editable mode
Write-Host "Installing crypto_pipeline package (editable)..." -ForegroundColor Yellow
uv pip install -e . --python .venv\Scripts\python.exe

# 5. Apply mashumaro compatibility patch required by dbt-core 1.8.x
Write-Host "Applying mashumaro patch for dbt compatibility..." -ForegroundColor Yellow
.venv\Scripts\python.exe scripts\fix_dbt.py

# 6. Create .env if not exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env created from .env.example" -ForegroundColor Green
} else {
    Write-Host ".env already exists." -ForegroundColor Green
}

# 7. Create data directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\parquet" | Out-Null
New-Item -ItemType Directory -Force -Path "data\duckdb" | Out-Null

Write-Host "=== Setup complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Start Kafka:        docker compose -f docker/compose.yml up -d"
Write-Host "  2. Activate venv:      . .\.venv\Scripts\Activate.ps1"
Write-Host "  3. Set DUCKDB_PATH:    `$env:DUCKDB_PATH = (Resolve-Path 'data\duckdb\crypto.duckdb').Path"
Write-Host "  4. Start Producer:     python src/crypto_pipeline/producer/main.py"
Write-Host "  5. Start Consumer:     python src/crypto_pipeline/consumer/main.py  (new terminal)"
Write-Host "  6. Init DuckDB:        python scripts/init_duckdb.py"
Write-Host "  7. Build dbt models:   dbt run --project-dir warehouse/dbt/crypto_dbt --profiles-dir warehouse/dbt"
Write-Host "  8. Launch Dashboard:   streamlit run dashboard/app.py"
