# Analysis: WAN Performance portal integration

This review checks the spec, plan, tasks, research, and remote code against each other. Row IDs (R##) point to `design/research.md`. Decision IDs (D-#) point to `design/research.md`.

## Consistency review

| ID | Check | Result |
|---|---|---|
| C-1 | Synthetic route prefix in spec, plan, contracts, and tasks | Consistent: `/wan-performance/preview/` (FR-004, D-6, `contracts/routes.md`, T018). PR 4208 uses the root prefix (R93). The change is recorded as a defect (A-2). |
| C-2 | Live route prefix in spec, plan, contracts, and tasks | Consistent: `/wan-performance/live/` (R92, R135). |
| C-3 | Nested paths in plan and tasks | Consistent. Tasks name the nested paths from the plan file map. |
| C-4 | Task count | 37 tasks (T001 to T033 and four final tasks) in `tasks.md` and `4200-STATUS.json`. |
| C-5 | Requirement count | 21 requirements (FR-001 to FR-021) in `spec.md` and `4200-STATUS.json`. |
| C-6 | Test module count | 13 new test modules in `plan.md` (12 modules and one guard) and `tests_planned` in `4200-STATUS.json`. |
| C-7 | Remote row count | 146 rows in `design/research.md` and `remote_checks` in `4200-STATUS.json`. The summary repeats the count. |
| C-8 | Decision count | 15 decisions in `design/research.md` and `decisions` in `4200-STATUS.json`. Three are human decisions (D-1, D-2, D-3). |
| C-9 | Out-of-scope items | SLE page and replacement pages are out of scope in `spec.md`, and the plan adds no file for them. |
| C-10 | Legacy path | The new slug `wan-portal-integration` avoids the legacy path (D-12). |
| C-11 | Closing keyword | `tasks.md` T-PR uses `Refs #4200`. This deviates from the brief template (D-13). |

## Defects in existing work

| ID | Defect | Evidence |
|---|---|---|
| A-1 | PR 4208 merge state is DIRTY, but its body says the branch is conflict-free. | R01, R02 |
| A-2 | The PR 4208 nav gate checks `wan_performance.overview` (synthetic route). The link targets `wan_performance.live.overview` (live route). | R93, R97, R98 |
| A-3 | PR 4208 gives six children to five directories in the WAN package. | R106 |
| A-4 | PR 4208 starts the background worker by default. | R97 (worker hunk in `web_portal/app.py`) |
| A-5 | PR 4208 writes SQLite and ArangoDB rows directly, not through `DataExporter`. | R133, constitution line 312 |
| A-6 | PR 4208 uses module-level route functions. A sampled line has no inline comment. | R92, R93, constitution lines 91 and 204 |
| A-7 | PR 4208 WAN modules use the standard logger, not a structured logger. | R107, R134, constitution line 182 |
| A-8 | PR 4208 deletes eight WAN test files that PR 4629 merged to main. | R70, R78, R06 |
| A-9 | PR 4208 changes unrelated type annotations in `web_portal/app.py` (`dict[str, Any]` to `dict`). | R97 |
| A-10 | PR 4208 renames private helper functions in `initialize_mist_session.py`. | R99 |
| A-11 | PR 4208 lists #4200 as a closing issue, although its body says `Refs`. | R01 |
| A-12 | Legacy record contains 17 forbidden placeholder tags. | R144 |
| A-13 | Legacy research has no Unverified section and no remote verification table. | R141 |
| A-14 | Legacy plan has no risk section and no rollback section. | R142 |
| A-15 | Legacy analysis gives counts at line 856 that conflict with its task audit. | R143 |
| A-16 | Legacy analysis cites commit `40278aa1948cda154f7372c1b0dd893b3865c9f5`, which does not resolve. | R45 |
| A-17 | Legacy parity file holds one three-dot ellipsis. | R145 |

## Requirement coverage

| Requirement | Tasks | Tests or guards | Gap |
|---|---|---|---|
| FR-001 | T029 | `tests/guardrails` (T033) | Inventory check is manual (R25). |
| FR-002 | T004, T017 | `tests/e2e/web_portal/test_wan_performance_live.py` | None. |
| FR-003 | T017, T018, T019, T023 | `test_wan_performance_live.py`, `test_wan_performance_offline.py` | None. |
| FR-004 | T016, T018, T024 | `tests/unit/wan_performance/domain/test_offline_fixtures.py`, `test_wan_performance_offline.py` | None. |
| FR-005 | T014 | `tests/unit/wan_performance/domain/test_domain.py` | None. |
| FR-006 | T013 | `tests/unit/wan_performance/domain/test_calendar_summaries.py` | None. |
| FR-007 | T015 | `tests/unit/wan_performance/domain/test_domain.py` | None. |
| FR-008 | T007 | `tests/unit/wan_performance/collection/test_snapshot_client.py` | None. |
| FR-009 | T008, T009 | `test_peer_insights.py`, `integration/test_request_admission.py` | None. |
| FR-010 | T005, T011 | `integration/test_background_refresh.py` | None. |
| FR-011 | T012, T028, T033 | `integration/test_history_repository.py`, `tests/guardrails` | None. |
| FR-012 | T009, T010, T025 | `integration/test_refresh_store.py`, `integration/test_request_admission.py` | None. |
| FR-013 | T020, T028 | `collection/test_live_service.py`, `test_wan_performance_live.py` | None. |
| FR-014 | T006, T021 | `collection/test_live_service.py` | None. |
| FR-015 | T022, T025 | `collection/test_live_service.py`, `integration/test_background_refresh.py` | None. |
| FR-016 | T019, T031 | `test_wan_performance_live.py` | None. |
| FR-017 | T023, T024 | `test_wan_performance_live.py`, `test_wan_performance_offline.py` | None. |
| FR-018 | T001, T002, T003, T032 | `test_wan_dashboard_cache_only.py`, `test_src_public_symbol_preservation.py` | None. |
| FR-019 | T030 | `test_wan_performance_live.py` | None. |
| FR-020 | T026 | `tests/guardrails/test_wan_portal_attribution.py` (planned) | Guard not yet written (U-1). |
| FR-021 | T026, T027 | `tests/guardrails/test_wan_portal_attribution.py` (planned) | Guard not yet written (U-2). |

## Success criteria coverage

| Criterion | Evidence |
|---|---|
| SC-001 | T029 and the classified rows in `design/research.md`. |
| SC-002 | This table. FR-020 and FR-021 map to the planned guard (T026, T027). |
| SC-003 | T023 and T024. |
| SC-004 | T013 (ten controlled inputs). |
| SC-005 | T016, T018, and T024. |
| SC-006 | T025. |
| SC-007 | T022 (mocked overview request with at most two gateway calls). |
| SC-008 | T028 (compose diff check). |

## Unresolved items

- U-1: The FR-020 guard is planned in T026. It is not yet written.
- U-2: The FR-021 guard is planned in T027. It is not yet written.
- U-3: D-1 (source reuse and visual rights) waits for a human decision.
- U-4: D-2 (retention, backfill, and purge) waits for a human decision.
- U-5: D-3 (executive, engineering, and SLE views) waits for a human decision.
- U-6: Issue owner asked for a human decision before PR 4208 reconciliation (issue comment 2026-11-10T21:57:21Z). D-11 keeps reconciliation open for the owner.
- U-7: Issues #4793, #4794, and #4795 stay open (R11-R13). Their fixes are preserved but not merged. Tasks T009 and T010 cover the affected code.
- U-8: The PR 4208 body says "conflict-free" (R02). GitHub reports DIRTY (R01). The owner must correct the body.
- U-9: Test pass counts from issue comments are not reproduced (research U-5).
- U-10: Live Mist behavior is unverified (research U-6).
- U-11: Issue 4200 stays open (D-13). The owner closes it after acceptance.

## Notes for the orchestrator

- The brief template asks for `Closes #<ISSUE>` in T-PR. This record uses `Refs #4200` because the issue owner keeps the issue open (D-13).
- The legacy record stays on PR 4208. The new record uses slug `wan-portal-integration` (D-12).
- No test, build, linter, or container command ran in this task. The brief forbids those commands in this phase (rule 2).
