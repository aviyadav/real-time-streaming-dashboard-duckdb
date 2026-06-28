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
    trade_ts_utc,
    price,
    qty
  from base
),

agg as (
  select
    pair,
    minute_bucket,

    count(*) as trade_count,
    sum(qty) as total_qty,
    sum(price * qty) as notional_usdt,
    sum(price * qty) / nullif(sum(qty), 0) as vwap,

    min(price) as low_price,
    max(price) as high_price
  from bucketed
  group by 1, 2
),

open_close as (
  -- DuckDB supports arg_min/arg_max: return price at earliest/latest timestamp in bucket
  select
    pair,
    minute_bucket,
    arg_min(price, trade_ts_utc) as open_price,
    arg_max(price, trade_ts_utc) as close_price
  from bucketed
  group by 1, 2
)

select
  a.pair,
  a.minute_bucket,
  o.open_price,
  a.high_price,
  a.low_price,
  o.close_price,
  a.vwap,
  a.trade_count,
  a.total_qty,
  a.notional_usdt
from agg a
join open_close o
  using (pair, minute_bucket)