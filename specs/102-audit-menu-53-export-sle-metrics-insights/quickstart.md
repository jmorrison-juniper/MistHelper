# Quickstart: Run Menu #53 - Export SLE metrics insights

Prerequisites:
- Python 3.13+ virtualenv
- Install dependencies: pip install -r requirements.txt (mistapi is required)
- Ensure data/ directory exists and is writable

Run the exporter (CSV only):

python MistHelper.py --menu 53 --site-id <SITE_ID> --duration 7d --output-format csv --out data/sle-metrics-<SITE_ID>.csv

Run exporter with SQLite persistence:

python MistHelper.py --menu 53 --site-id <SITE_ID> --duration 7d --output-format both --out-base data/sle-metrics-<SITE_ID>

Notes:
- Default page size for interactive pager: 50 (configurable via --page-size)
- Cache TTL: 1 hour (no change required for export behavior)
- CSV files are written to data/ by default; SQLite DB is data/mist_data.db

Developer quick runs (test mode):
- Use a smaller lookback for fast tests: --duration 1h --limit 10
- To run in test mode and point SQLite to a tmp file:

python MistHelper.py --menu 53 --site-id <SITE_ID> --duration 1h --output-format both --sqlite-db /tmp/test-mist-data.db --limit 10

Verifications after run:
- CSV contains header row and rows (or an empty CSV with header)
- If SQLite enabled: sqlite3 data/mist_data.db "SELECT COUNT(*) FROM sle_metrics WHERE site_id='<SITE_ID>';"
- Idempotency: re-run the same command and ensure row counts for the composite PK do not increase

Troubleshooting:
- If export fails during SQLite writes, logs will indicate error and exporter will attempt transaction rollback. Inspect logs at INFO/DEBUG for API paging and SQL statements (no secrets will be logged).


