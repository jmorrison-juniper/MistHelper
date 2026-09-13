# Phase 1 Quickstart: getMspSle

**Feature**: `587-mist-get-msp-sle`
**Date**: 2026-06-29
**Proposed menu number**: 59 (Misc cluster 56-59; re-verify at task generation)

This quickstart shows a developer how to run, test, and validate the new menu item
locally on Windows 11 + venv. Adapt path separators for Linux/Podman as needed.

## 1. Prerequisites

- Python 3.13+ in a venv at `.venv\`.
- `mistapi` 0.59+ installed (`pip install -r requirements.txt`).
- A valid `.env` at the repo root (never committed) with:

```dotenv
MIST_HOST=api.mist.com                      # Or your tenant cloud (api.eu.mist.com, etc.)
MIST_API_TOKEN=<your-api-token>             # Loaded by mistapi.APISession; never logged
MIST_TEST_MSP_ID=<known-msp-uuid>           # Optional; used by --test for non-interactive run
MIST_TEST_SLE_METRIC=wifi-connectivity      # Optional; defaults to wifi-connectivity in --test
MIST_TEST_SLE_DURATION=1d                   # Optional; defaults to 1d in --test
```

- Writable `data/` directory: `icacls data /grant Everyone:F /T` on Windows, or
  `chmod -R 777 data/` on Linux (the container runs as a non-root user).

## 2. Activate venv and verify environment

```powershell
.venv\Scripts\Activate.ps1                              # Windows venv activation
python --version                                        # Expect 3.13.x
python -c "import mistapi; print(mistapi.__version__)"  # Expect 0.59.x or newer
```

Verify the SDK module path exposes `getMspSle` (the enriched doc and spec.md
disagree on the canonical module path -- run one of these probes to find out which
one the installed SDK uses):

```powershell
python -c "import mistapi.api.v1.msps.sles as m; print('getMspSle' in dir(m))"
python -c "import mistapi.api.v1.msps.insights as m; print('getMspSle' in dir(m))"
```

Whichever probe prints `True` is the import path to use in MistHelper.

## 3. Interactive invocation

```powershell
python MistHelper.py                                    # Launch the menu
# At the prompt, enter:  59
# When prompted for "MSP ID":           <paste msp UUID>
# When prompted for "SLE metric":       wifi-connectivity
# When prompted for "sle (optional)":   <Enter to skip>
# When prompted for "duration (default 1d)": <Enter for default, or 7d, 2w, etc.>
# When prompted for "interval (optional)":   <Enter to skip, or 1h, 10m, 1d>
# When prompted for "start (optional)":      <Enter to skip, or -1d, -1w, epoch>
# When prompted for "end (optional)":        <Enter to skip, or now, epoch>
```

Expected console flow (ASCII-only):

```text
INFO  Fetching MSP SLE metric wifi-connectivity for msp <msp_id> window=duration=1d
DEBUG MSP SLE response: results=24 start=1719446400 end=1719532800 interval=3600
INFO  Writing 1 row to msp_sle via <backend>
DEBUG Export complete: backend=<backend> rows_written=1
```

## 4. Direct (non-interactive) invocation

```powershell
python MistHelper.py --menu 59                          # Skips main menu; runs item 59
```

When `--menu 59` is combined with `MIST_TEST_MSP_ID` / `MIST_TEST_SLE_METRIC` /
`MIST_TEST_SLE_DURATION` set in `.env`, no prompts appear and the menu item runs
end-to-end. This is the path `--test` uses.

## 5. Expected outputs (under `data/`)

| Backend           | Artifact                                                            |
|-------------------|---------------------------------------------------------------------|
| CSV               | `data/msp_sle.csv` (1 row appended/replaced)                        |
| SQLite (default)  | `data/mist_data.db` table `msp_sle`, 1 row upserted                 |
| ArangoDB + Redis  | `msp_sle` collection in ArangoDB; key cached in Redis               |

Re-running the menu item against the same
`(msp_id, metric, start, end, interval)` produces no duplicate row; the existing
row is replaced via `INSERT OR REPLACE` driven by the `composite_pk` strategy
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Re-running with a different
window or interval correctly produces a new row (different PK).

## 6. Verify the SQLite row

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/mist_data.db'); print(list(c.execute('SELECT msp_id, metric, start, end, interval, length(results_json) FROM msp_sle')))"
```

Expected: one tuple per (MSP, metric, window) combination you have queried:
`(msp_uuid, 'wifi-connectivity', 1719446400, 1719532800, 3600, results_json_byte_length)`.

## 7. Quality gates (run before commit)

All three must pass clean:

```powershell
python -m py_compile MistHelper.py                      # Syntax check; no output = pass
python -m ruff check MistHelper.py                      # Lint; must report 0 errors
python -m black --check MistHelper.py                   # Format check; drop --check to auto-fix
```

Then run the project's test sweep (menu 59 is in the default range; not in the
heavy / destructive skip list of 14, 18, 63-65, 90-100):

```powershell
python MistHelper.py --test                             # Non-interactive sweep using .env IDs
```

## 8. Implementation skeleton (for reference during task generation)

