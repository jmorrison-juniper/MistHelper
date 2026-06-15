# Tasks: Org Marvis Client APIs Menu Set

**Input**: Design documents from `specs/1000-org-marvis-client-apis/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/menu-operations-contract.md ✓, quickstart.md ✓

**Tests**: Included — FR-015, FR-016, FR-017 mandate regression tests for happy path, failure path, pagination, and export compatibility.

**Operations in scope** (5 total, all safe read-only):
- Operation A: Org Marvis Client Insights Export
- Operation B: Org Marvis Client Events Count
- Operation C: Org Marvis Client Events Search (paginated, search-after)
- Operation D: Org Marvis Client Stats Count
- Operation E: Org Marvis Client Stats Search (paginated, search-after)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files or no shared blockers)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths listed in each task

---

## Phase 1: Setup

**Purpose**: Confirm SDK endpoint availability and claim menu operation number slots before writing any code.

- [ ] T001 Locate and verify the five mistapi 0.63.0 Org Marvis Client callable names (`getOrgMarvisClientInsights`, `countOrgMarvisClientEvents`, `searchOrgMarvisClientEvents`, `countOrgMarvisClientStats`, `searchOrgMarvisClientStats`) are importable in MistHelper.py — document confirmed names as inline comment block at top of feature section in `MistHelper.py`
- [ ] T002 Identify five consecutive available menu operation number slots in `MistHelper.py` menu dispatch table; record chosen numbers in `specs/1000-org-marvis-client-apis/quickstart.md` under a "Menu Number Assignments" heading

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helpers and PK strategy registrations that ALL five user story operations depend on before any handler can be written.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete.

- [ ] T003 [P] Implement `_validate_duration_input(value: str) -> bool` helper function inside the relevant class in `MistHelper.py`; returns `True` for accepted formats, returns `False` and prints corrective guidance otherwise; add unit test in `tests/unit/test_marvis_client_apis.py`
- [ ] T004 [P] Implement `_prompt_optional_filters(prompt_map: dict) -> dict` helper in `MistHelper.py` that loops `safe_input()` prompts for each optional filter key and allows operator to skip each one; add unit test in `tests/unit/test_marvis_client_apis.py`
- [ ] T005 [P] Implement `_handle_search_after_pagination(search_fn, base_params: dict, page_limit: int) -> list` helper in `MistHelper.py` that drives multi-page traversal using search-after continuation token, catches malformed/expired token errors with actionable message, and supports operator restart from first page; add unit test in `tests/unit/test_marvis_client_apis.py`
- [ ] T006 Register all five `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries in `MistHelper.py`:
  - `getOrgMarvisClientInsights` → `natural_pk` with uniqueness-preserving key (stable insight ID preferred; composite org/client/type/timestamp fallback)
  - `countOrgMarvisClientEvents` → `composite_pk` with deterministic scope key (`org_id`, `window_start`, `window_end`, `group_key`, `filters_hash`)
  - `searchOrgMarvisClientEvents` → `composite_pk` with idempotent detail key (`event_id` preferred; fallback org/client/type/timestamp)
  - `countOrgMarvisClientStats` → `composite_pk` with deterministic scope key parallel to events count
  - `searchOrgMarvisClientStats` → `composite_pk` with idempotent detail key (`stat_id` preferred; fallback org/client/metric/timestamp)

**Checkpoint**: Helpers and PK strategies complete — user story implementation can begin

---

## Phase 3: User Story 1 — Export Org Marvis Client Insights (Priority: P1) 🎯 MVP

**Goal**: Operator can select insights export, apply optional filters and duration, retrieve insight records, and receive CSV/SQLite output with execution summary.

**Independent Test**: Run insights export with default filters and with optional filters; verify CSV and SQLite outputs are generated with non-zero record counts and summary is printed.

### Tests for User Story 1 ⚠️ Write first — ensure FAIL before implementation

- [ ] T007 [P] [US1] Add happy-path regression test for insights export: mock `getOrgMarvisClientInsights` return; assert exporter called with correct `api_function_name`; assert row count in summary in `tests/unit/test_marvis_client_apis.py`
- [ ] T008 [P] [US1] Add edge-case test for insights export empty dataset: mock returns empty list; assert "no records" summary is printed without error in `tests/unit/test_marvis_client_apis.py`
- [ ] T009 [P] [US1] Add invalid-duration test for insights export: pass bad duration string; assert validation rejects and no API call is made in `tests/unit/test_marvis_client_apis.py`

