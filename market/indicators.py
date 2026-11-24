"""Trailing indicators on one symbol in ascending session order."""
import pandas as pd


def smooth(series, period, alpha):
    """Recursive mean initialized with the first complete arithmetic mean."""
    valid = series.dropna()
    result = pd.Series(float("nan"), index=series.index)
    if len(valid) >= period:
        seeded = valid.iloc[period - 1:].copy()
        seeded.iloc[0] = valid.iloc[:period].mean()
        result.loc[seeded.index] = seeded.ewm(alpha=alpha, adjust=False).mean()
    return result


def indicators(bars):
    if not bars.index.is_monotonic_increasing or not bars.index.is_unique:
        raise ValueError("Expected unique ascending sessions for one symbol.")
    out = bars.copy()
    close = bars.close
    out["SMA 20"] = close.rolling(20).mean()
    out["EMA 20"] = smooth(close, 20, 2/21)
    out["MACD"] = smooth(close, 12, 2/13) - smooth(close, 26, 2/27)
    out["Signal 9"] = smooth(out.MACD, 9, 2/10)
    out["Histogram"] = out.MACD - out["Signal 9"]
    delta = close.diff()
    gain = smooth(delta.clip(lower=0), 14, 1/14)
    loss = smooth(-delta.clip(upper=0), 14, 1/14)
    out["RSI 14"] = (100 * gain / (gain + loss)).mask((gain + loss) == 0, 50)
    prev = close.shift(1)
    tr = pd.concat([bars.high - bars.low, (bars.high - prev).abs(), (bars.low - prev).abs()], axis=1).max(axis=1)
    out["ATR 14"] = smooth(tr, 14, 1/14)
    return out
