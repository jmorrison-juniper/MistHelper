# Phase 1 Data Model: 1029-ap-profile-migration

**Date**: 2026-07-27
**Status**: Complete

Two persisted artifacts are added by this feature:

1. A **migration backup file** — one JSON file per migration invocation
   under `data/`, written before the first PUT and updated at end of
   run (or on failure).
2. A **revert audit line** — one JSONL row per revert invocation, appended
   to the existing MistHelper telemetry file via `TelemetryEmitter`.

No schema migration and no database. All entities live in local files
under `data/` only.

---

## 1. Migration backup file

### 1.1 File name

`data/ap-profile-migration_<UTC-timestamp>_<source-profile-id>_to_<target-profile-id>.json`

- `<UTC-timestamp>` is ISO 8601 basic format `YYYYMMDDTHHMMSSZ` (for
  example `20260727T193045Z`). This sorts chronologically as a plain
  string.
- `<source-profile-id>` and `<target-profile-id>` are the full UUIDs of
  the device profiles as returned by Mist.

### 1.2 File format

Single JSON object, UTF-8, `json.dumps(..., indent=2, sort_keys=False)`.

### 1.3 Top-level fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `schema_version` | integer | Yes | Fixed at `1` for this feature. Lets a future revert operation detect an unknown backup format and refuse to proceed. |
| `org_id` | string (UUID) | Yes | The Mist org this migration ran against. Revert refuses if the operator's current org does not match. |
| `migration_timestamp_utc` | string (ISO 8601 extended) | Yes | Wall-clock time of migration start, for example `2026-07-27T19:30:45Z`. Human-readable counterpart to the filename timestamp. |
| `source_profile_id` | string (UUID) | Yes | The profile every AP was bound to before migration. This is the ID the revert PUT-s each AP back to. |
| `target_profile_id` | string (UUID) | Yes | The profile every AP was bound to after migration. |
| `source_profile_snapshot` | object | Yes | Full JSON returned by `mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile(org_id, source_profile_id)` at migration time. Preserves the source profile's complete state (name, radio config, RF template ref, and so on) for future forensic use. |
| `target_profile_snapshot` | object | Yes | Full JSON returned by the same call for the target profile. |
| `aps_planned` | array of `APRecord` | Yes | Ordered list of every AP the migration intended to reassign. Populated once, before the first PUT. |
| `aps_reassigned` | array of string (UUID) | Yes | AP IDs that the migration actually reassigned successfully. Written at end of run. On mid-run failure, contains the partial-success prefix of `aps_planned` up to (but not including) the failed AP. Revert reads this list. |
| `outcome` | string enum | Yes | One of `"success"`, `"partial"`, `"failure"`, `"dry_run"`. `"dry_run"` is set only when the file is written; in practice a dry run writes no file at all (FR-015), so `"dry_run"` is reserved and never appears on disk in v1. |
| `failure_detail` | object or null | Conditional | Set when `outcome == "partial"` or `outcome == "failure"`. See section 1.5. |

### 1.4 `APRecord` shape

Each element of `aps_planned` is an object with these fields:

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `device_id` | string (UUID) | Yes | The AP device UUID. This is the ID PUT via `updateSiteDevice`. |
| `site_id` | string (UUID) | Yes | The site the AP is under. Required because `updateSiteDevice` is a site-scoped endpoint. |
| `mac` | string | Yes | The AP MAC (canonical Mist form, no separators — for example `5c5b350e0001`). Included so the operator can identify the AP in the Mist UI. |
| `hostname` | string or null | No (may be null) | The AP hostname if Mist knows one. Null when the device has never checked in with a name set. |

### 1.5 `failure_detail` shape

Set only on `outcome == "partial"` or `outcome == "failure"`.

| Field | Type | Purpose |
|-------|------|---------|
| `failed_device_id` | string (UUID) | The AP whose PUT ultimately failed after all retries. |
| `failed_site_id` | string (UUID) | The site of the failed AP. |
| `error_message` | string | Short human-readable summary of the API error (for example the last `mistapi` exception `str(exc)`). |
| `reassigned_count` | integer | Length of `aps_reassigned` at the moment of failure — for the summary print. |
| `planned_count` | integer | Length of `aps_planned` — for the summary print. |

### 1.6 Validation rules (used by the revert operation, FR-020)

Every backup file the revert loads must satisfy all these rules. If any
rule fails, the revert prints the offending field name and refuses to
proceed without changing any AP.

1. `schema_version == 1`.
2. `org_id`, `source_profile_id`, `target_profile_id`,
   `migration_timestamp_utc` are non-empty strings.
3. `aps_planned` is a list.
4. Every element of `aps_planned` has non-empty `device_id`, `site_id`,
   and `mac`.
5. `aps_reassigned` is a list of strings; every entry is also present as
   a `device_id` in `aps_planned` (defensive — prevents a hand-edited
   backup from reverting APs that were never in the migration).
6. `source_profile_snapshot.id == source_profile_id` and
   `target_profile_snapshot.id == target_profile_id`.

