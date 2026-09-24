# Implementation Plan: Multi-site device table and version check

**Issue**: #3249
**Spec**: [spec.md](./spec.md)

## Summary

The portal layer builds one row for each device and decides which sites need a running version read. The aggregate service stores the readings, the target records of the access point child, and the time of each change. The template and the browser script show the rows.

## Technical context

- Python 3.13, Flask, Jinja, and the existing `portal.js`. The change adds no dependency.
- The running version reader is `RunningFirmwareVersionResolver.fetch_site_running_versions` in `src/firmware/running_version.py`.
- The version rule is `version_outcome` in `src/upgrade_portal/upgrade/gate.py`.
- The age rule is `RunStalePolicy` in `src/upgrade_portal/api/run_controls/views.py`.

## Design decisions

### D1. The portal decides, and the service stores

The firmware layer never imports the portal package, and the version rule lives in the portal. A read decision inside the service would need a second copy of the rule, or an injected rule. The plan therefore puts the decision in a new portal module. The service receives one public method that stores the readings through its bounded compare-and-set loop.

### D2. The readings live on the operation record

The service replaces a whole child on every status read. A reading inside a child could therefore disappear when two tabs poll at the same moment. The plan stores the readings in two operation fields that no child write touches.

- `device_versions` maps a MAC address to `{"version", "read_at", "reads"}`.
- `versions_final` lists the child identifiers that received their final read.

### D3. The access point child stores target records

The site children already store `targets`. The access point child now stores the same records. The service never rebuilds a plan from the access point child, so the new field cannot break a submit, a status read, or a cancel. A record from an earlier release falls back to `target_ids`.

### D4. The service writes `updated_at` only on a change

`_cas` compares the candidate with the current record. It writes `updated_at` only when the two differ. A poll of a finished operation therefore keeps its time. The route helper `_cas_operation` follows the same rule, and a new record starts with `updated_at`.

### D5. One seam for the version reader

The route reads the reader from the configuration key `ORG_DEVICE_VERSION_READER`. The default reader calls the running version resolver. The contract tests and the browser tests install a stand-in, so no test opens a socket.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/upgrade/org_devices.py` | New. `CloudTargetLists`, `StoredReadings`, `OrgChildDevices`, and `OrgDeviceRows`. These classes build one row for each device and make no cloud call. |
| `src/upgrade_portal/upgrade/org_versions.py` | New. `VersionReadResult`, `ReadPlan`, and `OrgVersionRefresh`. These classes decide which sites need a running version read, and they read each site one time. |
| `src/firmware/aggregate_upgrade_service.py` | The access point child stores `targets`. The record stores `site_names` and `updated_at`. `_cas` writes `updated_at` on a change. A new public method `record_device_versions`. |
| `src/upgrade_portal/app/routes/org_upgrade.py` | The summary carries the rows, the account, the address, and the time. The refresh reads the versions. The submit stores the operator. |
| `src/upgrade_portal/app/assets/templates/upgrade/org_progress.html` | The device table, the account, the address, and the age. |
| `src/upgrade_portal/app/assets/static/js/portal.js` | `paintOrgUpgradeDevices` and the age repaint. |
| `tests/e2e/upgrade_portal/conftest.py` | The stand-in lists real MAC addresses, the second site holds its own addresses, and a stand-in version reader answers each site. |

## Test plan

- Unit: `tests/unit/upgrade_portal/test_org_devices.py` covers the state order, the failure reason, the fallback rows, the version check, and the read budget.
- Unit: `tests/unit/firmware/test_aggregate_upgrade_service.py` covers the access point target records, `record_device_versions`, and the `updated_at` rule.
- Contract: `tests/contract/upgrade_portal/test_org_upgrade_routes.py` covers the page, the poll answer, and the operator record.
- Browser: `tests/e2e/upgrade_portal/test_org_upgrade_flow.py` checks the device table, the version check, and the account.

## Risks

- A stats read costs quota. The read budget in the spec bounds the calls for each device.
- A failed read stores no reading, so the next refresh reads the site again. The browser stops the poll when the operation ends, so this retry stops too.
- The stats answer can lag behind the cloud job. The third read case of the budget repairs a false mismatch while the child runs.
