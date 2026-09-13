# Tasks: Menu 1 Constitution Compliance & OrgExportUtils Decomposition

**Input**: Design documents from `/specs/003-menu1-compliance-refactor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: No separate test suite requested. Validation uses the built-in `python MistHelper.py --test` runner (skip list: 14, 18, 63-65, 90-100).

**Organization**: Tasks grouped by user story. All code changes are in `MistHelper.py` (single-file architecture). `README.md` updated in Polish phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Since all implementation tasks edit the same file (`MistHelper.py`), [P] is only used for tasks targeting different files

---

## Phase 1: Setup

**Purpose**: Verify branch state and confirm current code matches research findings

- [X] T001 Checkout branch `003-menu1-compliance-refactor`, verify clean working tree, and confirm `OrgExportUtils` class location (~line 10670) and all 5 target methods exist in MistHelper.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the new class skeleton that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create empty `OrgAlarmEventExporter` class with docstring immediately before `class OrgExportUtils` (~line 10670) in MistHelper.py. Use `@staticmethod` convention per R2. Docstring must describe the class as a focused exporter for alarm and event time-series data.

**Checkpoint**: Class skeleton exists — user story implementation can now begin

---

## Phase 3: User Story 1 — Alarm Export Works Identically After Restructuring (Priority: P1) MVP

**Goal**: Menu Option #1 produces identical output after restructuring. Zero user-visible behavior change.

**Independent Test**: Run `python MistHelper.py --menu 1` before and after changes; compare CSV output file contents, console output, and log entries. Both runs must produce equivalent results.

### Implementation for User Story 1

- [X] T003 [US1] Copy `alarms()` `@staticmethod` verbatim from `OrgExportUtils` (~line 11667) into `OrgAlarmEventExporter` in MistHelper.py. Preserve all logic, parameters, API calls, error handling, and logging exactly as-is.
- [X] T004 [US1] Update `menu_actions` dict entry `"1"` from `OrgExportUtils.alarms` to `OrgAlarmEventExporter.alarms` (~line 50236) in MistHelper.py
- [X] T005 [US1] Update `DataCollectionManager._refresh_support_data()` alarms tuple from `OrgExportUtils.alarms` to `OrgAlarmEventExporter.alarms` (~line 18515) in MistHelper.py
- [X] T006 [US1] Remove `alarms()` method definition from `OrgExportUtils` (~line 11667) in MistHelper.py
- [X] T007 [US1] Run `python -m py_compile MistHelper.py` to verify syntax after US1 changes

**Checkpoint**: Menu 1 (alarm export) routes to new class and produces identical output. MVP is functional and testable.

---

## Phase 4: User Story 2 — Alarm Operations Organized in a Focused Unit (Priority: P2)

**Goal**: `OrgAlarmEventExporter` contains exactly 5 public methods (constitutional maximum), all semantically related to alarm/event time-series exports.

**Independent Test**: Count public methods in `OrgAlarmEventExporter` (must be exactly 5). Verify all operations are time-series event exports. Run `--menu 2` and `--menu 63` to confirm routing works.

### Implementation for User Story 2

- [X] T008 [US2] Add `_export_data()` private `@staticmethod` helper to `OrgAlarmEventExporter` in MistHelper.py. Duplicate logic from `OrgExportUtils.export_data()` (~line 10679) as a private method. This helper is used by `alarm_templates()` and `events()`.
- [X] T009 [US2] Copy `alarm_templates()` `@staticmethod` from `OrgExportUtils` (~line 11536) into `OrgAlarmEventExporter` in MistHelper.py. Change internal call from `OrgExportUtils.export_data()` to `OrgAlarmEventExporter._export_data()`.
- [X] T010 [US2] Copy `events()` `@staticmethod` from `OrgExportUtils` (~line 11563) into `OrgAlarmEventExporter` in MistHelper.py. Change internal call from `OrgExportUtils.export_data()` to `OrgAlarmEventExporter._export_data()`.
- [X] T011 [US2] Copy `device_events()` `@staticmethod` from `OrgExportUtils` (~line 11694) into `OrgAlarmEventExporter` in MistHelper.py. Preserve all logic verbatim.
- [X] T012 [US2] Copy `device_events_52w()` `@staticmethod` from `OrgExportUtils` (~line 11722) into `OrgAlarmEventExporter` in MistHelper.py. Preserve all logic verbatim.
- [X] T013 [US2] Update `menu_actions` dict entries `"2"` to `OrgAlarmEventExporter.device_events` (~line 50237) and `"63"` to `OrgAlarmEventExporter.device_events_52w` (~line 50338) in MistHelper.py
- [X] T014 [US2] Update `DataCollectionManager._refresh_support_data()` device_events tuple from `OrgExportUtils.device_events` to `OrgAlarmEventExporter.device_events` (~line 18516) in MistHelper.py
- [X] T015 [US2] Remove `alarm_templates()`, `events()`, `device_events()`, and `device_events_52w()` method definitions from `OrgExportUtils` in MistHelper.py
- [X] T016 [US2] Verify `OrgAlarmEventExporter` has exactly 5 public methods + 1 private helper, all methods under 25 lines and 5 parameters. Run `python -m py_compile MistHelper.py`.

**Checkpoint**: All 5 methods live in `OrgAlarmEventExporter`. `OrgExportUtils` reduced from 56 to 51 methods. Menus 1, 2, 63 all route correctly.

---

## Phase 5: User Story 3 — Clear, Non-Redundant Feedback for NOC Engineers (Priority: P3)

**Goal**: Alarm export produces exactly one info-level start message, not two redundant messages.

**Independent Test**: Run Menu 1 and count info-level log messages at operation start. Must see exactly one start message.

### Implementation for User Story 3

- [X] T017 [US3] Consolidate redundant logging in `OrgAlarmEventExporter.alarms()` in MistHelper.py. Replace the two nearly-identical info messages ("Starting organization alarms export" and "Starting search for all open org alarms...") with a single clear info message per operational phase.

**Checkpoint**: Menu 1 produces clean, non-redundant log output. One start message, one completion message.

---

## Phase 6: User Story 4 — Restructuring Pattern Is Repeatable (Priority: P3)

**Goal**: The extraction approach is self-documenting and replicable for future `OrgExportUtils` decomposition.

**Independent Test**: A developer can read the class docstring and understand how to extract the next group of methods using the same pattern.

### Implementation for User Story 4

- [X] T018 [US4] Enhance `OrgAlarmEventExporter` class docstring in MistHelper.py to document the extraction pattern: (1) identify 5 semantically related methods, (2) create new class before `OrgExportUtils`, (3) duplicate `_export_data()` if needed, (4) move methods verbatim, (5) update menu_actions + cross-references, (6) remove from source class.

**Checkpoint**: Pattern is documented in-code. Future extractions can follow the same approach.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and deployment

- [X] T019 Grep MistHelper.py for any remaining references to `OrgExportUtils.alarms`, `OrgExportUtils.alarm_templates`, `OrgExportUtils.events`, `OrgExportUtils.device_events`, or `OrgExportUtils.device_events_52w` and fix any missed references
- [X] T020 Run `python -m py_compile MistHelper.py` for final syntax validation
- [X] T021 Run `python MistHelper.py --test` to verify zero regressions across all non-skipped menu operations
- [ ] T022 [P] Update README.md changelog with `version YY.MM.DD.HH.MM - Extract OrgAlarmEventExporter from OrgExportUtils (5-Item Rule compliance)` and update operation count if needed
- [ ] T023 Execute full deployment pipeline: `git add` + `git commit` + `git push origin main`, wait for container build, `podman pull`, restart container, `podman ps` to verify

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — MVP, must complete first
- **US2 (Phase 4)**: Depends on Foundational — can start after US1 or in parallel with US1 (same file limits true parallelism)
- **US3 (Phase 5)**: Depends on US1 (alarms() must be in new class before modifying logging)
- **US4 (Phase 6)**: Depends on US2 (class must be complete before documenting the full pattern)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P2)**: Can start after Foundational (Phase 2) — Independent of US1, but sequencing after US1 avoids merge conflicts in same file
- **US3 (P3)**: Depends on US1 completion (alarms() must exist in OrgAlarmEventExporter)
- **US4 (P3)**: Depends on US2 completion (full class structure must exist to document the pattern)

### Within Each User Story

- Copy method(s) to new class before updating references
- Update references before removing from source class
- Syntax check after removals to catch errors early

### Parallel Opportunities

- **T022** (README.md) can run in parallel with any MistHelper.py task since it's a different file
- All other tasks are sequential due to single-file architecture
- US1 and US2 are logically parallelizable but practically sequential (same file)

---

## Parallel Example: Phase 7 (Polish)

```text
# T022 can run in parallel with T019-T021 since it edits a different file:
Parallel group A: T019 Grep for missed references in MistHelper.py
Parallel group A: T022 Update README.md changelog

