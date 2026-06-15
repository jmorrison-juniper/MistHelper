# Tasks: Site Marvis Config Actions

**Input**: Design documents from `specs/1001-site-marvis-config-actions/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/menu-operations-contract.md ✓, quickstart.md ✓

**Tests**: Included — FR-012 and FR-013 explicitly require automated coverage for safe count/search behavior, feedback validation, and destructive delete guard behavior in test mode.

**Operations in scope** (4 total):
- Operation A: Site Marvis Config Action Count (safe)
- Operation B: Site Marvis Config Action Search (safe, paginated)
- Operation C: Submit Site Marvis Config Action Feedback (mutating)
- Operation D: Delete Site Marvis Config Action by ID (destructive)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files or no shared blockers)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths listed in each task

---

## Phase 1: Setup

**Purpose**: Verify SDK callable names, reserve menu slots, and lock down scope documentation before code changes begin.

- [ ] T001 Verify the four mistapi 0.63.0 site Marvis config action callable names (`countSiteMarvisConfigActions`, `searchSiteMarvisConfigActions`, `submitSiteMarvisConfigFeedback`, `deleteSiteMarvisConfigAction`) are available for use from the Mist SDK path consumed by `MistHelper.py`; record confirmed names in `specs/1001-site-marvis-config-actions/research.md`
- [ ] T002 Identify four available menu operation number slots in `MistHelper.py` for the new Site Marvis Config Action workflows and record the chosen menu numbers under a new `Menu Number Assignments` heading in `specs/1001-site-marvis-config-actions/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared validation, site-scope prompting, audit/export shaping, and PK registrations that every operation depends on.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete.

