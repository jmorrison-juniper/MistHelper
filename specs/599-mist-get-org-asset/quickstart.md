# Phase 1 Quickstart: getOrgAsset (menu 195)

**Feature**: 599-mist-get-org-asset | **Date**: 2026-06-29

This quickstart shows a developer how to run the new menu item locally, what `.env`
variables it needs, what files appear under `data/` afterwards, and which quality gates
must pass before commit.

## Required .env Variables

The new menu item reuses the existing Mist authentication scaffolding. No new variables
are introduced; the only new optional convenience is documenting which org / asset to
target during `--test`.

```ini
# Required for any Mist API call
MIST_HOST=api.mist.com                                          # Or your cloud region host
MIST_API_TOKEN=replace-with-your-personal-api-token             # Never commit this value

# Optional defaults consumed by menu 195
MIST_DEFAULT_ORG_ID=a97c1b22-a4e9-411e-9bfd-d8695a0f9e61        # Used as the org_id prompt default
MIST_TEST_ASSET_ID=53f10664-3ce8-4c27-b382-0ef66432349f         # Optional, --test only
```

If `MIST_TEST_ASSET_ID` is unset, the `--test` sweep skips menu 195 with a `WARNING` log
line and exits 0; this preserves the existing CI contract.

## How to Run Locally

```powershell
# 1. Activate the local virtualenv (Windows + venv is the standard environment)
.venv\Scripts\Activate.ps1

# 2. Confirm the .env file holds MIST_HOST and MIST_API_TOKEN
Get-Content .env | Select-String 'MIST_HOST|MIST_API_TOKEN'

# 3. Interactive invocation -- menu-driven
python MistHelper.py
#   At the main menu, type 195 and press Enter.
#   Prompt 1: "Enter org_id [default: <MIST_DEFAULT_ORG_ID>]: "
#   Prompt 2: "Enter asset_id: "
#   On success, the row count and the destination file name are echoed to stdout.

# 4. Direct invocation -- automation-friendly
python MistHelper.py --menu 195 --org-id a97c1b22-a4e9-411e-9bfd-d8695a0f9e61 `
                                  --asset-id 53f10664-3ce8-4c27-b382-0ef66432349f
```

## Expected Output Under data/

After a successful run the following files exist under the project's `data/` directory
(exact set depends on the configured backend in `.env`):

| Backend                | File / Object                                              | Contents                                  |
|------------------------|------------------------------------------------------------|-------------------------------------------|
| CSV (default)          | `data\get_org_asset.csv`                                   | One header row + one data row             |
| SQLite (always)        | `data\mist_data.db` -> table `get_org_asset`               | One row keyed on the asset `id`           |
| ArangoDB+Redis (opt-in)| ArangoDB collection `get_org_asset` + Redis cache key      | One document + cached lookup              |

A second invocation with the same `asset_id` upserts the existing row in place (no
duplicates) because the primary key strategy is `natural_pk` on `id`.

## Example Method Outline

The new method on `OrgExportUtils` (full implementation lives in `tasks.md` / source
code, this is a developer-facing sketch only):

```python
@staticmethod
def export_org_asset(org_id: str = "", asset_id: str = "") -> None:  # Menu 195 entrypoint
    """Fetch one BLE asset by UUID and persist via DataExporter."""
    validated_org_id = org_id or safe_input(                # Prompt with .env default when blank
        "Enter org_id: ", context="org_asset:org_id"
    )
    validated_asset_id = asset_id or safe_input(            # Always prompt when missing
        "Enter asset_id: ", context="org_asset:asset_id"
    )
    if not is_mist_uuid(validated_org_id) or not is_mist_uuid(validated_asset_id):
        logging.warning("Invalid UUID supplied to menu 195; aborting before API call")
        return                                              # Early-out per Principle III
    logging.info(                                           # INFO before the SDK call
        "Fetching asset %s for org %s", validated_asset_id, validated_org_id
    )
    response = mistapi.api.v1.orgs.assets.getOrgAsset(      # The single SDK call
        APISESSION, validated_org_id, validated_asset_id
    )
    asset_record = response.data or {}                      # Normalize to dict
    logging.debug(                                          # DEBUG after the SDK call
        "getOrgAsset returned name=%s mac=%s",
        asset_record.get("name"), asset_record.get("mac"),
    )
    DataExporter.write_with_format_selection(               # Persist the one-row dataset
        data=[asset_record] if asset_record else [],
        filename="get_org_asset",
        api_function_name="getOrgAsset",
    )
```

The method body is 18 executable lines (under the 25-line cap), takes 2 parameters
(under the 5-parameter cap), and has 4 logical blocks (under the 5-block cap) -- the
5-Item Rule passes with margin.

## Quality Gates (run before every commit)

```powershell
# Required, in this order:
python -m py_compile MistHelper.py            # Must produce no output
python -m ruff check MistHelper.py            # Must report 0 violations
python -m black --check MistHelper.py         # Must report would-not-be-reformatted

# Functional verification:
python MistHelper.py --test                   # The --test sweep includes menu 195 when
                                              # MIST_TEST_ASSET_ID is set, skips it otherwise
```

If any gate fails, do not commit. Fix the violation (or, for ruff / black, run them
without `--check` to auto-fix), re-run the full quality gate sequence, then commit.

## Smoke-Test Acceptance

The new menu item is considered ready when:

1. `python -m py_compile MistHelper.py` returns exit code 0 with no output.
2. `python -m ruff check MistHelper.py` returns exit code 0.
3. `python -m black --check MistHelper.py` returns exit code 0.
4. `python MistHelper.py --menu 195` against a known asset writes
   `data\get_org_asset.csv` and the SQLite row, with logs showing the `INFO` /
   `DEBUG` pair around the SDK call.
5. Re-running step 4 does not duplicate the SQLite row (upsert verified).
6. SSH disconnect mid-prompt exits the process with code 0 and no traceback
   (`safe_input()` EOF path verified).
