# Feature Specification: Synthetic Test Trigger

**Feature Branch**: `feat/3563-synthetic-test-trigger`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 283 trigger a synthetic test on demand. Menus 33 and 34 read synthetic test results, but no operation starts one. Before a cutover an operator wants to prove RADIUS reachability from a switch or run the site synthetic test now instead of at the next schedule. The operation asks for a site, a scope (site, one device, or RADIUS check from one switch), and the test parameters. It starts the test, polls the result endpoint until the result arrives or a timeout passes, prints the result, and writes SyntheticTestTrigger.csv with the request and the result."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start a site validation now (Priority: P1)

A NOC engineer selects a site and starts the site synthetic test without waiting for the next scheduled run.

**Why this priority**: This gives the operator the fastest pre-cutover proof for the whole site.

**Independent Test**: Mock the Mist API, accept the `y` confirmation, return one poll result, and verify the export row.

**Acceptance Scenarios**:

1. **Given** a selected site and a `y` confirmation, **When** the operator chooses site scope, **Then** MistHelper starts the site test, polls for a result, prints it, and writes `data/SyntheticTestTrigger.csv`.
2. **Given** a selected site and any answer other than `y`, **When** the operator reaches the confirmation prompt, **Then** MistHelper cancels before it sends a trigger.

---

### User Story 2 - Start one device validation now (Priority: P2)

A NOC engineer selects one device and starts a device synthetic test with the parameters that the Mist API supports.

**Why this priority**: This proves one switch, AP, or gateway path when the cutover affects one location.

**Independent Test**: Mock the selected device, assert the request body matches the OpenAPI schema, and return one device poll result.

**Acceptance Scenarios**:

1. **Given** a selected site and device, **When** the operator enters a device test type and parameters, **Then** MistHelper sends the schema-compliant body to the device synthetic test endpoint.
2. **Given** no result arrives before the timeout, **When** polling reaches `SYNTHETIC_TEST_TIMEOUT_SECONDS`, **Then** MistHelper prints a clear timeout message and writes the request summary with the timeout result.

---

### User Story 3 - Prove switch RADIUS reachability (Priority: P3)

A NOC engineer selects one switch and tests RADIUS reachability without exposing the shared secret.

**Why this priority**: RADIUS reachability is sensitive because it includes a password value.

**Independent Test**: Mock the RADIUS trigger, capture logs and export rows, and verify that the password is masked everywhere.

**Acceptance Scenarios**:

1. **Given** a selected switch, username, profile, and password, **When** the operator starts the RADIUS check, **Then** MistHelper sends the password to Mist only in the request body.
2. **Given** the RADIUS check completes, **When** MistHelper logs and exports the result, **Then** the password is not present in logs or `SyntheticTestTrigger.csv`.

### Edge Cases

- If site selection fails, MistHelper stops before it prompts for test parameters.
- If device selection fails, MistHelper stops before it sends a device or RADIUS trigger.
- If the poll result never arrives before the timeout, MistHelper writes a timeout row with a clear message.
- If the Mist API returns an empty search response, MistHelper continues polling until the timeout.
- If a RADIUS password is entered, MistHelper masks it before logging or export.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose menu `283` as an `interactive` operation through the integration wiring manifest.
- **FR-002**: The operation MUST prompt for a site with the existing `PromptUtils` site helper.
- **FR-003**: The operation MUST prompt for one of three scopes: site, one device, or RADIUS check from one switch.
- **FR-004**: The operation MUST ask for `y` or `N` before any trigger call and cancel on every answer except `y`.
- **FR-005**: The poll MUST stop after `SYNTHETIC_TEST_TIMEOUT_SECONDS`, default `120`, and report a clear timeout message.
- **FR-006**: The RADIUS check MUST mask the shared secret in every log line and MUST NOT write it to the output file.
- **FR-007**: The request body MUST follow the OpenAPI schema in `documentation/mist-api-openapi3json.json`.
- **FR-008**: The operation MUST write `SyntheticTestTrigger.csv` under `data/` through the shared export path.
- **FR-009**: The operation MUST record menu wiring in `specs/3563-synthetic-test-trigger/wiring.md` for the integration pull request.
- **FR-010**: The feature MUST include `changelog.d/issue-3563-synthetic-test-trigger.md` with one `Added` section.

### Key Entities *(include if feature involves data)*

- **Synthetic Test Request**: The selected site, optional device, scope, test type, non-secret parameters, and confirmation result.
- **Synthetic Test Result**: The status, failure flag, reason, latency, throughput values, timestamp, and timeout message.
- **Export Row**: A safe flat record that combines the request summary and the returned result without secrets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A mocked site trigger sends one API call only after the operator answers `y`.
- **SC-002**: A mocked timeout stops at the configured timeout and returns a user-readable timeout message.
- **SC-003**: A RADIUS run leaves no password value in captured logs or export rows.
- **SC-004**: The unit suite proves the site body, device body, timeout, cancellation, export, wiring, and release-note requirements.

## Assumptions

- The integration pull request adds the menu row, import line, registry entry, and documentation updates.
- The operation uses `DataExporter.write_with_format_selection` so the existing data directory policy controls the final path.
- Device scope uses the existing `PromptUtils.select_device_id_from_inventory` helper and filters by device type when needed.
- Polling uses the existing synthetic test read endpoints from menus 33 and 34 instead of a new endpoint.