- [ ] T003 [P] Implement a shared site-scope prompt helper in `MistHelper.py` that collects `org_id`, `site_id`, and optional time/filter inputs via `safe_input()` for Site Marvis Config Action operations; add focused unit coverage for valid/invalid scope input in `tests/unit/test_site_marvis_config_actions.py`
- [ ] T004 [P] Implement shared validation helpers in `MistHelper.py` for duration/time-window checks, action ID format checks, allowlisted feedback types, bounded comments, and feedback value type/range enforcement; add focused unit coverage for rejection cases in `tests/unit/test_site_marvis_config_actions.py`
- [ ] T005 [P] Implement a shared site Marvis config action pagination helper in `MistHelper.py` that traverses multi-page search responses, tracks page counters, and reports partial progress safely on page failure; add unit coverage for multi-page success and malformed continuation handling in `tests/unit/test_site_marvis_config_actions.py`
- [ ] T006 Implement `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries in `MistHelper.py` for all four datasets: `countSiteMarvisConfigActions`, `searchSiteMarvisConfigActions`, `submitSiteMarvisConfigFeedback`, and `deleteSiteMarvisConfigAction`, using the deterministic keys defined in `specs/1001-site-marvis-config-actions/data-model.md`
- [ ] T007 Implement shared result-normalization/export-shaping helpers in `MistHelper.py` for count/search/feedback/delete outputs so each workflow emits deterministic records with org/site/action context before `DataExporter.write_with_format_selection()` is called; add unit coverage in `tests/unit/test_site_marvis_config_actions.py`

**Checkpoint**: Shared prompts, validators, pagination, PK strategy, and export shaping are complete — user stories can begin.

---

## Phase 3: User Story 1 - Export site Marvis config action data safely (Priority: P1) 🎯 MVP

**Goal**: Operators can count and search Site Marvis Config Actions for a selected site, including multi-page retrieval, without mutating production state.

**Independent Test**: Run count and search for a selected site with and without optional filters; verify exported output, stable keys, page totals, empty-result behavior, and zero mutation calls.

### Tests for User Story 1 ⚠️ Write first — ensure FAIL before implementation

- [ ] T008 [P] [US1] Add happy-path regression test for `countSiteMarvisConfigActions` in `tests/unit/test_site_marvis_config_actions.py`; assert the count result is normalized, exported with `api_function_name="countSiteMarvisConfigActions"`, and summarized clearly
- [ ] T009 [P] [US1] Add invalid-scope/window validation test for the count workflow in `tests/unit/test_site_marvis_config_actions.py`; assert validation blocks the API call and shows corrective guidance
- [ ] T010 [P] [US1] Add happy-path regression test for paginated `searchSiteMarvisConfigActions` in `tests/unit/test_site_marvis_config_actions.py`; mock a multi-page response, assert all pages are collected, and assert duplicate-safe export behavior
- [ ] T011 [P] [US1] Add empty-result regression test for `searchSiteMarvisConfigActions` in `tests/unit/test_site_marvis_config_actions.py`; assert successful completion with explicit empty-summary messaging and valid export call
- [ ] T012 [P] [US1] Add malformed pagination/continuation failure test for `searchSiteMarvisConfigActions` in `tests/unit/test_site_marvis_config_actions.py`; assert actionable recovery guidance and partial-progress reporting

### Implementation for User Story 1

- [ ] T013 [US1] Implement the Site Marvis Config Action count handler in `MistHelper.py`; reuse the shared site-scope prompt/validation helpers, call `countSiteMarvisConfigActions`, normalize/export the count dataset with `api_function_name="countSiteMarvisConfigActions"`, and print scope-aware execution summary (depends on T003, T004, T006, T007)
- [ ] T014 [US1] Implement the Site Marvis Config Action search handler in `MistHelper.py`; reuse the shared site-scope prompt/validation helpers, drive multi-page traversal through the pagination helper, normalize/export records with `api_function_name="searchSiteMarvisConfigActions"`, and print page/row totals (depends on T003, T004, T005, T006, T007)
- [ ] T015 [US1] Wire the new count and search handlers into the menu labels and dispatch paths in `MistHelper.py` using the slots recorded in `specs/1001-site-marvis-config-actions/quickstart.md` (depends on T002, T013, T014)

**Checkpoint**: US1 is independently functional — safe count/search export workflows work end-to-end.

---

## Phase 4: User Story 2 - Submit config-action feedback with guardrails (Priority: P2)

**Goal**: Operators can submit Site Marvis Config Action feedback only after strict validation passes, with clear rejection guidance for invalid input.

**Independent Test**: Run the feedback workflow with valid and invalid inputs; verify invalid payloads never call the mutating API and valid payloads export an audit-friendly result dataset.

### Tests for User Story 2 ⚠️ Write first — ensure FAIL before implementation

- [ ] T016 [P] [US2] Add valid-feedback happy-path regression test for `submitSiteMarvisConfigFeedback` in `tests/unit/test_site_marvis_config_actions.py`; assert validated payload submission, exporter call with `api_function_name="submitSiteMarvisConfigFeedback"`, and success summary
- [ ] T017 [P] [US2] Add required-field rejection test for the feedback workflow in `tests/unit/test_site_marvis_config_actions.py`; assert missing `action_id` or feedback fields block the API call
- [ ] T018 [P] [US2] Add allowlist/type/range validation rejection tests for the feedback workflow in `tests/unit/test_site_marvis_config_actions.py`; assert unsupported feedback types, invalid values, and overlong comments are rejected pre-call with field-level guidance

### Implementation for User Story 2

- [ ] T019 [US2] Implement the Site Marvis Config Action feedback submission handler in `MistHelper.py`; collect site/action context and feedback input via `safe_input()`, enforce shared validation helpers, call `submitSiteMarvisConfigFeedback` only on valid payloads, normalize/export the audit result with `api_function_name="submitSiteMarvisConfigFeedback"`, and print success/rejection summaries (depends on T003, T004, T006, T007)
- [ ] T020 [US2] Wire the feedback submission handler into the menu labels and dispatch paths in `MistHelper.py` using the slot recorded in `specs/1001-site-marvis-config-actions/quickstart.md` (depends on T002, T019)

**Checkpoint**: US2 is independently functional — guarded feedback submission works and blocks invalid mutation attempts.

---

## Phase 5: User Story 3 - Delete a config action only with explicit confirmation (Priority: P3)

**Goal**: Operators can delete a Site Marvis Config Action by ID only after warning + exact typed confirmation, while unattended test mode remains hard-guarded.

**Independent Test**: Run delete with wrong confirmation, cancel path, and exact confirmation path; verify the destructive API call occurs only on exact confirmation and test mode remains skipped/guarded with explicit reporting.

### Tests for User Story 3 ⚠️ Write first — ensure FAIL before implementation

- [ ] T021 [P] [US3] Add delete confirmation mismatch regression test in `tests/unit/test_site_marvis_config_actions.py`; assert `deleteSiteMarvisConfigAction` is not called and cancellation is reported clearly
- [ ] T022 [P] [US3] Add exact-confirmation happy-path regression test in `tests/unit/test_site_marvis_config_actions.py`; assert warning banner precedes prompt, API call executes only after exact match, and result exports with `api_function_name="deleteSiteMarvisConfigAction"`
- [ ] T023 [P] [US3] Add unattended `--test` mode guard regression test in `tests/unit/test_site_marvis_config_actions.py`; assert destructive delete remains skipped or hard-blocked with explicit reporting in automated runs

### Implementation for User Story 3

- [ ] T024 [US3] Implement the Site Marvis Config Action delete handler in `MistHelper.py`; collect site/action context, show destructive warning banner, require exact typed confirmation, block on mismatch/cancel, call `deleteSiteMarvisConfigAction` only after exact confirmation, normalize/export destructive audit result with `api_function_name="deleteSiteMarvisConfigAction"`, and print cancellation/success/failure summary (depends on T003, T004, T006, T007)
- [ ] T025 [US3] Wire the delete handler into the menu labels and dispatch paths in `MistHelper.py` using the slot recorded in `specs/1001-site-marvis-config-actions/quickstart.md`, and update the automated test guard list in `MistHelper.py` so destructive execution remains skipped in unattended test mode (depends on T002, T024)

**Checkpoint**: US3 is independently functional — destructive delete path is safe, explicit, and test-guarded.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish export compatibility, documentation, and release hygiene shared across all user stories.

- [ ] T026 [P] Add CSV and SQLite export compatibility regression tests for count/search/feedback/delete outputs in `tests/unit/test_site_marvis_config_actions.py`
- [ ] T027 [P] Add output failure regression tests for all four operations in `tests/unit/test_site_marvis_config_actions.py`; mock `DataExporter.write_with_format_selection()` failures and assert actionable operator guidance without silent loss
- [ ] T028 Update `README.md` to increase the documented operation count by 4 and add the new Site Marvis Config Action menu entries with their safety classes
- [ ] T029 Update `CHANGELOG.md` with a feature entry describing the four new Site Marvis Config Action operations, validation safeguards, destructive confirmation guard, and mistapi 0.63.0 support
- [ ] T030 Run and record feature-specific verification from `specs/1001-site-marvis-config-actions/quickstart.md`, then run repository quality gates for `MistHelper.py` (`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`) before implementation handoff or PR preparation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **User Story phases (Phases 3–5)**: All depend on Phase 2 completion; can then proceed in priority order or in parallel if staffed
- **Polish (Phase 6)**: Depends on completion of the user stories being delivered

### User Story Dependencies

| Story | Depends on | Integration notes |
| - | - | - |
| US1 (P1) — Safe count/search export | Phase 2 complete | Reuses shared site-scope prompting, validation, pagination, and export shaping |
| US2 (P2) — Feedback submission | Phase 2 complete | Reuses shared site-scope prompting, validation, and export shaping; no dependency on US1 runtime behavior |
| US3 (P3) — Destructive delete | Phase 2 complete | Reuses shared site-scope prompting, validation, and export shaping; also updates unattended test guard path |

### Within Each User Story

1. Write tests first and confirm they fail
2. Complete shared prerequisites from Phase 2 before handler implementation
3. Implement handler logic before menu wiring
4. Complete menu wiring before story-level validation checkpoint

### Parallel Opportunities

- T003, T004, T005 can run in parallel in Phase 2
- T008–T012 can run in parallel in US1 test phase
- T016–T018 can run in parallel in US2 test phase
- T021–T023 can run in parallel in US3 test phase
- T026 and T027 can run in parallel in Phase 6
- After Phase 2, US1, US2, and US3 can be implemented by different engineers in parallel if coordination on `MistHelper.py` is managed carefully

---

## Parallel Execution Example: User Story 1

```text
T001 → T002 (sequential)
         ↓
T003 ─┐
T004 ─┼─→ T006 → T007
T005 ─┘
         ↓
T008 ─┐
T009 ─┼─→ T013 → T014 → T015
T010 ─┤
T011 ─┤
T012 ─┘
```

### Additional Parallel Examples

```text
US2 test batch: T016, T017, T018
US3 test batch: T021, T022, T023
Polish batch: T026, T027
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate safe count/search workflows independently
5. Stop for review if only MVP scope is needed

### Incremental Delivery

1. Setup + Foundational establish safe shared infrastructure
2. US1 delivers immediate operator value with read-only exports
3. US2 adds controlled mutation with strict validation
4. US3 adds destructive completeness with hard safety gates
5. Polish finalizes docs, export coverage, and release readiness

### Suggested MVP Scope

Implement through **T015** for a useful, low-risk first increment.

---

## Notes

- All tasks use explicit file paths and strict checklist formatting for direct LLM execution.
- Test tasks are included because the feature spec explicitly requires automated coverage and destructive-path guards.
- `MistHelper.py` is a hot file in this repo; parallel work is possible, but only with deliberate coordination to avoid file-overlap conflicts.
