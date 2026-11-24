import argparse
import os
from datetime import date
from pathlib import Path
from requests import RequestException
from .data import fetch
from .store import save, DEFAULT_DB

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
CREDENTIALS = ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY")


def load_env(path=ENV_FILE):
    """Read Alpaca credentials from a local KEY=value file. Shell values take precedence."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip().strip("'\"")
        if sep and name in CREDENTIALS and value and not os.environ.get(name):
            os.environ[name] = value


def main():
    parser = argparse.ArgumentParser(description="Import complete historical IEX daily bars for the watchlist.")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    load_env()
    try:
        frame = fetch(args.start, args.end)
        snapshot = save(frame, args.start, args.end, args.db)
    except (ValueError, RequestException, KeyError, TypeError, AttributeError) as error:
        parser.exit(1, f"Import failed: {error}\n")
    print(f"{len(frame)} validated bars across four symbols. Snapshot {snapshot}")


if __name__ == "__main__":
    main()
