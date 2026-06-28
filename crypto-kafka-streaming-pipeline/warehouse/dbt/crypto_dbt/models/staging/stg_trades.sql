{{ config(materialized='view', schema='stg') }}

with src as (
  select *
  from {{ source('ext', 'trades') }}
),

casted as (
  select
    pair,
    trade_date,
    hour,

    symbol,
    try_cast(trade_id as bigint) as trade_id,
    to_timestamp(try_cast(trade_ts as bigint) / 1000.0) as trade_ts_utc,
    try_cast(price as double) as price,
    try_cast(qty as double) as qty,
    try_cast(is_buyer_maker as boolean) as is_buyer_maker,

    -- Parse ISO string if possible; otherwise keep null instead of failing the model
    try_cast(ingested_at as timestamp) as ingested_at_utc,

    cast(event_id as varchar) as event_id,
    try_cast(schema_version as integer) as schema_version,
    cast(source as varchar) as source,

    -- handy unique key for testing/joins
    (cast(symbol as varchar) || ':' || cast(trade_id as varchar)) as trade_key
  from src
)

select * from casted