# Data Model: getSiteBeacon

## 1) BeaconLookupRequest

Represents validated operator input before SDK invocation.

- `org_id` (string, required when org-scoped prompt flow is used)
- `site_id` (UUID string, required)
- `beacon_id` (UUID string, required)
- `invoked_operation` (string, fixed: `getSiteBeacon`)
- `requested_at_epoch` (number, generated)

### Validation Rules

- `site_id` and `beacon_id` must be non-empty after `safe_input().strip()`.
- Reject obvious invalid UUID syntax early when validator exists; otherwise rely on API 404 and log warning.
- EOF/interrupt from `safe_input()` returns default/empty and exits operation cleanly with status 0.

## 2) SiteBeaconRecord

Canonical output record from Mist API response (`GET /sites/{site_id}/beacons/{beacon_id}`).

Core fields (expected):
- `id` (UUID, read-only, natural primary key)
- `site_id` (UUID, read-only)
- `org_id` (UUID, read-only)
- `map_id` (UUID, optional)
- `name` (string)
- `type` (enum-like string: `eddystone-uid` | `eddystone-url` | `ibeacon`)
- `mac` (string, optional)
- `x`, `y` (number, optional position)
- `power` (int, dBm)
- `ibeacon_uuid`, `ibeacon_major`, `ibeacon_minor` (nullable beacon profile fields)
- `eddystone_namespace`, `eddystone_instance`, `eddystone_url` (nullable beacon profile fields)
- `created_time`, `modified_time` (epoch numbers)
- `for_site` (boolean)

### Validation Rules

- `id` must exist for persistence/upsert.
- Numeric fields (`x`, `y`, `power`, epoch values) must remain numeric after flattening.
- Nullables must remain nullable; do not coerce null to placeholder strings.

## 3) ExportEnvelope

Normalized payload passed to exporter and backend router.

- `records` (list[SiteBeaconRecord], usually length 1)
- `api_function_name` (string, fixed: `getSiteBeacon`)
- `filename_or_table` (string target for CSV/SQLite)
- `raw_data` (optional original payload for polyglot routing)

### Persistence Behavior

- CSV: append/write operation-specific file in `data/`.
- SQLite: upsert using `ENDPOINT_PRIMARY_KEY_STRATEGIES['getSiteBeacon']` (`natural_pk` on `id`).
- ArangoDB/Redis (if enabled): routed through `DatabaseRouter` with same API function name.

## Relationships

- `BeaconLookupRequest (1)` -> `(0..1) SiteBeaconRecord`
- `SiteBeaconRecord (1)` -> `(1) ExportEnvelope` during successful run

## State Transitions

1. `InputPending` -> `InputValidated`
2. `InputValidated` -> `ApiRequested`
3. `ApiRequested` -> `ApiSucceeded` | `ApiNotFound` | `ApiRateLimited` | `ApiError`
4. `ApiSucceeded` -> `Exported`
5. `ApiNotFound`/`ApiRateLimited`/`ApiError` -> `LoggedAndExitedCleanly`
