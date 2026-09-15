# Feature Specification: Isolated AppContext State

**Feature Branch**: `2667-appcontext-state`

**Created**: 2026-09-15

**Status**: Draft

**Input**: User description: "Fix shared AppContext state in the entry point for issue #2667."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Each bootstrap owns a context (Priority: P1)

A host can create two `ApplicationBootstrap` objects in one process. Each bootstrap must receive a separate `AppContext` unless the caller passes a context object.

**Why this priority**: Shared sessions can leak the organization, the MSP grants, and the output state between invocations.

**Independent Test**: Construct two `ApplicationBootstrap(parse_cli=False)` objects with startup side effects patched out. Mutate one context. Confirm the second context stays clear.

**Acceptance Scenarios**:

1. **Given** two default bootstrap objects, **When** the first context stores a session, **Then** the second context has no session.
2. **Given** a caller passes one `AppContext` to two bootstrap objects, **When** both are created, **Then** both use that explicit context.
3. **Given** `MainEntrypoint.run()` starts, **When** it creates a bootstrap object, **Then** the invocation receives a fresh context.

### Edge Cases

- If a legacy caller reads `MistHelper.apisession` before bootstrap, the default entry-point context remains available.
- If a web host bootstraps twice in one process, the active context changes to the context for that bootstrap.
- If tests monkeypatch legacy module attributes, the module bridge writes to the active context only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create a new `AppContext` for each `ApplicationBootstrap` when no context is supplied.
- **FR-002**: The system MUST let a caller pass an `AppContext` explicitly.
- **FR-003**: The system MUST activate the bootstrap context before startup writes to legacy module attributes.
- **FR-004**: The system MUST keep legacy module context views working during the active invocation.
- **FR-005**: The system MUST cover the defect with a regression test that fails on `origin/main`.

### Key Entities

- **AppContext**: Holds one invocation's session, organization, MSP grants, output format, progress emitter, and runtime flags.
- **ApplicationBootstrap**: Owns startup parsing and side effects for one CLI or web invocation.
- **MainEntrypoint**: Owns the active context bridge for legacy module readers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two default bootstrap objects do not share the same `AppContext`.
- **SC-002**: A session written to the first bootstrap context is absent from the second bootstrap context.
- **SC-003**: The focused regression test passes after the fix.
- **SC-004**: The local compile, lint, format, type, and focused test gates pass.

## Assumptions

- Existing legacy module readers can continue to read `MainEntrypoint.context` during one active invocation.
- The initial class context can remain as a pre-bootstrap default if default bootstrap construction does not reuse it.
- No database schema, Mist API behavior, or menu operation changes are in scope.
