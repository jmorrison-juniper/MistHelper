# Feature Specification: Virtual Chassis Menu Guidance

**Feature Branch**: `fix/4747-virtual-chassis-menu-options`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue 4747, "Bug: virtual chassis messages name incorrect menu options". The issue is open. Its labels are `bug`, `MistHelper.py`, and `needs-human-review`. It has no comments.

## Clarifications

### Session 2026-11-26

- Q: Which menu numbers must the printed guidance name? A: Menu 161 for a single conversion, menu 162 for a bulk conversion by site list, and menu 14 for the conversion status check. The registry and the menu table on `main` agree (RC-25 to RC-27, RC-34 to RC-36).
- Q: Does the rollback guidance print after a bulk conversion? A: No. Only the single conversion path prints it. The bulk path does not call the success helper (RC-13, RC-15).
- Q: Does issue #4358 rename `tests/unit/test_virtual_chassis.py`? A: No. PR #4358 merged on 2026-11-13. It changes no path that contains `virtual` or `chassis`, and the file keeps its path on `main` (RC-49).
- Q: Does issue #2863 include the source file? A: Partly. The issue body names no file. The inventory that the body cites lists `src\mist\resources\device\virtual_chassis.py` (RC-50).
- Q: Does this change need approval before merge? A: Yes. The issue states that human review remains required. The `needs-human-review` label stays on the issue (D-11).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Status notes name the conversion menus (Priority: P1)

The status check prints usage notes at its end. The notes name menu 161 for a single conversion and menu 162 for a bulk conversion. An operator who follows a note reaches the matching operation.

**Why this priority**: The current notes send an operator to menu 92. Menu 92 selects a site and does not convert a switch.

**Independent Test**: Call the usage-note helper offline. The printed text names menus 161 and 162 and no other menu.

**Acceptance Scenarios**:

1. **Given** the status check ends, **When** the operator reads note 1, **Then** the note reads `Use menu 161 to convert individual switches`.
2. **Given** the status check ends, **When** the operator reads note 2, **Then** the note reads `Use menu 162 for bulk conversion by site list`.

### User Story 2 - The rollback note names the status check (Priority: P1)

A single conversion can change a device. The rollback guidance then names menu 14 for the conversion status check.

**Why this priority**: The current note sends an operator to menu 94. Menu 94 shows device statistics and does not verify a conversion.

**Independent Test**: Call the response handler with a success response offline. The printed text names menu 14 and no other menu.

**Acceptance Scenarios**:

1. **Given** a single conversion succeeds, **When** the rollback guidance prints, **Then** the guidance reads `Use menu 14 to verify conversion status after the device reboots.`

### User Story 3 - A menu change fails the tests (Priority: P2)

A maintainer changes a menu number in the registry or in the guidance. The offline tests fail until both sides agree again.

**Why this priority**: The defect passed the existing suite. No existing test checks the printed menu numbers (RC-41), so the suite cannot detect this defect.

**Independent Test**: Run the four new tests as described in `design/quickstart.md`. All four fail before the text change and pass after it.

**Acceptance Scenarios**:

1. **Given** the guidance names a menu, **When** the registry test runs, **Then** the menu has the expected category and a registered virtual chassis title.
2. **Given** a virtual chassis source file names menu 92, 93, or 94, **When** the static test runs, **Then** the test fails and names the file.

### Edge Cases

- A conversion that fails with an HTTP error or a `detail` error prints no rollback guidance. This behavior does not change.
- A dry run prints no rollback guidance. This behavior does not change (RC-106).
- A bulk conversion prints no rollback guidance. This behavior does not change. Adding it is out of scope (D-14).
- The status check prints a converted-prefix line that names no menu. The tests compare the exact set of named menus, so this line does not affect a result.
- A registry title that keeps the words `virtual chassis` passes the registry test. The test checks the category and the title words, not the full title.
- Operators with saved reports still see menus 92, 93, and 94 in those reports. The changelog fragment names the old and new numbers.

