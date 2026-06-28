# Crypto Kafka Streaming Pipeline

## Overview

This project implements a real-time crypto trade streaming and analytics
platform using a modern data engineering architecture. It ingests live
BTCUSDT trade data from Binance, streams events through Kafka, persists
partitioned Parquet files, transforms data using dbt and DuckDB, and
visualizes analytics through a Streamlit dashboard.

The system demonstrates event-driven ingestion, lakehouse-style storage,
analytical modeling, orchestration, observability, and
production-oriented design principles.

------------------------------------------------------------------------
## What This Project Demonstrates

-   Event-driven streaming architecture
-   Kafka-based durable ingestion
-   Hive-partitioned lake design
-   Lakehouse-style analytics with DuckDB
-   dbt modeling best practices (staging + marts)
-   Data quality testing
-   Observability and latency tracking
-   Lightweight orchestration
-   Interactive analytics dashboard

------------------------------------------------------------------------
## Architecture

``` mermaid
flowchart TD
    A[Binance WebSocket<br>BTCUSDT Trades] --> B[Python Producer]
    B --> C[Kafka Broker<br>KRaft Mode]
    C --> D[Python Consumer]
    D --> E[Partitioned Parquet Lake<br>pair/date/hour]
    E --> F[DuckDB External Views]
    F --> G[dbt Staging Models]
    G --> H[dbt Mart Models]
    H --> I[Streamlit Dashboard]
    H --> J[Pipeline Observability Tables]
```

------------------------------------------------------------------------

## Technology Stack

-   Python 3.11
-   Binance WebSocket API
-   Apache Kafka (Confluent 7.6.0, KRaft mode)
-   Confluent Kafka Python Client
-   Polars (Parquet writing)
-   DuckDB (Analytical engine)
-   dbt-core with dbt-duckdb
-   Streamlit + Plotly (Dashboard)
-   Windows Task Scheduler (Orchestration)
-   Docker Desktop

------------------------------------------------------------------------

## CI/CD Strategy

Although this project runs locally, it is structured to support CI/CD
workflows.

A production-ready CI/CD implementation would include:

-   Linting and formatting (Black, Ruff)\
-   Unit tests for producer and consumer components\
-   Automated dbt run and dbt test validation in CI\
-   Docker image build validation\
-   Environment-based configuration management

------------------------------------------------------------------------
## Data Flow

1.  Binance trade stream (`btcusdt@trade`) provides real-time trade
    events.
2.  Producer publishes events to Kafka topic `crypto.trades.v1`.
3.  Consumer reads from Kafka and writes partitioned Parquet files:
    -   `pair=BTCUSDT`
    -   `trade_date=YYYY-MM-DD`
    -   `hour=HH`
4.  DuckDB creates external views over Parquet files.
5.  dbt builds:
    -   `stg_trades` (cleaned staging layer)
    -   `fct_trades_1m` (1-minute aggregation)
    -   `fct_candles_1m` (OHLCV + VWAP)
    -   `fct_orderflow_1m` (buy/sell imbalance)
    -   `fct_ingestion_latency_1m` (latency metrics)
    -   `fct_pipeline_health_5m` (pipeline status metrics)
6.  Streamlit reads marts directly from DuckDB for visualization.
7.  Task Scheduler refreshes dbt models periodically.

------------------------------------------------------------------------

## Mart Models

### 1. fct_trades_1m

Aggregated trade statistics per minute.

### 2. fct_candles_1m

OHLCV candles with VWAP.

### 3. fct_orderflow_1m

Buy/sell imbalance metrics and volume ratios.

### 4. fct_ingestion_latency_1m

Per-minute ingestion latency percentiles.

### 5. fct_pipeline_health_5m

Recent trade counts and freshness metrics.

------------------------------------------------------------------------

## Observability

The system includes:

-   Ingestion latency (p95, p99)
-   Trade counts over rolling windows
-   Time since last trade
-   Time since last ingest
-   DLQ handling for invalid events

------------------------------------------------------------------------

## Orchestration

Windows Task Scheduler runs:

-   `dbt_refresh_marts.ps1` every 5 minutes (bounded execution window)
-   Optional nightly dbt test validation

Scripts are resilient and skip execution if no Parquet or DuckDB files
are present.

------------------------------------------------------------------------

## Production Deployment Considerations

For a production deployment, the following adaptations would be
recommended:

-   Replace local Parquet storage with object storage (S3, Azure Blob
    Storage, GCS)\
-   Run Kafka in a multi-broker cluster configuration\
-   Containerize producer and consumer services\
-   Use Airflow or a managed orchestration platform\
-   Implement secret management\
-   Enable centralized logging and monitoring

------------------------------------------------------------------------

## Future Enhancements

Potential enhancements include:

-   Multi-symbol streaming support\
-   Incremental dbt models for large-scale processing\
-   Real-time alerting based on latency thresholds\
-   Automated schema evolution handling\
-   Data retention and compaction strategies\
-   Containerized deployment of the Streamlit dashboard

------------------------------------------------------------------------

## Running the Project Locally

### Start Kafka

``` powershell
docker compose -f docker/compose.yml up -d
```

### Start Producer

``` powershell
python src/crypto_pipeline/producer/main.py
```

### Start Consumer

``` powershell
python src/crypto_pipeline/consumer/main.py
```

### Initialize DuckDB

``` powershell
python scripts/init_duckdb.py
```

### Build dbt Models

``` powershell
dbt run --project-dir warehouse/dbt/crypto_dbt --profiles-dir warehouse/dbt
```

### Launch Dashboard

``` powershell
streamlit run dashboard/app.py
```

------------------------------------------------------------------------

## Repository Structure

    crypto-kafka-streaming-pipeline/
    │
    ├── docker/
    ├── src/
    ├── data/
    │   ├── parquet/
    │   └── duckdb/
    ├── warehouse/
    │   └── dbt/
    ├── scripts/
    ├── dashboard/
    └── README.md

------------------------------------------------------------------------

## License

This project is intended for educational and portfolio demonstration
purposes.

## Author
Virendra Pratap Singh
Senior Data Architect | Data Engineering | Analytics Platforms
https://www.linkedin.com/in/virendra-pratap-singh-iitg/