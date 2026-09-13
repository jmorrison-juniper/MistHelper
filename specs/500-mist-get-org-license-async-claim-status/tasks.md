---
description: "Task list for GetOrgLicenseAsyncClaimStatus menu item"
---

# Tasks: GetOrgLicenseAsyncClaimStatus Menu Item

**Input**: Design documents from `specs/500-mist-get-org-license-async-claim-status/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/get_org_license_async_claim_status.md, quickstart.md
**Branch**: `500-mist-get-org-license-async-claim-status`

**Tests**: Tests are required by this feature spec (acceptance scenarios + quality gates + `--menu` smoke run).

**Organization**: Tasks are grouped by user story so the feature can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare implementation and test scaffolding for this endpoint addition.

- [X] T001 Confirm the next free safe-org export menu slot in `MistHelper.py` for `GetOrgLicenseAsyncClaimStatus` registration.
- [X] T002 [P] Create test scaffold for this endpoint flow in `tests/unit/test_org_license_async_claim_status.py`.
- [X] T003 [P] Create CLI smoke-test scaffold for menu invocation in `tests/integration/test_menu_org_license_async_claim_status.py`.

**Checkpoint**: Menu slot is identified and test files exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data-shaping and persistence pieces required before user-story behavior is implemented.

**⚠️ CRITICAL**: No user story implementation should begin before these tasks are complete.

- [X] T004 Add `getOrgLicenseAsyncClaimStatus` and `getOrgLicenseAsyncClaimStatusDetails` entries to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py`.
- [X] T005 Add summary-row flattening helper logic for async claim payloads in `MistHelper.py` (target table `org_claim_status_summary`).
- [X] T006 Add detail-row flattening helper logic for async claim payloads in `MistHelper.py` (target table `org_claim_status_details`).

**Checkpoint**: PK strategy and flattening logic are in place for all output backends.

---

## Phase 3: User Story 1 - Read-only data retrieval (Priority: P1) 🎯 MVP

**Goal**: A NOC engineer can run a new menu item that calls `GetOrgLicenseAsyncClaimStatus`, optionally includes detail rows, and exports results via DataExporter.

**Independent Test**: Run `python MistHelper.py --menu <new_number>` with a known org; verify summary export always writes under `data/`, detail export writes only when requested, and SQLite upserts on rerun.

### Tests for User Story 1

- [X] T007 [P] [US1] Add unit tests for org prompt handling (`safe_input`, UUID validation, detail flag parsing) in `tests/unit/test_org_license_async_claim_status.py`.
- [X] T008 [P] [US1] Add unit tests for API call/response handling (200, empty payload, 404/401 paths) in `tests/unit/test_org_license_async_claim_status.py`.
- [X] T009 [P] [US1] Add unit tests for summary/detail export payload mapping and `api_function_name` routing in `tests/unit/test_org_license_async_claim_status.py`.
- [X] T010 [US1] Add integration smoke test for `--menu` execution path in `tests/integration/test_menu_org_license_async_claim_status.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement `LicenseExportUtils.export_org_license_async_claim_status(...)` in `MistHelper.py` using `safe_input()` contexts and action logging.
- [X] T012 [US1] Implement SDK invocation (`mistapi.api.v1.orgs.claim.status.getOrgLicenseAsyncClaimStatus`) and response normalization in `MistHelper.py`.
- [X] T013 [US1] Implement summary export write via `DataExporter.write_with_format_selection(...)` in `MistHelper.py` using filename `org_<org_id[:8]>_claim_status_summary`.
- [X] T014 [US1] Implement optional detail export write via `DataExporter.write_with_format_selection(...)` in `MistHelper.py` using filename `org_<org_id[:8]>_claim_status_details`.
- [X] T015 [US1] Register the new menu label/handler mapping and menu dispatch wiring in `MistHelper.py` at the confirmed safe-org export slot.

**Checkpoint**: User Story 1 works end-to-end and is independently testable.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and release hygiene spanning the feature.

- [X] T016 [P] Update endpoint/menu documentation and operation count in `README.md`.
- [X] T017 [P] Add release note entry for this endpoint in `CHANGELOG.md`.
- [X] T018 Run syntax/lint/format gates against `MistHelper.py` (`python -m py_compile`, `ruff check`, `black --check`) and fix issues in `MistHelper.py`.
- [X] T019 Run quickstart validation steps from `specs/500-mist-get-org-license-async-claim-status/quickstart.md` and align any command/menu references in that file.

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

- Tests (T007-T010) should be written first and fail before implementation.
- Core method and API call (T011-T012) precede export wiring (T013-T014).
- Menu registration (T015) happens after method behavior is complete.

### Parallel Opportunities

- Phase 1: T002 and T003 can run in parallel.
- Phase 3 tests: T007, T008, and T009 can run in parallel.
- Phase 4 docs: T016 and T017 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel test authoring:
Task: "T007 [US1] prompt/validation tests in tests/unit/test_org_license_async_claim_status.py"
Task: "T008 [US1] API response-path tests in tests/unit/test_org_license_async_claim_status.py"
Task: "T009 [US1] export-mapping tests in tests/unit/test_org_license_async_claim_status.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Setup (Phase 1)
2. Complete Foundational (Phase 2)
3. Complete US1 (Phase 3)
4. Validate with `--menu` smoke run and backend outputs

### Incremental Delivery

1. Deliver US1 end-to-end in `MistHelper.py`
2. Finish docs/changelog updates
3. Run quality gates and quickstart validation before merge
