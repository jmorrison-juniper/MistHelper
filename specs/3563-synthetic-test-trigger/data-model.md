# Data Model: Synthetic Test Trigger

## SyntheticTestRequest

- `scope`: one of `site`, `device`, or `radius`.
- `site_id`: selected Mist site identifier.
- `device_id`: selected Mist device identifier for device and RADIUS scopes.
- `body`: OpenAPI-compliant request body.
- `summary`: non-secret request values for logs and export.
- `poll_filter`: site search filters or the selected device identifier.

Validation rules:

- Site scope uses only the optional `email` field.
- Device scope requires `type` and includes only fields that hold non-empty answers.
- RADIUS scope requires `user` and `password`, and defaults `profile` to `dot1x`.
- The password never appears in `summary` or `poll_filter`.

## SyntheticTestResult

- `status`: returned status or `timeout`.
- `failed`: boolean result when the API returns it.
- `reason`: returned failure reason or timeout message.
- `latency`, `rx_mbps`, `tx_mbps`: optional numeric measurements.
- `timestamp`: returned epoch timestamp.
- `raw`: safe normalized result dictionary.

State transitions:

1. `pending`: the trigger was accepted or scheduled.
2. `complete`: a poll returned a result that is not in progress.
3. `timeout`: no complete result arrived before the timeout.

## ExportRow

- Combines `SyntheticTestRequest.summary` and `SyntheticTestResult.raw`.
- Includes `site_id`, `scope`, `device_id`, `test_type`, `status`, `failed`, `reason`, and timing fields.
- Excludes `password`, `secret`, `token`, and equivalent credential fields.
