# Feature Specification: Generated Operations control labels

**Feature Branch**: `jmorrison-jnpr-fix-generated-control-labels`

**Created**: 2026-10-13

**Status**: Ready

**Input**: Repair issue #4059 without implementing issue #4041 as a feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify a generated parameter (Priority: P1)

An operator uses each visible parameter label to identify and select its control.

**Why this priority**: An unassociated label does not name the control for assistive technology.

**Independent Test**: Select menus 257 through 268 and each endpoint choice. Check every generated control against its visible label.

**Acceptance Scenarios**:

1. **Given** a generated parameter, **When** its label appears, **Then** the label references that parameter control.
2. **Given** an endpoint choice, **When** the operator changes the choice, **Then** each replacement control retains an associated label.
3. **Given** the existing form, **When** labels become associated, **Then** names, values, dependencies, request content, and mobile layout remain unchanged.

### Edge Cases

- A required parameter retains its visible required marker.
- A dependent parameter retains its label when the control becomes visible.
- An endpoint without additional parameters retains its existing controls.
- A text, number, or selection control uses the same association rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each generated parameter label MUST reference its control.
- **FR-002**: Menus 257 through 268 MUST satisfy FR-001 for every endpoint choice.
- **FR-003**: Field names, values, defaults, dependencies, and request content MUST remain unchanged.
- **FR-004**: The mobile layout MUST remain unchanged.
- **FR-005**: Tests MUST use an isolated portal without production credentials or live Mist operations.
- **FR-006**: The existing expected-failure proof MUST become a passing regression test for this defect only.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All examined generated controls in menus 257 through 268 have exactly one associated visible label.
- **SC-002**: No examined endpoint replacement leaves a stale label association.
- **SC-003**: All existing focused operation tests pass without changes to field behavior.
- **SC-004**: The form adds no horizontal overflow at a 402 by 874 mobile viewport.

## Assumptions

- The existing parameter names identify controls uniquely within the current form.
- Existing field identifiers are correct and do not need changes.
- Closed ownership blockers permit this narrow source repair.
- Issue #4041 supplies regression evidence only. It does not expand this change.
