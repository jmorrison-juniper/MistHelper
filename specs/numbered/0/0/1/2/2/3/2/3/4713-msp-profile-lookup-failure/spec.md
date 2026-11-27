# Feature Specification: MSP Profile Lookup Failure

**Feature Branch**: `fix/4713-msp-profile-lookup-failure`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4713: Runtime: MSP detection treats refused profile responses as no access

## Clarifications

### Session 2026-11-26

- Q: Does a refused profile response prove that the account has no MSP access? A: No. A refused response is a failed lookup. Only a valid profile proves confirmed absence.
- Q: What does menu 13 do when the grant list is empty? A: It makes one live lookup. It calls the single-organization callback only after a valid profile with zero MSP grants.
- Q: What does menu 13 do when the live lookup fails? A: It prints a failure message, calls no callback, and returns.
- Q: Does the grant list type change? A: No. Every caller outside two modules keeps its current input.

## Terms

This record uses each term below with one meaning only.

- **Profile lookup**: One `getSelf` API call and its validation.
- **Valid profile**: A profile lookup result with a 2xx status, a JSON object body, and a `privileges` list.
- **Failed lookup**: A profile lookup that returns no valid profile or raises an exception.
- **Confirmed absence**: A valid profile with zero MSP grants.
- **MSP grant**: One MSP-scoped entry in the `privileges` list.
- **Grant list**: The module global `msp_privileges` in `src/mist/resources/inventory/org_device_inventory_msp.py`.
- **Live lookup**: A profile lookup that menu 13 makes at dispatch time.
- **Lookup result**: The value of type `MspPrivilegeLookup` that `lookup_msp_privileges` returns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A refused profile lookup does not read as no access (Priority: P1)

An MSP operator runs menu 13 while the Mist API refuses the profile lookup with HTTP 403 or HTTP 503. The tool must not run the single-organization inventory as if the account had no MSP access. The tool prints a failure message and stops.

**Why this priority**: The defect sends an MSP operator down the wrong inventory path without a clear signal.

**Independent Test**: Use mocked profile responses with status 403 and status 503. Run the dispatch with an empty grant list. Verify that no callback runs and that the failure message appears.

**Acceptance Scenarios**:

1. **Given** an empty grant list and HTTP 403, **When** the operator selects menu 13, **Then** the tool prints the failure message and calls no callback.
2. **Given** an empty grant list and HTTP 503, **When** the operator selects menu 13, **Then** the tool prints the failure message and calls no callback.
3. **Given** a profile response with HTTP 403, **When** the detector reads it, **Then** it writes one warning naming HTTP 403 and returns a failed lookup.

---

### User Story 2 - A confirmed absence still runs the single-organization inventory (Priority: P1)

An organization-only account returns a valid profile with an empty `privileges` list. Menu 13 keeps its current behavior for that account.

**Why this priority**: The fix must not block accounts that have no MSP access.

**Independent Test**: Use a mocked profile response with status 200 and an empty `privileges` list. Run the dispatch with an empty grant list. Verify that the single-organization callback runs once.

**Acceptance Scenarios**:

1. **Given** an empty grant list and a valid profile with zero MSP grants, **When** the operator selects menu 13, **Then** the single-organization callback runs once.
2. **Given** a grant list that holds MSP grants, **When** the operator selects menu 13, **Then** the menu appears and the tool makes no profile lookup.

---

### User Story 3 - A live lookup that finds grants stops with a restart message (Priority: P2)

The startup lookup failed, so the grant list is empty. The live lookup now returns MSP grants. Menu 13 cannot load those grants into the running session. It prints a restart message and calls no callback.

**Why this priority**: The case is rare, but it must not fall through to the single-organization path.

**Independent Test**: Use an empty grant list and a live lookup that returns one MSP grant. Verify that the restart message appears and that no callback runs.

**Acceptance Scenarios**:

1. **Given** an empty grant list and a live lookup with MSP grants, **When** the operator selects menu 13, **Then** the restart message appears.

### Edge Cases

- The session is missing. The tool makes no API call and returns a failed lookup.
- The 2xx response body is not a JSON object, for example an HTML page from a proxy. The lookup fails.
- The 2xx response body has no `privileges` list, or it holds a null or text value. The lookup fails.
- The 2xx response body holds an empty `privileges` list. The lookup returns a valid profile with zero MSP grants.
- The API call raises a network error. The lookup fails. The log names the exception class and no exception text.
- HTTP 401 and HTTP 429 follow the rule for HTTP 403. The lookup fails.
- The unattended `--test` sweep runs menu 13 without an API token. The menu completes and prints its message.

## Requirements *(mandatory)*

### Functional Requirements

Profile validation:

- **FR-001**: The lookup MUST accept a response only when its status is 2xx, its body is a JSON object, and it has a `privileges` list.
- **FR-002**: The profile lookup MUST treat every other response as a failed lookup. A failed lookup MUST NOT count as confirmed absence.
- **FR-003**: The profile lookup MUST NOT make an API call when the session is missing. It MUST return a failed lookup.
- **FR-004**: The profile lookup MUST treat a raised exception as a failed lookup.
- **FR-005**: Each failed lookup MUST write one warning that names the reason. When the response has a status, the warning MUST include the status code.