### Implementation for User Story 1

- [ ] T010 [US1] Implement `_export_org_marvis_client_insights(apisession, org_id)` handler in `MistHelper.py`: collect optional filters via `_prompt_optional_filters()`; validate duration via `_validate_duration_input()`; call `getOrgMarvisClientInsights`; route result to existing `DataExporter.write_with_format_selection()` with `api_function_name="getOrgMarvisClientInsights"`; print execution summary (filters, effective window, row count) (depends T003, T004, T006)
- [ ] T011 [US1] Wire insights export handler to menu dispatch table in `MistHelper.py` using the slot assigned in T002; add human-readable menu label "Export Org Marvis Client Insights" (depends T010)

**Checkpoint**: US1 fully functional — insights export can be run end-to-end independently

---

## Phase 4: User Story 2 — Analyze Org Marvis Client Events (Priority: P2)

**Goal**: Operator can run event count for fast volume triage, then run event search with pagination and search-after continuation to retrieve full event records, both with CSV/SQLite output.

**Independent Test**: Run event count with optional filters; then run event search with same scope; verify count-to-search continuity for a sampled window; verify no duplicate/dropped records across a simulated two-page search response.

### Tests for User Story 2 ⚠️ Write first — ensure FAIL before implementation

- [ ] T012 [P] [US2] Add happy-path regression test for events count: mock `countOrgMarvisClientEvents`; assert aggregate rows exported with deterministic composite key in `tests/unit/test_marvis_client_apis.py`
- [ ] T013 [P] [US2] Add invalid-filter/duration test for events count: assert validation rejects invalid inputs pre-call in `tests/unit/test_marvis_client_apis.py`
- [ ] T014 [P] [US2] Add happy-path regression test for events search: mock two-page `searchOrgMarvisClientEvents` response; assert both pages collected; assert zero duplicate records using unique event IDs in `tests/unit/test_marvis_client_apis.py`
- [ ] T015 [P] [US2] Add malformed search-after token test for events search: mock expired token response; assert actionable error message printed and operator offered restart option in `tests/unit/test_marvis_client_apis.py`

### Implementation for User Story 2

- [ ] T016 [US2] Implement `_count_org_marvis_client_events(apisession, org_id)` handler in `MistHelper.py`: collect optional filters; validate duration; call `countOrgMarvisClientEvents`; export via `DataExporter.write_with_format_selection()` with `api_function_name="countOrgMarvisClientEvents"`; print execution summary (depends T003, T004, T006)
- [ ] T017 [US2] Implement `_search_org_marvis_client_events(apisession, org_id)` handler in `MistHelper.py`: collect optional filters and optional search-after token; validate duration; drive multi-page traversal via `_handle_search_after_pagination()`; export collected records via `DataExporter.write_with_format_selection()` with `api_function_name="searchOrgMarvisClientEvents"`; print execution summary with page traversal status and total row count (depends T003, T004, T005, T006)
- [ ] T018 [US2] Wire both event handlers to menu dispatch table in `MistHelper.py` using slots assigned in T002; add labels "Count Org Marvis Client Events" and "Search Org Marvis Client Events" (depends T016, T017)

**Checkpoint**: US1 and US2 both independently functional

---

## Phase 5: User Story 3 — Analyze Org Marvis Client Stats (Priority: P3)

**Goal**: Operator can run stats count and stats search (with pagination and search-after continuation) to monitor client-health trends and export complete stats records.

**Independent Test**: Run stats count then stats search for same scope; verify consistent export integrity; verify no dropped or duplicated records across simulated two-page stats search.

### Tests for User Story 3 ⚠️ Write first — ensure FAIL before implementation

- [ ] T019 [P] [US3] Add happy-path regression test for stats count: mock `countOrgMarvisClientStats`; assert deterministic composite key used in export in `tests/unit/test_marvis_client_apis.py`
- [ ] T020 [P] [US3] Add happy-path regression test for stats search: mock two-page `searchOrgMarvisClientStats` response; assert both pages collected with zero duplicates in `tests/unit/test_marvis_client_apis.py`
- [ ] T021 [P] [US3] Add malformed search-after token test for stats search: assert restart guidance shown in `tests/unit/test_marvis_client_apis.py`

