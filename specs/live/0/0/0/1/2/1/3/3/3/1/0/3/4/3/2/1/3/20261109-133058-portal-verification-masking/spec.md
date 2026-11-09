# Feature Specification: Portal verification masking

**Feature Branch**: `jmorrison-juniper-portal-verification-masking`

**Created**: 2026-11-09

**Status**: Approved for local implementation only

**Input**: Mask the menu 247 verification field without changing its submitted value or the existing positional answer contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enter a verification value privately (Priority: P1)

The operator enters the email verification value without displaying its characters to a nearby observer.

**Why this priority**: The current control displays the verification value.

**Independent Test**: Enter a synthetic value, inspect the control, and capture the submitted answer without executing a Mist operation.

**Acceptance Scenarios**:

1. **Given** menu 247, **When** the form opens, **Then** the verification control masks its characters and retains its label.
2. **Given** an empty verification control, **When** validation runs, **Then** the Run button remains disabled.
3. **Given** a synthetic value, **When** the operator selects Run, **Then** the submitted positional answer preserves every character.
4. **Given** another text control, **When** the form opens, **Then** that control remains an ordinary text control.

### Edge Cases

- Clearing the verification value disables Run again.
- Spaces, punctuation, and leading zeroes remain unchanged in the submitted value.
- Menu 247 remains available. The mitigation does not disable the operation.
- An unknown control type retains the current ordinary text behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Only the menu 247 email verification control MUST mask its displayed characters.
- **FR-002**: The control MUST retain its name, label, placeholder, and required status.
- **FR-003**: The submission MUST preserve the complete value and its existing position.
- **FR-004**: Other controls MUST retain their existing behavior.
- **FR-005**: Tests MUST use synthetic values and MUST NOT call Mist or read real credentials.
- **FR-006**: The change MUST remain local until the publication hold ends.

### Key Entities

- **Verification value**: The operator answer needed by menu 247.
- **Parameter definition**: The ordered control description supplied to the browser.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Exactly one registered verification control masks its characters.
- **SC-002**: Every tested synthetic answer reaches the submission unchanged.
- **SC-003**: Empty-value validation and label association pass every focused check.
- **SC-004**: Tests make zero Mist requests.

## Assumptions

- Native password masking is sufficient for this display-only mitigation.
- Masking does not encrypt the value or remove it from browser memory or request data.
- SDK log privacy remains unresolved. This change is not a complete security fix.
- The user permits the narrow `operation.py` change after the explicit handover from the owner of local issue #4129.
- Later integration must preserve commit `a34b593f0ae571d1c323552fd2c1bd40122b67a5` and its separate import comments.
- No public issue, pull request, push, rebase, or merge is permitted.
