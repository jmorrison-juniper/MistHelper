# Research: Menu 209 HTTP Error Handling

## Decision: Treat the native HTTP status as authoritative

**Decision**: Read `response.status_code` immediately after
`getSiteBeacon` returns. Treat 200-299 as success. Treat an absent or
non-integer status as compatibility success. Reject every other integer
status before payload normalization.

**Rationale**: The SDK can return an error-shaped dictionary in
`response.data`. The current code unwraps that dictionary and exports it as a
valid beacon row. The status identifies whether the payload is beacon data or
an error body.

**Alternatives considered**:

- Detect error keys in the dictionary. Rejected because an HTTP 2xx beacon
  dictionary can contain arbitrary fields. The specification makes the native
  status authoritative.
- Treat only HTTP 4xx and 5xx as failure. Rejected because the canonical gate
  accepts only 200-299 and rejects every other integer status.
- Change the SDK call. Rejected because `getSiteBeacon` is the required and
  working Mist SDK method.

## Decision: Read payload data only after status classification

**Decision**: Inspect `status_code` before the first read of
`response.data`. For a failed status, do not read the payload. For a 2xx,
absent, or non-integer status, preserve current payload normalization.

**Rationale**: This order prevents an error body from entering the normalizer.
It also meets the requirement that the native status remain available until
classification is complete.

**Alternatives considered**:

- Unwrap `response.data`, then inspect the status. Rejected because this keeps
  the defect-prone order.
- Normalize and discard rows after status inspection. Rejected because the
  failure must not enter normalization.
- Require every response double to expose a status. Rejected because current
  tests and compatibility paths can return a dictionary or an object without
  a readable status.

## Decision: Never inspect or log the response body during classification

**Decision**: Read only `status_code` and `url` during classification. Use
`the requested path` when the URL is absent. Emit exactly
`! Error fetching site beacon detail: HTTP <status> from <url>`.

**Rationale**: The response body is irrelevant to status classification. The
exact line gives the portal classifier a stable failure signal without
exposing or depending on body content.

**Alternatives considered**:

- Include `data["detail"]`. Rejected because the user-directed correction
  prohibits body inspection and makes the 404 body shape irrelevant.
- Include the complete response body. Rejected because the body can contain
  sensitive or excessive data.
- Use different text for each status. Rejected because the portal classifier
  requires one exact operator-facing shape.

## Decision: Use the PR #4068 local boolean gate shape

**Decision**: Add the same local gate shape used by PR #4068 inside
`SiteClientExporter`. Return `False` for 2xx, absent, or non-integer status.
Log the exact failure line and return `True` for every other integer status.

**Rationale**: This keeps native HTTP classification separate from exception
classification. It also prevents a native 429 from entering the
exception-based retry path.

**Alternatives considered**:

- Raise `RuntimeError`. Rejected because text that contains `429` can enter
  the existing exception retry path.
- Reuse or edit `SimpleEndpointExporter`. Rejected because PR #4068 is open
  and the issue requires an identical local gate in `site_client_exporter.py`.
- Add a new result dataclass. Rejected because this defect needs no new
  cross-module state.

## Decision: Keep exception-based 429 retry behavior unchanged

**Decision**: Preserve the current `except RuntimeError` logic. A thrown error
that contains `429` uses the existing bounded adaptive retry. A completed native response with status 429 fails through the local boolean
gate without retry.

**Rationale**: The specification distinguishes transport or SDK exceptions
from native HTTP responses. The existing adaptive retry contract applies only
to exceptions. Moving native status classification into the `try` block does
not require changes to the retry branch.

**Alternatives considered**:

- Retry native HTTP 429 responses. Rejected because the requirement preserves
  exception-based retry behavior and classifies each native integer status
  outside 200-299 as failure.
- Remove retries. Rejected because this would change established behavior.
- Raise a message that contains `429` for a native response. Rejected because
  the design must keep native 429 outside the exception retry branch.

## Decision: Extend the existing focused unit test class

**Decision**: Add response-status regressions to `TestGetSiteBeacon` in
`tests/unit/export/test_site_client_exporter.py`. Keep the existing menu wiring
integration test unchanged.

**Rationale**: The defect is local to response classification. The current unit
fixture already controls the SDK call, retry helper, sleep, prompts, and
exporter. It can prove the exact ordering and side-effect contract without a
live network.

**Alternatives considered**:

- Add browser or end-to-end tests. Rejected because no portal or browser
  behavior changes.
- Add live Mist tests. Rejected because tests must not use production
  credentials.
- Create a broad new test module. Rejected because the existing test class is
  the narrow owner of this behavior.

## Decision: Preserve all successful identities

**Decision**: Keep `api_function_name="getSiteBeacon"`, the natural primary key
on `id`, and `SiteBeacon_<site_id>_<beacon_id>.csv`.

**Rationale**: The defect affects only error classification. Successful export
identity and storage behavior already meet the specification.

**Alternatives considered**:

- Change the filename or primary key. Rejected because both are explicit
  compatibility requirements.
- Move successful normalization into a new module. Rejected because it widens
  the change with no defect benefit.

## Decision: Do not edit the open PR #4068 implementation

**Decision**: Do not edit
`src/operations/exporting/export/simple_endpoint_exporter.py`. Copy only the
canonical classification shape into the menu 209 owner during implementation.

**Rationale**: PR #4068 still owns the shared exporter file. A second branch
must not overlap that open pull request.

**Alternatives considered**:

- Move the helper into shared code. Rejected because it creates an open pull
  request conflict and widens the issue.
- Wait for PR #4068 to merge. Rejected because the local design can use the
  same contract without changing the owned file.

## Clarification Result

All technical questions have a selected design. No clarification remains.
