# Feature Specification: Juniper RMA prompt audit

**Feature Branch**: `jmorrison-juniper-prompt-audit-rma-paths`

**Created**: 2026-10-19

**Status**: Specified

**Input**: Repair the prompt audit and dependent identifier control counts for #4141.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect unanswered Juniper prompts (Priority: P1)

A maintainer compares each Juniper menu prompt with the browser controls.
The comparison must not require an exemption for a documented input path.

**Why this priority**: An undetected missing control can stop a browser operation before its export.

**Independent Test**: Audit the seven affected menus and compare their prompt counts with each selectable control sequence.

**Acceptance Scenarios**:

1. **Given** a Juniper menu, **When** the audit examines its handler, **Then** it reports each reachable prompt in order.
2. **Given** the seven repaired menus, **When** the guard runs, **Then** no audit exemption applies to them.

### User Story 2 - Count dependent identifiers (Priority: P1)

A maintainer sees the full control sequence for each key type.
The count includes the identifier between the key type and any later optional control.

**Why this priority**: A missing identifier shifts every later answer to the wrong prompt.

**Independent Test**: Compare both key choices for menus 295, 297, and 303, including a deliberately removed identifier.

**Acceptance Scenarios**:

1. **Given** either key choice, **When** the guard counts controls, **Then** it includes exactly one matching identifier.
2. **Given** a missing or extra control, **When** the focused test runs, **Then** the test fails with the menu and choice.

### Edge Cases

- Repeated calls to one helper represent separate prompts.
- Recursive calls must terminate within a bounded audit.
- A menu with no registry controls has an empty control sequence.
- Mutually exclusive controls must not be counted together.
- Both key choices require examination, even when only the second choice has a defect.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The audit MUST reach both documented Juniper input paths without changing their runtime behavior.
- **FR-002**: The guard MUST count dependent controls for every selectable Juniper key choice.
- **FR-003**: The guard MUST compare ordered prompt and control counts for all seven affected menus.
- **FR-004**: The seven exemptions MUST remain until the repaired audit and guard pass together.
- **FR-005**: Existing Juniper browser tests MUST remain and pass without external credentials.
- **FR-006**: Focused tests MUST reject missing, extra, and misplaced dependent controls.
- **FR-007**: The repair MUST preserve unrelated menu behavior and existing safety confirmations.

### Key Entities

- **Prompt sequence**: The ordered operator answers reached from a menu handler.
- **Control sequence**: The ordered browser controls for one complete choice path.
- **Audit exemption**: A recorded limitation that prevents the guard from judging a menu.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven affected menus pass the comparison without their former exemptions.
- **SC-002**: Both key choices pass for each of menus 295, 297, and 303.
- **SC-003**: Each deliberate missing, extra, or misplaced dependent control produces a failing comparison.
- **SC-004**: All existing Juniper browser scenarios pass with synthetic responses.

## Assumptions

- This repair changes development checks, not browser controls or Juniper service behavior.
- The shared audit belongs to `misthelper-devtools` and requires its own reviewed prerequisite.
- The existing browser tests establish the runtime prompt order.
- Other documented audit exemptions remain outside this issue.
