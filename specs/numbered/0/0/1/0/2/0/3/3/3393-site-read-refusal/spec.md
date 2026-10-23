# Feature Specification: Site read refusal

**Feature Branch**: `jmorrison-juniper-fix-org-upgrade-cloud-read`

**Created**: 2026-10-23

**Status**: Approved for implementation

**Input**: Repair issue #3393 without changing issue #3394 or starting a firmware operation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save after a cloud failure (Priority: P1)

An operator saves multi-site upgrade options after the cloud connection fails.
The portal names the cause and permits another save without changing the form.

**Why this priority**: The operator needs recovery instructions during a change window.

**Independent Test**: Fail the site read during a save with two selected sites.

**Acceptance Scenarios**:

1. **Given** entered options, **When** the site read fails, **Then** the portal returns 503 with a cloud-read message and recovery instructions.
2. **Given** a refused save, **When** the operator reads the form, **Then** each entered value remains and no new plan exists.
3. **Given** a restored connection, **When** the operator repeats the save, **Then** the portal saves the validated plan.

### User Story 2 - Read an affected page (Priority: P2)

An operator opens the options page or the confirmation page while the site read fails.
The portal reports the temporary cloud failure instead of an unexpected fault.

**Why this priority**: Each affected page needs the same explanation for the same failure.

**Independent Test**: Fail the site read when each page opens.

**Acceptance Scenarios**:

1. **Given** a valid selection, **When** either page cannot read the sites, **Then** the portal returns 503 with recovery instructions.
2. **Given** an existing plan, **When** the confirmation read fails, **Then** the portal preserves that plan and its saved options.

### Edge Cases

- A connection error and a timeout receive the same refusal.
- A refused replacement save preserves earlier saved options and plans.
- Missing sites keep the existing 404 refusal.
- Invalid options keep the existing 400 refusal.
- Successful reads retain the existing confirmation flow.
- Transport error details must not enter the response or reveal credentials.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The save and both page reads must return 503 for site transport failures.
- **FR-002**: Each refusal must name the cloud read and tell the operator how to repeat the action.
- **FR-003**: A failed save must create no plan, nonce, or saved options.
- **FR-004**: The options form must retain all entered values after a failed asynchronous save.
- **FR-005**: A refused replacement must preserve the earlier saved plan and browser state.
- **FR-006**: Existing successful reads, input validation, and missing-site refusals must remain unchanged.
- **FR-007**: Tests must use local mocks and must start no firmware operation.
- **FR-008**: The repair must not change the device-family selection rules of issue #3394.

### Mist Cloud Transport Requirements

The existing site reader uses `listOrgSites`, `listOrgSiteStats`, and the existing SDK pagination path.
This repair adds no transport and changes no SDK call.
Local contract tests replace the cloud-reader boundary and prove failure safety without credentials.

### Key Entities

- **Selection**: The signed organization and selected sites.
- **Options**: The operator choices, which remain unconfirmed after a failed save.
- **Plan**: The durable record that a successful save creates before typed confirmation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three affected actions return the temporary-service refusal for connection failures and timeouts.
- **SC-002**: A failed save creates zero plans and changes zero saved-option fields.
- **SC-003**: The browser retains every entered option after a refused save.
- **SC-004**: A successful repeated save reaches confirmation with the original choices.

## Assumptions

- Status 503 follows the existing cloud-failure convention in this portal.
- The existing asynchronous form retains values when the server refuses a save.
- A failed page read preserves an earlier plan but does not create a new plan.
- Human review remains necessary. This work does not close the issue, merge, or enable automatic merge.
