# Tasks: WiFi Pagination Failure Handling

**Input**: Numeric feature record at `specs/numbered/0/0/1/2/2/1/1/1/4656-wifi-pagination/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/wifi-pagination.md`, and `design/quickstart.md`.

## Phase 1: Setup

**Purpose**: Use the resolved managed route and keep shared Spec Kit state unchanged.

- [x] T001 Confirm the issue-numbered route and preserve `.specify/feature.json` in `specs/numbered/0/0/1/2/2/1/1/1/4656-wifi-pagination/` (delivered: `specs/numbered/0/0/1/2/2/1/1/1/4656-wifi-pagination/spec.md`)

## Phase 2: Foundational

**Purpose**: Record the SDK behavior and the page result states before the story changes.

- [x] T002 Document the `mistapi.get_all` limitation and the controlled `mistapi.get_next` path in `specs/numbered/0/0/1/2/2/1/1/1/4656-wifi-pagination/design/research.md`

## Phase 3: User Story 1 - Keep WiFi data after a later timeout (Priority: P1)

**Goal**: Retain earlier records and identify exported data as partial after a later transport timeout.

**Independent Test**: Return one native SDK page with a record, then raise a controlled timeout from the SDK session. Verify the record is exported and the complete-success message is absent.

### Tests for User Story 1

- [x] T003 Exercise a native SDK page link and controlled timeout in `tests/integration/export/test_wifi_clients_native_response_failures.py` (delivered: `tests/integration/export/test_wifi_clients_native_response_failures.py`)

### Implementation for User Story 1

- [x] T004 Retain validated pages and report partial output in `src/operations/exporting/export/wifi_clients_exporter.py` (delivered: `src/operations/exporting/export/wifi_clients_exporter.py`)

## Phase 4: User Story 2 - Reject a failed later WiFi page (Priority: P1)

**Goal**: Reject later HTTP failures without creating output that appears complete or valid-empty.

**Independent Test**: Return a successful native first page and a controlled HTTP 403 or 503 later page. Verify the failed status and absence of export output.

### Tests for User Story 2

- [x] T005 Test native later-page HTTP 403 and 503 responses in `tests/integration/export/test_wifi_clients_native_response_failures.py` (delivered: `tests/integration/export/test_wifi_clients_native_response_failures.py`)

### Implementation for User Story 2

- [x] T006 Validate every later page before adding its records in `src/operations/exporting/export/wifi_clients_exporter.py` (delivered: `src/operations/exporting/export/wifi_clients_exporter.py`)

## Phase 5: User Story 3 - Preserve first-page failure behavior (Priority: P2)

**Goal**: Keep first-page HTTP and body failures distinct from a complete valid-empty result.

**Independent Test**: Run the existing controlled first-page failure and valid-empty response tests. Verify their prior output behavior.

### Tests for User Story 3

- [x] T007 Verify first-page errors and valid-empty output in `tests/unit/export/test_wifi_clients_response_failures.py` and `tests/integration/export/test_wifi_clients_native_response_failures.py` (delivered: both test files)

### Implementation for User Story 3

- [x] T008 Preserve first-page validation and the complete-empty placeholder path in `src/operations/exporting/export/wifi_clients_exporter.py` (delivered: `src/operations/exporting/export/wifi_clients_exporter.py`)

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Record the change and validate the combined pagination contract.

- [x] T009 Add one release-note fragment for issues #4656 and #4657 in `changelog.d/issue-4656-wifi-pagination.md` (delivered: `changelog.d/issue-4656-wifi-pagination.md`)
- [x] T010 Run the focused tests listed in `specs/numbered/0/0/1/2/2/1/1/1/4656-wifi-pagination/design/quickstart.md` and the applicable lint, format, type, compile, complexity, security, test-quality, and STE checks
- [x] T011 Commit the validated change with a Conventional Commit subject and the required co-author trailer in the current Git branch

## Dependencies and Execution Order

### Phase Dependencies

- Setup and Foundational tasks have no code dependencies.
- User Story 1 depends on the Foundational task and establishes the shared page reader.
- User Story 2 depends on the shared page reader from User Story 1.
- User Story 3 verifies compatibility after the shared page reader exists.
- Polish checks depend on all three user stories.

### Parallel Opportunities

- The changelog fragment can be prepared independently from source and test edits.
- The unit tests for first-page behavior can be checked independently from the native later-page tests.
- The stories use the same exporter module, so implementation edits must remain serial.

## Implementation Strategy

The timeout-retention story is the MVP. Validate it with a controlled native SDK response and session. Then validate later HTTP failure rejection and first-page compatibility. Run the combined checks before the requested local commit.
