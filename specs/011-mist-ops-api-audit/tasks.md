# Tasks: Mist-Ops Platform API Endpoint Audit

**Input**: Design documents from `/specs/011-mist-ops-api-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per FR-010 — all corrected call sites must be covered by tests that verify SDK methods are called with correct arguments.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to workspace root. Source files are under `mist-ops-platform/src/`, tests under `mist-ops-platform/tests/`.

---

## Phase 1: Setup

**Purpose**: Ensure test infrastructure exists for the audit

- [X] T001 Create test directory structure at mist-ops-platform/tests/unit/mist/ with __init__.py files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core dataclass and service changes that ALL user stories depend on

**Why blocking**: MistEndpoint optional fields are required for US1 (new entity types with None read/write). list_all_entities is required for US1 (sync service refactoring through registry).

- [X] T002 Modify MistEndpoint dataclass to support optional read_method and write_method, add list_method field in mist-ops-platform/src/shared/mist/types.py
- [X] T003 [P] Add list_all_entities() method and _paginate() helper to MistEndpointService in mist-ops-platform/src/shared/mist/endpoints.py (Note: [P] for coding — different file from T002 — but has logical test dependency on T002 for MistEndpoint.list_method field)
- [X] T004 Test MistEndpoint construction with optional fields and list_method in mist-ops-platform/tests/unit/mist/test_types.py
- [X] T005 [P] Test list_all_entities pagination follows response.next across multiple pages in mist-ops-platform/tests/unit/mist/test_pagination.py

**Checkpoint**: Foundation ready — MistEndpoint supports optional fields, list_all_entities handles pagination. User story work can begin.

---

## Phase 3: User Story 1 — Verify All SDK Method Calls Are Valid (Priority: P1) MVP

**Goal**: Every call that mist-ops-platform makes to the Juniper Mist cloud uses a real, existing method from the mistapi Python library, routed through the entity registry.

**Independent Test**: For each of the 23 registered entity types, confirm the module path resolves to an importable module and every non-None method name exists on that module via `importlib.import_module()` and `hasattr()`.

**Scope**: Fixes 1 broken module path (site_info), 1 wrong method name (org_wlan), adds 9 new entity types, and refactors 7 registry bypass calls across 6 files.

### Implementation for User Story 1

- [X] T006 [US1] Fix org_wlan read_method from getOrgWlan to getOrgWLAN and site_info api_module from sites.site to sites.sites in mist-ops-platform/src/shared/mist/types.py
- [X] T007 [US1] Add 9 new entity types (self_identity, org_site_list, org_inventory, org_device_list, device_stats, audit_log, firmware_device, firmware_site, firmware_org) to ENTITY_ENDPOINT_MAP in mist-ops-platform/src/shared/mist/types.py
- [X] T008 [P] [US1] Refactor direct mistapi.api.v1.self.self.getSelf() call to use self_identity via MistEndpointService in mist-ops-platform/src/shared/services/auth.py
- [X] T009 [P] [US1] Refactor list_entities with getOrgDevice to use org_device_list via list_all_entities in mist-ops-platform/src/worker/checks/pre_checks.py
- [X] T010 [P] [US1] Refactor list_entities with getOrgDevice to use org_device_list via list_all_entities in mist-ops-platform/src/worker/checks/post_checks.py
- [X] T011 [P] [US1] Refactor list_entities with listOrgSites and getOrgInventory to use org_site_list and org_inventory via list_all_entities in mist-ops-platform/src/worker/sync/inventory.py
- [X] T012 [P] [US1] Refactor list_entities with getSiteDeviceStats to use device_stats via read_entity in mist-ops-platform/src/worker/sync/status.py
- [X] T013 [P] [US1] Refactor list_entities with listOrgAuditLogs to use audit_log via list_all_entities in mist-ops-platform/src/worker/sync/events.py
- [X] T014 [US1] Test all 23 registered entity types resolve valid SDK modules and callable methods in mist-ops-platform/tests/unit/mist/test_registry_validation.py (Note: T026 reuses this verification as a final cross-check)
- [X] T014b [US1] Test refactored consumer behavior: auth.py uses self_identity, pre_checks.py uses org_device_list, post_checks.py uses org_device_list, status.py uses device_stats — verify each consumer calls the registry correctly in mist-ops-platform/tests/unit/mist/test_consumer_registry_usage.py

**Checkpoint**: All SDK calls route through the entity registry with correct module paths and method names. MVP is complete — all 7 bypass calls eliminated, 2 existing entries fixed, 9 new types added. Consumer behavior validated per SC-007.

---

## Phase 4: User Story 2 — Fix Method Signature Mismatches (Priority: P1)

**Goal**: Every call site passes the correct parameters in the correct order so that write operations (config pushes, rollbacks) do not crash.

**Independent Test**: Compare each call site's keyword arguments against the actual MistEndpointService method signature. Every mismatch is corrected from api_module/write_method pattern to entity_type/ids/body pattern.

**Scope**: Fixes 3 call sites across 2 files (executor.py has 1 write_entity, rollback.py has 1 read_entity + 1 write_entity).

### Implementation for User Story 2

- [X] T015 [P] [US2] Fix write_entity() call from api_module/write_method kwargs to entity_type/ids/body in mist-ops-platform/src/worker/deploy/executor.py
- [X] T016 [P] [US2] Fix read_entity() and write_entity() calls from api_module/read_method/write_method kwargs to entity_type/ids pattern in mist-ops-platform/src/worker/deploy/rollback.py
- [X] T017 [US2] Test executor and rollback pass entity_type and ids as correct positional/keyword arguments in mist-ops-platform/tests/unit/mist/test_deploy_calls.py

**Checkpoint**: All deploy service calls use the correct MistEndpointService interface — no more api_module/write_method kwargs.

---

## Phase 5: User Story 3 — Fix Response Handling Inconsistencies (Priority: P2)

**Goal**: The system correctly interprets API responses so that success/failure states are accurately detected via derived properties on ApiResult.

**Independent Test**: Verify ApiResult.success returns True for 2xx and False otherwise. Verify ApiResult.error extracts detail from response data on non-2xx. Verify all consumer code sites that reference .success/.error work without AttributeError.

**Scope**: Adds 2 derived properties to ApiResult, validates 5 consumer sites across executor.py, rollback.py, and pre_checks.py.

### Implementation for User Story 3

- [X] T018 [US3] Add .success and .error derived properties to ApiResult dataclass in mist-ops-platform/src/shared/mist/endpoints.py
- [X] T019 [P] [US3] Test ApiResult .success returns True for 2xx codes and .error returns None; test .error extracts data detail for non-2xx in mist-ops-platform/tests/unit/mist/test_api_result.py
- [X] T020 [P] [US3] Test executor, rollback, and pre_checks consumer code correctly branches on .success and logs .error in mist-ops-platform/tests/unit/mist/test_response_consumers.py

**Checkpoint**: ApiResult provides .success/.error properties. All 5 consumer sites reference valid attributes.

---

## Phase 6: User Story 4 — Add Pagination for List Operations (Priority: P2)

**Goal**: List operations that retrieve sites, devices, events, and inventory handle pagination so that complete data sets are returned.

**Independent Test**: Mock SDK responses with response.next set across 3 pages. Verify list_all_entities combines all pages. Verify sync services for org_site_list, org_inventory, and audit_log return complete results.

**Scope**: Pagination mechanism implemented in Phase 2 (T003, T005). Sync services refactored to use list_all_entities in Phase 3 US1. This phase validates end-to-end pagination for the 3 paginated entity types identified by API docs (R-09).

### Tests for User Story 4

- [X] T021 [US4] Test inventory and events sync services retrieve all pages with mock multi-page responses for org_site_list (limit=100), org_inventory (limit=100), and audit_log in mist-ops-platform/tests/unit/mist/test_sync_pagination.py

**Checkpoint**: All paginated list operations confirmed to retrieve complete data sets across multiple pages.

---

## Phase 7: User Story 5 — Cross-Reference Internal Method Calls (Priority: P3)

**Goal**: Internal service-to-service method calls use correct method names, and the firmware orchestrator can trigger actual upgrades via the SDK.

**Independent Test**: Verify drift scanner calls compute_diff (not compute) on DiffService. Verify FirmwareOrchestrator.execute_upgrade() calls write_entity with firmware_site entity type and correct payload structure.

**Scope**: 1 internal method name fix (drift.py), 1 new method added (firmware.py execute_upgrade).

### Implementation for User Story 5

- [X] T022 [P] [US5] Fix self._diff.compute() to self._diff.compute_diff() in mist-ops-platform/src/worker/checks/drift.py
- [X] T023 [P] [US5] Add execute_upgrade() method to FirmwareOrchestrator that calls write_entity with firmware_site entity type (per data-model.md) in mist-ops-platform/src/worker/deploy/firmware.py. MUST call validate_upgrade() before execute_upgrade() per Constitution III (Safety-First — firmware is a destructive operation). Capture upgrade_id from response.
- [X] T024 [P] [US5] Test drift scanner calls compute_diff on DiffService in mist-ops-platform/tests/unit/mist/test_drift.py
- [X] T025 [P] [US5] Test firmware execute_upgrade calls MistEndpointService.write_entity with firmware_site and correct payload in mist-ops-platform/tests/unit/mist/test_firmware.py

**Checkpoint**: All internal method calls use correct names. Firmware orchestrator can trigger upgrades through the entity registry.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [X] T026 [P] Run SDK import verification script: importlib.import_module + hasattr for all 23 entity types against installed mistapi 0.60.4 (cross-check of T014 — reuses same verification technique as final gate)
- [X] T027 Run quickstart.md 11-step validation and confirm all steps pass
- [X] T028 [P] Run full pytest suite and verify zero AttributeError, ModuleNotFoundError, or TypeError across all call sites

**Note on spec edge cases**: 4 edge cases (SDK upgrade, deprecated methods, unexpected response structure, module reorganization) are addressed through defensive coding in existing tasks — not separate tasks. Registry entry validation (T014/T026) catches import/path issues; ApiResult properties (T018) handle response variation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (MistEndpoint optional fields, list_all_entities)
- **US2 (Phase 4)**: Depends on Phase 2 only (no dependency on US1)
- **US3 (Phase 5)**: Depends on Phase 2 only (no dependency on US1 or US2)
- **US4 (Phase 6)**: Depends on Phase 2 (pagination) + Phase 3 US1 (entity types + sync service refactoring)
- **US5 (Phase 7)**: Depends on Phase 2 (MistEndpoint optional fields for write-only firmware types) + Phase 3 US1 (firmware entity types in registry)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — no dependencies on other stories. Can run in parallel with US1
- **US3 (P2)**: Can start after Phase 2 — no dependencies on US1 or US2
- **US4 (P2)**: Depends on US1 (entity types and sync service refactoring must exist)
- **US5 (P3)**: Depends on US1 (firmware entity types must be in registry)

### Within Each User Story

- Registry/infrastructure changes before consumer refactoring
- Implementation before tests
- Same-file tasks are sequential; different-file tasks marked [P] can be parallel

### Parallel Opportunities

- **Phase 2**: T002 and T003 can run in parallel (different files). T004 and T005 can run in parallel (different test files)
- **Phase 3**: T008-T013 can ALL run in parallel (6 different consumer files, all depend on T006-T007 being done first)
- **Phase 4**: T015 and T016 can run in parallel (different files)
- **Phase 5**: T019 and T020 can run in parallel (different test files)
- **Phase 7**: All 4 tasks can run in parallel (4 different files)
- **Cross-phase**: US1, US2, and US3 can all start simultaneously after Phase 2

---

## Parallel Example: User Story 1

```text
# Sequential: Registry changes in types.py (same file)
T006: Fix org_wlan + site_info entries
T007: Add 9 new entity types

