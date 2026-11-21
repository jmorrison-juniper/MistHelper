# Feature Specification: Locked Bootstrap Sources

**Feature Branch**: `jmorrison-juniper-fix-locked-bootstrap-mirror`

**Created**: 2026-11-15

**Status**: Draft

**Input**: Repair issue #4774 without changing dependency records or exposing private sources.

## User Scenarios & Testing

### User Story 1 - Create a Worktree Environment (Priority: P1)

A contributor creates a worktree environment with the committed dependency record.
A pip source setting must not make a valid locked installation fail without a clear reason.

**Why this priority**: Contributors need a reliable environment before they can work.

**Independent Test**: Compare isolated installation attempts with and without synthetic source settings.

**Acceptance Scenarios**:

1. **Given** a valid dependency record, **When** a contributor runs setup, **Then** setup uses the committed record.
2. **Given** a configured pip source, **When** setup runs, **Then** it reports any necessary source-policy distinction.
3. **Given** an installation failure, **When** setup reports the result, **Then** it stops and identifies the failure.

### User Story 2 - Preserve Explicit Source Choices (Priority: P2)

A contributor can retain an explicit package-source policy without exposing private source details.

**Why this priority**: A source policy can express an organization's package access requirements.

**Independent Test**: Run setup with synthetic explicit source settings and inspect the child settings and reports.

**Acceptance Scenarios**:

1. **Given** an explicit UV source setting, **When** setup starts, **Then** it preserves that setting or reports a conflict.
2. **Given** private source details, **When** setup reports its decision, **Then** the report omits those details.

### Edge Cases

- A primary source, an extra source, or both can be configured.
- The source can be unavailable, or installation can fail for a different reason.
- Source settings can have different precedence or can be empty.
- A second invocation must not retain an earlier invocation's decision.

## Requirements

### Functional Requirements

- **FR-001**: Setup MUST use the committed dependency record without modifying it.
- **FR-002**: Setup MUST distinguish pip source settings from explicit UV source settings.
- **FR-003**: Setup MUST preserve intentional explicit UV settings or stop with an actionable diagnostic.
- **FR-004**: Setup MUST report any change in the treatment of an explicit pip source policy.
- **FR-005**: Setup MUST stop when locked installation fails and MUST NOT use an unlocked fallback.
- **FR-006**: Setup MUST keep source values and credentials out of its diagnostics.
- **FR-007**: Setup MUST leave caller configuration unchanged.
- **FR-008**: Tests MUST use synthetic sources and MUST NOT contact a private mirror.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each supported synthetic source case has a deterministic pass or explicit failure.
- **SC-002**: No regression case changes the dependency record or exposes a source value.
- **SC-003**: A failed installation makes no later setup attempt.

## Assumptions

- The existing dependency record is authoritative and is outside this change.
- A staging smoke requires an authorized token and a verified staging organization.
- Windows verification requires access to a Windows host and is not implied by a macOS test.
