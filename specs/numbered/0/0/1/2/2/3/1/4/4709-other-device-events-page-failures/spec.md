# Feature Specification: Other-Device Event Export Fails Closed on Failed Pages

**Feature Branch**: `fix/4709-other-device-events-page-failures`

**Record Folder**: `specs\numbered\0\0\1\2\2\3\1\4\4709-other-device-events-page-failures`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4709, "Runtime: site other-device event export reports failed pages as complete"

**Input**: GitHub issue #4709 (state OPEN, labels `bug`, `tests`, `in-progress`), read on 2026-11-26.

## Context

Menu 258 exports other-device events for one selected site. The exporter calls `mistapi.get_all`. That call does not check the HTTP status of each page. A failed first page becomes an empty result, and the menu prints the no-data message. A failed later page on the documented list shape adds no rows, and the menu writes the first page as a complete export. A failed later page on the documented dict shape raises an error with no file, and its message names no HTTP status.

Warning: an operator can take an incomplete export for a complete record. The current code can cause this loss with no error message.

The #1794 owner retains the exporter file for another local repair. Source edits wait for a file-scoped handoff. See research.md, decision D-2.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop a partial export when a later page fails (Priority: P1)

An operator selects menu 258. Page 1 succeeds. Page 2 fails with HTTP 503 and an empty body. The menu reports a failure and writes no file.

**Why this priority**: The current code writes partial rows and reports a completed export. The defect has severity high, because it can hide a real failure.

**Independent Test**: Mock the first search response with a `next` value. Mock `mistapi.get_next` to return HTTP 503 with an empty body. Run the menu operation. Verify no writer call and one ERROR line that names page 2.

**Acceptance Scenarios**:

1. **Given** page 1 returns one row and a `next` value, **When** page 2 returns HTTP 503 with an empty body, **Then** the menu logs an ERROR line, writes no file, and returns to the menu loop.
2. **Given** page 1 returns HTTP 200, **When** page 2 returns malformed JSON, **Then** the menu writes no file and logs an ERROR line.

### User Story 2 - Report a failed first page as a failure (Priority: P1)

An operator selects menu 258. The first response returns HTTP 403 or HTTP 503 with a JSON error. The menu reports the HTTP failure and prints no no-data message.

**Why this priority**: The current code prints "No other-device event data found for this site" for a failed request. The operator then believes that the site has no events.

**Independent Test**: Mock the first response with status 403 and a JSON error body. Run the menu operation. Verify no no-data message and one ERROR line that names HTTP 403.

**Acceptance Scenarios**:

1. **Given** the first response returns HTTP 403, **When** the menu runs, **Then** it logs an ERROR line with HTTP 403 and prints no no-data message.
2. **Given** the first response returns HTTP 503, **When** the menu runs, **Then** it logs an ERROR line with HTTP 503 and writes no file.

### User Story 3 - Keep the no-data result for a complete empty read (Priority: P2)

An operator selects menu 258 for a site with no events. The response returns HTTP 200, zero rows, and `total` 0. The menu prints the no-data message and writes no file.

**Why this priority**: A complete empty result is valid. This change must keep that result.

**Independent Test**: Mock a 200 response with `results` set to an empty list, `total` set to 0, and no `next` value. Verify the no-data message and no writer call.

**Acceptance Scenarios**:

1. **Given** the first response returns HTTP 200 with zero rows and `total` 0, **When** the menu runs, **Then** it prints the no-data message and writes no file.

### User Story 4 - Write one complete export when every page passes (Priority: P2)

An operator selects menu 258. Two pages return HTTP 200. The rows total two. The menu writes one file that holds both rows.

**Why this priority**: The success path must keep working after this change.

**Independent Test**: Mock two 200 pages with `total` 2. Verify one writer call with two rows and `api_function_name` set to `searchSiteOtherDeviceEvents`.

**Acceptance Scenarios**:

1. **Given** page 1 has one row and a `next` value, **When** page 2 has one row and no `next` value, **Then** the writer runs once with two rows.

### Edge Cases

