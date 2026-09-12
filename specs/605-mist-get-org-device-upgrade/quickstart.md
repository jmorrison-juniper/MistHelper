# Phase 1 Quickstart: getOrgDeviceUpgrade (menu 96)

**Feature**: 605-mist-get-org-device-upgrade
**Date**: 2026-06-30
**Audience**: Junior NOC engineers and developers extending MistHelper.

## What this menu item does

Retrieves the full status of a single multi-device firmware upgrade job
identified by its UUID. Output includes the job-level configuration
(`target_version`, `strategy`, `enable_p2p`, `force`) plus one detail row
per affected site, with per-phase device MAC lists (`downloading`,
`downloaded`, `upgraded`, `failed`, `skipped`, etc.). Read-only -- safe to
re-run while an upgrade is in progress to monitor evolution.

## Required .env variables

```ini
# Mandatory for every MistHelper run
MIST_HOST=api.mist.com               # Or api.eu.mist.com / api.gc1.mist.com
MIST_API_TOKEN=<your-api-token>      # Org-scoped Mist API token

# Optional but strongly recommended -- avoids retyping the org UUID
MIST_ORG_ID=<your-org-uuid>          # Used as the default when prompted
```

The `upgrade_id` is NOT placed in `.env` -- it is per-invocation user
input (UUIDs come and go as upgrades complete).

## How to discover a valid upgrade_id

Run the sibling menu item first:

```powershell
# Activate venv (Windows 11 standard dev environment)
.venv\Scripts\Activate.ps1

# List recent upgrade jobs for the org -- copy a UUID from the output
python MistHelper.py --menu <listOrgDeviceUpgrades-menu-number>
```

The CSV/SQLite output will contain one row per upgrade job with an `id`
column; that is the value to paste into the menu 96 prompt.

## Run the new menu item

### Interactive mode (manual prompts)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py
# Then enter "96" at the menu prompt, then the two UUIDs.
```

Example session:

```text
Select menu option: 96
Org ID [default from .env]: <Enter>           # accepts MIST_ORG_ID default
Upgrade ID (UUID, see menu for listOrgDeviceUpgrades): 53f10664-3ce8-4c27-b382-0ef66432349f
INFO  Fetching device upgrade detail for org 11111111-... upgrade 53f10664-...
DEBUG Upgrade detail: strategy=canary target=0.14.29411 sites=4 total=37
INFO  Flattening 4 site rows
INFO  Writing org_device_upgrade and org_device_upgrade_site_details
DEBUG Wrote 1 summary row and 4 detail rows
```

### Direct (non-interactive) invocation

```powershell
python MistHelper.py --menu 96
# Even with --menu, the safe_input() prompts still fire. To run hands-off,
# pre-populate MIST_ORG_ID in .env and pipe the upgrade_id on stdin:
echo 53f10664-3ce8-4c27-b382-0ef66432349f | python MistHelper.py --menu 96
```

## Expected outputs in `data/`

After a successful run with org `11111111-2222-3333-4444-555555555555`
and upgrade `53f10664-3ce8-4c27-b382-0ef66432349f`:

```text
data/
|-- org_device_upgrade_11111111_53f10664.csv                     # 1 summary row
|-- org_device_upgrade_site_details_11111111_53f10664.csv        # N per-site rows
`-- mist_data.db                                                  # SQLite, both tables upserted
```

If the active backend is ArangoDB+Redis, the same two logical entities
land in their respective collections / cache keys; the CSV files are
still emitted as a fallback artifact.

## Method outline (target for implementation)

The Phase 2 task list will implement a method like the sketch below on
`FirmwareUpgradeStatusChecker` (MistHelper.py line 18421). Every
executable line carries an inline comment per Principle VI; logging
brackets every meaningful action per Principle VII.

```python
def export_org_device_upgrade_detail(self, org_id: str, upgrade_id: str) -> None:
    """Fetch one device-upgrade job and persist it to all configured backends."""
    # Validate upgrade_id shape before any network call -- fail fast on typos
    if not UUID_RE.match(upgrade_id):                              # Cheap regex guard
        logging.warning("Invalid upgrade UUID: %s", upgrade_id)    # ASCII-only warning
        return                                                     # Early exit, no API call
    # Log before SDK call so trace shows intent even if the call hangs
    logging.info("Fetching device upgrade detail for org %s upgrade %s", org_id, upgrade_id)
    response = mistapi.api.v1.orgs.devices.upgrade.getOrgDeviceUpgrade(   # The one and only API call
        self.apisession, org_id, upgrade_id                        # Both UUIDs are path params
    )
    upgrade_record = response.data or {}                           # Empty-payload safe access
    logging.debug(                                                 # Post-call summary at DEBUG
        "Upgrade detail: strategy=%s target=%s sites=%d",
        upgrade_record.get("strategy"),
        upgrade_record.get("target_version"),
        len(upgrade_record.get("upgrades", [])),
    )
    summary_row = self._flatten_upgrade_summary(org_id, upgrade_record)   # Build single summary row
    site_rows = self._flatten_upgrade_site_rows(org_id, upgrade_record)   # Build N detail rows
    logging.info("Writing 1 summary row and %d site detail rows", len(site_rows))
    DataExporter.write_with_format_selection(                      # Multi-backend persistence
        [summary_row],
        FilePathUtils.get_csv_path(f"org_device_upgrade_{org_id[:8]}_{upgrade_id[:8]}.csv"),
        api_function_name="getOrgDeviceUpgrade",                   # Drives PK strategy lookup
    )
    DataExporter.write_with_format_selection(                      # Second table for the detail rows
        site_rows,
        FilePathUtils.get_csv_path(
            f"org_device_upgrade_site_details_{org_id[:8]}_{upgrade_id[:8]}.csv"
        ),
        api_function_name="getOrgDeviceUpgrade_site_details",      # Sibling PK strategy entry
    )
```

## Quality gates (MUST all pass before commit)

```powershell
# Syntax check -- silent on success
python -m py_compile MistHelper.py

# Lint -- must report zero issues for changed lines
python -m ruff check MistHelper.py

# Format check -- run without --check to auto-fix if needed
python -m black --check MistHelper.py

# Functional smoke test -- menu 96 lives inside the 90-100 skip cluster,
# so the explicit --menu flag bypasses the test harness skip list.
python MistHelper.py --menu 96
```

Once all four pass, commit via the mandatory deployment pipeline
documented in `.github/copilot-instructions.md` (Step 1 -> Step 6:
validate -> commit -> push -> wait for container build -> pull image
-> restart container -> verify with `podman ps`).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `PermissionError: '/app/data/script.log'` | Container `data/` not writable | `chmod -R 777 data/` on the host before container run |
| `mistapi.APIException 404` | Upgrade job UUID does not exist for this org | Run the sibling list endpoint to confirm the UUID |
| Empty CSV | Upgrade completed and was purged by Mist (>30 day retention) | Expected -- run against a recent upgrade UUID |
| EOFError traceback | `safe_input()` not used somewhere new | Re-check the prompt code; wrap all `input()` in `safe_input()` |
| Duplicate SQLite rows on re-poll | PK strategy entry missing or misnamed | Verify both `getOrgDeviceUpgrade` and `getOrgDeviceUpgrade_site_details` are present in `ENDPOINT_PRIMARY_KEY_STRATEGIES` |
