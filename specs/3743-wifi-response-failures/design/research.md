# Research: WiFi response failures

## Native Response Boundary

**Decision**: Read status and body evidence before accepting records.

**Rationale**: Native `APIResponse` starts with `data = {}` and `status_code = None`.
Its constructor catches parse errors.
An empty or malformed HTTP 200 body therefore retains an empty parsed object.
The object preserves the raw body in `raw_data`.

The constructor also retains actual HTTP refusal statuses.
The current exporter never checks them.

**Alternatives considered**: A status check alone cannot identify malformed HTTP 200 data.
An empty-results check cannot distinguish a failed response from a valid empty response.

## Native Pagination Boundary

**Decision**: Use `mistapi.get_next` and validate each returned page.

**Rationale**: Native `get_all` copies list bodies or a search body's `results`.
It appends later pages without a status check.
It can silently accept refused pages that contain an empty `results` array.
Checking only the first page cannot prevent that loss.

Native `get_next` passes the current response's `next` link to `mist_get`.
The response builds that link from a search body or page headers.
The repair keeps this SDK behavior and record order.

**Alternatives considered**: An aggregate count check misses losses without totals.
A guarded first-page proxy leaves later responses unchecked.
An endpoint-family migration exceeds the reserved scope.

## Existing Parse Helper

**Decision**: Reuse `ResponseIntegrityChecker.body_failed_to_parse` for retained malformed-body evidence.

**Rationale**: This existing helper avoids exposing body contents.
Empty-body and record-shape checks still belong at the WiFi boundary.
The helper remains read-only.

## Shipped Handler and Output

**Decision**: Drive the imported `SiteClientExporter.wifi_clients` handler through native controlled SDK transport.

**Rationale**: Menu 64 registers that handler.
The handler constructs the actual exporter and supplies the shipped collaborators.
The tests retain real site selection, record processing, and final CSV writes.

The empty-data placeholder bypasses `DataExporter`.
The complete-record path uses `DataExporter.write_with_format_selection`.
Both paths must remain inaccessible after a response failure.

The existing filename is `SiteWiFiClients.CSV`.
The unchanged final writer can append a lowercase suffix.
Tests observe that filename diagnostically, not as desired behavior.

## Local Workflow

**Decision**: Use the app-created branch and feature-only SpecKit artifacts.

**Rationale**: The feature hook requires branch switching.
The standard context hooks write shared `.specify` state.
The user prohibits both actions.
Current templates remain the source for the feature artifacts.

The normal bootstrap failed during the copied interpreter's `ensurepip` process.
The documented UV recovery created only this worktree's ignored environment.
The second normal bootstrap installed unchanged runtime and development requirements.

## Detector Evidence

**Decision**: Call the imported actual handler directly in each native test.

**Rationale**: The pinned detector follows imported source aliases, not fixture-object methods.
Real literal statuses or `status_code` parameters reach the transport.
Forced native analysis must report discovered and analyzed counts separately.
Static classification never replaces red and green runtime proof.

The final read-only classification checks sixteen source-driving native test functions.
The coverage slice is nonempty and credits all six failure modes.
The applicability model requires HTTP status cases only.
The SDK catches network exceptions and parses JSON internally.
Independent native runtime proof covers those failures despite that applicability limit.
