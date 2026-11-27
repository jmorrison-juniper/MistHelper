# Feature Specification: API Fetch Failures

**Feature Branch**: `fix/4762-api-fetch-failures`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4762, "Runtime: site and inventory API errors appear as empty results." The two fetch helpers return an empty list after an HTTP error. Callers cannot tell a failure from an empty result.

## Clarifications

### Session 2026-11-26

- Q: Does a successful read with no items count as a failure? A: No. A 2xx response with no items returns an empty list. (FR-005)
- Q: Which callers change? A: Each optional lookup in `design/contracts/optional-lookups.md`. Required reads keep their code and receive the new error. (FR-009, FR-010)
- Q: Does a direct-mode menu session end when a required read fails? A: Yes, under the existing menu error policy. Container mode returns to the menu. (D-13)
- Q: Where do the new integration tests go? A: In `tests/integration/export/`. `tests/integration/` holds 26 children on `main`. (D-10, R125, R126)
- Q: Does this change repair the direct `mistapi.get_all` readers? A: No. Those readers need a separate issue. (D-5)

## User Scenarios and Testing *(mandatory)*

### User Story 1 - Required read reports a failure (Priority: P1)

An operator runs an export or a report that needs the site list or the device inventory. The Mist API returns an HTTP error for that read. The tool stops the operation with a clear error. It does not show an empty result.

**Why this priority**: An empty result looks like valid data. An operator can then act on a false inventory.

**Independent Test**: Mock the first page of each fetch helper with HTTP 403 and HTTP 503. Each helper raises `APIFetchError`. Neither helper returns an empty list.

**Acceptance Scenarios**:

1. **Given** a first page with HTTP 403, **When** a fetch helper runs, **Then** it raises `APIFetchError`. The message contains the operation name, the org ID, and the cause.
2. **Given** a later page with HTTP 503, **When** a fetch helper runs, **Then** it raises `APIFetchError` and returns no partial list.
3. **Given** the inventory read in the AP model export fails, **When** the export runs, **Then** the error reaches the menu dispatcher.

### User Story 2 - Optional lookup warns and continues (Priority: P1)

An operator runs a report that adds site names. The site-name read fails. The report keeps its rows. It writes one warning and uses the existing fallback values.

**Why this priority**: Site names enrich the output. A failed name lookup must not stop the device data.

**Independent Test**: Mock the site read with HTTP 403 and HTTP 503 for each optional lookup. Each lookup returns its empty fallback and logs one warning. The device rows remain.

**Acceptance Scenarios**:

1. **Given** a site read with HTTP 503, **When** `SiteNameLookup.fetch` runs, **Then** it returns an empty lookup and logs one warning.
2. **Given** a site read with HTTP 403, **When** the offline device report fetches data, **Then** it returns the device statistics with the `Unknown Site` fallback.
3. **Given** a site read with HTTP 503, **When** the gateway export runs, **Then** it writes each gateway row with the `Unknown` site fields.

### User Story 3 - Tests prove both paths (Priority: P2)

A reviewer runs the new tests. Each new failure case fails before the change. The tests use real mistapi response objects. They do not set the status field by hand on a mock.

**Why this priority**: A mock with the wrong status field hides the defect. The unpublished candidate work showed this risk. Issue comments 2 and 3 record it.

**Independent Test**: Run the two test modules named in `tasks.md`. Before implementation, the new failure cases fail. After implementation, every case passes.

**Acceptance Scenarios**:

1. **Given** a first page with no HTTP status, **When** the unit test runs, **Then** the helper raises `APIFetchError`.
2. **Given** an optional lookup warning, **When** the integration test reads the log, **Then** the warning names the org ID and the cause, with no credential.

### Edge Cases

- An organization with no sites returns HTTP 200 and an empty list. The helper returns an empty list. It does not raise.
- A connection or proxy failure gives no HTTP status. The helper raises `APIFetchError` with the cause `no HTTP status`.
- A later page returns HTTP 200 with a payload that is neither a list nor a dict with `results`. The helper raises `APIFetchError`.
- A next link repeats. The helper raises `APIFetchError` and stops paging.
- HTTP 429 remains after the SDK retries. The helper raises `APIFetchError`.
- The fast export path regenerates a missing site cache file. A failed regeneration returns `False`. The export then uses the optional lookup.

