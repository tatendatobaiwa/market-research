from datetime import date
from streamlit.testing.v1 import AppTest
from market import data, store


def test_demo_controls_and_empty_store(monkeypatch,tmp_path):
    monkeypatch.setenv("MARKET_DB",str(tmp_path/"empty.sqlite"))
    app = AppTest.from_file("app.py", default_timeout=15).run()
    assert not app.exception and "Synthetic" in app.warning[0].value
    app.selectbox[0].select("VOO").run()
    assert app.header[0].value == "VOO"
    app.selectbox[1].select(30).run()
    assert len(app.dataframe[0].value) == 30
    app.radio[0].set_value("Historical snapshots").run()
    assert "No historical snapshot" in app.info[0].value
    assert not app.exception


def test_historical_screen_with_mock_snapshot(monkeypatch,tmp_path):
    path = tmp_path/"test.sqlite"
    store.save(data.demo(),date(2024,1,2),date(2024,6,28),path)
    monkeypatch.setenv("MARKET_DB",str(path))
    app = AppTest.from_file("app.py", default_timeout=15).run()
    app.radio[0].set_value("Historical snapshots").run()
    assert not app.exception
    assert "IEX" in app.info[0].value and app.metric[0].value != "Warming up"


def test_snapshot_missing_symbol(monkeypatch,tmp_path):
    path = tmp_path/"partial.sqlite"
    frame = data.demo()
    store.save(frame[frame.symbol != "NVDA"],date(2024,1,2),date(2024,6,28),path)
    monkeypatch.setenv("MARKET_DB",str(path))
    app = AppTest.from_file("app.py", default_timeout=15).run()
    app.radio[0].set_value("Historical snapshots").run()
    assert not app.exception
    assert "no bars for NVDA" in app.error[0].value
