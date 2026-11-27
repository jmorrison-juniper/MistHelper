# Feature Specification: Isolate Marvis Alarm Handling Modules

**Feature Branch**: `chore/4008-marvis-alarm-handling`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4008. Move the alarm acknowledgement and alarm join modules into one child package. The Marvis actions package then holds five structural children. Keep behavior, imports, and module-level names unchanged. This issue is a bounded child of parent issue #3824.

## Clarifications

### Session 2026-11-26

- Q: Which modules move? A: Only `acknowledgement.py` and `alarms.py`. They move from `src/mist/intelligence/marvis/actions/` to `src/mist/intelligence/marvis/actions/alarm_handling/`. Source: issue #4008, Constraints.
- Q: Does the record route match the issue number? A: Yes. The base-5 digits of 4008 are `00112013`, so the route is `0\0\1\1\2\0\1\3`. Source: research R33 and E-8.
- Q: May the change edit the symbol guard file now? A: No. Open PR #4208 holds `tests/guardrails/test_src_public_symbol_preservation.py`. The edit waits for a release or a file-scoped handoff. Source: research R44 and D-3.
- Q: Does a legacy record exist? A: Yes, on the archive branch `archive/laptop-20261121/jmorrison-juniper-4008-marvis-alarm-isolation`. It is not on main. Its claims are checked in research L1 to L10. Its text is not reused. Source: research R48 to R57.
- Q: Do logger names change? A: Yes. Each logger uses `__name__`, so each name gains the `alarm_handling` segment. No config or test names the old logger. Source: D-10 and E-3.
- Q: Does any Mist API request change? A: No. Every alarm request stays in `client.py`. Source: research R08 and R09.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the actions package within the structure limit (Priority: P1)

The maintainer finds five structural children in the Marvis actions package. The maintainer finds two structural children in the alarm handling package.

**Why this priority**: The nested ratchet counts the actions package as a violation until the move lands. Later changes need the limit to stay enforced.

**Independent Test**: Run the structure guard test and the nested ratchet test on the moved layout. Both tests pass.

**Acceptance Scenarios**:

1. **Given** the moved layout, **When** the structure guard lists the actions package, **Then** it finds `alarm_handling`, `client.py`, `model.py`, `operation.py`, and `selection.py`.
2. **Given** the moved layout, **When** the nested ratchet measures the tree, **Then** it reports 32 violations and 235 total excess.

---

### User Story 2 - Keep menu 270 behavior (Priority: P1)

The operator runs menu 270. The operator gets the same export, alarm join, and acknowledge step as before the move.

**Why this priority**: Menu 270 writes exported rows and can send the alarm acknowledge request. A silent change harms the operator.

**Independent Test**: Run the focused Marvis action tests and the portal exposure guard. Both pass with canonical import paths.

**Acceptance Scenarios**:

1. **Given** the moved modules, **When** the focused tests import them by canonical path, **Then** every focused test passes.
2. **Given** a confirmed acknowledge step, **When** the batch code runs, **Then** it uses the same batch size constant and the same note text.

---

### User Story 3 - Prove that no module-level name is lost (Priority: P2)

The maintainer confirms that each module-level name of the moved modules still exists at its new path.

**Why this priority**: A lost name breaks each importer. The moved modules have no test that reports such a loss by itself.

**Independent Test**: Run the symbol preservation guard. It reports zero lost names for both moved modules.

**Acceptance Scenarios**:

1. **Given** the two new mapping entries, **When** the rename-aware test compares the base modules with the moved modules, **Then** it reports no lost name.

### Edge Cases

