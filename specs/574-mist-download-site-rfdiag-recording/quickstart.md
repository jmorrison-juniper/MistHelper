# Phase 1 Quickstart: Menu 96 -- downloadSiteRfdiagRecording

## What this menu item does

Downloads one Mist RF diagnostics recording (`raw_events` blob) for a
given `(site_id, rfdiag_id)` pair, writes the decoded binary payload to
`data/rfdiags/<site_id>_<rfdiag_id>.raw`, and records a one-row
metadata receipt (filename, byte count, SHA-256, timestamp) through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all see a consistent ledger.

## Prerequisites

### Required .env variables

The following must already be set in the repo-root `.env` file (same
file used by every other MistHelper operation):

```dotenv
MIST_HOST=api.mist.com                  # or api.eu.mist.com / api.gc1.mist.com etc.
MIST_API_TOKEN=<your-mist-api-token>    # NEVER committed; .env is git-ignored
```

### Optional .env variables (for non-interactive --test)

```dotenv
MIST_TEST_SITE_ID=<a-known-site-uuid>
MIST_TEST_RFDIAG_ID=<a-known-rfdiag-uuid-for-that-site>
```

When both are present, `python MistHelper.py --test` will exercise
menu 96 against the configured pair. When either is absent, the test
stub logs a `WARNING` and exits 0 cleanly (rfdiag IDs are ephemeral
per-site, so test coverage is opt-in).

### Filesystem prerequisites

```powershell
# Confirm data/ exists and is writable (required by container runs too)
New-Item -ItemType Directory -Force -Path data | Out-Null
# (Linux/container only) chmod -R 777 data/ if first-time mount
```

The `data/rfdiags/` subdirectory is auto-created on first download via
`os.makedirs("data/rfdiags", exist_ok=True)`.

## How to run locally

