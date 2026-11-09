# Feature Specification: Cache generator error reporting

**Feature Branch**: `jmorrison-juniper-cache-error-reporting`

**Created**: 2026-11-09

**Status**: Approved

**Input**: Issue #1794, limited to cache generator failure reporting.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Diagnose a generation failure (Priority: P1)

The operator needs the filename, generator name, and exception type when cache generation fails.

**Why this priority**: Failure context must not expose secrets from the callback.

**Independent Test**: Use a simulated failing generator and inspect its failure record.

**Acceptance Scenarios**:

1. **Given** a failing generator, **When** generation runs, **Then** the result indicates failure and the record reports the exception type without exception text or traceback.
2. **Given** a successful generator, **When** generation runs, **Then** the result indicates success without a failure record.

### User Story 2 - Stop generation safely (Priority: P2)

An operator interrupt must stop generation instead of becoming an ordinary failure.

**Why this priority**: Cancellation must retain its existing behavior.

**Independent Test**: Use simulated interrupts and confirm that each reaches the caller.

**Acceptance Scenarios**:

1. **Given** an interrupted generator, **When** generation runs, **Then** the same interrupt reaches the caller without a failure or success record.

### Edge Cases

- A generator raises an ordinary exception other than a file error.
- A generator raises a keyboard interrupt or requests process exit.
- A missing cache causes the public entry point to invoke the generator.
- An exception or a chained exception contains a labeled or unlabeled secret.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Ordinary generator failures must retain the existing failure return.
- **FR-002**: Each failure record must retain the filename, generator name, and exception type.
- **FR-003**: Successful generation must retain its existing result and operator message.
- **FR-004**: Interrupts and exit requests must reach the caller unchanged.
- **FR-005**: Tests must use simulated generators and no live Mist operation.
- **FR-006**: The emitted failure record must exclude callback exception text and traceback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every tested ordinary failure reports its type in one error record without callback exception text.
- **SC-002**: Every tested success invokes generation once and reports success.
- **SC-003**: Every tested interrupt reaches the caller without a false completion message.
- **SC-004**: Every tested filtered handler output excludes the synthetic callback secrets.

## Assumptions

- The existing ordinary-exception boundary is intentional because callers supply generators.
- This slice changes one source file and its existing test file only.
- Issue #1794 remains open for the other slices.
- No push, pull request, or merge belongs to this slice.
