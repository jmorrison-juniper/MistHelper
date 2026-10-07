# Feature Specification: Clarify the Phase-Watch Submission Boundary

**Feature Branch**: `jmorrison-juniper-docs-3332-phase-watch-boundary`

**Created**: 2026-10-06

**Status**: Draft

**Issue Title**: `docs(upgrade): clarify the phase-watch submission boundary`

**Input**: GitHub issue #3332, Child 1 only

## User Scenarios & Testing

### User Story 1 - Understand the Phase-Watch Boundary (Priority: P1)

As an operator, I need clear phase-watch wording so that I do not treat observation as a new upgrade submission.

**Why this priority**: An incorrect interpretation can cause an operator to start another upgrade during an uncertain submission.

**Independent Test**: Review each approved wording location and confirm that each statement uses the same submission boundary.

**Acceptance Scenarios**:

1. **Given** the portal sent upgrade requests, **When** the phase watch starts, **Then** the wording says that it observes submitted work.
2. **Given** an operator reads the phase-watch wording, **When** the operator identifies phase-watch actions, **Then** the wording says that the watch sends no firmware request.
3. **Given** the phase watch shows submitted work, **When** the operator evaluates the result, **Then** the wording does not claim cloud acceptance.
4. **Given** the portal sent requests for each device family, **When** the operator reads the result, **Then** the wording does not claim ordered submission.

---

### User Story 2 - Respond Safely to an Uncertain Submission (Priority: P2)

As an operator, I need a direct warning so that I do not start another upgrade when a submission result is uncertain.

**Why this priority**: A second upgrade can add risk when the first submission result is not known.

**Independent Test**: Review the operator warning and confirm that it prohibits another upgrade during an uncertain submission result.

**Acceptance Scenarios**:

1. **Given** a submission result is uncertain, **When** the portal presents the operator warning, **Then** the warning says not to start another upgrade.
2. **Given** the warning describes uncertainty, **When** an operator reads it, **Then** the warning does not define a recovery action or a retry rule.

### Edge Cases

- The wording must remain correct when the cloud has not confirmed request acceptance.
- The wording must remain correct when device-family requests can finish in an unknown order.
- The wording must not imply that observation starts before the portal sends upgrade requests.
- The wording must not imply that the phase watch can send, repeat, or repair a firmware write.

## Requirements

### Functional Requirements

- **FR-001**: The wording MUST state that the phase watch starts after the portal sends upgrade requests.
- **FR-002**: The wording MUST state that the phase watch observes submitted work.
- **FR-003**: The wording MUST state that the phase watch sends no firmware request.
- **FR-004**: The wording MUST state that the phase watch does not prove cloud acceptance.
- **FR-005**: The wording MUST state that the phase watch does not prove that the portal sent device types in phase order.
- **FR-006**: The operator warning MUST say not to start another upgrade when a submission result is uncertain.
- **FR-007**: The change MUST alter wording only.
- **FR-008**: The wording MUST remain consistent in the upgrade driver, the organization cascade walk, the organization phase list, and the phase-watch contract.
- **FR-009**: The release-note fragment MUST describe the wording clarification for issue #3332.
- **FR-010**: The change MUST NOT define or change the settle timeout.
- **FR-011**: The change MUST NOT define or change reachability gates.
- **FR-012**: The change MUST NOT define or change retry rules.
- **FR-013**: The change MUST NOT define or change resume behavior.
- **FR-014**: The change MUST NOT define or change firmware writes.
- **FR-015**: The change MUST NOT define or change lock behavior.
- **FR-016**: The change MUST NOT define or change durable states.
- **FR-017**: The change MUST NOT define or change route behavior.

### Approved Wording Scope

The implementation phase can update only these files:

- `src/interfaces/portals/upgrade_portal/upgrade/driver.py`
- `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`
- `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html`
- `tests/contract/upgrade_portal/test_org_phase_watch_contract.py`
- `tests/unit/upgrade_portal/test_org_phase_list_parity.py`
- `changelog.d/issue-3332-phase-watch-wording.md`

## Success Criteria

### Measurable Outcomes

- **SC-001**: All four approved wording locations state the same phase-watch submission boundary.
- **SC-002**: Each approved wording location states that the phase watch sends no firmware request.
- **SC-003**: No approved wording location claims cloud acceptance or proves that the portal sent device types in phase order.
- **SC-004**: The operator warning contains one direct instruction not to start another upgrade when a submission result is uncertain.
- **SC-005**: A review of the approved file set finds no behavior change and no change to any excluded subject.

## Assumptions

- The portal sends the upgrade requests before the phase watch starts.
- The phase watch observes work that the portal already submitted.
- Cloud acceptance can remain unknown after the portal sends a request.
- Device-family submission order is not evidence that the phase watch provides.
- Existing behavior remains unchanged because this feature changes wording only.
