# Feature Specification: Discoverable Upgrade Confirmation Navigation

**Feature Branch**: `fix/2447-confirmation-navigation`
**Created**: 2026-09-10
**Status**: Ready for implementation
**Input**: GitHub issue #2447 — operators cannot discover the final confirmation page from an awaiting upgrade run.

## User Scenarios & Testing

### User Story 1 - Resume a prepared upgrade (Priority: P1)

An operator viewing a prepared upgrade run must be able to reach the final confirmation page without knowing or typing a hidden URL.

**Why this priority**: Without this path, a prepared run cannot be completed through normal UI navigation.

**Independent Test**: Seed an `awaiting_confirmation` run, open its run page, and follow the visible action to the confirmation page.

**Acceptance Scenarios**:
1. **Given** an existing run in `awaiting_confirmation` with a verified pre-check, **when** the operator opens the run page, **then** a visible Review/Confirm action links to that run's confirmation page.
2. **Given** the visible action, **when** the operator selects it, **then** the browser opens the matching confirmation page and shows the confirmation safety controls.
3. **Given** a run without a verified pre-check or with an unavailable run record, **when** the operator opens the run page, **then** no misleading final-confirmation action is offered.

### User Story 2 - Preserve safety gates (Priority: P1)

The new navigation must expose the confirmation page but must not bypass site-lock, pre-check, target, or typed-confirmation safeguards.

**Independent Test**: Open the link with a run whose safety prerequisites are incomplete and verify the confirmation controls remain locked.

**Acceptance Scenarios**:
1. **Given** a confirmation page reached through the new link, **when** the site is not owned, **then** the begin control remains unavailable and the page explains the required lock state.
2. **Given** a valid confirmation page, **when** the operator has not typed the exact confirmation word, **then** the begin control remains disabled.

### Edge Cases
- The run state changes between page render and link selection; the confirmation page must re-evaluate current stored safety state.
- A run has a pre-check but zero targets; the link may be visible for review, while the confirmation page keeps start disabled and explains why.
- The operator refreshes or opens the link in a second tab; the link remains stable and identifies the same run.

## Requirements

### Functional Requirements
- **FR-001**: The run page MUST show a clearly labeled Review/Confirm action for an `awaiting_confirmation` run with a verified pre-check.
- **FR-002**: The action MUST navigate to the existing confirmation page for the same run without requiring manual URL entry.
- **FR-003**: The action MUST have a stable accessibility/test identifier.
- **FR-004**: The run page MUST NOT present the action for states that are not ready for confirmation.
- **FR-005**: The confirmation route MUST continue to enforce all existing safety gates and MUST NOT start an upgrade merely because it was reached through the link.
- **FR-006**: Automated route and browser tests MUST cover rendering and navigation from History/run-page recovery.
- **FR-007**: Issue #2447 MUST be updated with the SpecKit artifacts, implementation evidence, and test results.

### Key Entities
- **Upgrade run**: A persisted workflow record with state, pre-check, targets, and site identity.
- **Confirmation page**: The final review screen that requires all safety prerequisites and exact typed confirmation before any upgrade submission.

## Success Criteria

- **SC-001**: An operator can reach the confirmation page from an `awaiting_confirmation` run in one visible click.
- **SC-002**: 100% of prepared runs rendered by the route expose the correct run-specific destination.
- **SC-003**: Existing confirmation safeguards remain unchanged and all focused contract/E2E tests pass.
- **SC-004**: A Playwright usability run completes the History → run page → confirmation path without direct URL entry.

## Assumptions
- The existing confirmation route and safety checks are the source of truth; this feature adds discoverability only.
- A run is considered ready for the link when its state is `awaiting_confirmation` and it has a pre-check identifier.
- The production gateway upgrade will not be submitted during validation.

## Non-Goals
- Changing upgrade submission authorization or confirmation wording.
- Repairing the other lifecycle defects recorded in issue #2447.
- Scheduling or starting a production firmware upgrade.
