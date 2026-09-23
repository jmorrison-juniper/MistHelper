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

## Functional Requirements

- FR-001: The options view must return selected_types, reboot, junos_file_action, and force.
- FR-002: The options template must restore saved values and keep first-visit defaults.
- FR-003: The browser must hide and disable controls that do not apply to the selected families.
- FR-004: The canary phases field must show only for the canary strategy.
- FR-005: The reboot delay placeholder must be guidance, not an example value.
- FR-006: A request refusal must move focus to the flash message.
- FR-007: Option refusal text must name a page label and must not name an internal field.
