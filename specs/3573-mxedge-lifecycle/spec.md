# Feature Specification: Mist Edge Lifecycle Operation

**Feature Branch**: `feat/3573-mxedge-lifecycle`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 293 Mist Edge lifecycle: claim, assign, bounce ports, upgrade. Five menus read Mist Edge data (50, 71, 201, 205, 253) and none changes it. An operator who claims a Mist Edge, assigns it to a site, bounces its data ports, or upgrades it must open the Mist UI. Mist offers one endpoint for each step. The operation opens a sub-menu with claim (claim code), assign to site, unassign from site, bounce data ports, and upgrade (with the upgrade status read). Each step shows the target, asks for a typed confirmation word (CLAIM, ASSIGN, UNASSIGN, BOUNCE, UPGRADE), sends the request, and writes MxEdgeLifecycleLog.csv."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Claim a Mist Edge (Priority: P1)

An operator must claim a Mist Edge into the selected organization without opening the Mist portal. The operator enters the claim code, reviews the target organization, types `CLAIM`, and the system sends the claim request.

**Why this priority**: A device must be in organization inventory before assignment, port bounce, or upgrade steps can run.

**Independent Test**: Run the claim path with a fake client. Verify that no request is sent before the `CLAIM` word and that the claim code never appears in logs.

**Acceptance Scenarios**:

1. **Given** an operator enters a claim code, **When** the operator types `CLAIM`, **Then** the system sends body `{"code": "<claim-code>"}` and writes one log row without the code.
2. **Given** an operator enters a claim code, **When** the operator types any word except `CLAIM`, **Then** the system sends no request and writes no claim code to any log message.
3. **Given** the operator enables dry-run, **When** the operator types `CLAIM`, **Then** the system records a dry-run row and sends no request.

---

### User Story 2 - Assign or unassign a Mist Edge (Priority: P2)

An operator must move one or more Mist Edges into a site or remove them from a site. The operator selects the target device identifiers, confirms the target site when needed, types `ASSIGN` or `UNASSIGN`, and the system sends the matching request.

**Why this priority**: Site assignment is the policy boundary for a Mist Edge data path.

**Independent Test**: Run assign and unassign with a fake client. Verify the request bodies and the confirmation guard for each step.

**Acceptance Scenarios**:

1. **Given** a Mist Edge identifier and a site identifier, **When** the operator types `ASSIGN`, **Then** the system sends body `{"mxedge_ids": ["<id>"], "site_id": "<site-id>"}`.
2. **Given** a Mist Edge identifier, **When** the operator types `UNASSIGN`, **Then** the system sends body `{"mxedge_ids": ["<id>"]}`.
3. **Given** dry-run is enabled, **When** the operator confirms assign or unassign, **Then** the system writes a dry-run row and sends no request.

---

### User Story 3 - Bounce data ports (Priority: P3)

An operator must bounce Mist Edge data ports after they check tunnel and LACP evidence. The operator enters one Mist Edge identifier and the port list, types `BOUNCE`, and the system sends the bounce request.

**Why this priority**: A controlled port bounce can repair a tunnel interface without replacing the appliance.

**Independent Test**: Run the bounce path with a fake client. Verify the request body and the confirmation guard.

**Acceptance Scenarios**:

1. **Given** a Mist Edge identifier and ports `0,2`, **When** the operator types `BOUNCE`, **Then** the system sends body `{"ports": ["0", "2"]}`.
2. **Given** the operator enters an empty port list, **When** the step validates input, **Then** the system refuses the request before confirmation.
3. **Given** dry-run is enabled, **When** the operator types `BOUNCE`, **Then** the system writes a dry-run row and sends no request.

---

### User Story 4 - Upgrade a Mist Edge and poll status (Priority: P4)

An operator must upgrade one or more Mist Edges and watch the upgrade status. The operator enters the device identifiers and version, types `UPGRADE`, and the system polls until the upgrade completes or the timeout expires.

**Why this priority**: Upgrade status gives the operator a safer finish point than a submitted request alone.

**Independent Test**: Run the upgrade path with a fake client whose status changes. Verify polling stops on a terminal status and stops at `UPGRADE_POLL_TIMEOUT_SECONDS`.

**Acceptance Scenarios**:

1. **Given** a Mist Edge identifier and version `latest`, **When** the operator types `UPGRADE`, **Then** the system sends an upgrade body with `mxedge_ids` and `versions`.
2. **Given** the status API returns a running status and then a completed status, **When** polling runs, **Then** the system stops after the completed status.
3. **Given** the status API never returns a completed status, **When** the timeout expires, **Then** the system stops polling and writes a timeout row.
4. **Given** dry-run is enabled, **When** the operator types `UPGRADE`, **Then** the system writes a dry-run row and sends no request.

### Edge Cases

- If no active API session exists, the operation stops before a prompt can trigger a request.
- If an operator enters the wrong confirmation word, the step sends no request.
- If a dry-run is selected, the step writes a row that names the intended action and sends no request.
- If a claim code is present, the system redacts it from logs and the CSV file.
- If the upgrade response does not include an upgrade identifier, the system reads the upgrade list and uses the newest matching upgrade.
- If the upgrade status stays nonterminal until the timeout, the system reports `timeout` and stops polling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST add menu `293` as a destructive operation through the wiring manifest.
- **FR-002**: The system MUST show a sub-menu with `claim`, `assign`, `unassign`, `bounce data ports`, and `upgrade` steps.
- **FR-003**: Each step MUST require its typed confirmation word before it sends a request.
- **FR-004**: Each step MUST support dry-run and MUST send no request during dry-run.
- **FR-005**: The claim step MUST never write the claim code to a log message or output row.
- **FR-006**: Each request body MUST match the OpenAPI schema for its Mist operation.
- **FR-007**: The upgrade step MUST poll status until a terminal status occurs or `UPGRADE_POLL_TIMEOUT_SECONDS` expires.
- **FR-008**: The system MUST write `MxEdgeLifecycleLog.csv` under `data/` with one row per request or dry-run.
- **FR-009**: The wiring manifest MUST include every section required by the fleet contract.
- **FR-010**: The release note fragment MUST exist at `changelog.d/issue-3573-mxedge-lifecycle.md`.
- **FR-011**: The implementation MUST reuse the existing Mist Edge read patterns from menu 50 and menu 71 where applicable.

### Key Entities

- **Lifecycle Step**: One destructive action selected by the operator. It carries a name, a confirmation word, a request body, and a dry-run flag.
- **Lifecycle Log Row**: One CSV row under `data/` that records the step, target identifiers, dry-run state, request status, and a redacted detail.
- **Upgrade Poll Result**: The latest upgrade status read during the polling loop. It records whether the upgrade is terminal, timed out, or still running.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Unit tests prove all five steps send no request before the correct confirmation word.
- **SC-002**: Unit tests prove all five request body shapes match the OpenAPI examples.
- **SC-003**: Unit tests prove the claim code never appears in captured logs or output rows.
- **SC-004**: Unit tests prove dry-run sends zero API calls for all five steps.
- **SC-005**: Unit tests prove upgrade polling stops on a terminal status and on timeout.
- **SC-006**: The package and tests pass py_compile, ruff, black, mypy, pydocstyle, pytest, vulture, and interrogate.

## Assumptions

- The integration pull request will add the menu entry to `MistHelper.py`, `OperationRegistry`, primary key strategy records, and generated references.
- The installed `mistapi` package exposes the named Mist Edge operation IDs.
- `latest` is an acceptable upgrade version alias when the Mist API recommends it.
- The operation stores local evidence only in `data/MxEdgeLifecycleLog.csv`.