## Safety Statements

Warning: a virtual chassis conversion changes the Mist cloud. This change runs no conversion, and no new test starts one.

Warning: a conversion can need a factory reset and re-adoption to revert. The printed guidance states this (RC-09).

Caution: an operator who follows the old status note reaches menu 92. Menu 92 selects a site and starts no conversion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The status usage notes MUST name menu 161 for a single virtual chassis conversion.
- **FR-002**: The status usage notes MUST name menu 162 for a bulk conversion by site list.
- **FR-003**: The rollback guidance MUST name menu 14 for the conversion status check.
- **FR-004**: No printed virtual chassis guidance MUST name menu 92, 93, or 94.
- **FR-005**: Each comment and docstring in `virtual_chassis.py` MUST name the registered menu for its operation.
- **FR-006**: The docstring and comment in `tests/test_virtual_chassis.py` MUST name menu 161 for the single conversion path.
- **FR-007**: An offline test MUST compare each menu named by the guidance with `MistHelper.menu_actions` and `OperationRegistry`.
- **FR-008**: The new tests MUST run offline. They MUST NOT call a Mist API function or start a conversion.
- **FR-009**: The typed `CONVERT` confirmations MUST stay unchanged in the single and bulk paths.
- **FR-010**: The mistapi call sites and the registry categories MUST stay unchanged.
- **FR-011**: The change MUST add one changelog fragment under `changelog.d/`.
- **FR-012**: The change MUST NOT edit `MistHelper.py`, `CHANGELOG.md`, or any generated menu page.

### Mist Cloud Transport Requirements

- Not applicable. This change adds no Mist Cloud request and changes no existing request.
- Both conversion paths call `mistapi.api.v1.sites.devices.convertSiteVirtualChassisToVirtualMac` (RC-14, RC-15, RC-86).
- The endpoint is `/api/v1/sites/{site_id}/devices/{device_id}/vc/convert_to_virtualmac` in the local OpenAPI file (RC-85).
- No owned WebSocket transport is involved.

### Key Entities

- **Menu entry**: One row in `MistHelper.menu_actions`. It holds the menu number, the title, the category, and the destructive flag.
- **Registry entry**: One row in `OperationRegistry._REGISTRY`. It holds the category and the skip reason.
- **Guidance line**: One printed line that names one menu number.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The status usage notes name exactly menus 161 and 162.
- **SC-002**: The rollback guidance names exactly menu 14.
- **SC-003**: Each menu named by the guidance has the registered category and a virtual chassis title.
- **SC-004**: No virtual chassis source line and no root test line names menu 92, 93, or 94.
- **SC-005**: The four new tests fail before the text change and pass after it.
- **SC-006**: Each applicable gate in `tasks.md` reports its expected result, with no new finding.
- **SC-007**: Remote CI reports each required check as passed on the pull request.

## Assumptions

- A-1: The base is `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local module copy matches the remote blob (RC-03).
- A-2: Menus 161, 162, and 14 keep their titles and categories during this change.
- A-3: Operators read the printed text during a run. They do not depend on saved older reports.
- A-4: No open pull request changes a target file at research time. Task T001 repeats this check.
- A-5: The pinned mistapi 0.64.1 keeps the two called functions. This change does not alter the calls.
- A-6: A human reviews the pull request before merge.

## Out of Scope

- Changing menu numbers, titles, handlers, or categories.
- Changing the typed confirmations, dry-run behavior, or API calls.
- Adding rollback guidance to the bulk path (D-14).
- Splitting `virtual_chassis.py` or the unit test module. The plan records a separate remediation action.
- Editing historical records, such as `CHANGELOG.md`, `documentation/issue_checklists.md`, and older `specs/` folders.
- Renaming the unit test module. The rename claim in the issue is stale (RC-49).
- Running a conversion, a status check, or any live Mist operation.
