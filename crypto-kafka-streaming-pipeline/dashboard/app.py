from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DB_PATH = Path("data/duckdb/crypto.duckdb")

# dbt-duckdb commonly creates schemas like main_marts, main_stg
MARTS_SCHEMA = "main_marts"


@st.cache_data(ttl=15)
def query_df(sql: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()


def table_exists(schema: str, table: str) -> bool:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        q = f"""
        select count(*) as cnt
        from information_schema.tables
        where table_schema = '{schema}' and table_name = '{table}'
        """
        return con.execute(q).fetchone()[0] > 0
    finally:
        con.close()


st.set_page_config(page_title="Crypto Streaming Dashboard", layout="wide")

st.title("Crypto Kafka Streaming Pipeline — Dashboard")

if not DB_PATH.exists():
    st.error("DuckDB file not found. Run `python scripts/init_duckdb.py` and then `dbt run` to build marts.")
    st.stop()

required = ["fct_candles_1m", "fct_orderflow_1m", "fct_trades_1m"]
missing = [t for t in required if not table_exists(MARTS_SCHEMA, t)]
if missing:
    st.error(
        f"Missing marts in schema `{MARTS_SCHEMA}`: {', '.join(missing)}.\n\n"
        "Run dbt to create them:\n"
        "`dbt run --project-dir warehouse/dbt/crypto_dbt --profiles-dir warehouse/dbt`"
    )
    st.stop()

# Sidebar controls
st.sidebar.header("Controls")

# Pair list from candles table
pairs_df = query_df(f"select distinct pair from {MARTS_SCHEMA}.fct_candles_1m order by pair")
pairs = pairs_df["pair"].tolist() if not pairs_df.empty else ["BTCUSDT"]
pair = st.sidebar.selectbox("Pair", pairs, index=0)

lookback_minutes = st.sidebar.selectbox("Lookback window", [30, 60, 180, 360, 720, 1440], index=2)
end_ts = datetime.now(timezone.utc)
start_ts = end_ts - timedelta(minutes=int(lookback_minutes))

st.sidebar.caption(f"Time window (UTC): {start_ts.strftime('%Y-%m-%d %H:%M')} → {end_ts.strftime('%H:%M')}")

# Pipeline health (if exists)
st.subheader("Pipeline Health")

if table_exists(MARTS_SCHEMA, "fct_pipeline_health_5m"):
    health = query_df(f"select * from {MARTS_SCHEMA}.fct_pipeline_health_5m order by pair")
    st.dataframe(health, width='stretch')
else:
    st.info("`fct_pipeline_health_5m` not found (optional).")

col1, col2 = st.columns([2, 1])

# Candles
candles_sql = f"""
select *
from {MARTS_SCHEMA}.fct_candles_1m
where pair = '{pair}'
  and minute_bucket >= TIMESTAMP '{start_ts.strftime("%Y-%m-%d %H:%M:%S")}'
order by minute_bucket
"""
candles = query_df(candles_sql)

with col1:
    st.subheader("Candles (1m): OHLC + VWAP")

    if candles.empty:
        st.warning("No candle data found in the selected window. Let the pipeline run a bit and refresh.")
    else:
        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=candles["minute_bucket"],
                open=candles["open_price"],
                high=candles["high_price"],
                low=candles["low_price"],
                close=candles["close_price"],
                name="OHLC",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=candles["minute_bucket"],
                y=candles["vwap"],
                mode="lines",
                name="VWAP",
            )
        )

        fig.update_layout(
            height=520,
            xaxis_title="Minute (UTC)",
            yaxis_title="Price (USDT)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        st.plotly_chart(fig, width='stretch')

with col2:
    st.subheader("Latest candle stats")
    if not candles.empty:
        latest = candles.iloc[-1]
        st.metric("Trade count (1m)", int(latest["trade_count"]))
        st.metric("Total qty (1m)", float(latest["total_qty"]))
        st.metric("Notional USDT (1m)", float(latest["notional_usdt"]))
        st.metric("VWAP", float(latest["vwap"]))
    else:
        st.info("No data in window.")

# Order flow
st.subheader("Order Flow (1m): Buy/Sell Imbalance")

orderflow_sql = f"""
select *
from {MARTS_SCHEMA}.fct_orderflow_1m
where pair = '{pair}'
  and minute_bucket >= TIMESTAMP '{start_ts.strftime("%Y-%m-%d %H:%M:%S")}'
order by minute_bucket
"""
of = query_df(orderflow_sql)

if of.empty:
    st.warning("No orderflow data found in the selected window.")
else:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=of["minute_bucket"], y=of["qty_imbalance"], name="Qty imbalance"))
    fig2.add_trace(go.Scatter(x=of["minute_bucket"], y=of["buy_qty_ratio"], mode="lines", name="Buy qty ratio"))
    fig2.update_layout(height=360, xaxis_title="Minute (UTC)", legend=dict(orientation="h"))
    st.plotly_chart(fig2, width='stretch')

# Raw 1m aggregation
st.subheader("Trades Summary (1m)")

trades_sql = f"""
select *
from {MARTS_SCHEMA}.fct_trades_1m
where pair = '{pair}'
  and minute_bucket >= TIMESTAMP '{start_ts.strftime("%Y-%m-%d %H:%M:%S")}'
order by minute_bucket desc
limit 200
"""
trades = query_df(trades_sql)
st.dataframe(trades, width='stretch')

st.caption("Tip: Keep producer/consumer running and refresh the page to see new minutes appear.")