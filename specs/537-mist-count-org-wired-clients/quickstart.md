# Phase 1 Quickstart: countOrgWiredClients (Menu 88)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Data model**: [data-model.md](./data-model.md)
**Contract**: [contracts/count_org_wired_clients.md](./contracts/count_org_wired_clients.md)

## What This Menu Item Does

Calls `GET /api/v1/orgs/{org_id}/wired_clients/count` via the `mistapi` SDK and
writes the distinct-attribute count of wired clients to the configured output
backend under `data/`.

## Required .env Variables

In the repository-root `.env` (git-ignored), the following keys must be set:

```dotenv
MIST_HOST=api.mist.com                     # Or the regional cloud host
MIST_API_TOKEN=<your-mist-api-token>       # Never logged
MIST_ORG_ID=<default-org-uuid>             # Used as the prompt default
```

The container reads the same file via the `-v "${PWD}/.env:/app/.env:ro"`
mount in the documented `podman run` command.

## Running the Menu Item Locally (Windows venv)

```powershell
# Activate the dev venv (standard project pattern)
.venv\Scripts\Activate.ps1

# Interactive run
python MistHelper.py
# Then enter `88` at the menu prompt

# Direct (non-interactive) invocation -- preferred for scripting
python MistHelper.py --menu 88
```

## Example Interactive Session

```text
> python MistHelper.py --menu 88
Org ID [c0ffee00-0000-0000-0000-000000000000]:                <ENTER>
Distinct attribute (blank for API default): mac               <ENTER>
Duration [1d]: 7d                                             <ENTER>
Limit [100]:                                                  <ENTER>
INFO: Counting wired clients for org c0ffee00-... distinct=mac duration=7d limit=100
DEBUG: Wired client count: total=42 distinct_values=42 limit=100
INFO: Flattening 1 summary row + 42 result rows
DEBUG: Flattened to 43 rows
INFO: Writing org_wired_clients_count_c0ffee00_mac_7d.csv (backend=auto)
DEBUG: Wrote 43 rows to data/org_wired_clients_count_c0ffee00_mac_7d.csv
DEBUG: Upserted 43 rows into SQLite table org_wired_clients_count
```

## Expected Output Locations

- CSV: `data/org_wired_clients_count_<org_id_short>_<distinct>_<duration>.csv`
- SQLite: row(s) upserted into `data/mist_data.db`, table
  `org_wired_clients_count`
- ArangoDB (when polyglot backend is active): documents in collection
  `org_wired_clients_count`; graph edges into the `orgs` vertex collection
  per spec 188

## Method Outline (For Implementers)

The new method lives on the existing `WiredClientExportUtils` class in
`MistHelper.py`. Every executable line carries an inline comment in the final
implementation; the outline below shows the comment density expected by
Principle VI.

