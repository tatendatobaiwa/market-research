import numpy as np
import pandas as pd
import pytest
from market.indicators import indicators


def bars(prices):
    close = pd.Series(prices, dtype=float)
    return pd.DataFrame(dict(close=close, high=close+1, low=close-1))


def test_linear_prices():
    out = indicators(bars(range(1, 51)))
    assert out["SMA 20"].first_valid_index() == 19
    assert out["EMA 20"].first_valid_index() == 19
    assert out["MACD"].first_valid_index() == 25
    assert out["Signal 9"].first_valid_index() == 33
    assert out["RSI 14"].first_valid_index() == 14
    assert out["ATR 14"].first_valid_index() == 13
    assert out.iloc[-1][["SMA 20","EMA 20","MACD","Signal 9","Histogram","RSI 14","ATR 14"]].tolist() == pytest.approx([40.5,40.5,7,7,0,100,2])


def test_step_response():
    out = indicators(bars([20]*40 + [30]))
    row = out.iloc[-1]
    assert row["ATR 14"] == pytest.approx((13*2+11)/14)
    assert row["EMA 20"] == pytest.approx(20+20/21)
    assert row["SMA 20"] == 20.5
    macd = 20/13 - 20/27
    assert row.MACD == pytest.approx(macd)
    assert row["Signal 9"] == pytest.approx(macd/5)


def test_rsi_mixed_and_extremes():
    out = indicators(bars([20, 22]*8))
    assert out["RSI 14"].iloc[14] == 50
    assert out["RSI 14"].iloc[15] == pytest.approx(100*15/28)
    for values, expected in [([5]*20,50), (range(30,10,-1),0)]:
        assert indicators(bars(values))["RSI 14"].iloc[-1] == expected


def test_prefix_invariance():
    frame = bars(np.random.default_rng(42).uniform(20, 50, 100))
    pd.testing.assert_frame_equal(indicators(frame.iloc[:55]), indicators(frame).iloc[:55])
    with pytest.raises(ValueError):
        indicators(frame.iloc[::-1])