- A second open pull request changes the symbol guard file. The move waits for the release. See D-3.
- A test or an import still names an old path. The old import fails, and the old-path search reports the line. The change adds no alias. See D-1.
- The shared checkout holds unrelated edits. Use a new worktree from main. Never stage the unrelated files. See T001.
- A log filter names the old logger. The repository holds no such filter, and the focused tests read `__name__`. See D-10.
- A generated menu map changes. Keep only the changed generated file. See D-12.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST move `acknowledgement.py` and `alarms.py` with `git mv` into `src/mist/intelligence/marvis/actions/alarm_handling/`.
- **FR-002**: The change MUST leave exactly five direct children in the actions package and exactly two in `alarm_handling`.
- **FR-003**: Active imports, test imports, and patch targets MUST use canonical paths. The change MUST add no alias at an old path.
- **FR-004**: Each module-level name of the moved modules MUST stay available at its new path. Behavior MUST stay unchanged.
- **FR-005**: The pull request body MUST record the logger name change and the class module path change.
- **FR-006**: Active documentation MUST name the canonical path. No active document MUST name an old path.
- **FR-007**: The generated menu references MUST pass the CI check. A generated file MUST change only when its content changes.
- **FR-008**: The nested baseline MUST drop the Marvis actions entry. The expected message MUST read `32 violations, 235 total excess`.
- **FR-009**: The change MUST add one release-note fragment under `changelog.d/` for issue 4008.
- **FR-010**: No existing guard assertion MUST be removed, skipped, or relaxed.
- **FR-011**: Publication MUST wait until the held guard file is released or a file-scoped handoff exists.
- **FR-012**: Every applicable local gate MUST pass before the local commit. Remote CI MUST pass before the merge.
- **FR-013**: Each touched pre-existing violation MUST appear in the plan. Each one MUST have a remediation action under parent issue #3824.

### Mist Cloud Transport Requirements

- No Mist REST method changes. The moved modules call no mistapi function.
- The client keeps its alarm search call to `mistapi.api.v1.orgs.alarms.searchOrgAlarms`. See research R08 and R58.
- The client keeps its acknowledge call to `mistapi.api.v1.orgs.alarms.ackOrgMultipleAlarms`. See research R09 and R59.
- Mist API evidence comes from `documentation/mist-api-openapi31yaml.yaml`, lines 5330 for search and 5226 for acknowledge. See research R37 and R38.
- No owned WebSocket transport is added or changed.

### Key Entities

- **MarvisAlarmAcknowledger**: Sends explicit alarm identifiers after the second confirmation. It moves with `acknowledgement.py`. Its behavior does not change.
- **MarvisAlarmAcknowledgeResult**: Holds one result row for each alarm in the acknowledge step. It does not change.
- **MarvisAlarmJoin**: Adds eight alarm columns to each exported action row. It moves with `alarms.py`.
- **MarvisAlarmIndex**: Maps each alarm by its `action_id` and by its `id`. It moves with `alarms.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The structure guard test and the nested ratchet test pass on the moved layout.
- **SC-002**: All 223 test functions in the focused selection pass.
- **SC-003**: The rename-aware symbol test reports zero lost names for both moved modules.
- **SC-004**: The nested ratchet reports 32 violations and 235 total excess.
- **SC-005**: Remote CI reports every required check as successful on the pull request head.

## Assumptions

- The worktree uses Python 3.15 or newer and the installed `mistapi` 0.64.1. See research R30 and R60.
- The archive branches stay on GitHub. The reviewed candidate content stays available as a reference.
- The move adds no service, so no container run is needed.
- The shared checkout keeps its five unrelated edits. Those edits belong to other work.

## Out of Scope

- Splitting `_send_batches` or `apply`. A remediation issue under parent #3824 tracks both functions (D-6).
- Reducing the top-level name counts of `acknowledgement.py`, `alarms.py`, or `operation.py` (D-6).
- Editing historical records under `specs/`, including `specs/3339-marvis-alarm-join`.
- Changing menu behavior, Mist API calls, output columns, or the web dashboard.
- Changing logic in `client.py`, `model.py`, `selection.py`, or `operation.py`. Only imports and one docstring change.
- Editing `tests/guardrails/test_src_public_symbol_preservation.py` before PR #4208 releases it.
- Rebasing the older candidate branch as it stands (D-9).