```python
def export_org_wired_clients_count(self):                                       # Menu 88 entry point on WiredClientExportUtils
    org_id = safe_input(                                                        # safe_input handles SSH/container EOF cleanly
        f"Org ID [{self.default_org_id}]: ",                                    # Show .env default in the prompt
        context="wired_clients_count:org_id",                                   # Context tag for the EOF log message
    ).strip() or self.default_org_id                                            # Empty input keeps the .env default
    if not is_valid_uuid(org_id):                                               # Validate before spending an API call
        logging.warning("Invalid org_id %s -- aborting", org_id)                # ASCII-only warning, no traceback
        return                                                                  # Early return on validation failure
    distinct = safe_input(                                                      # Prompt for the grouping field
        "Distinct attribute (blank for API default): ",                         # Blank means do not pass the param
        context="wired_clients_count:distinct",                                 # Context tag for EOF
    ).strip() or None                                                           # None tells mistapi to omit the query param
    duration = safe_input(                                                      # Prompt for the time window
        "Duration [1d]: ",                                                      # 1d matches the Mist API default
        context="wired_clients_count:duration",                                 # Context tag for EOF
    ).strip() or "1d"                                                           # Empty input keeps the API default
    limit = self._parse_limit(                                                  # Helper coerces to int with fallback
        safe_input(                                                             # Prompt for the result-array cap
            "Limit [100]: ",                                                    # 100 matches the Mist API default
            context="wired_clients_count:limit",                                # Context tag for EOF
        ),                                                                      # Inner safe_input returns the raw string
        default=100,                                                            # Fallback when parsing fails
    )                                                                           # End of helper call
    logging.info(                                                               # Action log BEFORE the API call (Principle VII)
        "Counting wired clients for org %s distinct=%s duration=%s limit=%d",   # %s/%d lazy formatting per Principle V
        org_id, distinct, duration, limit,                                      # Token is never in the log line
    )                                                                           # End of info log
    response = mistapi.api.v1.orgs.wired_clients.count.countOrgWiredClients(    # Sole permitted Mist client per Constitution
        self.api_session,                                                       # Shared APISession from .env
        org_id,                                                                 # Path parameter
        distinct=distinct,                                                      # Query param, None -> omitted
        duration=duration,                                                      # Query param, default 1d
        limit=limit,                                                            # Query param, default 100
    )                                                                           # End of SDK call
    payload = response.data or {}                                               # mistapi returns APIResponse; .data is the JSON dict
    results = payload.get("results", [])                                        # Bounded array per the schema
    logging.debug(                                                              # Action log AFTER the API call (Principle VII)
        "Wired client count: total=%d distinct_values=%d limit=%d",             # ASCII-only debug summary
        payload.get("total", 0), len(results), payload.get("limit", 0),         # Defensive .get for partial responses
    )                                                                           # End of debug log
    rows = self._flatten_count_payload(org_id, distinct, payload)               # 1 summary row + N result rows
    DataExporter.write_with_format_selection(                                   # Multi-backend write per FR-004
        data=rows,                                                              # Flattened list of dicts
        filename=self._count_filename(org_id, distinct, duration),              # Filename pattern from research.md
        api_function_name="countOrgWiredClients",                               # PK lookup key for ENDPOINT_PRIMARY_KEY_STRATEGIES
    )                                                                           # End of DataExporter call
```

The `_flatten_count_payload`, `_parse_limit`, and `_count_filename` helpers
are private methods on the same `WiredClientExportUtils` class (Principle II
-- no module-level wrappers).

## Quality Gates (Mandatory Before Commit)

```powershell
python -m py_compile MistHelper.py                          # Syntax check; no output = pass
python -m ruff check MistHelper.py                          # Lint check; must be clean
python -m black --check MistHelper.py                       # Format check; rerun without --check to auto-fix
python MistHelper.py --test                                 # Full automated sweep; menu 88 is in scope
```

All four must succeed before the change is committed. The container build
pipeline (`.github/workflows/container-build.yml`) re-runs `py_compile` and
the lint/format suite on `main` push; only after CI is green is the GHCR
image refreshed.

## Verifying the Output

```powershell
# CSV inspection
Get-Content data\org_wired_clients_count_*.csv -TotalCount 5

# SQLite inspection (requires sqlite3 in PATH or VS Code sqlite extension)
sqlite3 data\mist_data.db "SELECT distinct_value, count FROM org_wired_clients_count WHERE distinct = 'mac' ORDER BY count DESC LIMIT 10;"

# Confirm idempotent upsert by re-running and counting rows
python MistHelper.py --menu 88                              # Re-run with the same inputs
sqlite3 data\mist_data.db "SELECT COUNT(*) FROM org_wired_clients_count WHERE org_id = '<uuid>' AND distinct = 'mac';"
# The count must be unchanged across runs over the same window.
```

## Troubleshooting

- `PermissionError` on `data/script.log` inside the container: run `chmod -R
  777 data/` on the host before the first container start. The container's
  non-root `misthelper` user needs write access to the mount.
- 401 from Mist: check `MIST_API_TOKEN` in `.env`; never paste the token
  into a log file or commit.
- 404 from Mist: the `org_id` was rejected by the API; the menu logs a
  `WARNING` and exits with code 0 -- no traceback.
- Empty `results` array: the menu logs `WARNING: no data returned` and still
  writes the envelope row so subsequent SQL queries do not silently break.
