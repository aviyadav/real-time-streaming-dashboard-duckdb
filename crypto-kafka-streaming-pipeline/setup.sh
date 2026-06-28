#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────
# Crypto Kafka Streaming Pipeline — Linux/macOS setup
# Uses uv (https://docs.astral.sh/uv) when available;
# falls back to standard venv + pip otherwise.
# ──────────────────────────────────────────────────

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${CYAN}${BOLD}=== Crypto Kafka Streaming Pipeline — Setup ===${RESET}"

# ── 1. Detect or create virtual environment ──────────────────
USE_UV=false
if command -v uv &>/dev/null; then
    USE_UV=true
    echo -e "${GREEN}✓ uv detected — using fast resolver${RESET}"
else
    echo -e "${YELLOW}⚠ uv not found — falling back to venv + pip${RESET}"
    echo -e "${YELLOW}  (install uv for faster setup: curl -LsSf https://astral.sh/uv/install.sh | sh)${RESET}"
fi

if $USE_UV; then
    # ── uv path ──────────────────────────────────────────────
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating virtual environment with uv...${RESET}"
        uv venv .venv --python 3.11
    else
        echo -e "${GREEN}✓ .venv already exists${RESET}"
    fi

    echo -e "${YELLOW}Installing dependencies with uv...${RESET}"
    uv pip install -r requirements.txt --python .venv/bin/python

    # Install the crypto_pipeline package in editable mode
    echo -e "${YELLOW}Installing crypto_pipeline package (editable)...${RESET}"
    uv pip install -e . --python .venv/bin/python

    # Apply mashumaro compatibility patch required by dbt-core 1.8.x
    echo -e "${YELLOW}Applying mashumaro patch for dbt compatibility...${RESET}"
    .venv/bin/python scripts/fix_dbt.py

else
    # ── standard venv + pip fallback ─────────────────────────
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${RESET}"
        python3 -m venv venv
    else
        echo -e "${GREEN}✓ venv already exists${RESET}"
    fi

    echo -e "${YELLOW}Activating and upgrading pip...${RESET}"
    source venv/bin/activate
    python -m pip install --upgrade pip

    echo -e "${YELLOW}Installing dependencies from requirements.txt...${RESET}"
    pip install -r requirements.txt

    echo -e "${YELLOW}Installing crypto_pipeline package (editable)...${RESET}"
    pip install -e .

    # Apply mashumaro compatibility patch required by dbt-core 1.8.x
    echo -e "${YELLOW}Applying mashumaro patch for dbt compatibility...${RESET}"
    python scripts/fix_dbt.py
fi

# ── 2. Create .env from example ──────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env created from .env.example${RESET}"
else
    echo -e "${GREEN}✓ .env already exists${RESET}"
fi

# ── 3. Create data directories ───────────────────────────────
echo -e "${YELLOW}Creating data directories...${RESET}"
mkdir -p data/parquet data/duckdb
echo -e "${GREEN}✓ data/parquet/  data/duckdb/${RESET}"

# ── 4. Done ──────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}=== Setup complete! ===${RESET}"
echo ""
echo -e "${BOLD}Next steps:${RESET}"
echo ""
echo -e "  ${BOLD}1. Start Kafka${RESET}"
echo "     docker compose -f docker/compose.yml up -d"
echo ""
if $USE_UV; then
    echo -e "  ${BOLD}2. Activate venv${RESET}"
    echo "     source .venv/bin/activate"
else
    echo -e "  ${BOLD}2. Activate venv${RESET}"
    echo "     source venv/bin/activate"
fi
echo ""
echo -e "  ${BOLD}3. Set DUCKDB_PATH${RESET}"
echo "     export DUCKDB_PATH=\"\$(pwd)/data/duckdb/crypto.duckdb\""
echo ""
echo -e "  ${BOLD}4. Start Producer${RESET}"
echo "     python src/crypto_pipeline/producer/main.py"
echo ""
echo -e "  ${BOLD}5. Start Consumer${RESET} (separate terminal)"
echo "     python src/crypto_pipeline/consumer/main.py"
echo ""
echo -e "  ${BOLD}6. Initialize DuckDB${RESET}"
echo "     python scripts/init_duckdb.py"
echo ""
echo -e "  ${BOLD}7. Build dbt models${RESET}"
echo "     dbt run --project-dir warehouse/dbt/crypto_dbt --profiles-dir warehouse/dbt"
echo ""
echo -e "  ${BOLD}8. Launch Dashboard${RESET}"
echo "     streamlit run dashboard/app.py"
echo ""