- The response has no integer status because of a transport failure. The menu treats the page as failed (FR-003).
- The response returns HTTP 404 for an unknown site. The menu logs an ERROR line and does not raise (FR-014, C-2).
- A 2xx body is not an object with a list `results`. The menu rejects the page (FR-004).
- A row in `results` is not an object. The menu rejects the page (FR-004).
- A later response repeats a `next` value that the menu already requested. The menu rejects the read (FR-006).
- A `next` value is an empty string. The menu treats the page as the last page (FR-005).
- `total` is larger than the row count and no `next` value exists. The menu rejects the read (FR-007).
- No page reports `total`. The menu uses the `next` values only (A-2).
- `X-Page-Page` is not an integer. The menu rejects the read (FR-008).
- HTTP 204 returns with no body. The menu treats the body as unusable (FR-004).
- HTTP 429 returns. The menu logs an ERROR line. This change adds no retry (C-4).
- The SDK call raises an exception. The outer guard logs it, and the menu returns (FR-014).
- A response body contains a credential-like value. The menu logs no body text (FR-011).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The exporter MUST check the HTTP status of the first search page before it reads any row.
- **FR-002**: The exporter MUST check the HTTP status of each later page before it accepts that page's rows.
- **FR-003**: The exporter MUST reject a page with no integer status or with a status outside 200 through 299.
- **FR-004**: The exporter MUST reject a 2xx page whose body is not an object with a list `results`, or whose row is not an object.
- **FR-005**: The exporter MUST request each later page until a page omits `next` or sends an empty `next` value.
- **FR-006**: The exporter MUST reject a `next` value that it has already requested.
- **FR-007**: The exporter MUST reject a read whose row count differs from `total` when a page reports `total`.
- **FR-008**: The exporter MUST reject `X-Page-Total`, `X-Page-Limit`, or `X-Page-Page` headers that are not integers.
- **FR-009**: The exporter MUST NOT call the writer after any rejected page or any rejected total check.
- **FR-010**: The exporter MUST log one ERROR line for each rejected page, with the site name, the page number, and the HTTP status or failure class.
- **FR-011**: The exporter MUST NOT log a response body, a cursor value, a URL, or a credential in any message.
- **FR-012**: The exporter MUST print the no-data message and skip the writer when a complete read has zero rows.
- **FR-013**: The exporter MUST call the writer once with every row when a complete read has at least one row.
- **FR-014**: The menu operation MUST return to the menu loop after a failure and MUST NOT raise an exception to the loop.
- **FR-015**: The exporter MUST use mistapi methods for every request and MUST NOT send a direct HTTP request.
- **FR-016**: The exporter MUST send the first request as `searchSiteOtherDeviceEvents(session, site_id)` with no added query parameter.
- **FR-017**: The exporter MUST keep the filename rule, the operationId `searchSiteOtherDeviceEvents`, and the composite key `mac` and `timestamp`.
- **FR-018**: The change MUST add no module-level name to `src/operations/exporting/export/site_other_device_events_exporter.py`.
- **FR-019**: The change MUST add an inline comment to each changed line and action logs around each request.
- **FR-020**: The change MUST add the changelog fragment `changelog.d/issue-4709-other-device-events-page-failures.md`.
- **FR-021**: The change MUST NOT edit any file before the #1794 owner posts a file-scoped handoff.
- **FR-022**: The change MUST NOT edit an organization exporter, a firmware file, or an organization configuration file.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- **Mist methods used**: `mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents` for the first page. `mistapi.get_next` for each later page.
- **Retired method**: `mistapi.get_all`. It adds the rows of a failed page without a status check (research.md, RC-65 and RC-66).
- **SDK insufficiency contract**: The current exporter accepts an empty list for a failed first page (RC-02). Tests 3 and 7 in plan.md reproduce the defect before the fix.
- **SDK authentication contract**: Both calls use the session from `SourceDependencyResolver.apisession` (exporter line 73). No token enters a log message (FR-011).
- **SDK endpoint parity contract**: The SDK path `/api/v1/sites/{site_id}/otherdevices/events/search` matches OpenAPI path line 35577 (RC-22 and RC-70).
- **Failure safety contract**: Tests 1 to 15 in plan.md, with two cases for Test 7, cover failed, malformed, incomplete, and transport failures.
- **Secret redaction contract**: Test 14 in plan.md checks that failure log messages hold no body, cursor, or URL.
- **Owned transport**: None. The constitution exception for an owned WebSocket transport does not apply.

### Key Entities *(include if feature involves data)*

- **Search page**: One response from the search endpoint. It holds an HTTP status, a body or headers, and an optional `next` value.
- **Event row**: One object in `results`. Its natural key is `mac` with `timestamp` (RC-12).
- **Complete read**: A read where every page passes and the row count matches `total` when a page reports `total`.
- **Incomplete read**: A read that ends at a rejected page or a rejected total check. It writes no file.
- **Writer call**: One call to `DataExporter.write_with_format_selection`. Only a complete read with rows makes this call.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each failure reproduction in issue #4709 produces an ERROR line and no writer call in the unit tests.
- **SC-002**: A failed later page produces no writer call and no partial file in the unit tests.
- **SC-003**: A complete empty read prints the no-data message and produces no file in the unit tests.
- **SC-004**: Each applicable local gate reports its expected result for the changed files.
- **SC-005**: `symbol-diff` reports no module-level name changed for the exporter file.
- **SC-006**: The remote test quality gate reports zero new findings on the pull request commit.

## Clarifications

### Session 2026-11-26

- **C-1**: Which commit is the base? Answer: `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The owner candidate is reference evidence only (D-1).
- **C-2**: Is HTTP 404 a failure or an empty result? Answer: A failure. Log an ERROR line and write no file. Spec 894 line 65 describes a logged warning, and this change makes that warning an ERROR line.
- **C-3**: Does a failure stop the menu? Answer: No. The operation returns to the menu loop (FR-014).
- **C-4**: Does this change add retries? Answer: No. The SDK retries HTTP 429 inside the request layer (`__api_request.py`, line 228 onward). This change adds no retry.

## Assumptions

- **A-1**: Each search page returns `results` as a list. OpenAPI schema lines 94500 to 94511 define the page fields (RC-23 and RC-24).
- **A-2**: `total` is optional in the schema. The schema describes `total` as the count across all pages (RC-23). When no page reports `total`, the check uses `next` only. The live API behavior is unverified (U-2).
- **A-3**: `mistapi.get_next` follows the body `next` value of a search page (`__pagination.py` line 34, RC-67).
- **A-4**: The search time window stays at the API default. The SDK docstring states the `duration` default as `1d` (RC-71). This change keeps the window unchanged (D-6).
- **A-5**: The tests use mocks only. This change makes no live Mist call and no database write.
- **A-6**: The #1794 owner keeps the outer `except Exception` guard in this change (D-9).

## Non-Goals

- Changing the outer guard that the #1794 audit owns.
- Changing the organization other-device export or the organization audit log export. A follow-up issue owns these paths.
- Changing mistapi or any vendored SDK file.
- Adding retry, backoff, or a page cap.
- Changing CSV columns, filenames, primary keys, or the writer.
- Changing the menu title, the menu category, or the operation registry.
- Closing issues #1794, #4707, or #4710.
