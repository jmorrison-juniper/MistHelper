# Feature Specification: Typed operation outcomes

**Feature Branch**: `jmorrison-juniper-typed-operation-outcomes`
**Created**: 2026-10-19
**Status**: Contract batch
**Input**: Part of #3168. Establish the result contract before producer migrations.

## User Scenarios & Testing

### User Story 1 - Preserve the operation result (Priority: P1)

An operation author supplies a result with one explicit state and a readable
message. Message wording must not determine the state.

**Why this priority**: The portal currently reads log text to decide the result.
This contract is a prerequisite for removing that behavior.

**Independent Test**: Construct each permitted result with different messages.
Confirm that each result keeps its supplied state.

**Acceptance Scenarios**:

1. **Given** a completed result, **when** its message contains failure words,
   **then** its state remains completed.
2. **Given** an empty result, **when** its message changes,
   **then** its state remains no output.
3. **Given** missing input or a failure, **when** the result contains no marker
   phrase, **then** it keeps the supplied failure state.

### User Story 2 - Reject an invalid result (Priority: P1)

An operation author receives an explicit error when a result has an unsupported
state or an unreadable message.

**Why this priority**: A malformed result must not become an apparent success.

**Independent Test**: Supply an unknown state, missing text, or a value with
the wrong type. Confirm that construction fails.

**Acceptance Scenarios**:

1. **Given** an unknown state, **when** the author constructs a result,
   **then** construction reports the invalid state.
2. **Given** a valid result, **when** a caller attempts to change a field,
   **then** the result rejects the change.

### Edge Cases

- A message contains `failed to`, `could not`, `0 `, or `no site selected`.
- A required message contains only spaces or line breaks.
- Optional detail is absent, blank, or has the wrong type.
- A result passes through serialization without a state change.

## Requirements

### Functional Requirements

- **FR-001**: Supply one immutable operation result with a state, a message,
  and optional detail.
- **FR-002**: Permit only `completed`, `no_output`, `missing_input`, and `failed`.
- **FR-003**: Require a nonblank message and reject invalid values explicitly.
- **FR-004**: Preserve supplied text without using it to infer the state.
- **FR-005**: Keep portal classification and all existing handler behavior
  unchanged in this contract batch.
- **FR-006**: Record producer migration, lambda conversion, and portal replacement
  as serial prerequisites. Do not introduce a prose fallback.

### Key Entities

- **Operation outcome**: The explicit state and explanation of one operation.
  Detail supplies an optional explanation without credentials or private data.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All four permitted states retain their meaning for every tested
  message variant.
- **SC-002**: Every tested unsupported state and malformed text value fails
  construction with an explicit error.
- **SC-003**: A result retains all three fields through serialization.
- **SC-004**: This batch changes zero existing handler or portal verdict paths.

## Assumptions

- This batch establishes the contract only. It does not fix the portal prose
  defect and does not close #3168.
- The coordinator authorized this boundary on 2026-10-19.
- The unmerged specification in [PR #4019](https://github.com/jmorrison-juniper/MistHelper/pull/4019)
  requires serial migrations before portal replacement.
- The old telemetry design in spec 1021 shipped no production type named
  `OperationOutcome`. The new handler contract uses that name.
- Tests need no Mist session, network request, production credential, or device.
