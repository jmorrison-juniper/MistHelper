---
description: "Task list for [Spec 671] getSiteBeacon endpoint"
---

# Tasks: getSiteBeacon Menu Endpoint

**Input**: Design documents from `specs/671-mist-get-site-beacon/`  
**Prerequisites**: `plan.md`, `spec.md`  
**Branch**: `671-mist-get-site-beacon`

**Tests**: Tests are required for this feature (explicit request + spec acceptance checklist).

**Organization**: Tasks are grouped by user story so implementation and validation can be completed independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare menu slot, test files, and endpoint-specific scaffolding.

- [X] T001 Confirm and reserve the next sequential menu option for `getSiteBeacon` in `MistHelper.py`
- [X] T002 [P] Add/extend `getSiteBeacon` unit-test scaffolding in `tests/unit/export/test_site_client_exporter.py`
- [X] T003 [P] Create menu smoke-test scaffold for the new operation in `tests/integration/test_menu_site_beacon_detail.py`

**Checkpoint**: Menu slot and test harness scaffolding are ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared endpoint metadata and dispatch prerequisites required before story implementation.

**⚠️ CRITICAL**: Complete this phase before implementing user-story behavior.

- [X] T004 Add `getSiteBeacon` entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `src/refactors/endpoint_primary_key_strategies.py`
- [X] T005 Add operation-registry classification for the new menu option in `src/utils/operation_registry.py`
- [X] T006 Add reusable site/beacon prompt-and-validation helper flow in `src/export/site_client_exporter.py`

**Checkpoint**: PK strategy, operation classification, and prompt/validation scaffolding are in place.

---

## Phase 3: User Story 1 - Read-only data retrieval (Priority: P1) 🎯 MVP

**Goal**: A NOC engineer can run a new menu action that calls `mistapi.api.v1.sites.beacons.getSiteBeacon()` and exports the response to configured backends.

**Independent Test**: Run `python MistHelper.py --menu <new_id>` with known site/beacon IDs; verify output under `data/`, verify SQLite upsert behavior (no duplicate PK rows), and confirm graceful exit on EOF input.

### Tests for User Story 1

- [X] T007 [P] [US1] Add happy-path unit test for `getSiteBeacon` API invocation and export call in `tests/unit/export/test_site_client_exporter.py`
- [X] T008 [P] [US1] Add prompt/validation and `safe_input()` EOF handling unit tests in `tests/unit/export/test_site_client_exporter.py`
- [X] T009 [P] [US1] Add empty-response and API-error path unit tests in `tests/unit/export/test_site_client_exporter.py`
- [X] T010 [US1] Add menu-dispatch integration smoke test for the new menu option in `tests/integration/test_menu_site_beacon_detail.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `getSiteBeacon` export workflow (site/beacon prompts, logging, SDK call) in `src/export/site_client_exporter.py`
- [X] T012 [US1] Wire `DataExporter.write_with_format_selection(..., api_function_name="getSiteBeacon")` and deterministic filename logic in `src/export/site_client_exporter.py`
- [X] T013 [US1] Register the new menu handler/label mapping in `MistHelper.py`
- [X] T014 [US1] Ensure adaptive retry/rate-limit behavior is applied to `getSiteBeacon` call path in `src/export/site_client_exporter.py`
- [X] T015 [US1] Align interactive-safe routing for the new menu option in `src/utils/operation_registry.py`

**Checkpoint**: US1 is end-to-end functional and independently testable.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, release notes, and final validation.

- [X] T016 [P] Update menu documentation and operation count for the new endpoint in `README.md`
- [X] T017 [P] Update menu reference entry for the new endpoint in `documentation/menu_reference.md`
- [X] T018 [P] Add `[Spec 671] getSiteBeacon` release note entry in `CHANGELOG.md`
- [X] T019 Run targeted regression tests for touched endpoint wiring in `tests/unit/export/test_site_client_exporter.py` and `tests/integration/test_menu_site_beacon_detail.py`
- [X] T020 Run acceptance validation commands (`py_compile`, `ruff`, `black --check`, `--menu` smoke run) against `MistHelper.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all story work.
- **Phase 3 (US1)**: Depends on Phase 2 completion.
- **Phase 4 (Polish)**: Depends on US1 completion.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational; no dependency on other user stories.

### Within US1

- Write tests first (T007-T010), verify they fail, then implement.
- Implement endpoint workflow before final menu registration.
- Keep operation-registry classification synchronized with menu wiring.

### Parallel Opportunities

- Setup: T002 and T003 can run in parallel.
- US1 tests: T007, T008, and T009 can run in parallel.
- Polish docs: T016, T017, and T018 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel test authoring for US1:
Task: "T007 [US1] happy-path unit test in tests/unit/export/test_site_client_exporter.py"
Task: "T008 [US1] safe_input/EOF unit tests in tests/unit/export/test_site_client_exporter.py"
Task: "T009 [US1] empty/error-path unit tests in tests/unit/export/test_site_client_exporter.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Setup (Phase 1)
2. Complete Foundational (Phase 2)
3. Complete US1 (Phase 3)
4. Validate with CLI `--menu` smoke run and backend output checks

### Incremental Delivery

1. Deliver endpoint metadata + routing prerequisites
2. Deliver US1 endpoint behavior and tests
3. Deliver docs/changelog updates
4. Run validation gates before merge
