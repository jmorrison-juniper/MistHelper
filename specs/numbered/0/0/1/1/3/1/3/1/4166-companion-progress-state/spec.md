# Feature Specification: Keep Companion Progress Out of Tracked Files

**Feature Branch**: `fix/4166-companion-progress-state`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Prevent Companion progress updates from making the main checkout dirty after a sync."

## User Scenarios & Testing

### User Story 1 - Keep a clean checkout (Priority: P1)

A network operations engineer uses the specification workflow after syncing the main checkout. The workflow does not change tracked progress records automatically.

**Why this priority**: An automatic change makes each sync dirty and forces engineers to review unrelated files.

**Independent Test**: Check the workflow configuration and confirm that each automatic progress action is disabled.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** a specification workflow step finishes, **Then** an automatic progress action does not change a tracked progress record.
2. **Given** a user-authored specification change, **When** the workflow finishes, **Then** the user-authored change remains available for review.

### Edge Cases

- If a new automatic Companion progress action is added, the regression check must fail until its policy is explicit.
- If the workflow configuration is missing or invalid, the regression check must fail.

## Requirements

### Functional Requirements

- **FR-001**: The specification workflow MUST NOT automatically change tracked progress records when a progress step finishes.
- **FR-002**: The workflow MUST preserve user-authored changes to specifications and progress records.
- **FR-003**: The workflow MUST disable automatic progress actions for specification, planning, task generation, implementation, and both convergence events.
- **FR-004**: A regression check MUST detect an enabled or missing automatic progress action.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All six automatic progress actions are disabled.
- **SC-002**: A clean checkout remains unchanged by the six automatic progress actions.
- **SC-003**: The regression check fails if one of the six actions is enabled or absent.

## Assumptions

- Companion's automatic progress actions are the source of the reported tracked-file changes.
- Users can continue to edit progress records explicitly when they need to preserve that information.
- The Companion extension and unrelated Git workflow actions remain enabled.
