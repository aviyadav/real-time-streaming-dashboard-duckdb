{{ config(materialized='table', schema='marts') }}

with base as (
  select
    pair,
    trade_ts_utc,
    ingested_at_utc
  from {{ ref('stg_trades') }}
  where trade_ts_utc is not null
),

windowed as (
  select
    pair,
    count(*) filter (where trade_ts_utc >= now() - interval 5 minute) as trades_last_5m,
    max(trade_ts_utc) as max_trade_ts_utc,
    max(ingested_at_utc) as max_ingested_at_utc
  from base
  group by 1
)

select
  pair,
  trades_last_5m,
  max_trade_ts_utc,
  max_ingested_at_utc,
  datediff('second', max_trade_ts_utc, now()) as seconds_since_last_trade,
  datediff('second', max_ingested_at_utc, now()) as seconds_since_last_ingest
from windowed