### 1.7 State transitions

```text
[start] --write pre-PUT snapshot--> aps_planned populated, aps_reassigned = []
        --each successful PUT-----> aps_reassigned.append(device_id)
        --last PUT success--------> outcome = "success"; failure_detail = null
        --PUT failure mid-run-----> outcome = "partial"; failure_detail set;
                                    file re-written with the partial-success
                                    aps_reassigned list
        --backup write fails------> outcome = "failure" (never written to disk;
                                    only used in log lines); no PUT is issued
```

### 1.8 Example (elided)

```json
{
  "schema_version": 1,
  "org_id": "203d3d02-dbc0-4c1b-bc44-13e2d1e1a1ff",
  "migration_timestamp_utc": "2026-07-27T19:30:45Z",
  "source_profile_id": "aaaa1111-2222-3333-4444-555566667777",
  "target_profile_id": "bbbb1111-2222-3333-4444-555566667777",
  "source_profile_snapshot": { "id": "aaaa1111-...", "name": "Data-Transfer-Device-Profile", "type": "ap", "...": "..." },
  "target_profile_snapshot": { "id": "bbbb1111-...", "name": "Main-Device-Profile", "type": "ap", "...": "..." },
  "aps_planned": [
    { "device_id": "5c5b350e-0001-...", "site_id": "site-uuid-1", "mac": "5c5b350e0001", "hostname": "ap-lobby-1" },
    { "device_id": "5c5b350e-0002-...", "site_id": "site-uuid-1", "mac": "5c5b350e0002", "hostname": null }
  ],
  "aps_reassigned": [
    "5c5b350e-0001-...",
    "5c5b350e-0002-..."
  ],
  "outcome": "success",
  "failure_detail": null
}
```

---

## 2. Revert audit line (JSONL)

### 2.1 File location

Appended by the existing `TelemetryEmitter` under `data/`. This feature
does not introduce a new telemetry file; it appends events with a
distinct `event_type` to the existing MistHelper telemetry stream.

### 2.2 Event shape (single JSONL row)

| Field | Type | Purpose |
|-------|------|---------|
| `event_type` | string | Fixed value `"ap_profile_migration_revert"`. |
| `timestamp_utc` | string (ISO 8601 extended) | Wall-clock time of the revert invocation (start). |
| `org_id` | string (UUID) | The Mist org the revert ran against. |
| `backup_file_path` | string | Absolute path to the backup file the revert consumed. |
| `source_profile_id` | string (UUID) | The profile the revert PUT each AP back to. |
| `planned_count` | integer | How many AP IDs the backup listed. |
| `reverted_count` | integer | How many APs were successfully PUT back. |
| `missing_count` | integer | How many listed AP IDs no longer exist in the org (skipped with a warning per FR-023). |
| `failed_count` | integer | How many APs failed the PUT after retries. |
| `outcome` | string enum | One of `"success"`, `"partial"`, `"failure"`. `"partial"` covers the missing-AP-with-warning case in FR-023. |

### 2.3 Example (single line, formatted here for readability)

```json
{
  "event_type": "ap_profile_migration_revert",
  "timestamp_utc": "2026-07-28T09:15:12Z",
  "org_id": "203d3d02-dbc0-4c1b-bc44-13e2d1e1a1ff",
  "backup_file_path": "/repo/data/ap-profile-migration_20260727T193045Z_aaaa..._to_bbbb....json",
  "source_profile_id": "aaaa1111-2222-3333-4444-555566667777",
  "planned_count": 5,
  "reverted_count": 4,
  "missing_count": 1,
  "failed_count": 0,
  "outcome": "partial"
}
```

---

## 3. Entities recap (matches spec `Key Entities` section)

| Entity | Representation |
|--------|----------------|
| Device profile | Full JSON as returned by Mist; embedded in the backup file (`source_profile_snapshot`, `target_profile_snapshot`). |
| AP (Access Point) device | Represented compactly in `aps_planned` as `APRecord` (device_id, site_id, mac, hostname). Full Mist device JSON is not stored — the revert only needs the IDs to PUT. |
| Migration backup | The JSON file described in section 1. |
| Revert audit record | The JSONL row described in section 2. |

---

## 4. Change-set summary

| Kind | Artifact | Location |
|------|----------|----------|
| NEW file (runtime) | one per migration | `data/ap-profile-migration_*.json` |
| APPENDED lines (runtime) | one per revert | existing JSONL via `TelemetryEmitter` |
| NEW committed code | `class APProfileMigrationManager` | `src/device/ap_profile_migration_manager.py` |
| MODIFIED committed code | Two new destructive entries | `src/utils/operation_registry.py` |
| MODIFIED committed code | Menu dispatch for 207 and 208 | `MistHelper.py` |
| NEW committed tests | Unit tests for both handlers | `tests/unit/device/test_ap_profile_migration_manager.py` |

No schema migration, no database, no new top-level package, no new
third-party dependency.
