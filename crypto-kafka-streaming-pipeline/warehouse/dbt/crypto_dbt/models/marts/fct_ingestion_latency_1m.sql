{{ config(materialized='table', schema='marts') }}

with base as (
  select
    pair,
    date_trunc('minute', trade_ts_utc) as minute_bucket,
    trade_ts_utc,
    ingested_at_utc
  from {{ ref('stg_trades') }}
  where trade_ts_utc is not null
    and ingested_at_utc is not null
),

calc as (
  select
    pair,
    minute_bucket,
    datediff('second', trade_ts_utc, ingested_at_utc) as latency_seconds
  from base
)

select
  pair,
  minute_bucket,
  count(*) as trade_count,
  avg(latency_seconds) as avg_latency_s,
  min(latency_seconds) as min_latency_s,
  max(latency_seconds) as max_latency_s,
  approx_quantile(latency_seconds, 0.95) as p95_latency_s,
  approx_quantile(latency_seconds, 0.99) as p99_latency_s
from calc
group by 1, 2