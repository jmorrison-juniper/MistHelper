# Feature Specification: RRM optimize or reset plan capture

**Feature Branch**: `feat/3571-rrm-reset-plan`  
**Issue**: `#3571`  
**Menu**: `291`  
**Category**: `destructive`  
**Created**: 2026-09-29  
**Status**: Draft  
**Input**: "menu 291 RRM optimize or reset with a before and after channel plan"

## User Scenarios and Testing

### User Story 1 - Capture an RRM optimization change (Priority: P1)

A NOC engineer selects a site, selects `OPTIMIZE`, captures the current plan, confirms the action, and receives before, after, and diff files.

**Why this priority**: Optimization can change channels or power. The operator needs a before record before Mist changes radios.

**Independent Test**: Use fixture channel plans, confirm `OPTIMIZE`, assert that the before writer runs before the client request, then assert that the diff lists only changed radios.

**Acceptance Scenarios**:

1. **Given** a selected site and action `OPTIMIZE`, **When** the operator types `OPTIMIZE`, **Then** the operation writes `RrmPlanBefore.csv` before it calls `optimizeSiteRrm`.
2. **Given** a selected site and action `OPTIMIZE`, **When** `--dry-run` is enabled, **Then** the operation writes `RrmPlanBefore.csv` and sends no Mist change request.

---

### User Story 2 - Reset AP radios to RRM control (Priority: P1)

A NOC engineer selects a site, selects `RESET`, captures the current plan, confirms the action, and sends the reset request.

**Why this priority**: A reset changes radio control for every AP at the site. The operator needs a durable before record.

**Independent Test**: Use a fake client and writer, confirm `RESET`, and assert that `resetSiteAllApsToUseRrm` starts only after the before write.

**Acceptance Scenarios**:

1. **Given** a selected site and action `RESET`, **When** the operator types `RESET`, **Then** the operation writes `RrmPlanBefore.csv` before it calls `resetSiteAllApsToUseRrm`.
2. **Given** a selected site and action `RESET`, **When** the operator types any other value, **Then** the operation sends no Mist request.

---

### User Story 3 - Compare the post-action channel plan (Priority: P2)

A NOC engineer waits for a configured settle period, captures the site plan again, and receives a diff that names changed radios only.

**Why this priority**: The operator needs a focused report that shows channel, width, or power differences.

**Independent Test**: Use before and after fixtures, then assert that unchanged radios are absent from `RrmPlanDiff.csv`.

**Acceptance Scenarios**:

1. **Given** before and after captures, **When** only one radio changes power, **Then** the diff has one row for that radio.
2. **Given** no `RRM_SETTLE_SECONDS`, **When** the operation waits, **Then** the settle time is `300` seconds.
3. **Given** `RRM_SETTLE_SECONDS=5`, **When** the operation waits, **Then** the settle time is `5` seconds.

### Edge Cases

- If the site prompt returns no site, the operation stops before any file write or Mist change request.
- If the confirmation word does not match the selected action, the operation stops after the before capture.
- If the before capture cannot be written, the operation sends no Mist change request.
- If the after capture fails, the operation keeps the before file and logs the failure.
- If a radio is missing from the after capture, the diff marks the radio as `missing_after`.

## Requirements

### Functional Requirements

- **FR-001**: The operation MUST use menu number `291` and category `destructive`.
- **FR-002**: The operation MUST support actions `OPTIMIZE` and `RESET`.
- **FR-003**: The operation MUST ask the operator to type `OPTIMIZE` or `RESET` before it sends a Mist change request.
- **FR-004**: The operation MUST support `--dry-run` and send no Mist change request when dry-run is enabled.
- **FR-005**: The operation MUST capture and write `RrmPlanBefore.csv` before it sends a Mist change request.
- **FR-006**: The operation MUST reuse the channel plan read used by menu `86`.
- **FR-007**: The operation MUST call `optimizeSiteRrm` for `OPTIMIZE`.
- **FR-008**: The operation MUST call `resetSiteAllApsToUseRrm` for `RESET`.
- **FR-009**: The operation MUST default the settle time to `300` seconds.
- **FR-010**: The operation MUST read `RRM_SETTLE_SECONDS` from the environment when it is set to a positive integer.
- **FR-011**: The operation MUST write `RrmPlanAfter.csv` after the settle time.
- **FR-012**: The operation MUST write `RrmPlanDiff.csv` with only radios whose channel, width, or power changed.
- **FR-013**: The operation MUST log before and after each Mist API call without logging secrets.
- **FR-014**: The wiring manifest MUST state the deferred menu registration details for the integration pull request.
- **FR-015**: The release note fragment MUST name issue `#3571`.

### Key Entities

- **RRM Action**: The destructive action. Values are `OPTIMIZE` and `RESET`.
- **RRM Radio Plan Row**: One AP radio with site, AP identity, band, channel, width, and power.
- **RRM Plan Diff Row**: One changed radio with before and after channel, width, and power values.
- **RRM Run Settings**: Runtime settings, including dry-run and settle seconds.

## Success Criteria

- **SC-001**: A unit test proves that a Mist change request cannot occur before `RrmPlanBefore.csv` is written.
- **SC-002**: A unit test proves that wrong confirmation and dry-run mode send no Mist change request.
- **SC-003**: A unit test proves that the diff contains changed radios only.
- **SC-004**: A unit test proves that the settle time default is `300` seconds and the environment override works.
- **SC-005**: The local gates for the new package and tests pass before the draft pull request opens.

## Assumptions

- The integration pull request registers menu `291` and imports `RrmResetOperation`.
- The operator runs the destructive action during a maintenance window.
- CSV export uses the existing MistHelper data directory behavior.
- The `optimizeSiteRrm` request body can be omitted unless the OpenAPI schema requires fields.