Detector contract:

- **FR-006**: `lookup_msp_privileges` MUST return a lookup result with `succeeded` set to false for every failed lookup. It MUST set `succeeded` to true for every valid profile, including a profile with zero MSP grants.
- **FR-007**: `detect_msp_privileges` MUST keep its list return type. It MUST return the grants of the lookup result, and an empty list for a failed lookup.

Dispatch:

- **FR-008**: When the grant list holds MSP grants, menu 13 MUST NOT make a profile lookup.
- **FR-009**: When the grant list is empty, menu 13 MUST make one live lookup before it calls any callback.
- **FR-010**: Menu 13 MUST call the single-organization callback only after a valid live lookup with zero MSP grants.
- **FR-011**: After a failed live lookup, menu 13 MUST print the failure message, MUST call no callback, and MUST return.
- **FR-012**: After a valid live lookup with MSP grants, menu 13 MUST print the restart message, MUST call no callback, and MUST return.

Safety and scope:

- **FR-013**: No log line, console line, or exception message MUST contain a response body, an exception message, a token, or a password. The exception class name is the only exception detail that the code MAY log.
- **FR-014**: The change MUST NOT change the type of the grant list. It MUST NOT change the inputs of callers outside `src/foundation/support/refactors/msp_privilege_detection.py` and `src/mist/resources/inventory/org_device_inventory_msp.py`.
- **FR-015**: The change MUST add no module under `src/`.

Verification and documentation:

- **FR-016**: Tests MUST cover statuses 401, 403, 429, and 503. They MUST also cover a missing `privileges` list, a non-object body, an exception, a missing session, and each dispatch branch.
- **FR-017**: `documentation/wiki/MSP-Support.md` and `documentation/operator-guide.md` MUST describe the failed-lookup behavior. A changelog fragment MUST record the fix.

### Key Entities

- **Profile response**: The SDK response that `getSelf` returns. Key attributes: `status_code` and `data`.
- **MSP grant**: One MSP-scoped privilege entry. Natural key: `msp_id`. Attributes: `msp_name`, `role`, and `scope`.
- **Lookup result**: The return value of `lookup_msp_privileges`. Attributes: `succeeded` and `grants`.
- **Grant list**: The module global `msp_privileges`. It holds the MSP grants from the startup or login path.

### Mist Cloud Transport Requirements

- The feature uses one mistapi REST method, `mistapi.api.v1.self.self.getSelf`. The SDK defines it at line 17 of `.venv\Lib\site-packages\mistapi\api\v1\self\self.py`.
- The feature adds no REST method and no direct HTTP call.
- The feature owns no WebSocket transport. The SDK insufficiency contract does not apply.
- SDK authentication stays unchanged. The `getSelf` path `/api/v1/self` matches the OpenAPI path at line 25460 of `documentation/mist-api-openapi31yaml.yaml`.
- Failure safety: tests cover statuses 401, 403, 429, and 503, a raised exception, and a missing session.
- Secret redaction: a test asserts that neither exception text nor response body text reaches the captured logs.

### Success Criteria

- **SC-001**: A mocked HTTP 403 and a mocked HTTP 503 each produce zero callback calls and one warning that names the status.
- **SC-002**: Every test in the two changed test modules passes. Each new case fails on the unchanged code, except the regression guard in T005. A new name that the code lacks fails the case at import or at patch time.
- **SC-003**: With a non-empty grant list, the dispatch test makes zero profile lookups.
- **SC-004**: Each applicable gate in `tasks.md` reports the expected result.
- **SC-005**: The changed-file list matches the change map in `plan.md`.
- **SC-006**: The redaction test finds no exception text and no response body text in the captured logs.

### Assumptions

- The pinned mistapi version is 0.64.1. It satisfies the pin `mistapi>=0.64.0,<0.65`.
- The SDK sets `status_code` on each response that `mist_get` returns. Line 48 of `__api_response.py` sets it from the HTTP response.
- A successful `getSelf` call returns a JSON object with a `privileges` list. The OpenAPI 200 response is `admin`, and `admin` has a `privileges` property at line 67996.
- One more profile lookup for an organization-only account stays within the rate-limit rule in `AGENTS.md`.
- Operators use menu 13 in an interactive session. The unattended sweep reaches menu 13 only through the safe sweep.

### Out of Scope

- Carrying the lookup result through the `MainEntrypoint` context and the startup, restore, and login messages. This work needs `MistHelper.py` and `main_entrypoint.py`. A follow-up issue is required.
- The grant-list readers `OrgConfigExporter` (`src/operations/exporting/export/org_config_exporter.py`, line 71) and the firmware cache (`src/operations/execution/firmware/firmware_manager.py`, line 43). They treat an empty grant list as no access. A follow-up issue is required.
- The debug-only site-lookup failure in `MSPInventoryExporter._build_site_lookup`. Issue #4762 owns that file.
- The broad exception handlers across the code base. Issue #1794 owns that work.
- Any change to the OpenAPI file or to the installed mistapi package.
