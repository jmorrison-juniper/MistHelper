# Phase 1 Quickstart: countOrgDevices Menu Item

This quickstart explains how to run the new menu item locally, what to expect in the
`data/` directory, and which quality gates must pass before commit.

## Prerequisites

- Windows 11 + activated venv (`.venv\Scripts\Activate.ps1`)
- Python 3.13 or newer
- `mistapi` 0.59+ installed (`pip install -r requirements.txt` or `uv pip sync`)
- Populated `.env` at the repo root (see "Required `.env` variables" below)
- Read access to the target Mist organization

## Required `.env` Variables

```dotenv
# Mist Cloud connection (required by mistapi.APISession)
MIST_HOST=api.mist.com               # or your region: api.eu.mist.com, api.gc1.mist.com, ...
MIST_API_TOKEN=<paste-token-here>    # personal or service API token with org read scope

# Default org for --test mode and convenience prompt default
MIST_ORG_ID=<org-uuid-here>          # 8-4-4-4-12 UUID format
```

The API token is never logged or echoed to the console. The `.env` file is git-ignored.

## How to Run Locally (Interactive)

```powershell
# From the repo root, with venv active:
python MistHelper.py
# At the menu prompt, choose: 58
# Answer the prompts:
#   org_id   -> press Enter to accept MIST_ORG_ID, or paste a different UUID
#   distinct -> press Enter for "model", or type one of:
#               model | type | version | hostname | mac | site_id | mxedge_id | lldp_system_name
#   site_id  -> press Enter to skip (org-wide), or paste a site UUID
#   duration -> press Enter for "1d", or type 7d / 2w / -1d / etc.
#   limit    -> press Enter for 100, or type an integer
```

## How to Run Non-Interactively (Direct Invocation)

```powershell
python MistHelper.py --menu 58
# Reads MIST_ORG_ID from .env and uses defaults for all optional prompts.
```

## Expected `data/` Output

After a successful run two files (CSV) and two SQLite tables are written:

```text
data/
├── org_devices_count_summary.csv     # one row appended per invocation per time window
├── org_devices_count_results.csv     # N rows per invocation (one per distinct group)
└── mist_data.db                      # SQLite tables:
                                      #   - org_devices_count_summary
                                      #   - org_devices_count_results
```

The polyglot ArangoDB + Redis backend (if enabled) receives the same data under
collection names `org_devices_count_summary` and `org_devices_count_results`.

## Example Invocation and Expected Output

```text
> python MistHelper.py --menu 58
INFO  Fetching countOrgDevices for org 4ac1d... grouped by model
INFO  Sent GET /api/v1/orgs/4ac1d.../devices/count?distinct=model&duration=1d&limit=100
DEBUG Count envelope: distinct=model total=7 results=7 start=1719522123 end=1719608523
INFO  Flattening 7 result rows from countOrgDevices
DEBUG Flatten complete: 1 summary row + 7 result rows
INFO  Writing org_devices_count_summary via DataExporter
INFO  Writing org_devices_count_results via DataExporter
DEBUG Wrote 1 row to data/org_devices_count_summary.csv (composite PK upsert)
DEBUG Wrote 7 rows to data/org_devices_count_results.csv (composite PK upsert)
INFO  Menu 58 complete
```

## Quality Gates (Run Before Every Commit)

Run each of these from the repo root with the venv active. All three must pass clean:

```powershell
# 1. Python syntax check (no output on success)
python -m py_compile MistHelper.py

# 2. Lint (must produce zero violations)
python -m ruff check MistHelper.py

# 3. Format check (no diff on success; drop --check to auto-fix)
python -m black --check MistHelper.py
```

Plus the project test sweep:

```powershell
# 4. Integration sweep (item 58 is included by default; not on the skip list)
python MistHelper.py --test
```

The test sweep exercises the new menu item using `MIST_ORG_ID` from `.env` and verifies
that the data files are created and that the SQLite tables receive the expected row
counts.

## Method Outline (for reviewers)

The new method `export_org_devices_count()` follows this skeleton (target class:
existing `OrgDeviceExportUtils` -- name verified at implementation). Every executable
line carries an inline comment in the final code; the outline below shows the action
log pattern required by Principle VII.

```python
def export_org_devices_count(self, org_id=None, distinct=None, filters=None):
    org_id = org_id or safe_input("Org UUID: ", context="org_devices_count:org_id")  # collect org from user/.env
    distinct = distinct or safe_input("Group by (model): ", context="org_devices_count:distinct") or "model"  # default grouping
    if not _looks_like_uuid(org_id):  # cheap UUID sanity check before API call
        logging.warning("Invalid org_id %s -- aborting menu 58", org_id)  # warn and bail per Principle III
        return
    logging.info("Fetching countOrgDevices for org %s grouped by %s", org_id, distinct)  # action-log BEFORE
    response = mistapi.api.v1.orgs.devices.countOrgDevices(  # sole transport into Mist Cloud
        self.apisession, org_id, distinct=distinct, **(filters or {})
    )
    envelope = response.data or {}  # API may return empty on 404; tolerate it
    results = envelope.get("results", [])  # array we will flatten one-row-per-bucket
    logging.debug("Count envelope: distinct=%s total=%d results=%d",
                  envelope.get("distinct"), envelope.get("total", 0), len(results))  # action-log AFTER
    summary_row, result_rows = self._flatten_count_envelope(org_id, distinct, envelope)  # private helper on same class
    DataExporter.write_with_format_selection(  # multi-backend write
        [summary_row], "org_devices_count_summary",
        api_function_name="countOrgDevices",
    )
    DataExporter.write_with_format_selection(  # results table written separately
        result_rows, "org_devices_count_results",
        api_function_name="countOrgDevices",
    )
    logging.info("Menu 58 complete")  # close out the action log
```

## Troubleshooting

| Symptom                                              | Likely Cause                  | Fix                                                                 |
|------------------------------------------------------|-------------------------------|---------------------------------------------------------------------|
| `EOFError` on first prompt                           | Container/SSH non-tty session | Confirmed handled by `safe_input()` -- it exits cleanly with code 0 |
| `401 Unauthorized` in logs                           | Bad / expired token           | Refresh `MIST_API_TOKEN` in `.env`                                  |
| `403 Permission Denied`                              | Token lacks org read scope    | Issue a new token with org-level read permission                    |
| `404 Not Found`                                      | Wrong `org_id`                | Verify UUID in Mist UI -> Organization Settings                     |
| `PermissionError: data/script.log`                   | Mounted `data/` not writable  | `chmod -R 777 data/` (container) or check NTFS ACL (Windows)        |
| Empty `results[]` array                              | No devices in window          | Widen `duration` or remove `site_id` filter                         |