Caution: a direct-mode menu run ends with exit code 1 after a required read fails. The operator must start the menu again.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both fetch helpers MUST raise `APIFetchError` when the first page status is outside 200 to 299 or missing.
- **FR-002**: Both fetch helpers MUST raise `APIFetchError` when a later page status is outside 200 to 299 or missing. They MUST NOT return a partial list.
- **FR-003**: Both fetch helpers MUST raise `APIFetchError` when a 2xx payload is neither a list nor a dict with a `results` list.
- **FR-004**: Both fetch helpers MUST return every item of every page, in page order, for both payload shapes.
- **FR-005**: Both fetch helpers MUST return an empty list when a 2xx read has no items.
- **FR-006**: `APIFetchError` MUST be nested in `APICoreFetchUtils`. It MUST subclass `RuntimeError`.
- **FR-007**: Later pages MUST come from `mistapi.get_next`. The change MUST NOT send a direct HTTP request.
- **FR-008**: Both fetch helpers MUST keep the request arguments of the current code.
- **FR-009**: Each optional lookup MUST catch only `APIFetchError`. It MUST log one warning, keep the empty lookup, and continue.
- **FR-010**: Each required read MUST NOT catch `APIFetchError`. The error MUST reach the caller.
- **FR-011**: The MSP site lookup MUST keep its broad catch. It MUST log the failure at warning level.
- **FR-012**: The prompt site cache MUST keep its `RuntimeError` fallback and its warning. It needs no code change.
- **FR-013**: No changed source file MUST add a module-level name.
- **FR-014**: Each warning and error MUST name the operation, the org ID, and the cause. It MUST contain no credential and only ASCII text.
- **FR-015**: Each behavior change MUST have a test that fails before the change.
- **FR-016**: The change MUST add one release-note fragment under `changelog.d/` that names issue 4762.

### Mist Cloud Transport Requirements

- The change uses `mistapi.api.v1.orgs.sites.listOrgSites`, `mistapi.api.v1.orgs.inventory.getOrgInventory`, and `mistapi.get_next`.
- The change adds no owned WebSocket transport.
- SDK insufficiency: `mistapi.get_all` does not check later page status. It stops without an error when a next page is missing. Evidence: rows R95 and R96 in `design/research.md`.
- SDK authentication: the change keeps the session argument `mh.apisession`.
- SDK endpoint parity: the calls match the OpenAPI operations. Evidence: rows R82 to R89.
- Contract tests cover output, failure handling, safety, and secret redaction. They are cases U-1 to U-11 and I-1 to I-13 in `tasks.md`.

### Key Entities

- **APIFetchError**: The error that a fetch helper raises. It names the operation, the org ID, and the cause.
- **Mist site row**: A dictionary returned by `listOrgSites`. The change does not alter its fields.
- **Mist inventory row**: A dictionary returned by `getOrgInventory`. The change does not alter its fields.
- **Optional lookup**: A site-name read that enriches output. Its failure logs one warning.
- **Required read**: A read that the output needs. Its failure reaches the caller.

## Success Criteria *(mandatory)*

- **SC-001**: Every first-page failure case in the fetch helper unit tests passes.
- **SC-002**: Every later-page failure case passes, and no partial list is returned.
- **SC-003**: Every optional lookup case in the integration tests passes with exactly one warning.
- **SC-004**: Every required read case raises `APIFetchError` to its caller.
- **SC-005**: The Symbols gate reports no module-level name change for each changed source file.
- **SC-006**: Every required CI check passes on the pull request.

## Assumptions

- **A-001**: `requirements.txt` keeps `mistapi==0.64.1` (row R66).
- **A-002**: A `requests.Response` object built offline supplies the status, the headers, and the JSON body to `mistapi.APIResponse`.
- **A-003**: The menu dispatcher policy stays unchanged.
- **A-004**: No open pull request touches the changed files. The check ran on 2026-11-26 with `gh pr list --state open`.

## Out of Scope

- Direct `mistapi.get_all` readers outside the fetch helpers. Examples in the repository are `msp_inventory_exporter.py` line 275 (row R29) and `gateway_export_utils.py` line 282 (row R39). They need a separate issue.
- The functions `_split_address` and `_split_full_address`. The issue owner asked to keep them unchanged.
- `tests/unit/export/test_site_device_exporter.py`. Session 79a9bb52 owns it.
- The blind exception work tracked in issue 1794.
- Menu text, CSV columns, and CSV file names.
- The `mistapi` version pin.
- Merge decisions beyond task T-MERGE in `tasks.md`.

Caution: editing `tests/unit/export/test_site_device_exporter.py` causes an ownership conflict with session 79a9bb52.
