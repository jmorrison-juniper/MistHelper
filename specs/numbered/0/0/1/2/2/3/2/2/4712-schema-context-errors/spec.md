# Feature Specification: Schema context errors

**Feature Branch**: `jmorrison-juniper-sqlite-context-failures`

**Created**: 2026-11-09

**Status**: Specified

**Input**: Issue #4712 requires local context failures to stop schema selection.

## User Scenarios & Testing

### User Story 1 - Preserve the endpoint schema (Priority: P1)

An operator needs an export to stop when an unexpected local failure prevents endpoint identification.

**Why this priority**: A local failure must not silently change the selected schema.

**Independent Test**: Inject a synthetic local failure and confirm that the original exception reaches the caller.

**Acceptance Scenarios**:

1. **Given** a matching endpoint context, **When** logging fails, **Then** the caller receives the original exception.
2. **Given** a broken context record, **When** inspection fails, **Then** the caller receives the original exception.
3. **Given** a valid inventory context, **When** selection succeeds, **Then** the natural primary key remains selected.

### User Story 2 - Preserve ordinary context detection (Priority: P2)

An operator needs valid endpoint detection and the legitimate unknown result to remain unchanged.

**Why this priority**: The repair must preserve normal exports.

**Independent Test**: Check each supported name pattern, the nearest match, absent frames, and unmatched frames.

**Acceptance Scenarios**:

1. **Given** matching frames, **When** detection runs, **Then** the nearest matching name returns.
2. **Given** no matching frame, **When** detection ends, **Then** `unknown` returns.
3. **Given** any detection outcome, **When** the method exits, **Then** its local frame reference is absent.

### Edge Cases

- The interpreter supplies no current frame.
- Reading a frame name or its parent raises an exception.
- Logging raises after a matching name is found.

## Requirements

### Functional Requirements

- **FR-001**: Unexpected local exceptions MUST propagate without schema substitution.
- **FR-002**: All six existing endpoint name patterns MUST retain their matching behavior.
- **FR-003**: Detection MUST return `unknown` only after a normal search without a match.
- **FR-004**: Detection MUST remove its local frame reference on success, absence, and failure.
- **FR-005**: Verification MUST use synthetic input with sockets and DNS blocked and no database operations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every injected local failure reaches the caller as the same exception object.
- **SC-002**: Every supported name pattern and legitimate absence case returns the expected name.
- **SC-003**: Every tested exit removes the local frame reference.
- **SC-004**: Verification performs zero network requests and opens zero databases.

## Assumptions

- This issue changes no schema declarations or existing database files.
- The reproduction demonstrates a strategy change, not data loss.
- Draft #4358 owns the schema test rename. Its owner granted an exclusive local handoff for the existing test.
- The user requires a local commit only, with no push or pull request.
