# Analysis: R0902 and R0903 class design

## Consistency Review

| Check | Spec | Plan | Tasks | Remote code | Result |
| - | - | - | - | - | - |
| Findings at `main` f03c6c9 | 25 (FR-001) | 25 (Complexity Tracking, rows 1 to 19 plus 6 resolved) | Not applicable | 9 R0902 and 16 R0903 (research register) | Consistent |
| Resolved findings | 6 (FR-002) | Six methods in the method table | T002, T004, T007, T008, T010, T012 | Six R0903 findings in research rows RC-10, RC-11, RC-13, RC-14, RC-15, RC-16 | Consistent |
| Remaining findings | 19 (SC-001) | 19 (Complexity Tracking) | T014 and TS-16 | Register rows 1 to 19 | Consistent |
| Requirements | 9 (FR-001 to FR-009) | Change map cites FR IDs | Coverage table maps each FR to a task and a test | Not applicable | Consistent |
| Tests | 15 pytest cases and 3 checks | Four modules, one fragment | 18 tests in the test count section | Four test modules at RC-28 to RC-30 and RC-23 | Consistent |
| Tasks | Not applicable | Change map | 18 tasks (14 implementation, 4 final) | Not applicable | Consistent |
| Remote checks | 59 rows | Not applicable | Not applicable | Research table has 59 rows | Consistent with STATUS and summary |

## Defects in the Existing Issue Work

1. **Title and count**: The title says 27 findings in 11 files. `main` f03c6c9 has 25 findings. `fake_gateway.py` has none (research row RC-25).
2. **Stale lines in the issue body**: `MistHelper.py` line 1087 is an `ImportError` line on `main` (research row RC-07). The class lines are 1207, 1744, and others (rows RC-01 to RC-04).
3. **Stale fake gateway finding**: The issue body places an R0903 finding at `fake_gateway.py` line 96. That line is a docstring on `main` (research row RC-26). `FakeClock` counts two public methods, because pylint counts `__call__` (research row RC-58).
4. **Stale paths**: The issue body names `src/org/juniper_rma`. That path is absent on `main` (research row RC-49). The current path is `src/operations/exporting/juniper_rma`.
5. **Stale PR ownership**: Issue comment 1 says PR #4607 still owns `MistHelper.py`. PR #4607 merged on 2026-11-13 (research row RC-51).
6. **Stale PR status**: Issue comment 2 says draft PR #4358 renames the three RMA tests. PR #4358 merged on 2026-11-13, and its file list holds no RMA test (research row RC-52).
7. **Attribute count drift**: Issue comment 2 gives 14 attributes for `OperationExecutor` at line 917. `main` has 15 attributes at line 918 (research row RC-20). The finding remains.
8. **Pylint version drift**: Issue comment 2 used Pylint 4.1.3. The `.venv` holds Pylint 4.1.4 (research rows RC-57 to RC-59). This record re-derives the counts from source, because the brief forbids running a linter.
9. **Branch name reference**: The issue body cites branch `3519-juniper-rma-correlation`. Issue 3519 is a closed CI issue about a pytest failure. It is not related to this issue.
10. **Command path**: The issue body reproduces with `.venv\Scripts\python.exe -m pylint src\org\juniper_rma`. The path `src\org\juniper_rma` is absent. `quickstart.md` gives the current paths.

## Rule Conflicts

1. **Changelog fragment**: The constitution requires one fragment for each change (research row RC-36, line 409). `changelog.d\README.md` rule 4 says no fragment for an internal-only change (research row RC-35). AGENTS.md limits fragments to user-visible changes (research row RC-37, line 342). The constitution supersedes other practice documents (research row RC-36, line 529). Decision D-11 follows the constitution.
2. **Compatibility shims**: AGENTS.md says not to keep a compatibility shim, an adapter, or a fallback path during a refactor (research row RC-37, line 88). The datetime adapter and the three fallback classes remain as recorded exceptions (decisions D-2 and D-3). Each one serves an import-time contract, not an old call site. Follow-up F-2 owns the adapter.

## Gate Scope Facts

- The CI pylint gate reads `src/` only (research row RC-34). Findings in `MistHelper.py`, `web_portal/`, and tests do not block CI. The register is the only control for those files.
- The final tasks verify with GitHub checks and a scope check. No local gate covers pull request creation or merge. This is a stated exception to the verification rule.

## Unresolved Items

1. **Follow-up F-1 (GlobalImportManager state)**: Proposed title: `Refactor: group GlobalImportManager import state into records`. Scope: `MistHelper.py` class lines 1207 to 2558, and readers in `src/foundation/support/refactors/serial_cc/import_initialization_service.py`. Risk: bootstrap order changes. Prerequisite: a test that pins the bootstrap order.
2. **Follow-up F-2 (datetime adapter)**: Proposed title: `Refactor: remove the datetime import adapter`. Scope: `_DateTimeHandler` (`MistHelper.py` line 1744), its binding (line 1404), and `_import_datetime` (line 1769). Risk: the module-level name `datetime` changes for every menu. Prerequisite: a characterization test for the name and the five `datetime.now(UTC)` calls.
3. **Follow-up F-3 (OperationExecutor state)**: Proposed title: `Refactor: group OperationExecutor run state into records`. Scope: `web_portal/services/operation.py` lines 918 to 1731, and private reads in the web portal tests (local search: 142 reads in 34 files). Risk: run lifecycle and event publication change. Prerequisite: tests that use public behavior instead of private attributes.
4. **Human review**: The brief does not require a human decision. No decision in this record falls under the human decision categories. The register and the follow-up scopes remain open for review by the orchestrator.
