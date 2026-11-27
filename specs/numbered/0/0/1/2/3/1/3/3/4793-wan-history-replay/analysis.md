# Specification Analysis Report: WAN history replay safety

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, `design/contracts/sample-replay.md`, and the remote code of the candidate branch at `843be63bc837513b4442dae69da9f0db922e0ed1`.

**Method**: A read-only pass. The pass compared each requirement with its task and test. It also compared each claim with the remote evidence rows of `design/research.md`. No test, linter, build, or write ran in this pass.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A1 | Evidence | HIGH | `src/interfaces/wan_performance/integration/` on `main` (RC-01 to RC-04) | Main holds no WAN history writer. The repair exists only on the candidate branch (RC-29, RC-30, RC-33). | Decision D-1 names PR #4208 as the carrier. Decision D-8 requires owner approval. |
| A2 | Defect | MEDIUM | `arango_history.py` line 178 (RC-35) | `ArangoHistory.upsert` does not check the commit result. The constitution forbids success before a verified write (RC-11). | FR-007. Tasks T004 and T009. |
| A3 | Defect | LOW | `arango_history.py` line 180 (RC-36) | A failing rollback can hide the original error. `ArangoArchive._abort` already guards this path (RC-65). | FR-008. Tasks T005 and T010. |
| A4 | Defect | MEDIUM | `snapshot_records.py` line 241 (RC-42) | `_rate_samples` overwrites a conflicting duplicate with no report. The issue requires an explicit report. | FR-009. Tasks T007 and T012. |
| A5 | Gap | MEDIUM | `test_live_service.py` line 133 (RC-54, RC-55) | No committed test refreshes a port with repeated API samples. The owner's six-sample result is not in the repository. | FR-010. Task T008. |
| A6 | Gap | LOW | `record_codec.py` line 424 (RC-39) | The changed-data error names no time. An operator cannot match the error to one sample. | FR-013. Tasks T006 and T011. |
| A7 | Gap | MEDIUM | `live_routes.py` lines 336 to 341 (RC-43, RC-44) | The portal shows generic text for a conflict. The issue asks for an explicit report. | Decision D-6 and unresolved item U-1. |
| A8 | Inconsistency | LOW | `documentation/wan-performance.md` line 46 (RC-69) | The document states a confirmed Arango commit for archive appends. The upsert path did not confirm it. | FR-007 closes the code gap. Task T013 aligns the sentence. |
| A9 | Process | HIGH | Pull request #4208 merge state (remote, read with `gh pr view`) | The branch reports `CONFLICTING` with `main`. The compare API reports the repair commit 52 commits behind `main`. | Risk R1 in `plan.md`. Task T-PR rebases first. The stop rule of `AGENTS.md` applies at 20 conflicting lines. |
| A10 | Process | MEDIUM | Local `.github\copilot-instructions.md` and `.specify\memory\constitution.md` | The local copies differ from remote `main`. The local instructions have 473 lines. Remote `main` has 601 lines. | This record cites remote line numbers only. Task T-PR rebases the branch. |
| A11 | Process | LOW | Pull request #4208 body (RC-14 rule) | The body does not contain `Closes #4793`. | Task T-PR adds the closing keyword. |
| A12 | Structure | MEDIUM | `arango_history.py`, `snapshot_records.py`, `record_codec.py` (RC-33, RC-41, RC-37) | The touched modules already exceed the structure limits. | Four remediation actions in `plan.md` Complexity Tracking. |
| A13 | Evidence | HIGH | Commit `15c69b1176f7ae7c24e010aba3d29915ef228610` (RC-62) | GitHub returns HTTP 422 for the reproduction commit. The first reproduction in the issue cannot run. | Unresolved item U-2. The committed replay test covers the same path (RC-48). |
| A14 | Evidence | MEDIUM | `test_history_repository.py` (RC-51, RC-52) | The issue asks for a focused Arango regression before verification. The replay test exists. No commit test exists. | FR-007. Task T004. |
| A15 | Ambiguity | LOW | Issue body, "avoid duplicate statistical weighting" | The repository gives no definition of this phrase. | The spec defines it as one stored row for each sample key (FR-001, FR-003, FR-010). |

