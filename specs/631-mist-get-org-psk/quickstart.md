# Quickstart: getOrgPsk (Menu 96)

**Feature**: 631-mist-get-org-psk
**Date**: 2026-06-30

This document is a developer-facing quickstart for the new menu item. It
covers local invocation, required environment, expected output, an example
session, and the mandatory quality gates.

## What This Menu Does

Menu 96 fetches the full detail of a single Pre-Shared Key by its UUID from
`GET /api/v1/orgs/{org_id}/psks/{psk_id}` and writes the record to
`data/org_psk_detail_{org_id}_{psk_id}.csv` (CSV backend), the
`org_psk_detail` table in `data/mist_data.db` (SQLite), or the corresponding
ArangoDB collection + Redis cache entries (polyglot backend).

## How to Run Locally

### Interactive (menu-driven)

```powershell
# From the repo root, with the venv active
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the top-level menu, enter: 96
# When prompted, enter the org UUID (or press Enter to accept the .env default)
# When prompted, enter the PSK UUID
```

### Direct (automation)

```powershell
# Pipe both identifiers on stdin -- safe_input reads them in order
"$env:MIST_ORG_ID`n53f10664-3ce8-4c27-b382-0ef66432349f" | python MistHelper.py --menu 96
```

The `--menu 96` flag jumps straight to the new operation and exits after
completion. Exit code 0 = success (record written or "no data returned"
logged cleanly); non-zero = an unhandled exception (should never occur --
`safe_input()` and the standard `try/except` wrapper catch EOF and API
errors).

## Required `.env` Variables

| Variable            | Required | Purpose                                                |
|---------------------|----------|--------------------------------------------------------|
| `MIST_HOST`         | Yes      | Mist Cloud region host, e.g. `api.mist.com`.           |
| `MIST_API_TOKEN`    | Yes      | API token for the target org.                          |
| `MIST_ORG_ID`       | Yes      | Default org UUID; prompt uses it as a default.         |
| `MIST_PSK_ID_TEST`  | No       | If set and `--test` mode is active, the PSK prompt is auto-answered. |

No new `.env` variables are introduced by this menu item.

## Expected `data/` Output

| Backend        | Artifact                                                      |
|----------------|---------------------------------------------------------------|
| CSV (default)  | `data/org_psk_detail_{org_id}_{psk_id}.csv` (one row)         |
| SQLite         | Row upserted into `data/mist_data.db` table `org_psk_detail`  |
| ArangoDB+Redis | Vertex in `psks` collection + edges per spec 188; Redis cache under `psk:{id}` |

## Example Invocation

```
$ python MistHelper.py --menu 96
[INFO] Menu 96: Get Org PSK Detail (getOrgPsk)
Enter org_id [<MIST_ORG_ID default>]:
Enter psk_id: 53f10664-3ce8-4c27-b382-0ef66432349f
[INFO] Fetching PSK detail for org a97c1b22-a4e9-411e-9bfd-d8695a0f9e61 psk 53f10664-3ce8-4c27-b382-0ef66432349f
[DEBUG] PSK detail: id=53f10664-3ce8-4c27-b382-0ef66432349f name=guest-day ssid=Guest usage=multi
[INFO] Writing org_psk_detail (1 row) via DataExporter
[DEBUG] DataExporter wrote 1 row to data/org_psk_detail_a97c1b22_53f10664.csv
[INFO] Menu 96 complete
```

If the PSK ID does not exist, the Mist API returns 404; MistHelper logs:

```
[WARNING] getOrgPsk returned 404 for psk 53f10664-... in org a97c1b22-...; no data written
```

and exits with code 0 (the run itself is not an error; the request simply
returned no data).

## Implementation Sketch (for the eventual PR)

The new method on `OrgExportUtils` will look like this (target: <=25 lines
per Constitution Principle I). Every executable line carries an inline
comment per Principle VI, and action logging brackets each meaningful step
per Principle VII:

```python
def export_org_psk_detail(self, org_id: str, psk_id: str) -> None:
    """Fetch a single PSK by ID and export via DataExporter (menu 96)."""
    # Log the intent BEFORE any API traffic (Principle VII)
    logging.info("Fetching PSK detail for org %s psk %s", org_id, psk_id)
    # Validate UUID shape; log warning and return early on malformed input
    if not is_mist_uuid(org_id) or not is_mist_uuid(psk_id):  # Principle III
        logging.warning("Invalid UUID: org=%s psk=%s", org_id, psk_id)
        return
    # Invoke the SDK -- sole permitted path to Mist Cloud (Principle II)
    response = mistapi.api.v1.orgs.psks.getOrgPsk(self.apisession, org_id, psk_id)
    # Extract the payload; endpoint returns a single dict (see contracts/)
    psk_record = getattr(response, "data", None)
    # Handle 404 / empty response cleanly (Principle III safety)
    if not psk_record:
        logging.warning("getOrgPsk returned no data for psk %s", psk_id)
        return
    # Log NON-SECRET metadata only; NEVER log passphrase (Principle V)
    logging.debug("PSK detail: id=%s name=%s ssid=%s usage=%s",
                  psk_record.get("id"), psk_record.get("name"),
                  psk_record.get("ssid"), psk_record.get("usage"))
    # Wrap the single object into a one-row list for DataExporter's contract
    rows = [psk_record]
    # Log before the write step (Principle VII)
    logging.info("Writing org_psk_detail (%d row) via DataExporter", len(rows))
    # Persist through the multi-backend exporter (constitution-mandated path)
    DataExporter.write_with_format_selection(
        data=rows,                                     # One-row payload
        filename=f"org_psk_detail_{org_id}_{psk_id}",  # Disambiguated per call
        api_function_name="getOrgPsk",                 # PK strategy lookup key
    )
    # Log completion (Principle VII)
    logging.info("Menu 96 complete")
```

The dispatch entry in the menu loop (function name subject to actual menu
registration convention in `MistHelper.py`) becomes:

```python
# Menu 96: Get Org PSK Detail (single-record fetch by ID)
96: lambda: OrgExportUtils(apisession).export_org_psk_detail(  # Class method call
    safe_input("Enter org_id [%s]: " % default_org_id, context="org_psk_detail:org_id") or default_org_id,
    safe_input("Enter psk_id: ", context="org_psk_detail:psk_id"),
),
```

## Quality Gates (Run Before Every Commit)

All three must be clean before commit and push:

```powershell
# 1. Syntax check -- no output means valid
python -m py_compile MistHelper.py

# 2. Lint check -- must pass with no findings
python -m ruff check MistHelper.py

# 3. Format check -- run without --check to auto-fix
python -m black --check MistHelper.py

# 4. Test sweep -- new menu 96 is inside the default sweep range (60-96)
python MistHelper.py --test
```

If any gate fails, do NOT commit. Fix the finding, re-run all four gates,
then commit with the version-timestamp convention:

```powershell
git add MistHelper.py README.md CHANGELOG.md
git commit -m "version YY.MM.DD.HH.MM - add menu 96 getOrgPsk"
git push origin main
```

Do not push before the four gates are green. The GitHub Actions
`container-build.yml` workflow validates syntax before building the container
image and will reject a broken commit.
