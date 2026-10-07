# Contract: Menu 209 Response Classification

## Purpose

This contract defines how menu 209 classifies the native
`getSiteBeacon` response. It does not change the Mist API method, menu
registration, prompts, export identity, or storage backends.

## Input Contract

The operation calls:

```text
mistapi.api.v1.sites.beacons.getSiteBeacon(
    apisession,
    site_id=<validated site identifier>,
    beacon_id=<validated beacon identifier>,
)
```

The response can expose:

- `status_code`
- `url`
- `data`

The operation must inspect only `status_code` first. It can inspect `url` only
for a failed integer status. It must not inspect `data` during classification.

## Classification Contract

### Integer HTTP failure

If `status_code` is an integer outside 200-299:

1. Classify the operation as failed.
2. Do not call `_normalize_site_beacon_payload`.
3. Do not build an export filename.
4. Do not call `DataExporter.write_with_format_selection`.
5. Read `url`, with `the requested path` as the fallback when it is absent.
6. Emit exactly
   `! Error fetching site beacon detail: HTTP <status> from <url>`.
7. Do not read, normalize, format, or log the response body.

Example:

`! Error fetching site beacon detail: HTTP 404 from https://api.mist.com/api/v1/sites/site-id/beacons/beacon-id`

### Readable successful status

If `status_code` is an integer from 200 through 299:

1. Read `data`.
2. Use the existing payload normalizer.
3. Preserve the existing export and no-data branches.

Any body shape with HTTP 2xx remains successful input because the native
status is authoritative.

### Missing or non-integer status

If `status_code` is absent or is not an integer:

1. Preserve the current compatibility behavior.
2. Use `response.data` when the response exposes it.
3. Otherwise, use the response value as the payload.
4. Preserve existing normalization and exception behavior.

## Retry Contract

### Exception-based HTTP 429

If the SDK raises `RuntimeError` and the exception text contains `429`:

1. Preserve the existing retry limit.
2. Preserve adaptive delay calculation.
3. Preserve sleep behavior.
4. Preserve the first-error rule.
5. Export only after a later successful response.

### Native HTTP 429 response

If the SDK returns a response whose `status_code` is 429:

1. Treat it as a terminal HTTP failure.
2. Do not call the adaptive delay helper.
3. Do not sleep.
4. Do not retry.
5. Do not export.

## Response Body Boundary

The classification gate must not inspect or log:

- `response.data`
- `data["detail"]`
- The complete response object
- The complete response payload
- Headers
- Request data
- Session data
- Tokens
- Authorization data

## Success Compatibility Contract

For a successful dictionary payload:

- Export exactly one normalized row.
- Keep `api_function_name="getSiteBeacon"`.
- Keep the natural primary key `id`.
- Keep `SiteBeacon_<site_id>_<beacon_id>.csv`.

For a successful empty payload:

- Report the existing no-data result.
- Do not call the exporter.
- Do not create an artifact.

## Verification Matrix

| Case | Status | Payload or exception | Expected result |
| - | - | - | - |
| Missing beacon | 404 | Any body, including an inaccessible body | Exact failure line. No body access or export. |
| Server failure | 500 | Any body | Exact failure line. No normalization or export. |
| Native rate limit | 429 | Any payload | Failure. No retry and no export. |
| Redirect | 302 | Any payload | Failure. No normalization or export. |
| Informational status | 199 | Any payload | Failure. No normalization or export. |
| Exception rate limit | N/A | `RuntimeError("429 ...")` | Existing adaptive retry path |
| Successful beacon | 200 | Beacon dictionary | One unchanged export call |
| Successful empty | 200 | `None` | Existing no-data result |
| Status unavailable | Absent | Beacon dictionary | Existing compatibility path |
| Non-integer status | `"404"` | Beacon dictionary | Existing compatibility path |

## Ownership Contract

The implementation must add the canonical local gate shape inside
`site_client_exporter.py`. It must not edit
`simple_endpoint_exporter.py` while PR #4068 is open.
