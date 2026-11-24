from datetime import date
from unittest.mock import Mock
import numpy as np
import pytest
from market import data, store

START, END = date(2024, 7, 3), date(2024, 7, 5)


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "test")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "test")


def page(symbols, token):
    bars = {s: [dict(t=f"2024-07-{day}T04:00:00Z",o=10,h=12,l=9,c=11,v=120)
                for day in ("03","05")] for s in symbols}
    return Mock(status_code=200, json=lambda: dict(bars=bars, next_page_token=token))


def test_paginated_import_and_revisions(tmp_path, credentials):
    get = Mock(side_effect=[page(data.SYMBOLS[:2],"next"), page(data.SYMBOLS[2:],None)])
    frame = data.fetch(START, END, get)
    assert len(frame) == 8
    params = get.call_args.kwargs["params"]
    assert (params["page_token"], params["feed"], params["adjustment"]) == ("next","iex","split")
    path = tmp_path / "market.sqlite"
    first = store.save(frame, START, END, path)
    assert first == store.save(frame, START, END, path)
    assert len(store.catalog(path)) == 1
    frame.loc[frame.symbol == "MSFT","close"] = 12
    second = store.save(frame, START, END, path)
    assert second != first
    assert store.load(path, first, "MSFT").close.tolist() == [11,11]
    assert store.load(path, second, "MSFT").close.tolist() == [12,12]


@pytest.mark.parametrize("field,value", [("high",9),("low",10000),("open",0),("close",np.nan),
    ("close",np.inf),("volume",-5),("volume",1.5),("date","2024-07-04"),("symbol","IBM")])
def test_bad_values(field, value):
    frame = data.demo()
    if field == "volume":
        frame[field] = frame[field].astype(float)
    frame.loc[0,field] = value
    with pytest.raises(ValueError):
        data.validate(frame, data.sessions(date(2024,1,2),date(2024,6,28)))


def test_duplicate_and_missing_sessions(credentials):
    for pages in [[page(data.SYMBOLS[:2],None)], [page(data.SYMBOLS,"a"),page(data.SYMBOLS,None)]]:
        with pytest.raises(ValueError, match="Missing, duplicate"):
            data.fetch(START, END, Mock(side_effect=pages))


def test_repeated_token_and_http_failure(credentials):
    with pytest.raises(ValueError, match="Repeated"):
        data.fetch(START, END, Mock(return_value=page([], "loop")))
    with pytest.raises(ValueError, match="HTTP 403"):
        data.fetch(START, END, Mock(return_value=Mock(status_code=403)))


def test_missing_credentials_and_invalid_range(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    with pytest.raises(ValueError, match="credentials"):
        data.fetch(START, END)
    with pytest.raises(ValueError):
        data.sessions(END, START)
