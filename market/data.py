"""Complete daily watchlist snapshots in US market time."""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
import os

import exchange_calendars as xc
import numpy as np
import pandas as pd
import requests

SYMBOLS = ("NVDA", "MSFT", "AMD", "VOO")
FIELDS = ["open", "high", "low", "close", "volume"]
NY = ZoneInfo("America/New_York")
URL = "https://data.alpaca.markets/v2/stocks/bars"


def sessions(start: date, end: date):
    if start > end or end >= datetime.now(NY).date() or start < date(2016, 1, 1):
        raise ValueError("Choose a historical range from 2016 through yesterday, inclusive.")
    cal = xc.get_calendar("XNYS", start="2015-01-01", end=f"{end.year + 1}-12-31")
    result = cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))
    if result.empty:
        raise ValueError("Range contains no US equity sessions.")
    return result


def fetch(start, end, get=requests.get):
    expected = sessions(start, end)
    key, secret = (os.getenv(name) for name in ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY"))
    if not key or not secret:
        raise ValueError("Set both Alpaca paper market-data credentials in the environment.")
    params = dict(symbols=",".join(SYMBOLS), timeframe="1Day", adjustment="split",
                  feed="iex", limit=10000, sort="asc",
                  start=datetime.combine(start, time.min, NY).isoformat(),
                  end=datetime.combine(end, time(23, 59, 59), NY).isoformat())
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    rows, seen = [], set()
    while True:
        response = get(URL, params=params.copy(), headers=headers, timeout=30, allow_redirects=False)
        if response.status_code != 200:
            raise ValueError(f"Alpaca returned HTTP {response.status_code}. Check entitlement, rate limit or network.")
        body = response.json()
        for symbol, bars in body["bars"].items():
            for b in bars:
                ts = pd.Timestamp(b["t"])
                day = ts.tz_convert(NY).date().isoformat()
                rows.append((symbol, day, b["o"], b["h"], b["l"], b["c"], b["v"]))
        token = body.get("next_page_token")
        if not token:
            break
        if token in seen:
            raise ValueError("Repeated Alpaca page token.")
        seen.add(token)
        params["page_token"] = token
    return validate(pd.DataFrame(rows, columns=["symbol", "date", *FIELDS]), expected)


def validate(frame, expected):
    df = frame.copy()
    index = pd.MultiIndex.from_product([SYMBOLS, expected.strftime("%Y-%m-%d")],
                                       names=["symbol", "date"])
    df = df.set_index(["symbol", "date"]).sort_index()
    if not df.index.is_unique or not df.index.sort_values().equals(index.sort_values()):
        raise ValueError("Missing, duplicate or unexpected symbol/session. Snapshot rejected.")
    values = df[FIELDS].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(values).all().all():
        raise ValueError("Non-finite OHLCV.")
    prices = values[FIELDS[:4]]
    if (prices <= 0).any().any() or (prices.min(axis=1) != prices.low).any() or (prices.max(axis=1) != prices.high).any():
        raise ValueError("Inconsistent OHLC range.")
    v = values.volume
    if (v < 0).any() or (v % 1 != 0).any() or (v >= 2**63).any():
        raise ValueError("Invalid share volume.")
    values["volume"] = v.astype("int64")
    return values.reset_index()


def demo():
    days = sessions(date(2024, 1, 2), date(2024, 6, 28))
    parts = []
    for i, symbol in enumerate(SYMBOLS):
        rng = np.random.default_rng(117 + i)
        close = (70 + i * 18) * np.exp(rng.normal(.0005, .013, len(days)).cumsum())
        opening = close * np.exp(rng.normal(0, .006, len(days)))
        parts.append(pd.DataFrame(dict(symbol=symbol, date=days.strftime("%Y-%m-%d"),
            open=opening, high=np.maximum(opening, close)*1.007, low=np.minimum(opening, close)*.993,
            close=close, volume=rng.integers(10000, 300000, len(days)))))
    return validate(pd.concat(parts), days)
