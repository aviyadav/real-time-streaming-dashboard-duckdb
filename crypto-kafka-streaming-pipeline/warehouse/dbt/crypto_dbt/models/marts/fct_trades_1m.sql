{{ config(materialized='table', schema='marts') }}

with base as (
  select
    pair,
    trade_ts_utc,
    price,
    qty
  from {{ ref('stg_trades') }}
  where trade_ts_utc is not null
),

bucketed as (
  select
    pair,
    date_trunc('minute', trade_ts_utc) as minute_bucket,
    price,
    qty
  from base
)

select
  pair,
  minute_bucket,
  count(*) as trade_count,
  sum(qty) as total_qty,
  sum(price * qty) as notional_usdt,
  avg(price) as avg_price,
  min(price) as min_price,
  max(price) as max_price
from bucketed
group by 1, 2