### Implementation for User Story 3

- [ ] T022 [US3] Implement `_count_org_marvis_client_stats(apisession, org_id)` handler in `MistHelper.py`: same pattern as events count handler; call `countOrgMarvisClientStats`; export with `api_function_name="countOrgMarvisClientStats"`; print execution summary (depends T003, T004, T006)
- [ ] T023 [US3] Implement `_search_org_marvis_client_stats(apisession, org_id)` handler in `MistHelper.py`: same pattern as events search handler; call `searchOrgMarvisClientStats` via `_handle_search_after_pagination()`; export with `api_function_name="searchOrgMarvisClientStats"`; print execution summary with page traversal and row count (depends T003, T004, T005, T006)
- [ ] T024 [US3] Wire both stats handlers to menu dispatch table in `MistHelper.py` using slots assigned in T002; add labels "Count Org Marvis Client Stats" and "Search Org Marvis Client Stats" (depends T022, T023)

**Checkpoint**: All three user stories independently functional — full feature scope complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Export compatibility tests, output failure tests, documentation updates, and quality gates.

- [ ] T025 [P] Add CSV and SQLite export compatibility regression tests for all five operations (one test per operation asserting both output targets work) in `tests/unit/test_marvis_client_apis.py`
- [ ] T026 [P] Add output failure regression tests for all five operations: mock `DataExporter.write_with_format_selection()` raising `IOError`; assert actionable message printed and no corrupted artifact left in `tests/unit/test_marvis_client_apis.py`
- [ ] T027 Update `README.md` operation count (+5) and add all five operations to the menu operations table under the Org Marvis Client group
- [ ] T028 Add `CHANGELOG.md` entry for feature 1000: describe the five new Org Marvis Client menu operations, safe read-only scope, mistapi 0.63.0 compatibility, and pagination support
- [ ] T029 Run full quality gates against `MistHelper.py` (`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`) and resolve any violations before PR

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **User Story phases (3, 4, 5)**: All depend on Phase 2 completion; can then proceed in priority order (P1 → P2 → P3) or in parallel if staffed
- **Polish (Phase 6)**: Depends on all desired user story phases being complete

### User Story Dependencies

| Story | Depends on | Integration notes |
| - | - | - |
| US1 (P1) — Insights | Phase 2 complete | No dependency on US2/US3 |
| US2 (P2) — Events | Phase 2 complete | Reuses T003/T004/T005 helpers from Phase 2 |
| US3 (P3) — Stats | Phase 2 complete | Reuses T003/T004/T005 helpers from Phase 2 |

### Within Each User Story

1. Tests written and confirmed failing before implementation
2. Foundational helpers (T003/T004/T005) before handler
3. PK strategy (T006) before handler
4. Handler implemented before menu wiring
5. Menu wiring before story checkpoint

### Parallel Opportunities

- T003, T004, T005 in Phase 2 can run in parallel (different helper functions)
- T007, T008, T009 in Phase 3 can run in parallel (all tests, no shared state)
- T012, T013, T014, T015 in Phase 4 can run in parallel
- T019, T020, T021 in Phase 5 can run in parallel
- T025, T026 in Phase 6 can run in parallel
- US1, US2, US3 can be worked by different engineers simultaneously after Phase 2 completes

---

## Parallel Execution Example: User Story 1

```text
T001 → T002 (sequential)
         ↓
T003 ─┐
T004 ─┤ (parallel in Phase 2)
T005 ─┤
T006 ─┘
         ↓
T007 ─┐
T008 ─┤ (parallel tests, Phase 3 — write FIRST, verify FAIL)
T009 ─┘
         ↓
T010 → T011 (sequential implementation + wiring)
```

---

## Implementation Strategy

**MVP scope**: Complete Phase 1 + Phase 2 + Phase 3 (US1: Insights Export) — delivers immediate operator value with one working operation.

**Full delivery**: Phases 1–6 in sequence. US2 and US3 follow identical structural patterns to US1, so each subsequent story is faster to implement.

**Suggested sprint boundary**: Phase 3 (US1) as sprint 1 delivery; Phases 4–5 (US2/US3) as sprint 2; Phase 6 (polish + docs) completes sprint 2 before PR.
