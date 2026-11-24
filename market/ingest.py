import argparse
from datetime import date
from pathlib import Path
from requests import RequestException
from .data import fetch
from .store import save, DEFAULT_DB


def main():
    parser = argparse.ArgumentParser(description="Import complete historical IEX daily bars for the watchlist.")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    try:
        frame = fetch(args.start, args.end)
        snapshot = save(frame, args.start, args.end, args.db)
    except (ValueError, RequestException, KeyError, TypeError, AttributeError) as error:
        parser.exit(1, f"Import failed: {error}\n")
    print(f"{len(frame)} validated bars across four symbols. Snapshot {snapshot}")


if __name__ == "__main__":
    main()
