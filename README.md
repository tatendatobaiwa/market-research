# Market notebook

A local daily technical-analysis dashboard for NVDA, MSFT, AMD and VOO. Open the synthetic demo immediately, or import historical bars using an entitled Alpaca paper account. The application only reads market data.

## Run locally

Use Python 3.12. From the extracted project directory on Linux or macOS, run

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

On Windows use `py -3.12 -m venv .venv` and activate with `.venv\Scripts\Activate.ps1`. Open the localhost address Streamlit prints. Select an instrument and the number of sessions. Momentum, Range and volume, and Daily observations show the indicators and underlying values. Chart zoom windows preserve indicator warm-up history. Synthetic demo uses a fixed seed and historical session dates to generate artificial OHLCV for interface testing.

## Import private historical data

Obtain Alpaca paper credentials with the appropriate data entitlements for your own local research. Set `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` in the shell environment. In Bash, the commands below read them without echoing or putting them into shell history.

```bash
read -rsp 'Paper key ID: ' APCA_API_KEY_ID && echo
read -rsp 'Paper secret: ' APCA_API_SECRET_KEY && echo
export APCA_API_KEY_ID APCA_API_SECRET_KEY
python -m market.ingest --start 2024-01-02 --end 2024-12-31
```

In Windows PowerShell, with the virtual environment activated, the commands below prompt for both values. The secret stays hidden as you type, and neither value reaches the command history.

```powershell
$env:APCA_API_KEY_ID = Read-Host 'Paper key ID'
$secret = Read-Host 'Paper secret' -AsSecureString
$env:APCA_API_SECRET_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret))
Remove-Variable secret
python -m market.ingest --start 2024-01-02 --end 2024-12-31
```

The variables last only for that PowerShell window. Avoid `setx`, which stores them permanently in the user profile.

Alternatively, put `APCA_API_KEY_ID=...` and `APCA_API_SECRET_KEY=...` on separate lines of a `.env` file in the project directory, then run only the `python -m market.ingest` line. Git ignores `.env`. Values already set in the shell take precedence over the file. The file stores the secret unencrypted, so keep it private.

Both dates are inclusive New York dates. Imports stop before the current New York day. Refresh the dashboard and select **Historical snapshots**. Each immutable snapshot covers the entire requested range. To extend it, rerun with the original start and a later end date. Select an older snapshot to reproduce a previous view. Identical data for the same request reuses its first retrieval timestamp. Updates are manual.

By default both processes use `data/market.sqlite` relative to the project directory. For another path, pass `--db` to the CLI and set `MARKET_DB` to the same path for the dashboard. Keep this database private. The local dashboard binds to loopback.

## Architecture

| Component | Responsibility |
| --- | --- |
| market/data.py | Fetch paginated daily IEX bars over HTTPS, normalize timestamps, validate the four-symbol panel, generate a separate deterministic demo |
| market/ingest.py | Parse the date interval and store a snapshot only after validation succeeds |
| market/store.py | Store bars and metadata together in one SQLite transaction, retain revisions, load a single symbol in session order |
| market/indicators.py | Calculate trailing features for one symbol using only observed bars through each session |
| app.py | Select data source, vintage, instrument and display window, then render the same feature calculations |
| tests/ | Numeric reference tests, prefix-invariance checks, provider-contract fixtures, storage and Streamlit interaction tests |

The SHA-256 snapshot identifier covers source, requested dates and sorted normalized bars. Reproduce a chart with the same snapshot ID, code and dependencies. The archive includes direct dependency pins. Dependencies for a new platform may resolve to different transitive versions.

## Indicator conventions

| Feature | Definition | First available observation |
| --- | --- | --- |
| SMA 20 | Arithmetic mean of the last 20 closes | 20 |
| EMA 20 | Seed with the first 20 closes' mean, then apply weight 2/21 to each new close | 20 |
| MACD | EMA 12 less EMA 26, both mean-seeded | 26 |
| Signal / histogram | Nine-value EMA of MACD / MACD less signal | 34 |
| RSI 14 | Wilder average gains and losses, seeded with 14 close-to-close changes, then smoothed with weight 1/14. All gains gives 100, all losses 0, flat seed 50 | 15 |
| ATR 14 | Wilder average of the largest of high minus low, absolute high minus previous close, and absolute low minus previous close. First bar uses high minus low | 14 |

A short snapshot shows warm-up gaps. An EMA calculated from a different starting date can differ owing to its seed. Indicators describe the observed series. The dashboard provides no calibrated probabilities or performance estimates.

## Verification and scope

Milestone verification used Python 3.12, pytest, Streamlit AppTest and a local HTTP health check. All 23 automated cases passed. Streamlit emitted an upstream Altair deprecation warning. Authentication against Alpaca remains unverified because this run had no credentials. Tests use constructed bars and mock paginated responses. Browser visual inspection was blocked by the execution environment's Chromium socket restrictions.

Research notes, data rights, calendar assumptions, evidence limits, Botswana instruments and the proposed out-of-sample evaluation are in [docs/research.md](docs/research.md). Modeling, cost-aware backtests, the paper ledger and broker connectivity are later milestones.

The delivered archive contains source and configuration. To start version control after extraction, run `git init`. Commit and push policy is in AGENTS.md.
