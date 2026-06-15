---
description: "Task list for feature implementation"
---

# Tasks: Org Async Claim Menu Operations (mistapi 0.63.0)

**Feature**: `specs/203-org-async-claims/`
**Input**: plan.md, spec.md, research.md, data-model.md, contracts/menu-operations-contract.md, quickstart.md
**Operations added**: 208 (list async claims), 209 (create async claim — destructive), 210 (get async claim status)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Parallelizable — no incomplete-task dependencies, different file scope
- **[US1/2/3]**: Maps to User Story from spec.md (P1/P2/P3)

---

## Phase 1: Setup (Baseline Verification)

**Purpose**: Confirm working baseline before any edits.

- [ ] T001 Verify compile baseline passes with no errors: `python -m py_compile MistHelper.py` from repo root
- [ ] T002 [P] Confirm async-claim SDK symbol names from `docs/UPSTREAM_mistapi_changes.md` (listOrgAsyncClaims, createOrgAsyncClaim, getOrgAsyncClaimStatus) and note any naming discrepancies for adapter handling in research.md

**Checkpoint**: Baseline clean — safe to proceed with foundational wiring.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that ALL user story handlers depend on. Must complete before any Phase 3–5 work.

**⚠️ CRITICAL**: No handler implementation can begin until T003 and T004 are complete.

- [ ] T003 Add three `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries in `MistHelper.py` for `listOrgAsyncClaims` (natural_pk on claim_id / composite fallback org_id+scheduled_at+timestamp), `createOrgAsyncClaim` (natural_pk on claim_id / composite fallback org_id+submitted_at+status), and `getOrgAsyncClaimStatus` (composite_pk org_id+claim_id+timestamp)
- [ ] T004 Register menu entries 208, 209, and 210 in the `menu_actions` dict in `MistHelper.py` with correct descriptions and safety-class labels (safe/destructive) matching contracts/menu-operations-contract.md

**Checkpoint**: PK strategies and menu registry in place — story phases can now begin.

---

## Phase 3: User Story 1 — Export Org Async Claims (Priority: P1) 🎯 MVP

**Goal**: Safe read-only list/export of org async claim records using existing DataExporter pipeline.

**Independent Test**: Run menu 208 with a valid org context — confirms records exported to data/ or clean empty-result message with no configuration changes.

### Tests for User Story 1

- [ ] T005 [P] [US1] Write unit tests for `list_org_async_claims()` covering: API success with records, API success with empty list (valid outcome), and API exception path in `tests/unit/test_async_claims.py`

### Implementation for User Story 1

- [ ] T006 [US1] Implement `list_org_async_claims()` handler in `MistHelper.py` — call `mistapi.api.v1.orgs.licenses.listOrgAsyncClaims(apisession, org_id)`, flatten result with `flatten_nested_fields_in_list`, export via `DataExporter.save_data_to_output(flat_rows, filename, api_function_name="listOrgAsyncClaims")`, log before/after API call, surface empty-result message to operator
- [ ] T007 [US1] Wire menu 208 dispatch in `MistHelper.py` to call `list_org_async_claims()`, ensuring org context is resolved via existing `get_cached_or_prompted_org_id()` flow

**Checkpoint**: Menu 208 fully functional — list/export independently testable.

---

## Phase 4: User Story 2 — Create Org Async Claim (Priority: P2)

**Goal**: Destructive create operation gated behind exact typed confirmation (`CREATE`), with no API call dispatched on confirmation failure.

**Independent Test**: Select menu 209 — verify (a) wrong/empty confirmation cancels without API call and (b) correct `CREATE` confirmation submits and returns created claim response.

### Tests for User Story 2

- [ ] T008 [P] [US2] Write unit tests for `create_org_async_claim()` covering: confirmation mismatch cancels with no API call, empty confirmation cancels with no API call, correct confirmation dispatches API and handles success response, and API exception after confirmed dispatch in `tests/unit/test_async_claims.py`

### Implementation for User Story 2

- [ ] T009 [US2] Implement `create_org_async_claim()` handler in `MistHelper.py` — collect payload fields via `safe_input()`, invoke `_confirm_destructive("CREATE", "org_async_claim_create")` gate, return early on failure, call `mistapi.api.v1.orgs.licenses.createOrgAsyncClaim(apisession, org_id, body)` only after confirmed, export response via `DataExporter.save_data_to_output(..., api_function_name="createOrgAsyncClaim")`, log before/after API call
- [ ] T010 [US2] Wire menu 209 dispatch in `MistHelper.py` to call `create_org_async_claim()` with org context resolved via existing flow
- [ ] T011 [US2] Add menu 209 to the destructive-operation skip map in `run_systematic_test()` in `MistHelper.py` so default `--test` execution skips it per FR-011

**Checkpoint**: Menu 209 fully functional — confirmation gate verified, destructive skip active.

---

## Phase 5: User Story 3 — Retrieve Async Claim Status by ID (Priority: P3)

**Goal**: Safe status lookup by claim ID with empty/blank ID rejection before any API call.

**Independent Test**: Enter known claim ID at menu 210 — returns status fields and exports result; blank claim ID input is rejected with retry/cancel path and does not call API.

### Tests for User Story 3

- [ ] T012 [P] [US3] Write unit tests for `get_org_async_claim_status()` covering: blank/whitespace claim_id rejected before API call, valid claim_id dispatches API and exports success response, and API 404/permission error surfaced as operator feedback in `tests/unit/test_async_claims.py`

### Implementation for User Story 3

- [ ] T013 [US3] Implement `get_org_async_claim_status()` handler in `MistHelper.py` — prompt for claim_id via `safe_input()`, reject empty/whitespace with user message and return early, call `mistapi.api.v1.orgs.licenses.getOrgAsyncClaimStatus(apisession, org_id, claim_id)` (with backward-compat adapter for SDK naming if needed per research.md Decision 2), flatten result, export via `DataExporter.save_data_to_output(..., api_function_name="getOrgAsyncClaimStatus")`, log before/after API call
- [ ] T014 [US3] Wire menu 210 dispatch in `MistHelper.py` to call `get_org_async_claim_status()` with org context resolved via existing flow

**Checkpoint**: All three menu operations functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation alignment and full quality-gate pass.

- [ ] T015 [P] Update `README.md` — change operation count from 207 to 210 and add rows for menus 208, 209, 210 to the menu coverage table (per FR-012)
- [ ] T016 [P] Add versioned entry in `CHANGELOG.md` for mistapi 0.63.0 org async-claim menu support (menus 208–210) in Keep-a-Changelog format with UTC timestamp (per FR-013)
- [ ] T017 Run full quality gates from repo root per quickstart.md: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`, `pytest tests/unit -q -ra` — confirm all pass before committing

