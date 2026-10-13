# Feature Specification: Runtime-Dependent Portal Controls

**Feature Branch**: `4053-runtime-dependent-controls`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Repair the missing browser controls for menus 91 and 195. Keep command-line behavior. Carry browser answers to the correct prompts, reject invalid or exhausted input, and require explicit selection before any optional write-back. Menus 94-96 are already fixed and stay out of scope."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter the manufacturer report (Priority: P1)

An operator runs menu 91 in the browser and can enter one manufacturer name or leave the field empty to include every manufacturer.

**Why this priority**: The missing control prevents the operator from selecting the report that the menu supports.

**Independent Test**: Request the menu 91 form and run its answer through the existing prompt. Verify the named manufacturer is selected, and an empty answer keeps every manufacturer.

**Acceptance Scenarios**:

1. **Given** menu 91 has manufacturers, **When** the operator enters an exact manufacturer name, **Then** the report filters to that manufacturer.
2. **Given** menu 91 has manufacturers, **When** the operator leaves the field empty, **Then** the report includes every manufacturer.
3. **Given** the operator enters a name that is not present, **When** the prompt reads it, **Then** the operation rejects the value and does not select another manufacturer.

### User Story 2 - Audit a selected address file safely (Priority: P1)

An operator runs menu 195 in the browser and selects the available primary file, optional authority file, optional business name, and post-table action.

**Why this priority**: A positional answer sent to the wrong prompt can audit an unintended file or cause an operation to stop incorrectly.

**Independent Test**: Request menu 195 controls with mocked files and settings, then exercise the prompt chain with those answers. Verify each answer reaches its intended prompt.

**Acceptance Scenarios**:

1. **Given** more than one address file exists, **When** the operator opens menu 195, **Then** the form offers the current server-side file choices for the primary file.
2. **Given** exactly one address file exists, **When** the operator opens menu 195, **Then** the operation keeps its existing automatic primary-file selection and the next answer reaches the authority-file prompt.
3. **Given** an authority-file choice is available, **When** the operator selects a file or skips it, **Then** the choice reaches only the authority-file prompt.
4. **Given** the operator chooses to save the comparison, **When** the operation reaches the write-back gate, **Then** it makes no Mist change unless the operator explicitly selects yes.
5. **Given** an invalid or exhausted browser answer, **When** the relevant prompt reads it, **Then** the operation stops or takes its documented safe default without consuming a later answer as a substitute.

### Edge Cases

- No address files exist when the operator opens menu 195.
- The address-file list changes after the form is built.
- A submitted file choice is invalid or no longer available.
- The configured business name removes the business-name prompt.
- The operator chooses quit, so no report or write-back prompt follows.
- No address rows qualify for write-back.
- The browser answer queue ends before a prompt receives a value.
- Menus 94, 95, and 96 remain unchanged and retain their current controls.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 91 MUST provide an optional browser control for the manufacturer prompt.
- **FR-002**: An empty menu 91 answer MUST preserve the existing all-manufacturer report behavior.
- **FR-003**: A menu 91 answer MUST select the exact requested manufacturer or be rejected.
- **FR-004**: Menu 195 MUST show primary-file choices only when its prompt requires a choice.
- **FR-005**: Menu 195 MUST build file choices from the server-side address-file list available when the form is built.
- **FR-006**: Menu 195 MUST keep every browser answer aligned with the prompt that asks for it, including optional prompts and prompts that do not run.
- **FR-007**: Menu 195 MUST preserve the optional authority-file and business-name prompts.
- **FR-008**: Menu 195 MUST offer an explicit save or quit choice after it displays the comparison.
- **FR-009**: Menu 195 MUST require an explicit affirmative operator choice before address write-back.
- **FR-010**: Missing, invalid, or stale browser answers MUST stop safely or use an existing safe default without reaching another prompt with the wrong answer.
- **FR-011**: The command-line prompt behavior for menus 91 and 195 MUST remain available.
- **FR-012**: The existing controls for menus 94, 95, and 96 MUST remain unchanged.
- **FR-013**: Tests for this repair MUST use mocked files and provider responses and MUST make no Mist API call.

### Key Entities

- **Browser answer**: A value submitted by the operator for one menu prompt.
- **Address-file choice**: A server-side CSV or TSV file that menu 195 can audit.
- **Write-back decision**: The operator's explicit choice to allow or decline a change to Mist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every browser control for menus 91 and 195 maps to the prompt that uses its answer in all tested prompt-order cases.
- **SC-002**: All valid menu 91 manufacturer choices select the requested manufacturer, and an omitted choice preserves the all-manufacturer result.
- **SC-003**: No invalid, stale, or exhausted browser answer causes menu 195 to write to Mist or to hang.
- **SC-004**: Menus 94, 95, and 96 retain their existing controls.
- **SC-005**: All tests run without production credentials or live Mist requests.

## Assumptions

- An operator can identify a manufacturer by its exact name after menu 91 fetches the report data.
- Menu 195 continues to use its current automatic selection when only one primary address file exists.
- Menu 195 keeps the existing save, quit, and write-back confirmation rules.
- Issue #4029 is the parent tracking record. Current main already fixes menus 94 through 96, so the repair covers only the residual menu 91 and 195 defects.
