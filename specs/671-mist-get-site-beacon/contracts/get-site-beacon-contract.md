# Contract: getSiteBeacon Menu Operation

## Operation Identity

- **Issue**: #1420
- **Spec**: `/specs/671-mist-get-site-beacon/spec.md`
- **operationId**: `getSiteBeacon`
- **SDK Method**: `mistapi.api.v1.sites.beacons.getSiteBeacon`
- **HTTP Path**: `GET /api/v1/sites/{site_id}/beacons/{beacon_id}`

## Inputs

### Required

- `site_id` (string UUID)
- `beacon_id` (string UUID)

### Input acquisition contract

- All prompts must use `safe_input()`.
- EOF/interrupt must not raise traceback; operation exits cleanly.
- Empty/invalid values must be validated before API call when possible.

## Execution Contract

1. Log `INFO` before API invocation.
2. Call `getSiteBeacon` exactly once for one validated `(site_id, beacon_id)` pair.
3. On success, normalize payload to list form for exporter compatibility.
4. Log `DEBUG` with row/count summary after response handling.

## Persistence Contract

- Must call:
  - `DataExporter.write_with_format_selection(data, filename, api_function_name='getSiteBeacon')`
- Backend expectations:
  - CSV output under `data/`
  - SQLite upsert using `ENDPOINT_PRIMARY_KEY_STRATEGIES['getSiteBeacon']`
  - ArangoDB/Redis routing enabled when configured

## Error Contract

- 404 and other API errors: surfaced as structured logs/warnings, no traceback crash.
- 429: adaptive rate-limit handling engaged per existing delay metrics and retry system.

## Documentation Contract

Implementation PR for this issue must also update:
- README menu table (new operation entry + count)
- CHANGELOG entry
- Endpoint key strategy registry with `getSiteBeacon`
