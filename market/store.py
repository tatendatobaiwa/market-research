"""Atomic, immutable snapshots. A content digest identifies a data vintage."""
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import sqlite3
import pandas as pd

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "market.sqlite"
SOURCE = "Alpaca / IEX · daily · split-adjusted · USD"


def save(frame, start, end, path=DEFAULT_DB):
    frame = frame.sort_values(["symbol", "date"])
    digest = sha256(f"{SOURCE}|{start}|{end}\n".encode() + frame.to_csv(
        index=False, float_format="%.17g").encode()).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS snapshots
            (id TEXT PRIMARY KEY, source TEXT, start TEXT, end TEXT, fetched TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS bars (snapshot TEXT, symbol TEXT, date TEXT,
            open REAL, high REAL, low REAL, close REAL, volume INTEGER,
            PRIMARY KEY(snapshot,symbol,date))""")
        inserted = db.execute("INSERT OR IGNORE INTO snapshots VALUES (?,?,?,?,?)",
            (digest, SOURCE, str(start), str(end), datetime.now(timezone.utc).isoformat()))
        if inserted.rowcount:
            db.executemany("INSERT INTO bars VALUES (?,?,?,?,?,?,?,?)",
                           ((digest, *r) for r in frame.itertuples(index=False, name=None)))
    return digest


def catalog(path=DEFAULT_DB):
    if not path.exists():
        return []
    with closing(sqlite3.connect(path)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM snapshots ORDER BY fetched DESC")]


def load(path, snapshot, symbol):
    with closing(sqlite3.connect(path)) as db:
        return pd.read_sql_query("""SELECT date,open,high,low,close,volume FROM bars
            WHERE snapshot=? AND symbol=? ORDER BY date""", db, params=(snapshot, symbol),
            parse_dates=["date"], index_col="date")
