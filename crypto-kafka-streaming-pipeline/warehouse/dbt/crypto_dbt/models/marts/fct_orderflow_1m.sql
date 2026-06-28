{{ config(materialized='table', schema='marts') }}

with base as (
  select
    pair,
    date_trunc('minute', trade_ts_utc) as minute_bucket,
    price,
    qty,
    is_buyer_maker
  from {{ ref('stg_trades') }}
  where trade_ts_utc is not null
),

calc as (
  select
    pair,
    minute_bucket,

    count(*) as trade_count,
    sum(qty) as total_qty,
    sum(price * qty) as notional_usdt,

    -- buyer-initiated (buyer is NOT maker)
    sum(case when is_buyer_maker = false then qty else 0 end) as buy_qty,
    sum(case when is_buyer_maker = false then price * qty else 0 end) as buy_notional_usdt,

    -- seller-initiated (buyer IS maker)
    sum(case when is_buyer_maker = true then qty else 0 end) as sell_qty,
    sum(case when is_buyer_maker = true then price * qty else 0 end) as sell_notional_usdt
  from base
  group by 1, 2
)

select
  pair,
  minute_bucket,
  trade_count,
  total_qty,
  notional_usdt,

  buy_qty,
  sell_qty,
  buy_notional_usdt,
  sell_notional_usdt,

  -- imbalance metrics (handy demo fields)
  (buy_qty - sell_qty) as qty_imbalance,
  (buy_notional_usdt - sell_notional_usdt) as notional_imbalance,

  -- ratios (null-safe)
  buy_qty / nullif(total_qty, 0) as buy_qty_ratio,
  sell_qty / nullif(total_qty, 0) as sell_qty_ratio,
  buy_notional_usdt / nullif(notional_usdt, 0) as buy_notional_ratio,
  sell_notional_usdt / nullif(notional_usdt, 0) as sell_notional_ratio
from calc