**Checkpoint**: All acceptance criteria (SC-001 through SC-005) satisfied. Ready for commit/PR.

---

## Dependency Graph

```text
T001 → T003 → T006 → T007  [US1 complete]
T001 → T003 → T009 → T010  [US2 main path]
T001 → T003 → T013 → T014  [US3 main path]
T001 → T004 → T007, T010, T014  [menu wiring]
T002 → T006, T009, T013  [SDK symbol confirmation]
T011 → (no dependents, standalone harness edit)
T005, T008, T012 → T017  [tests must exist before final gate run]
T015, T016 → T017  [docs must be updated before gate run]
```

**Stories are independent**: US2 and US3 implementation can begin in parallel with US1 once Phase 2 is complete.

## Parallel Execution Per Story (Phase 2 complete)

```text
[Phase 3 US1]  T005, T006 (parallel start) → T007
[Phase 4 US2]  T008, T009 (parallel start) → T010 → T011
[Phase 5 US3]  T012, T013 (parallel start) → T014
[Phase 6]      T015, T016 (parallel)        → T017
```

## Implementation Strategy

**MVP scope (Story 1 only)**: Complete T001–T004 + T005–T007 to deliver list/export capability without any destructive risk.

**Full delivery**: Continue T008–T016 sequentially by priority, then T017 as final gate.

## Summary

| Metric | Value |
| - | - |
| Total tasks | 17 |
| US1 tasks | 3 (T005–T007) |
| US2 tasks | 4 (T008–T011) |
| US3 tasks | 3 (T012–T014) |
| Foundational tasks | 2 (T003–T004) |
| Setup tasks | 2 (T001–T002) |
| Polish tasks | 3 (T015–T017) |
| Parallelizable | T002, T005, T008, T012, T015, T016 |
| MVP scope | T001–T007 (7 tasks, US1 only) |
