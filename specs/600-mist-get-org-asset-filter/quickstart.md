# Phase 1 Quickstart: getOrgAssetFilter (Menu 97)

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-29

This quickstart shows how to run the new menu item locally during development and
how to verify it before opening a PR.

## 1. Prerequisites

- Python 3.13+ with the repo venv activated (`.venv\Scripts\Activate.ps1` on
  Windows).
- `mistapi` 0.59+ installed (already in `requirements.txt`).
- A `.env` file at the repo root containing the variables listed below.
- Write access to `data/` (run `chmod -R 777 data/` on Linux/Podman or ensure the
  Windows folder is not read-only).

## 2. Required `.env` variables

```dotenv
# Mist Cloud credentials (REQUIRED -- never commit this file)
MIST_HOST=api.mist.com                          # or api.eu.mist.com, etc.
MIST_API_TOKEN=<your Mist API token>            # from Mist UI > My Account > API Tokens

# Optional default for the org prompt; pressing Enter at the prompt accepts this
MIST_ORG_ID=<UUID of your test org>

# Optional storage backend selection (CSV is the default if unset)
MISTHELPER_OUTPUT_BACKEND=csv                   # one of: csv, sqlite, arangodb
```

`MIST_API_TOKEN` is read by `mistapi.APISession` and is never logged. There is no
environment default for `MIST_ASSET_FILTER_ID`; the user must supply it interactively
or via the `--menu` CLI shortcut (see step 4).

## 3. Expected `data/` output

| Backend                | Filename                                | Notes                                |
|------------------------|-----------------------------------------|--------------------------------------|
| CSV (default)          | `data/org_asset_filter.csv`             | One row appended per run.            |
| SQLite                 | `data/mist_data.db` table `org_asset_filter` | Upserted via natural PK on `id`.|
| ArangoDB + Redis       | Collection `org_asset_filter` + Redis cache key | Edges to org / site documents.   |

The SQLite table is created on first run by `DataExporter.write_with_format_selection`
using the registered `ENDPOINT_PRIMARY_KEY_STRATEGIES['getOrgAssetFilter']` entry.

## 4. Example invocations

### Interactive flow

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# At the main menu, select 97 (Get Org Asset Filter (BLE) details by ID).
# Prompts:
#   Organization ID (UUID): <press Enter to accept MIST_ORG_ID, or paste a UUID>
#   Asset Filter ID (UUID): <paste the UUID copied from the Mist UI or
#                            from a prior run of getOrgAssetFilters>
```

### Direct (scriptable) flow

```powershell
python MistHelper.py --menu 97
# Same prompts as above. EOF from a piped stdin is handled cleanly by safe_input()
# and the process exits 0.
```

### Container flow

```powershell
podman exec -it misthelper python MistHelper.py --menu 97
```

### Verifying SQLite output

```powershell
python -c "import sqlite3; c = sqlite3.connect('data/mist_data.db'); print(list(c.execute('SELECT id, name, disabled FROM org_asset_filter')))"
```

## 5. Implementation sketch

The new method on `OrgAssetFilterExportUtils` follows this skeleton (full inline
comments and `logging` calls are mandatory per Constitution VI and VII):

```python
def export_org_asset_filter(self, org_id: str, asset_filter_id: str) -> None:
    # Validate both UUIDs before consuming an API call quota.
    if not self._is_valid_uuid(org_id):                               # cheap shape check
        logging.warning("Invalid org_id supplied: %s", org_id)        # ASCII WARNING
        return                                                        # early exit
    if not self._is_valid_uuid(asset_filter_id):                      # cheap shape check
        logging.warning("Invalid asset_filter_id supplied: %s", asset_filter_id)
        return                                                        # early exit
    logging.info("Fetching asset filter %s for org %s",               # action log: before
                 asset_filter_id, org_id)
    response = mistapi.api.v1.orgs.asset_filters.getOrgAssetFilter(   # sole SDK call
        self.apisession, org_id, asset_filter_id)
    record = response.data or {}                                      # tolerate 404 None
    logging.debug("Asset filter retrieved: name=%s disabled=%s",      # action log: after
                  record.get("name"), record.get("disabled"))
    DataExporter.write_with_format_selection(                          # multi-backend write
        [record], "org_asset_filter",
        api_function_name="getOrgAssetFilter")
```

The prompt-collection wrapper that the menu loop calls into uses
`safe_input("Organization ID (UUID): ", context="org_asset_filter:org_id")` and
`safe_input("Asset Filter ID (UUID): ", context="org_asset_filter:assetfilter_id")`.

## 6. Quality gates (run before committing)

```powershell
python -m py_compile MistHelper.py          # syntax (no output = pass)
python -m ruff check MistHelper.py          # lint (must be clean)
python -m black --check MistHelper.py       # format (drop --check to auto-fix)
python MistHelper.py --menu 97              # smoke-test against a known org / filter
```

Heavy / destructive sweep (`python MistHelper.py --test`) skips operations 14, 18,
63-65, and 90-100, which includes the new menu number 97. Therefore the operation is
validated by the explicit `--menu 97` invocation above rather than by the broad test
sweep.

## 7. CHANGELOG entry template

```
## [version YY.MM.DD.HH.MM] - 2026-MM-DD

### Added
- Menu 97: Get Org Asset Filter (BLE) details by ID
  (`mistapi.api.v1.orgs.asset_filters.getOrgAssetFilter`). Persisted to
  `data/org_asset_filter.csv` (CSV) and table `org_asset_filter` (SQLite) using
  natural PK on `id`.
```