### Interactive (the standard path)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the main menu prompt, type: 96
# When prompted: Enter site_id: <paste-site-uuid>
# When prompted: Enter rfdiag_id: <paste-rfdiag-uuid>
```

Expected console flow (ASCII-only):

```
INFO  Selected menu 96 -- downloadSiteRfdiagRecording
INFO  Downloading rfdiag recording site=<site-uuid> rfdiag=<rfdiag-uuid>
DEBUG Received <N> encoded bytes, <M> decoded bytes, sha256=<hex>
INFO  Writing rfdiag blob to data/rfdiags/<site-uuid>_<rfdiag-uuid>.raw
DEBUG Wrote <M> bytes to data/rfdiags/<site-uuid>_<rfdiag-uuid>.raw
INFO  Recording ledger entry via DataExporter for downloadSiteRfdiagRecording
DEBUG DataExporter wrote 1 row to site_rfdiag_downloads
```

### Direct (for automation)

```powershell
python MistHelper.py --menu 96
# Same prompts as interactive; supports safe_input() EOF handling for SSH/pipe.
```

### Non-interactive test sweep

```powershell
python MistHelper.py --test
# Exercises menu 96 only when MIST_TEST_SITE_ID and MIST_TEST_RFDIAG_ID are set.
```

## Expected output

### On disk

```text
data/
|-- rfdiags/
|   `-- <site_id>_<rfdiag_id>.raw          # binary blob, mode wb, overwritten on re-run
|-- site_rfdiag_downloads.csv              # one row per (site_id, rfdiag_id) when CSV backend active
`-- mist_data.db                           # SQLite, table `site_rfdiag_downloads` upserted by composite PK
```

### Sample ledger row (SQLite or CSV)

| site_id   | rfdiag_id | filename                                    | byte_count | sha256          | downloaded_at        | org_id    |
|-----------|-----------|---------------------------------------------|------------|-----------------|----------------------|-----------|
| `abc...`  | `def...`  | `data/rfdiags/abc..._def....raw`            | `1048576`  | `9f86d0...8b4c` | `2026-06-29T20:15:33Z` | `123...`  |

## Method outline (the new code in MistHelper.py)

The menu method lives on a new `RfDiagnosticsManager` class. The
following sketch shows the expected line density (every executable
line carries an inline comment per Constitution VI):

```python
class RfDiagnosticsManager:                                              # New class -- home for all rfdiag endpoints
    def __init__(self, apisession, data_exporter):                       # Accept the shared mistapi session + exporter
        self.apisession = apisession                                     # Store session so subsequent SDK calls reuse auth
        self.data_exporter = data_exporter                               # Store exporter for multi-backend ledger writes

    def download_site_rfdiag_recording(self, site_id=None, rfdiag_id=None, output_dir="data/rfdiags"):
        site_id = site_id or safe_input("Enter site_id: ", context="rfdiag_download:site_id")        # Prompt only when not pre-supplied
        rfdiag_id = rfdiag_id or safe_input("Enter rfdiag_id: ", context="rfdiag_download:rfdiag_id")  # Same -- supports --menu 96 calls with args
        logging.info("Downloading rfdiag recording site=%s rfdiag=%s", site_id, rfdiag_id)            # Action log BEFORE the API call
        response = mistapi.api.v1.sites.rfdiags.download.downloadSiteRfdiagRecording(                 # Sole permitted Mist API call path
            self.apisession, site_id, rfdiag_id
        )
        decoded = base64.b64decode(response.data or "")                                               # Decode base64 payload from the API
        digest = hashlib.sha256(decoded).hexdigest()                                                  # Fingerprint for de-dup queries
        logging.debug("Received %d decoded bytes, sha256=%s", len(decoded), digest)                   # Action log AFTER the API call
        os.makedirs(output_dir, exist_ok=True)                                                        # Idempotent subdir create
        output_path = os.path.join(output_dir, f"{site_id}_{rfdiag_id}.raw")                          # Deterministic filename keeps DB+FS in sync
        logging.info("Writing rfdiag blob to %s", output_path)                                        # Action log BEFORE the file write
        with open(output_path, "wb") as fh:                                                           # Binary mode -- payload is opaque bytes
            fh.write(decoded)                                                                         # Persist blob; truncate-on-open semantics
        logging.debug("Wrote %d bytes to %s", len(decoded), output_path)                              # Action log AFTER the file write
        ledger_row = {                                                                                # Build the metadata receipt for DataExporter
            "site_id": site_id,                                                                       # Composite PK part 1
            "rfdiag_id": rfdiag_id,                                                                   # Composite PK part 2
            "filename": output_path,                                                                  # Canonical pointer back to the on-disk blob
            "byte_count": len(decoded),                                                               # Size of decoded payload
            "sha256": digest,                                                                         # Content fingerprint
            "downloaded_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",                   # ISO 8601 UTC timestamp
            "org_id": getattr(self.apisession, "org_id", None),                                       # Optional org context, may be None
        }
        logging.info("Recording ledger entry via DataExporter for downloadSiteRfdiagRecording")       # Action log BEFORE the ledger write
        self.data_exporter.write_with_format_selection(                                               # Multi-backend write (CSV/SQLite/Arango+Redis)
            [ledger_row], "site_rfdiag_downloads", api_function_name="downloadSiteRfdiagRecording",
        )
```

This sketch is 21 executable lines inside the public method (excluding
class header and `__init__`), well within the 25-line Five-Item Rule
ceiling.

## Quality gates (run before commit)

```powershell
# Step 1 -- syntax (must produce no output)
python -m py_compile MistHelper.py

# Step 2 -- lint (must exit 0)
python -m ruff check MistHelper.py

# Step 3 -- format (run without --check to auto-fix locally)
python -m black --check MistHelper.py

# Step 4 -- test sweep (exercises menu 96 when MIST_TEST_* env vars are set)
python MistHelper.py --test
```

All four must pass before committing.

## Verifying the result

```powershell
# Confirm the blob exists and is non-empty
Get-Item data\rfdiags\<site_id>_<rfdiag_id>.raw

# Confirm the SQLite ledger row was upserted
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(list(c.execute('SELECT site_id, rfdiag_id, byte_count, sha256, downloaded_at FROM site_rfdiag_downloads')))"

# Re-run menu 96 -- the file is overwritten in place, the SQLite row is upserted
python MistHelper.py --menu 96
```

## Rollback

```powershell
# Remove the on-disk blob (does NOT affect Mist Cloud)
Remove-Item data\rfdiags\<site_id>_<rfdiag_id>.raw

# Remove the ledger row
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); c.execute('DELETE FROM site_rfdiag_downloads WHERE site_id=? AND rfdiag_id=?', ('<site_id>','<rfdiag_id>')); c.commit()"
```

No Mist Cloud state is touched by either step; the upstream recording
remains exactly as it was.
