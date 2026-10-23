# Research

## Decision

Read `response.status_code` before reading `response.data`.
Raise `RuntimeError` for an integer status outside 200 through 299.

## Rationale

The installed `mistapi.__api_response.APIResponse` stores the HTTP status and parsed JSON independently.
Its constructor logs error responses but does not raise them.
`getSiteBeacon` returns the session response unchanged.
The current main branch normalizes an error mapping into one export row.
The baseline test module passes 22 tests but does not exercise a returned error status.

## Alternatives considered

The shared `http_failure` helper logs a failure and returns a boolean.
It does not raise the runtime error required by the existing adaptive retry procedure.
Body-text checks cannot distinguish valid data from an error and do not follow the SDK contract.
New retry abstractions would expand this repair without a functional need.

## Resources

- Issue #4028 and its sanitized image confirm that a 404 produces a successful row.
- The issue has no comments. Its artifacts endpoint returns HTTP 404.
- Local SDK source supplies the response contract without a cloud request.
