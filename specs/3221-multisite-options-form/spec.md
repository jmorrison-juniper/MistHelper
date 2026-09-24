# Feature Specification: Multi-site options form repair

## Problem

The multi-site upgrade options page reset saved choices, showed controls that did not apply, and left a refused Review out of view.

## User Stories

### Story 1: Saved choices return after Back

Given an operator saves multi-site options, when the operator returns from confirmation, then the page shows the same families, reboot choice, Junos action, and force choice.

### Story 2: Only applicable controls show

Given an operator changes the selected device families, when a family is cleared, then the page hides and disables the controls that apply only to that family.

### Story 3: Reboot delay guidance is clear

Given the reboot delay is empty, when the operator reads the field, then the placeholder states that an empty value reboots as soon as the write ends.

### Story 4: A refusal is visible

Given the Review is refused, when the message appears, then focus moves to the message and the text names a page label.

### Story 5: Each page keeps its own labels

Given a label test reads one page, when the test compares the label table with that page, then each label in the table matches a label that the page paints.

## Functional Requirements

- FR-001: The options view must return selected_types, reboot, junos_file_action, and force.
- FR-002: The options template must restore saved values and keep first-visit defaults.
- FR-003: The browser must hide and disable controls that do not apply to the selected families.
- FR-004: The canary phases field must show only for the canary strategy.
- FR-005: The reboot delay placeholder must be guidance, not an example value.
- FR-006: A request refusal must move focus to the flash message.
- FR-007: Option refusal text must name a page label and must not name an internal field.
- FR-008: The multi-site page must use a label table of its own. The single-site table must hold only the labels of the single-site page. Issue #3273 records the test failure that the shared table caused.
- FR-009: A refused target version must name the version control of the device family that holds the refused model.
- FR-010: If the route cannot read a canary phase, the failure percentage, or the start time, the refusal must name the multi-site control. The refusal must not repeat the typed value.
- FR-011: If no selected device type holds a typed target version, the refusal must name the control "Device types to upgrade".
