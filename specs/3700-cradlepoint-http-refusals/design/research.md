# Research: Cradlepoint HTTP refusals

## Decision 1: Use the transport status

The installed SDK constructor copies `requests.Response.status_code` without
discarding decoded dictionaries for HTTP refusals.
Its `APIResponse(None, url)` keeps `status_code=None` and `data={}`.
Neither dictionary data nor an empty dictionary proves success.

Read `status_code` before reading `data`.
Require a real integer in the standard HTTP range.
Accept only HTTP `200` through `299`.
Name absent or unusable status as an unavailable transport status.

## Decision 2: Keep the existing failure boundary

The menu method already catches failures and prints an error notice.
Raise a bounded `RuntimeError` that contains only the operation and safe status context.
The menu then stops before `_build_row` and `_persist`.

Do not add another exception class or restructure the menu method.

## Decision 3: Preserve payload semantics

A successful HTTP `200` can contain a nonempty integration `error` field.
The installed SDK itself can report that field through its diagnostic logger.
MistHelper must still export that valid integration status.
Do not interpret error text as HTTP failure.

Empty and non-dictionary successful bodies retain the existing empty-result behavior.
Malformed-JSON policy does not change.

## Decision 4: Reject unsuitable shared helpers

Existing export status helpers substitute `200` for missing or unusable statuses.
That policy conflicts with FR-003.
The insight refusal helper also extracts and logs body text.
That behavior conflicts with this issue's secret-free diagnostic boundary.

`src/api/response_integrity.py` checks silent body parse failures.
It does not establish HTTP success and remains unchanged.

## Decision 5: Measure real callbacks

Use native SDK responses from controlled `requests.Response` values.
Replace only the endpoint, transport boundary, organization selector, and shared writer.
Use the Python profiling callback to count real row and persistence method calls.
Do not replace those production methods.

The transport mock raises if any live request occurs.
Each test prints checked-case and callback counts.
