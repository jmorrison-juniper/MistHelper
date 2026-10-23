# Research: WAN Probe Response Status

## Decision

Check the SDK response status before accessing `data`, and accept the configuration only when the status is HTTP 200.

## Evidence

- The installed `mistapi` 0.64.1 `APIResponse` stores `status_code` independently from `data`.
- Its initializer parses the body even when the status is 400 or higher. Therefore, plausible `port_config` data does not prove that Mist accepted the request.
- Existing code checks for HTTP 200 after the device update. The same success status applies to the configuration read.
- Merged PR #4383 tests HTTP 403 on the write response. It does not test a refused device configuration read.

## Alternatives Considered

- **Trust the parsed body**: Rejected because the SDK parses bodies for error responses.
- **Treat a missing status as success**: Rejected because the SDK response contract supplies a status and an absent status cannot establish success.
- **Raise an exception for a non-200 status**: Rejected because the operation already reports Mist status failures as a `FAILED` result. SDK exceptions remain on the existing `ERROR` path.

## Safety

All response tests use local `requests.Response` objects and the SDK response wrapper. They make no network request.
