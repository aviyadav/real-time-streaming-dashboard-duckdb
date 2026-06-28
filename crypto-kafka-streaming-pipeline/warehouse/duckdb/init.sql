-- Create a schema for raw/external data
CREATE SCHEMA IF NOT EXISTS ext;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS marts;

-- External view over your Hive-partitioned parquet lake
-- Note: pair/trade_date/hour will be discovered from folder names (Hive partitions)
CREATE OR REPLACE VIEW ext.trades AS
SELECT *
FROM read_parquet('data/parquet/trades/**/*.parquet');

-- Optional: a convenience view selecting key columns
CREATE OR REPLACE VIEW ext.trades_core AS
SELECT
  pair,
  trade_date,
  hour,
  symbol,
  trade_id,
  trade_ts,
  price,
  qty,
  is_buyer_maker,
  ingested_at,
  event_id,
  schema_version,
  source
FROM ext.trades;