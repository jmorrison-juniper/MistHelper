# Feature Specification: Endpoint family per-choice prompts

**Feature Branch**: `feat/3256-family-prompts`

**Created**: 2026-09-23

**Status**: Draft

**Input**: Issue #3256 asks the Operations portal to model the per-choice prompts for menus 263 through 268.

## User Scenarios & Testing

### User Story 1 - Run endpoint family rows from the browser (Priority: P1)

An operator selects one endpoint family row in the Operations portal. The portal shows the endpoint chooser first. After the operator selects one endpoint, the portal shows the required controls for that endpoint.

**Why this priority**: Menus 263 through 268 are command-line only today. The operator cannot run them from the browser.

**Independent Test**: Select one operation in each family. Confirm that the portal shows the controls from that operation and enables Run only after each required answer exists.

**Acceptance Scenarios**:

1. **Given** a menu 263 through 268 row, **When** the operator selects an endpoint, **Then** the portal shows the later controls for that endpoint.
2. **Given** a selected endpoint with required controls, **When** one required answer is empty, **Then** the portal keeps Run disabled.
3. **Given** all required answers exist, **When** the operator starts the run, **Then** the answer order matches the command-line prompt order.

### Edge Cases

- If an endpoint has no later prompt, the chooser alone must enable Run after selection.
- If an endpoint requires the cached organization identifier, the portal must not add an extra queued answer that shifts later prompts.
- If the operator changes the endpoint choice, the portal must remove the old dynamic controls.

## Requirements

### Functional Requirements

- **FR-001**: The portal MUST make menus 263 through 268 browser-runnable after it can render per-choice controls.
- **FR-002**: The portal MUST build each endpoint family chooser from the exporter table.
- **FR-003**: Each chooser option MUST carry the selected operation's `required` tuple.
- **FR-004**: The portal MUST render required controls in the same order that the handler reads prompts.
- **FR-005**: The portal MUST keep Run disabled until every visible required control has an answer.
- **FR-006**: The portal MUST not queue a cached organization identifier answer when the handler does not call `input()` for it.
- **FR-007**: The guard test MUST prove at least one operation in each family and state the source table count.

### Key Entities

- **Endpoint family menu**: One menu row from 263 through 268 with one exporter source table.
- **Endpoint option**: One operation row from `EndpointFamilyExporter`, including its operation name and required tuple.
- **Dynamic control**: One portal control rendered after an endpoint option is selected.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Six endpoint family rows return to `interactive` in `PARAMETER_REGISTRY`.
- **SC-002**: The guard test checks all six source tables and at least one option in each table.
- **SC-003**: The browser shows readable endpoint names and later controls for a selected option.
- **SC-004**: Local verification runs the changed unit tests and one browser check on port 9606.

## Assumptions

- The Operations portal already supplies the active organization identifier through application context.
- The `EndpointFamilyExporter.required` tuple remains the source of truth for endpoint identifiers.
- Destructive operation numbers are outside the menu range in this issue.
