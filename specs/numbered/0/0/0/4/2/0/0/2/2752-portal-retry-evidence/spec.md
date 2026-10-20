# Feature Specification: Portal retry evidence

**Feature Branch**: `jmorrison-juniper-portal-retry-evidence`

**Created**: 2026-10-19

**Status**: Implemented

**Input**: Complete the bounded portal retry repair for #2752.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explain a capture retry (Priority: P1)

The operator needs the first timeout cause after a later attempt returns no data, fails, or succeeds.

**Why this priority**: A later result must not remove the cause of an earlier failure.

**Independent Test**: Supply a timeout and a distinct later result through a mocked capture dependency.

**Acceptance Scenarios**:

1. **Given** a timeout followed by no data, **When** capture stops, **Then** a warning retains the timeout class and message.
2. **Given** a timeout followed by success, **When** capture returns, **Then** the warning remains and the successful value stays unchanged.
3. **Given** three timeouts, **When** attempts end, **Then** the first timeout remains in the warnings.

### User Story 2 - Explain tracker failures (Priority: P1)

The operator needs the first file failure after a later read or replacement succeeds or fails.

**Why this priority**: The tracker supports restart recovery during an upgrade.

**Independent Test**: Use temporary files and controlled file failures without a device connection.

**Acceptance Scenarios**:

1. **Given** different read failures, **When** the reader returns no data, **Then** a warning retains the first failure.
2. **Given** a replacement failure followed by success, **When** replacement completes, **Then** its warning retains the first failure.
3. **Given** exhausted replacement attempts and a cleanup failure, **When** replacement raises, **Then** it raises the final replacement failure.
4. **Given** an absent tracker, **When** the reader checks it, **Then** it returns the existing empty result without an absence warning.

### User Story 3 - Explain a settle retry (Priority: P2)

The operator needs the first ping failure at the normal warning level.

**Why this priority**: Debug-only evidence is not visible at the normal operator boundary.

**Independent Test**: Supply distinct ping outcomes through the existing single-attempt dependency.

**Acceptance Scenarios**:

1. **Given** a ping failure followed by success or a false result, **When** the check returns, **Then** a warning retains the first failure.
2. **Given** distinct failures through exhaustion, **When** the check raises, **Then** the final exception remains unchanged and the first warning remains.

### Edge Cases

- A missing file remains a normal initial state.
- Cleanup failure must not replace the final replacement exception.
- Immediate success produces no failure warning.
- Diagnostics must not include tracker contents.
- Placeholder settle checks must not gain artificial external operations.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preserve the first failure class and message in operator-visible capture, tracker, and ping diagnostics.
- **FR-002**: Preserve attempt limits, delays, successful values, empty results, and final exception contracts.
- **FR-003**: Preserve atomic tracker replacement, locking, and file paths.
- **FR-004**: Attempt scratch cleanup after replacement exhaustion and report its failure without replacing the replacement exception.
- **FR-005**: Exclude tracker contents and credentials from new diagnostics.
- **FR-006**: Use mocked dependencies and temporary files for verification. Make no live request or device change.

### Key Entities

- **Failed attempt**: An operation, attempt number, exception class, and exception message.
- **Tracker**: The existing restart record whose replacement must remain atomic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested first failure remains visible after a distinct later result.
- **SC-002**: Controlled sequences retain the exact existing attempt and delay counts.
- **SC-003**: The final replacement exception survives a cleanup failure by object identity.
- **SC-004**: Tests make zero live requests and zero device changes.

## Assumptions

- Warning logs satisfy the evidence requirement without a new result schema.
- API, firmware, and neighbor settle checks remain placeholders. They perform no external operation that can lose failure evidence.
- The existing ping dependency is the meaningful seam for settle retry verification.
- The preceding assessment covers the other manifest paths. This slice confirms the remaining portal paths on current main.
- A human must review this upgrade-path change. Do not enable automatic merge.
