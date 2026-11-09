# Feature Specification: Other-device event failure boundaries

**Feature Branch**: `jmorrison-juniper-other-device-event-audit`

**Created**: 2026-11-09

**Status**: Specified

**Input**: Audit the single broad handler in the other-device event export for issue #1794.

## User Scenarios & Testing

### User Story 1 - Report the correct failure (Priority: P1)

An operator must not receive a cloud request error for a local export defect.

**Why this priority**: A wrong error message prevents correct diagnosis.

**Independent Test**: Inject a local failure and confirm that the original failure reaches the caller.

**Acceptance Scenarios**:

1. **Given** a transformation defect, **When** the export runs, **Then** the original exception reaches the caller.
2. **Given** a writer defect, **When** the export runs, **Then** no cloud failure message appears.
3. **Given** private text in an exception, **When** the export fails, **Then** exporter error logs contain none of that text.

### User Story 2 - Preserve the menu experience (Priority: P2)

An operator retains site selection, successful exports, empty results, and the existing response behavior for external request failures.

**Why this priority**: A boundary repair must not change unrelated export behavior.

**Independent Test**: Use offline responses and verify each menu outcome.

**Acceptance Scenarios**:

1. **Given** selected site events, **When** the export runs, **Then** the writer receives normalized rows and the endpoint name.
2. **Given** no events or canceled selection, **When** the export runs, **Then** no writer runs.
3. **Given** an external request failure, **When** the existing SDK handles it, **Then** the menu operation still returns.

### Edge Cases

- Failures can occur during the first endpoint request or a subsequent page request.
- Endpoint and pagination failures retain the existing menu fallback.
- Returned HTTP error statuses are a separate finding, not part of this repair.

## Requirements

### Functional Requirements

- **FR-001**: Preserve selection, output naming, normalization, endpoint metadata, and empty-result behavior.
- **FR-002**: Let transformation and writer exceptions reach the caller.
- **FR-003**: Do not log arbitrary exception text or tracebacks in this exporter.
- **FR-004**: Preserve the menu fallback for endpoint and pagination exceptions, including malformed remote pages.
- **FR-005**: Run all tests without DNS, sockets, real writers, or production credentials.

### Mist Cloud Transport Requirements

Retain `mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents` and `mistapi.get_all`.
Inspect the installed SDK offline before selecting any caught exception.
Use the real SDK with a mocked HTTP session to prove external-failure behavior.
Do not introduce a transport or change response-status handling.

### Key Entities

- **Selected site**: The existing site identifier and display name.
- **Event rows**: The existing normalized records supplied to the selected export backend.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every injected local defect reaches the caller unchanged.
- **SC-002**: Zero exporter log records contain synthetic exception text.
- **SC-003**: All success, cancellation, empty-result, and external-failure scenarios preserve their existing outcomes.

## Assumptions

- This slice does not repair HTTP response-status handling or SDK logging.
- Tests use synthetic data only.
- Local exception propagation is intentional. A caller can apply its existing error policy.
