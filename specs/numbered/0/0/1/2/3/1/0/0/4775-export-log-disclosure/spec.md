# Feature Specification: Export Log Disclosure

**Feature Branch**: `jmorrison-juniper-csv-logging-disclosure-fix`

**Created**: 2026-11-15

**Status**: Partially blocked

**Input**: Repair issue #4775 without changes to the exported data.

## User Scenarios & Testing

### User Story 1 - Export without disclosure (Priority: P1)

An operator exports inventory while diagnostic logging is active. The export
contains the requested data, but the logs do not disclose the data.

**Why this priority**: Logs can reach a wider audience than an export.

**Independent Test**: Export synthetic marker values and compare the file with
the captured diagnostic logs.

**Acceptance Scenarios**:

1. **Given** synthetic cell values, **When** an operator exports rows with
   diagnostic logging, **Then** the file retains the values and the logs do not.
2. **Given** synthetic device and site values, **When** an operator exports
   inventory, **Then** the file retains the values and the logs do not.

### User Story 2 - Diagnose export progress (Priority: P2)

An operator uses aggregate counts and failure context to diagnose an export.

**Why this priority**: Removing data disclosure must not remove useful status.

**Independent Test**: Capture logs for successful and failed exports.

**Acceptance Scenarios**:

1. **Given** a successful export, **When** diagnostic logging is active,
   **Then** the logs report row and field counts without row contents.
2. **Given** an export failure, **When** the failure is reported, **Then**
   the logs retain the failure context.

### Edge Cases

- Empty data must not disclose values or report a successful row write.
- Cells containing carriage returns, line feeds, quotes, and commas retain
  their existing CSV behavior.
- A failed address parse must not disclose the address in a diagnostic log.

## Requirements

### Functional Requirements

- **FR-001**: Export logs MUST NOT include exported row or cell values.
- **FR-002**: Inventory diagnostic logs MUST NOT include device identifiers,
  site data, addresses, or rendered device tables.
- **FR-003**: Export logs MUST retain aggregate row and field counts.
- **FR-004**: The output MUST retain the existing CSV data and column order.
- **FR-005**: Failure reports MUST retain useful context without row contents.
- **FR-006**: Tests MUST use synthetic markers and verify output and logs.

### Key Entities

- **Export row**: A set of field names and values requested by an operator.
- **Diagnostic record**: A log entry that describes progress or a failure.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All synthetic markers in the selected scenarios remain in the
  expected output and none appear in captured logs.
- **SC-002**: Successful row exports report row and field counts.
- **SC-003**: CSV carriage-return regression scenarios continue to pass.

## Assumptions

- The scope is the shared CSV exporter and organization inventory exporter.
- The existing CSV fix remains the base of this change.
- Issue #4762 retains the inventory source. Its logging repair is blocked
  until the owner releases the file or integrates the change.
- An authenticated staging test requires an authorized token and a verified
  staging organization. Neither is available in this session.