# Then sequential:
T020 Final syntax validation
T021 Run --test suite
T023 Deploy
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002)
3. Complete Phase 3: User Story 1 (T003-T007)
4. **STOP and VALIDATE**: Run `--menu 1`, compare output to baseline
5. If MVP passes, continue to US2

### Incremental Delivery

1. Setup + Foundational → Class skeleton ready
2. Add US1 (alarms) → Test Menu 1 → MVP functional
3. Add US2 (remaining 4 methods) → Test Menus 2, 63 → Full extraction complete
4. Add US3 (logging) → Verify clean output → User experience improved
5. Add US4 (documentation) → Pattern documented → Future-proofed
6. Polish → Validate + Deploy → Production ready

### Single-File Constraint

All user stories edit `MistHelper.py`. Implementation must be sequential within each story. Cross-story parallelism is limited to documentation tasks (README.md). The recommended workflow is: US1 → US2 → US3 → US4 → Polish, executing tasks in order within each phase.

---

## Notes

- No [P] markers on MistHelper.py tasks — single-file architecture prevents true parallelism
- Dead code methods (`alarm_templates`, `events`) are included per FR-003 / R4 decision
- `OrgExportUtils` drops from 56 to 51 methods — still above 5-item limit, tracked as future debt
- Line numbers are approximate; verify current positions before each edit
- Skip list for `--test`: operations 14, 18, 63-65, 90-100
