# Feature Specification: Portal input privacy

**Feature Branch**: `jmorrison-juniper-portal-input-privacy`

**Created**: 2026-11-09

**Status**: Draft

**Input**: Protect queued portal answers from input diagnostics.

## User Scenarios & Testing

### User Story 1 - Protect submitted answers (Priority: P1)

An operator supplies answers to a portal operation. The operation receives the
answers, but input diagnostics do not disclose the values.

**Why this priority**: Operators can submit private values.

**Independent Test**: Run an operation with synthetic answers and inspect its
diagnostic records and events.

**Acceptance Scenarios**:

1. **Given** two queued answers, **When** an operation reads them, **Then** it
   receives the values in their original order.
2. **Given** an answer is read, **When** diagnostics are enabled, **Then** the
   diagnostic shows that a queued answer was consumed without its value.
3. **Given** an operation reads an answer, **When** the portal captures its
   diagnostics, **Then** neither the run log nor its events contain the answer.

### User Story 2 - Preserve input isolation (Priority: P2)

Concurrent operations receive only their own answers. An exhausted web queue
does not read from the console.

**Why this priority**: A change to diagnostics must not alter input behavior.

**Independent Test**: Run two synchronized operations with different answers
and test an empty queue and a console prompt.

**Acceptance Scenarios**:

1. **Given** two active operations, **When** each reads its answers, **Then**
   each receives only its own values.
2. **Given** an empty web queue, **When** an operation requests input, **Then**
   it receives the existing end-of-input error.
3. **Given** no web queue, **When** a caller requests input, **Then** the
   original console input receives the prompt.

### Edge Cases

- An empty answer remains an empty answer.
- Non-string queued values retain the existing string conversion.
- The queue is cleared after the operation.

## Requirements

### Functional Requirements

- **FR-001**: Input diagnostics MUST NOT include a queued answer.
- **FR-002**: A successful queued read MUST retain a useful diagnostic.
- **FR-003**: The input service MUST preserve queue order and value conversion.
- **FR-004**: The input service MUST preserve empty-queue and console behavior.
- **FR-005**: Concurrent operations MUST retain independent queues.
- **FR-006**: The portal run log and published events MUST NOT receive an
  answer from input-service diagnostics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every synthetic queued answer reaches its operation in order.
- **SC-002**: Zero synthetic answers appear in input diagnostics, run logs, or
  published events in the test.
- **SC-003**: Both synchronized operations receive only their own answers.

## Assumptions

- This change controls input-service diagnostics only. Other components that
  log an answer are outside this change.
- Existing portal event routing and run capture remain unchanged.
