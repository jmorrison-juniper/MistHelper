# Feature Specification: Capture Click Journey Qualification

**Feature Branch**: `jmorrison-juniper-qualify-issue-3380-capture-journey`

**Created**: 2026-10-03

**Status**: Draft

**Input**: Issue #3380 and the native browser run at the accepted base.

## User Scenarios & Testing

### User Story 1 - Prove the capture-to-confirm click journey (Priority: P1)

An operator starts from the site list and reaches the run confirmation page by
clicking the controls that the portal currently renders.

**Why this priority**: The current test can skip after the options page and
therefore does not prove that the operator can save a plan.

**Independent Test**: Run the unchanged browser journey with the local stand-in
fixture. Require zero skips and complete the History return to the confirm page.

**Acceptance Scenarios**:

1. **Given** the local portal lists a site with AP, switch, and gateway devices,
   **When** the browser starts a run, **Then** the create response is 201.
2. **Given** the options page renders, **When** the browser checks the AP,
   switch, and gateway controls, **Then** each type has a device and a version.
3. **Given** the browser selects the offered versions, **When** it saves the plan,
   **Then** the save response is 200 and the confirm page opens.
4. **Given** the confirm page opens, **When** the browser opens History and
   reopens the run, **Then** it reaches the confirm page again.

### User Story 2 - Report local journey faults as failures (Priority: P1)

The browser test fails if the server refuses run creation or the page omits a
type version.

**Why this priority**: These conditions identify defects in the local test
fixture or portal. A skip would hide them as a green result.

**Independent Test**: Call the journey guard with refused create statuses and
empty type controls. Verify that it fails before an options save or firmware
start action.

**Acceptance Scenarios**:

1. **Given** run creation answers 409 or 503, **When** the journey checks the
   response, **Then** the test fails with a status-specific reason.
2. **Given** the portal lists a type without an offered version, **When** the
   journey checks its control, **Then** the test fails before it saves a plan.

## Edge Cases

- Keep a skip for an unavailable browser separate from a portal or fixture fault.
- Do not cancel a run that the test did not create.
- Keep the refused second-start journey unchanged.

## Requirements

### Functional Requirements

- **FR-001**: The journey MUST use the three current type controls.

- **FR-002**: The journey MUST require a device and an offered version for each
  of the three device types.

- **FR-003**: The journey MUST fail when run creation answers 409 or 503.

- **FR-004**: The journey MUST use the existing option-selection and plan-save
  helper from `test_upgrade.py`.

- **FR-005**: The journey MUST retain run-ledger cleanup before site-lock release.

- **FR-006**: The interface contract MUST remove the obsolete select-all row and
  identify the current type controls.

- **FR-007**: The repair MUST NOT change a shared fixture or support module.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The browser journey passes with zero skips.
- **SC-002**: The complete click walk reaches the confirm page after reopening
  the run from History.
- **SC-003**: The guard tests fail if the server refuses creation or a type lacks
  a version.
- **SC-004**: Teardown leaves no site holds or live runs.

## Assumptions

- The native fixture continues to supply one device of each type.
- The local server continues to provide versions through the shipped selector.
- The journey does not start firmware.
