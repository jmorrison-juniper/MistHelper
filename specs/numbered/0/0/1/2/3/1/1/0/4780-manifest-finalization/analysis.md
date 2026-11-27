# Specification Analysis Report: Hardware Manifest Finalization After a File Lock

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, the two contracts, the two checklists, and the remote tree of `main`.

**Method**: A read-only pass built the requirement inventory, the task coverage map, and the code evidence map. The pass found the defects in the existing code. It also lists the open items.

## Defects in Existing Work

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A-01 | Defect | HIGH | `artifacts.py:444-459`, `artifacts.py:140`, `artifacts.py:264` | A refused final manifest replace leaves `manifest.json` at its last snapshot, which reads `writing`. Memory reads `failed`. The durable record never reaches a final state. | FR-002, FR-006 to FR-008. Tasks T010 to T012. |
| A-02 | Defect | HIGH | `factory.py:347`, `factory.py:354`, `models.py:334` | `finish_parent` ignores the result of `artifacts.finish()`. When every target completed, the parent reads FINISHED with "The batch finished." | FR-012. Task T014. |
| A-03 | Defect | HIGH | `operation.py:305`, `watch.py:82`, `console.py:118` | The CLI partial rule counts target outcomes only. A failed output with completed targets prints `Run status: complete`. | FR-013. Tasks T015 to T017. |
| A-04 | Defect | MEDIUM | `artifacts.py:457`, `artifacts.py:160`, `artifacts.py:121-124` | One refused in-run manifest replace fails the record. Later hardware saves then fail with "not writable." The run stops for every later target. | FR-003 to FR-005. Task T013. |
| A-05 | Defect | MEDIUM | `artifacts.py:121-140`, `factory.py:792-799` | A native file that publishes before a refused snapshot stays on disk. Its format reads failed, and the per-target file list omits it. | FR-010. Task T013 and TEST-07. |
| A-06 | Risk | MEDIUM | `artifacts.py:92-96`, `artifacts.py:121-124`, `artifacts.py:461-483` | The replace sleeps while the record lock is held. Each refused write blocks every target worker for up to 0.75 seconds. | FR-004. A later in-run write tries once without waits. |
| A-07 | Defect | LOW | `artifacts.py:452-455` | A refused write leaves `.manifest.tmp` on disk. No code removes the file. | FR-009. Task T010 and TEST-04. |
| A-08 | Gap | LOW | `artifacts.py:458` | The error event gives the exception name only. The logs cannot show the cause. | FR-011. Task T010 and TEST-05. |
| A-09 | Pinned defect | INFO | `test_ws_artifact_replace.py:169`, `test_ws_artifact_replace.py:223`, `test_ws_session_manager.py:415` | Existing tests pin the defect. Line 169 expects the record to fail at the first refusal. Line 223 expects the last complete manifest after a refused replace. | Line 169 is revised (TEST-10). Line 223 keeps its assertion, because the replace stays atomic. Line 415 keeps its assertion. |
| A-10 | Unverified | INFO | `artifacts.py:238`, `artifacts.py:595`, `artifacts.py:465-466`, `artifacts.py:677` | Three lock-holder hypotheses in research R2. None is proven. | Evidence task T019. Conditional fix T020. |
| A-11 | Mismatch | INFO | Issue #4780 text | "CLI status: incomplete" and "Durable report status: pending" have no matching literal in the code. The CLI prints `partial` or `complete` (`console.py:118`). | Recorded as U-4 in research. No code change. |

## Coverage Summary

| Requirement | Tasks | Tests |
|-------------|-------|-------|
| FR-001 | T001 | Existing test at `test_ws_artifact_replace.py:98` |
| FR-002 | T004, T010 | TEST-01, TEST-02 |
| FR-003 | T009, T013 | TEST-06, TEST-10 |
| FR-004 | T013 | TEST-06 |
| FR-005 | T013 | TEST-06 |
| FR-006 | T004, T012 | TEST-01 |
| FR-007 | T004, T012, T014 | TEST-02, TEST-08, TEST-10 |
| FR-008 | T002, T004, T011, T012 | TEST-02, TEST-03, TEST-11 |
| FR-009 | T004, T010 | TEST-04, TEST-11 |
| FR-010 | T013, T020 | TEST-07 |
| FR-011 | T010, T018, T019 | TEST-05 |
| FR-012 | T003, T006, T014 | TEST-08 |
| FR-013 | T007, T015, T016, T017, T018 | TEST-09 |
| FR-014 | T010, T012 | TEST-02, and the existing test at `test_ws_artifact_replace.py:223` |
| FR-015 | T-LOCAL-GATES | Full suite, which includes the transport contract tests |
| FR-016 | T019, T020 | TEST-05 (the fields that the evidence run reads) |
| FR-017 | T004 to T008 | TEST-01 to TEST-11 |

Each requirement has at least one task and at least one test.

## Consistency Checks

- The spec requirement IDs match the plan test IDs. TEST-01 to TEST-11 appear in tasks T004 to T008.
- The file list in the plan matches the file lists in the tasks.
- The states in `design/data-model.md` match `design/contracts/manifest-json.md`.
- The remote blob SHAs in `design/research.md` match the remote tree. The self-review compares each SHA with the tree.
- Each directory in the record holds five children or fewer.

## Unresolved Items

- Open questions U-1 to U-6 remain in `design/research.md`.
- The evidence task T019 may show a lock that lasts longer than 6.35 seconds. Risk R-6 in the plan then needs a second decision.
- Non-hardware batch presets also use the finalization budget (risk R-4).
