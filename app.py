from pathlib import Path
import os

import pandas as pd
import streamlit as st

from market.data import SYMBOLS, demo
from market.indicators import indicators
from market.store import DEFAULT_DB, catalog, load

demo = st.cache_data(demo)
st.set_page_config(page_title="Market notebook", layout="wide")
st.title("Market notebook")
db = Path(os.getenv("MARKET_DB", str(DEFAULT_DB)))
mode = st.sidebar.radio("Data source", ["Synthetic demo", "Historical snapshots"])
symbol = st.sidebar.selectbox("Instrument", SYMBOLS)
if mode == "Synthetic demo":
    st.warning("Synthetic demo · All prices and volumes are generated examples.")
    raw = demo().query("symbol == @symbol").drop(columns="symbol").set_index("date")
    raw.index = pd.to_datetime(raw.index)
else:
    records = catalog(db)
    if not records:
        st.info("No historical snapshot yet. Run the import command in the README, then refresh.")
        st.stop()
    choice = st.sidebar.selectbox("Snapshot", records, format_func=lambda r:
        f"{r['start']} – {r['end']} · {r['id'][:8]}")
    raw = load(db, choice["id"], symbol)
    if raw.empty:
        st.error(f"Snapshot {choice['id'][:8]} has no bars for {symbol}. Select another snapshot or re-import.")
        st.stop()
    fetched = pd.Timestamp(choice["fetched"]).tz_convert("UTC")
    st.info(f"Historical snapshot · {choice['source']} · retrieved {fetched:%d %b %Y %H:%M} UTC")

full = indicators(raw)
window = st.sidebar.selectbox("Visible sessions", [30, 60, 120, "All"], index=1)
chart = full if window == "All" else full.tail(window)
last = full.iloc[-1]
st.header(symbol)
st.caption(f"Daily bars in USD · last session {full.index[-1]:%d %b %Y} · {len(chart)} sessions shown")

def display(value):
    return "Warming up" if pd.isna(value) else f"{value:,.2f}"

for col, label, field in zip(st.columns(3), ["Closing price · USD", "RSI · 14 sessions", "ATR · USD"], ["close", "RSI 14", "ATR 14"]):
    col.metric(label, display(last[field]))

st.subheader("Closing price and moving averages")
st.line_chart(chart[["close", "SMA 20", "EMA 20"]], color=["#183A45", "#CA7331", "#217C71"])
if pd.notna(last["SMA 20"]):
    relation = "above" if last.close > last["SMA 20"] else "below" if last.close < last["SMA 20"] else "equal to"
    st.caption(f"The last close is {relation} its 20-session mean of USD {last['SMA 20']:.2f}.")
momentum, risk, bars = st.tabs(["Momentum", "Range and volume", "Daily observations"])
with momentum:
    st.subheader("MACD and signal line")
    st.line_chart(chart[["MACD", "Signal 9"]])
    st.bar_chart(chart["Histogram"], color="#217C71")
    st.caption("MACD measures the distance between the 12- and 26-session EMAs. The histogram measures its distance from the signal line.")
    st.subheader("Relative strength index")
    st.line_chart(chart["RSI 14"])
with risk:
    st.subheader("Average true range · USD")
    st.line_chart(chart["ATR 14"])
    st.caption("ATR includes overnight gaps and measures the size of price moves in dollars.")
    st.subheader("Share volume")
    st.bar_chart(chart.volume, color="#217C71")
with bars:
    st.dataframe(chart.iloc[::-1], use_container_width=True)
    st.caption("Blank indicator cells are warm-up periods.")