## Defects in Existing Work

The candidate branch already fixes the reported path for SQLite and for mocked Arango replays. Its tests cover unchanged replays, changed data, and rollback (RC-48 to RC-51). The remaining defects are A2, A3, A4, A5, A6, and A8. Each has a task. A12 records the structure debt in the touched modules.

## Coverage Summary

| Requirement | Tasks | Tests | Notes |
|-------------|-------|-------|-------|
| FR-001 | T001 | RC-48 (existing) | SQLite replay. |
| FR-002 | T003, T009 | RC-51 (existing, updated) | Arango replay. |
| FR-003 | T001 | RC-48 (existing) | The first call of the test passes two equal samples. |
| FR-004 | T001, T003 | RC-49 and RC-51 (existing) | SQLite and Arango changed data. |
| FR-005 | T002 | RC-48 and RC-38 | Collection time differs, and the key is equal. |
| FR-006 | T002 | RC-48 | Both times stay in the stored payload. |
| FR-007 | T004, T009 | N1 (new) | Commit result check. |
| FR-008 | T005, T010 | N2 (new) | Rollback error handling. |
| FR-009 | T007, T012 | N4 and N5 (new) | Conflicts and identical duplicates. |
| FR-010 | T008 | N6 and N7 (new) | Repeated API samples and poll samples. |
| FR-011 | T001 | RC-67 (existing) | Hourly replacement. |
| FR-012 | T008, T-LOCAL-GATES | N6 (new) | The patched collector is the only source of samples. |
| FR-013 | T006, T011 | N3 (new) | The error names the sampled time. |
| FR-014 | T013 | STE gate row | Documentation check. |

Each requirement maps to at least one task and at least one test or gate row.

## Consistency Checks

- Each file row in `plan.md` Source Code has a task. The Arango module maps to T009 and T010. The record codec maps to T011. The snapshot module maps to T012. The test modules map to T004 to T008. The documents map to T013. The record maps to T-PR.
- Each task names exact repository paths and one verification command from the local gates table.
- The route `0/0/1/2/3/1/3/3` equals the base-5 digits of 4793. The sum is 3125 + 1250 + 375 + 25 + 15 + 3, which equals 4793. The script rule is RC-09.
- The record folder adds one child to `specs/numbered/0/0/1/2/3/1`. That folder keeps three children on `main` (RC-68).
- The record holds five children at the feature root and five children under `design/`.

## Metrics

| Metric | Value | Source |
|--------|-------|--------|
| Requirements | 14 | `spec.md` |
| Tasks | 17 | `tasks.md` (13 numbered and 4 final) |
| Planned new tests | 7 | `tasks.md` Phase 2 |
| Decisions | 9 | `design/research.md` |
| Human decisions | 1 | Decision D-8 |
| Remote checks | 69 | `design/research.md` table, `STATUS.json`, and the summary |

## Unresolved Items

- U-1: The operator-visible conflict text is deferred. A new exception class in `record_codec.py` would make a sixth child in a module that already holds five. A follow-up issue must add the text.
- U-2: Live ArangoDB persistence is unverified. This work uses mocks and real SQLite only.
- U-3: The claim that the live API repeats a retained timestamp is unverified. This work makes no Mist request. The local OpenAPI copy has no located `points` schema.
- U-4: The rebase result of PR #4208 is unknown. The current merge state is `CONFLICTING`.
- U-5: The owner decision on publication (Decision D-8) is open.
- U-6: The local checkout is stale. Its instruction files differ from remote `main`.
- U-7: The STE score and the gate results of the new text are unknown. This review runs no linter.
