# Contract: RF Diagnostics Package

## Purpose

This contract defines the planned interface for `src/troubleshooting/rf_diagnostics`. It also records the Mist API request and response shapes that tests must enforce.

## Package entry contract

The package exposes one operation class for menu wiring later:

```text
RfDiagnosticsOperation.run()
```

**Inputs**:

- An API session or client dependency.
- A safe input callable.
- A wait dependency for recording mode.
- A base data directory dependency, defaulting to `data/`.
- A clock dependency for run times and file names.

**Outputs**:

- Printed ASCII outcome text for the operator.
- One row appended to `data/RfDiagnostics.csv` for each run attempt.
- A file under `data/rfdiags/` for each successful recording download.

**Failure behavior**:

- Enter or any answer other than `y` cancels before remote action.
- Ctrl+C during recording wait requests stop before return.
- A failed stop produces a failed run and no success message.
- Empty download bytes produce a failed run and no saved-path success message.
- Secret values must not appear in output, logs, or audit rows.
- Action logs must include stable fields in the message or arguments, such as mode, site, target, status, byte count, or attempt count.

## Spectrum start contract

**Mist endpoint**: `POST /api/v1/sites/{site_id}/analyze_spectrum`

**Path parameters**:

- `site_id`: Required Mist site identifier.

**Request body schema**: `spectrum_analysis`

**Request body fields**:

- `band`: Required.
- `device_id`: Optional AP device identifier.
- `duration`: Optional duration.
- `format`: Optional output format.

**Success response**: HTTP 200 with `websocket_session` schema. The response includes `session`.

**Unit test obligations**:

- Assert that `band` is present.
- Assert that `device_id` is present when an AP was selected.
- Assert that no unrelated body fields are sent.
- Assert that the call happens only after explicit `y` confirmation.

## Spectrum running-state contract

**Mist endpoint**: `GET /api/v1/sites/{site_id}/analyze_spectrum`

**Path parameters**:

- `site_id`: Required Mist site identifier.

**Request body**: None.

**Success response**: HTTP 200 with `response_running_spectrum_analysis` schema. Fields can include `band`, `device_id`, `duration`, `format`, and `started_time`.

**SDK note**: The SDK lacks this function. Use `apisession.mist_get('/api/v1/sites/{site_id}/analyze_spectrum')` or an equivalent API-session method inside the RF diagnostics client.

**Terminal states**:

- `running`, `started`, `in_progress`, and `active` mean the scan is still running.
- `failed`, `failure`, and `error` mean the scan finished with failure.
- A payload with another status, a missing status, or a result object means the scan is final.
- Poll exhaustion means timeout.

**Unit test obligations**:

- Assert that the GET call has no body.
- Assert that polling stops at a final state or the poll limit.
- Assert that a timeout prints a clear failure.

## Recording start contract

**SDK method**: `mistapi.api.v1.sites.rfdiags.startSiteRecording`

**Mist endpoint**: `POST /api/v1/sites/{site_id}/rfdiags`

**Request body fields**:

- `name`: Required.
- `type`: Required.
- `duration`: Optional.
- `mac`: Optional client MAC.
- `sdkclient_id`: Optional.

**Unit test obligations**:

- Assert that `name` and `type` are present.
- Assert that `mac` uses the normalized client MAC when supplied.
- Assert that the call happens only after explicit `y` confirmation.

## Recording stop contract

**SDK method**: `mistapi.api.v1.sites.rfdiags.stopSiteRfdiagRecording`

**Mist endpoint**: `POST /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/stop`

**Request body**: No feature-specific body fields are required by this plan.

**Unit test obligations**:

- Assert that stop is requested after a normal wait.
- Assert that stop is requested after Ctrl+C interrupts the wait.
- Assert that download does not run when stop fails.

## Recording download contract

**SDK method**: `mistapi.api.v1.sites.rfdiags.downloadSiteRfdiagRecording`

**Mist endpoint**: `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download`

**Response**: Download bytes.

**Unit test obligations**:

- Assert that bytes are written under `data/rfdiags/`.
- Assert that file names include site, client MAC, and run time in safe form.
- Assert that empty bytes are treated as failure.

## Recording get and list contract

**Get SDK method**: `mistapi.api.v1.sites.rfdiags.getSiteRfdiagRecording`

**Get endpoint**: `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}`

**List discrepancy**: The assignment names `listSiteRfdiagRecording`, but OpenAPI and the SDK expose `getSiteSiteRfdiagRecording` at `GET /api/v1/sites/{site_id}/rfdiags` with `start`, `end`, `duration`, `limit`, and `page` query parameters. Use the actual OpenAPI and SDK name if listing is needed.