The actual class and method, with every executable line carrying the
constitution-mandated inline comment plus the before/after action logging pattern:

```python
class MspSLEExporter:                                                         # Distinct MSP scope, parallel to OrgSLEExporter
    """Exports MSP-level Service Level Expectation aggregates."""

    def __init__(self, apisession):                                            # DI of the shared Mist API session
        self.apisession = apisession                                           # Reused across all methods on this class

    def export_msp_sle(self, msp_id, metric, sle=None, window=None):           # <=5 params via window dict grouping
        """Fetch one MSP SLE aggregate and persist via DataExporter."""
        window = window or {}                                                  # Default empty dict simplifies .get calls below
        if not _looks_like_uuid(msp_id):                                       # Guard malformed input early
            logging.warning("Invalid msp_id %s -- aborting", msp_id)           # Log validation failure for audit
            return                                                             # Bail out before hitting the API
        if not metric or "/" in metric or "\\" in metric or ".." in metric:    # Reject empty / path-injection metric strings
            logging.warning("Invalid metric %s -- aborting", metric)           # Log validation failure for audit
            return                                                             # Bail out before hitting the API
        logging.info(                                                          # Action log BEFORE API call
            "Fetching MSP SLE metric %s for msp %s window=%s",
            metric, msp_id, window or "defaults",
        )
        response = mistapi.api.v1.msps.sles.getMspSle(                         # Sole permitted SDK invocation
            self.apisession, msp_id, metric,                                   # Positional path params per SDK convention
            sle=sle,                                                           # Optional query param
            duration=window.get("duration", "1d"),                             # Optional query param with documented default
            interval=window.get("interval"),                                   # Optional query param
            start=window.get("start"),                                         # Optional query param
            end=window.get("end"),                                             # Optional query param
        )
        payload = response.data or {}                                          # Tolerate empty body without KeyError
        results_array = payload.get("results") or []                           # Tolerate missing or null array
        logging.debug(                                                         # Action log AFTER API call (count summary)
            "MSP SLE response: results=%d start=%s end=%s interval=%s",
            len(results_array), payload.get("start"),
            payload.get("end"), payload.get("interval"),
        )
        msp_sle_row = {                                                        # Build the row in PK + body field order
            "msp_id": msp_id,                                                  # Inject path param for composite PK part 1
            "metric": metric,                                                  # Inject path param for composite PK part 2
            "start": payload.get("start"),                                     # Required upstream; PK part 3
            "end": payload.get("end"),                                         # Required upstream; PK part 4
            "interval": payload.get("interval"),                               # Required upstream; PK part 5
            "limit": payload.get("limit"),                                     # Optional; None when absent
            "results_json": json.dumps(results_array, separators=(",", ":")),  # Variable shape serialized to JSON
            "sle_filter": sle,                                                 # Echo of the optional sle query param
        }
        logging.info("Writing 1 row to msp_sle")                               # Action log BEFORE export
        DataExporter.write_with_format_selection(                              # Multi-backend output dispatch
            [msp_sle_row], "msp_sle",                                          # Filename / table base
            api_function_name="getMspSle",                                     # Drives PK strategy lookup
        )
        logging.debug("Export of msp_sle complete")                            # Action log AFTER export
```

The menu dispatch entry (one line) is registered next to the other Misc-cluster
items:

```python
59: ("Export MSP SLE aggregate (cross-org)",                                   # Human-readable label for the menu prompt
     lambda apisession: MspSLEExporter(apisession).export_msp_sle(             # Lambda binds the apisession at dispatch time
         msp_id=safe_input("MSP ID: ", context="msp_sle:msp_id"),              # Required path param 1
         metric=safe_input("SLE metric: ", context="msp_sle:metric"),          # Required path param 2
         sle=safe_input(                                                       # Optional query selector
             "sle (Enter to skip): ", context="msp_sle:sle") or None,          # Empty string -> None so SDK omits the param
         window={                                                              # Group the four window selectors per the 5-Item Rule
             "duration": safe_input(                                           # Default per upstream OpenAPI
                 "duration (default 1d): ", context="msp_sle:duration"
             ) or "1d",
             "interval": safe_input(                                           # Optional, blank-to-omit
                 "interval (Enter to skip): ", context="msp_sle:interval"
             ) or None,
             "start": safe_input(                                              # Optional, blank-to-omit
                 "start (Enter to skip): ", context="msp_sle:start"
             ) or None,
             "end": safe_input(                                                # Optional, blank-to-omit
                 "end (Enter to skip): ", context="msp_sle:end"
             ) or None,
         },
     )),
```

## 9. Rollback

If the new menu item misbehaves after deploy, revert by:

```powershell
git revert <commit-sha>                                 # Revert the version commit
git push origin main                                    # Trigger container-build.yml again
podman pull ghcr.io/jmorrison-juniper/misthelper:latest # Pull the reverted image
podman stop misthelper ; podman rm misthelper           # Stop and remove the running container
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" ghcr.io/jmorrison-juniper/misthelper:latest
```

The `msp_sle` table remains populated and harmless after rollback; drop it manually
if a clean state is needed: `DROP TABLE IF EXISTS msp_sle;`.
