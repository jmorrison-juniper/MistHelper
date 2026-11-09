# Offline SDK inspection

## Decision

Retain a broad catch only around the endpoint and pagination calls.
Do not classify a local transform or writer error as a cloud failure.
Do not include arbitrary exception text, exception arguments, or tracebacks in exporter logs.

## Evidence

The installed distribution is mistapi 0.64.1.
Paths below are relative to its installed `mistapi` package.

- `api/v1/sites/otherdevices.py`: `searchSiteOtherDeviceEvents` delegates to `mist_session.mist_get`.
- `__api_session.py`: `APISession` inherits `APIRequest` and does not override `mist_get`.
- `__api_request.py`: `mist_get` builds the URL and calls `_request_with_retry`.
  The retry wrapper catches requests transport exceptions and HTTP errors.
  It returns `APIResponse`, including after a transport failure.
- `__api_response.py`: `APIResponse` preserves status and response data.
  It catches response-decoding exceptions internally.
- `__pagination.py`: `get_all` calls `get_next`, which calls `mist_get` for subsequent pages.
  It directly indexes `response.data["results"]` on subsequent search pages.
  A malformed follow-up page can therefore raise `KeyError`.

No common SDK exception base covers that complete path.
A transport-only exception tuple would lose the existing malformed-page fallback.
The retained catch documents this boundary rather than a guessed taxonomy.

## Alternatives considered

- Remove the catch: rejected because malformed remote pages can raise from pagination.
- Catch requests exceptions only: rejected because the SDK already consumes these and pagination has different failure types.
- Keep persistence inside the catch: rejected because it hides local defects.
- Log exception class or text: unnecessary for the fixed operator fallback and unsafe for arbitrary private text.

## Separate response-status finding

`get_all` does not inspect `status_code`.
An HTTP 403 or 503 response with an error dictionary and no results becomes an empty list.
The exporter then reports no event data.
This behavior predates the repair and remains unchanged.
Offline tests record it explicitly without claiming that the request succeeded.

The SDK itself logs transport exception text.
This slice does not change third-party logging. Privacy assertions concern exporter-generated log records.
