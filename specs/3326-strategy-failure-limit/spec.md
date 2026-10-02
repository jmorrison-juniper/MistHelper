# Feature Specification: Strategy Failure Limit

**Feature Branch**: `jmorrison-juniper-strategy-failure-limit-controls`

**Created**: 2026-10-02

**Status**: Specified for local preparation

**Input**: Repair [issue #3326](https://github.com/jmorrison-juniper/MistHelper/issues/3326) with a template-only presentation change.

## User Scenarios & Testing

### User Story 1 - Show applicable controls (Priority: P1)

An operator sees the maximum failure percentage only when the selected strategy reads it.
The page must not suggest that Big bang applies a failure limit.

**Why this priority**: The current page offers a required value that the existing save correctly omits.

**Independent Test**: Load the actual organization options page and select each of its four strategy controls.

**Acceptance Scenarios**:

1. **Given** Canary, RRM, or Serial, **When** the page loads, **Then** the failure field is visible and enabled.
2. **Given** saved Big bang, **When** the page loads without JavaScript, **Then** the field is hidden and disabled.
3. **Given** an edited valid percentage, **When** strategies change repeatedly, **Then** applicable strategies restore the same value.
4. **Given** Big bang, **When** the operator selects Review, **Then** FormData and the save JSON omit the field.
5. **Given** an applicable strategy, **When** the operator selects Review, **Then** both payloads include the entered percentage.

### Edge Cases

- An enabled field retains its required state and its inclusive bounds of 0 through 100.
- A hidden field cannot block native form validation or receive keyboard focus.
- A saved zero remains zero. An absent saved percentage retains the default of 5.
- Repeated strategy changes do not clear an operator value.
- Review refusals keep the existing safety controls and messages.

## Requirements

### Functional Requirements

- **FR-001**: Hide and disable the failure field for Big bang before and after JavaScript runs.
- **FR-002**: Show and enable the failure field for Canary, RRM, and Serial.
- **FR-003**: Reuse the existing `data-org-requires-strategy` rule and shared visibility code.
- **FR-004**: Preserve the name, identifier, test identifier, label, bounds, default, required state, and saved value.
- **FR-005**: Omit disabled controls from FormData and the actual save JSON.
- **FR-006**: Retain a valid edited percentage across repeated strategy changes without a save.
- **FR-007**: Keep adjacent phase, device-version, reboot, Junos, Review, refusal, and keyboard behavior unchanged.
- **FR-008**: Use controlled cloud and process-owned store seams. Count SDK and firmware-start calls and require zero.
- **FR-009**: Prove failing guard decisions with direct negative controls and measured counts.
- **FR-010**: Validate desktop and narrow layouts with both current themes and actual strategy selectors.

### Key Entities

The existing strategy choice and maximum failure percentage remain unchanged.
This feature adds no record, schema, API field, or firmware policy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Four initial strategy cases have the required visibility, disabled state, and validation state.
- **SC-002**: Each applicable strategy posts the entered value. Big bang posts no failure percentage.
- **SC-003**: Repeated changes preserve the entered value and the existing model-specific version choices.
- **SC-004**: Browser evidence covers 1280-pixel desktop and a narrow viewport in `magenta` and `default`.
- **SC-005**: Negative controls fail for an absent rule and for a hidden enabled input.
- **SC-006**: Product changes affect only the owned organization options template. No firmware start occurs.

## Assumptions

The existing server omission for Big bang is intentional and remains authoritative.
The existing shared script already implements the required visibility and disabled state.
The parent authorizes a clean local validated commit only at queue position 40, after issue #3436.
No publication or delivery completion occurs before the parent's full verified-main SHA grant.
