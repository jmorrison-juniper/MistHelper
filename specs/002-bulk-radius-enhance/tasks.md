# Tasks: Bulk RADIUS WLAN Configuration Enhancements

**Input**: Design documents from `/specs/002-bulk-radius-enhance/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec. No test tasks generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. All changes are in `MistHelper.py` within the existing `BulkRadiusWLANConfigManager` class (~line 46064).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different methods/sections, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- All file paths reference `MistHelper.py` unless stated otherwise

---

## Phase 1: Setup

**Purpose**: Class-level constants and signature changes needed before any story work

- [X] T001 Add `CANCEL_KEYWORDS` class constant to `BulkRadiusWLANConfigManager` in MistHelper.py (~line 46087)
- [X] T002 Add `self.compliant_wlans` list to `__init__()` in MistHelper.py (~line 46087)
- [X] T003 Update `manage()` signature to accept `dry_run: bool = False` and store as `self.dry_run` in MistHelper.py (~line 46370)
- [X] T004 Update menu_actions dict entry "122" to use `lambda dry_run=False:` pattern in MistHelper.py (~line 50400)

**Checkpoint**: Class has new constant, new instance variable, updated entry point signature, and lambda wiring.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational phase needed. All changes are modifications to existing methods within `BulkRadiusWLANConfigManager`. Setup phase covers the prerequisites.

**Checkpoint**: Setup complete - user story implementation can begin.

---

## Phase 3: User Story 1 - Display All RADIUS WLANs Including Compliant (Priority: P1) MVP

**Goal**: Show ALL RADIUS-enabled WLANs in Menu 122 list with compliant ones marked "(COMPLIANT)" and non-compliant ones numbered for selection.

**Independent Test**: Run Menu 122 with org containing mix of compliant and non-compliant WLANs. Verify all RADIUS WLANs appear with compliant ones marked.

### Implementation for User Story 1

- [X] T005 [US1] Refactor `_filter_radius_wlans()` to populate both `self.radius_wlans` (non-compliant) and `self.compliant_wlans` (compliant) with `_compliance_status` metadata in MistHelper.py (~line 46177)
- [X] T006 [US1] Refactor `_display_wlans()` to show unified table with compliant WLANs marked "(COMPLIANT)" and `--` index, non-compliant numbered sequentially in MistHelper.py (~line 46197)
- [X] T007 [US1] Update `manage()` flow to distinguish two empty-list states: (a) no RADIUS WLANs found at all -> existing "No RADIUS-enabled WLANs found" message, (b) all RADIUS WLANs already compliant -> new "All WLANs already at target settings" message, in MistHelper.py (~line 46385)
- [X] T008 [US1] Update summary line in `_filter_radius_wlans()` to show counts for both compliant and non-compliant in MistHelper.py (~line 46195)

**Checkpoint**: Menu 122 shows full RADIUS WLAN inventory. Compliant WLANs visible but unselectable. All-compliant orgs get clear message.

---

## Phase 4: User Story 2 - Cancel/Back-Out at Any Screen (Priority: P1)

**Goal**: Engineers can type `q`, `quit`, `cancel`, or `back` at the selection prompt to exit cleanly without changes.

**Independent Test**: Run Menu 122, type `quit` at selection prompt, verify clean exit with no API calls.

### Implementation for User Story 2

- [X] T009 [US2] Add cancel keyword detection to `_parse_selection()` - return `None` sentinel when cancel keyword detected. Also ensure "all" keyword auto-excludes compliant WLANs (returns only non-compliant indices) in MistHelper.py (~line 46219)
- [X] T010 [US2] Update selection prompt text in `manage()` to show `or 'q' to cancel` hint in MistHelper.py (~line 46393)
- [X] T011 [US2] Update `manage()` to check for `None` return from `_parse_selection()` and exit with "Operation cancelled" in MistHelper.py (~line 46397)
- [X] T012 [US2] Update confirmation prompt messaging to explicitly state cancel behavior in MistHelper.py (~line 46407)

**Checkpoint**: Cancel commands work at selection prompt. Confirmation prompt still cancels on non-"APPLY" input (already working, improved messaging).

---

## Phase 5: User Story 3 - Respect --debug and --dry-run CLI Flags (Priority: P1)

**Goal**: Menu 122 honors `--dry-run` (preview without API calls) and `--debug` (verbose logging) flags consistently with other MistHelper operations.

**Independent Test**: Run `python MistHelper.py --menu 122 --dry-run`, select WLANs, confirm, verify no API calls made but full preview shown with DRYRUN_ CSV prefix.

### Implementation for User Story 3

- [X] T013 [US3] Update `_display_config()` to show DRY-RUN and/or DEBUG mode banners when flags are active in MistHelper.py (~line 46100)
- [X] T014 [US3] Add debug logging to `_scan_org_wlans()` - log full API response data when `is_debug_mode()` in MistHelper.py (~line 46141)
- [X] T015 [P] [US3] Add debug logging to `_filter_radius_wlans()` - log per-WLAN compliance evaluation when `is_debug_mode()` in MistHelper.py (~line 46177)
- [X] T016 [US3] Refactor `_apply_changes()` to skip API calls in dry-run mode, log "DRY-RUN: Would update" with payload details in MistHelper.py (~line 46278)
- [X] T017 [US3] Update `_record_change()` to set status as "DRY-RUN" when `self.dry_run` is True in MistHelper.py (~line 46322)
- [X] T018 [US3] Update `_export_audit_trail()` to prefix filename with "DRYRUN_" when `self.dry_run` is True in MistHelper.py (~line 46340)

**Checkpoint**: Dry-run mode prevents all API writes and generates DRYRUN_ CSV. Debug mode shows verbose API/evaluation details. Both flags work independently and together.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation updates

- [X] T019 Validate syntax with `python -m py_compile MistHelper.py`
- [X] T020 Update README.md changelog with version YY.MM.DD.HH.MM and enhancement description
- [X] T021 Commit, push, and execute full deployment pipeline (git push, wait for container build, pull image, restart container)
- [X] T022 Run quickstart.md validation scenarios against live container via SSH

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **User Stories (Phase 3-5)**: All depend on Setup (Phase 1) completion
  - US1, US2, US3 are all P1 priority
  - US3 depends on T003 (`self.dry_run` attribute) from Setup
  - US1 and US2 can proceed in parallel after Setup
  - US3 can proceed in parallel with US1/US2 after Setup
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on T002 (`self.compliant_wlans`). No dependencies on other stories.
- **User Story 2 (P1)**: Depends on T001 (`CANCEL_KEYWORDS`). No dependencies on other stories.
- **User Story 3 (P1)**: Depends on T003 (`self.dry_run`), T004 (lambda wiring). No dependencies on other stories.

### Within Each User Story

- Core method refactoring before flow integration
- Method-level changes before `manage()` orchestration updates

### Parallel Opportunities

- T001 and T002 can run in parallel (different parts of `__init__`/class body)
- T005 and T009 can run in parallel (different methods: `_filter_radius_wlans` vs `_parse_selection`)
- T013 and T015 can run in parallel (different methods: `_display_config` vs `_filter_radius_wlans`)
- T014 and T015 can run in parallel (different methods: `_scan_org_wlans` vs `_filter_radius_wlans`)
- T016, T017, T018 are sequential (all in apply/record/export chain)

---

## Parallel Example: Setup Phase

```text
# These setup tasks can be batched (different code sections):
T001: Add CANCEL_KEYWORDS class constant
T002: Add self.compliant_wlans to __init__()
# Then sequentially:
T003: Update manage() signature (depends on class being ready)
T004: Update menu_actions lambda (depends on manage() signature)
```

## Parallel Example: User Stories After Setup

```text
# After Setup is complete, all three stories can start in parallel:
Stream A (US1): T005 → T006 → T008 → T007
Stream B (US2): T009 → T010 → T011 → T012
Stream C (US3): T013 → T014, T015 (parallel) → T016 → T017 → T018
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 3: User Story 1 (T005-T008)
3. **STOP and VALIDATE**: Run Menu 122, verify compliant WLANs shown with "(COMPLIANT)"
4. Can deploy/demo with just compliance visibility

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add User Story 1 → Test: all RADIUS WLANs visible with compliance markers
3. Add User Story 2 → Test: cancel commands work at selection prompt
4. Add User Story 3 → Test: --dry-run and --debug flags honored
5. Polish → Syntax check, README update, deploy pipeline

### Single Developer Strategy (Recommended)

All three user stories are P1 and modify the same file/class. Sequential delivery in priority order minimizes merge conflicts:

1. Setup (T001-T004) → US1 (T005-T008) → US2 (T009-T012) → US3 (T013-T018) → Polish (T019-T022)

---

## Notes

- All 22 tasks modify a single file (`MistHelper.py`) within one class (`BulkRadiusWLANConfigManager`)
- No new files, classes, or packages required
- Cancel keywords are case-insensitive via `.strip().lower()` comparison
- Dry-run threads via lambda parameter pattern (matching Menu 104/113/114)
- Debug uses global `is_debug_mode()` helper (no parameter threading)
- Commit after each completed user story phase for safe checkpoints