# Parallel: All consumer refactoring (6 different files)
T008: auth.py          |
T009: pre_checks.py    |
T010: post_checks.py   |  All run simultaneously
T011: inventory.py     |
T012: status.py        |
T013: events.py        |

# Sequential: Validation test (depends on all above)
T014: test_registry_validation.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run test_registry_validation.py — all 23 entity types must resolve
5. All SDK calls now go through the registry with correct methods

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add US1 -> All SDK calls valid through registry (MVP!)
3. Add US2 -> Deploy service signatures fixed
4. Add US3 -> Response handling reliable
5. Add US4 -> Pagination verified for large orgs
6. Add US5 -> Internal methods + firmware complete
7. Polish -> Full validation pass

### Parallel Team Strategy

With multiple developers after Phase 2:
- Developer A: US1 (registry + refactoring)
- Developer B: US2 (signature fixes) + US3 (ApiResult)
- After US1 completes: Developer A takes US4 + US5

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- All file paths relative to workspace root (mist-ops-platform/ prefix)
- Research R-09 (API docs cross-reference) confirmed all SDK findings and added 7 refinements
- listOrgDevices is "Not paginated" per API docs — no pagination needed for org_device_list
- Firmware upgrade returns upgrade_id UUID — execute_upgrade should capture and return it
- Firmware reboot param is switches/gateways only (APs auto-reboot) — payload builder should respect device type
