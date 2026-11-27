# Specification Analysis Report: Weak zero-assertion triage

**Scope**: Consistency review of `spec.md`, `plan.md`, `tasks.md`, and the remote state of `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: Read-only analysis. No test, linter, analyzer run, or package install ran in this session. The counts come from a read-only classification script stored in `files/spec-drafts/_meta/2711-triage-scan.ps1`. The script reads the local files. Those files equal the `main` blobs for 120 of 121 baseline files. The remaining file is absent on `main`.

## 1. Defects in existing work

| ID | Defect | Evidence | Effect | Disposition |
| - | - | - | - | - |
| A-1 | The issue acceptance command does not work. | Issue body, criterion 4. Comment 31. The `tools/test_quality_analyzer` tree has zero paths on `main`. | A reviewer cannot reproduce the acceptance step. | Use `test-quality-analyzer` (clarification in `spec.md`). |
| A-2 | The baseline holds 313 stale entries. | Classification: 284 counted by the analyzer rule, 17 self-assert in TestCase, 12 for a missing file. | The baseline overstates the debt by 56 percent. | T004 removes them. |
| A-3 | The baseline keys include line numbers. | `misthelper-devtools` `baseline.py` line 6 names `line_number` in the key. Lines 55, 194, and 214 use it. | Each edit above a flagged test looks like a new finding. | Serial merges. Upstream request in T005. |
| A-4 | Comment 167 reports 18 new findings on `main`. The pinned gate passed on `main`. | Workflow run 45774119357 on `f03c6c9` (`workflow_dispatch`) has job `Test quality ratchet (gate)` at success. The 18 entries are 17 self-assert entries and 1 strong-mock entry, all shifted by 1 to 7 or by 3 lines. | The older analyzer in the author's environment disagrees with the pin. | Use the pin (D-1). T001 confirms the installed commit. |
| A-5 | The umbrella issue closed automatically three times. | Comments 30, 48, and 57 come from `github-actions`. PR #4515 body contains `Closes #2711`. | Closing keywords in slice pull requests close the campaign. | `Part of #2711` in each slice (D-7). |
| A-6 | The comments name the wrong pin. | Comment 145 says the main pin is 0.6.3. `requirements-dev.txt` line 197 pins `2239e7bd`, version 0.6.4 at line 3 of that commit. | Readers apply the wrong analyzer. | Use the pin. Correct the record in T001. |
| A-7 | Five counts disagree. | Comment 1: 875. Comment 31: 486. Comment 58: 459 (0.6.3). Comment 167: 545 checked findings (all rules). Baseline: 557. | Progress reports cannot compare. | Use T002 as the single count source. |
| A-8 | Pull request #4821 merged while comment 166 says it was a draft on a hold. | `gh pr list` reports MERGED on 2026-11-19. Comment 166 (2026-11-17) says draft with auto-merge off. | A file hold may have been bypassed. | Unverified. Recorded in `research.md`. |
| A-9 | Stale paths in comments. | Comment 155 cites `tests/unit/test_favicon.py`. That path is absent on `main`. The file is at `tests/unit/maps/standalone/interfaces/portals/test_favicon.py`. Comments 135 and 165 also cite relocated paths. | A reviewer edits a path that no longer exists. | Use current paths (D-8). |

## 2. Triage reconciliation

| Disposition | Entries | Share | Source of the count |
| - | -: | -: | - |
| Stale, counted by the analyzer rule | 284 | 51.0 percent | Classification of the body (assert statement 148, strong mock 136). |
| Stale, self-assert in TestCase | 17 | 3.1 percent | `self.assert*` in a TestCase method. |
| Stale, missing file | 12 | 2.2 percent | `tests/unit/test_bulk_switch_upgrader.py` absent on `main`. |
| Detector gap, mock call-count | 99 | 17.8 percent | `assert_called_once()`, `assert_awaited()`, `assert_called(args)`. |
| Detector gap, helper assertion | 20 | 3.6 percent | Assertion helper call. |
| Detector gap, Playwright expect | 10 | 1.8 percent | Calls to the Playwright `expect` function in `tests/e2e/upgrade_portal/`. |
| Zero construct | 115 | 20.6 percent | No assertion construct in the body. |
| **Total** | **557** | **100 percent** | Matches the baseline count. |

**Shift check**: All 94 shifted entries fall in the stale groups. None falls in the detector-gap or zero-construct groups. A shifted entry is not a finding under the pinned analyzer, so the full gate has no new findings. This matches the passing run on `main`.

**Predicted findings under the pin**: 129 plus 115 equals 244. T002 confirms this count.

## 3. Coverage summary

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 Pinned authority | T001, T002 | VC-G, VC-A |
| FR-002 One disposition per entry | T002, T003, T004 | Reconciliation in section 2 |
| FR-003 Write command only | T004, T016 | VC-A, rule-count comparison |
| FR-004 Repair zero-construct tests | T006 to T015 | VC-P per file |
| FR-005 Mutation controls | T006 to T015 | Recorded control in each pull request body |
| FR-006 Upstream routing | T005 | Upstream issue URL in a comment on #2711 |
| FR-007 Helper reads | T003 | VC-P on `tests/unit/utils/test_zscaler_catalogue.py` |
| FR-008 Current paths | T003 | Remote checks in `research.md` |
| FR-009 Closing hygiene | T-PR | Pull request body check |
| FR-010 Overlap and holds | T-PR | Open pull request file check |
| FR-011 Local gates | T-LOCAL-GATES | Gate output in each pull request |
| FR-012 Remote CI | T-REMOTE-CI | Job conclusion |
| FR-013 Open until complete | T016, T-MERGE | Weak-zero count equals 129 |

## 4. Consistency across artifacts

- The plan and the tasks name the same 27 repair files. The slice counts sum to 27 files and 115 entries.
- The spec, plan, and tasks use the same disposition names.
- The plan and the tasks use the same route. The route is `specs/numbered/0/0/0/4/1/3/2/1`.
- Each task names a path that exists on `main`, or it names the file as the target of a new change.
- No task lacks a requirement ID. No requirement lacks a task.

## 5. Unmapped tasks

None. Each task maps to at least one requirement.

## 6. Unresolved items

- U-1: The 18-finding report in comment 167 is not reproduced. The source analysis and the passing run support the explanation in A-4. T001 and T002 confirm it.
- U-2: The count of 244 is a prediction. T002 confirms it.
- U-3: The helper bodies behind 20 gap-helper entries are not read. T003 reads them.
- U-4: The cause of the `test_quality_gate` failure on pull request #4888 is not inspected. Issue #4902 holds the failure. Pull request #4888 is open.
- U-5: The closing text in pull requests #4506 and #4527 is not found by pattern search.

## 7. Metrics

- Baseline entries: 733 total, 557 for `weak_zero_assertions`, 121 files.
- Repair scope: 115 entries, 27 files, 10 slices.
- Detector-gap scope: 129 entries, 3 families, 1 upstream issue.
- Stale scope: 313 entries, removed by T004.
- Remote checks: 37 rows in `research.md` and `2711-STATUS.json`.
- Requirements: 13. Tasks: 20. Decisions: 10. Human decisions: 0.

## 8. Convergence after implementation

After T016, the baseline holds 305 entries. Of these, 129 are `weak_zero_assertions` detector-gap entries. The other 176 entries belong to other rules. The analyzer reports zero zero-construct findings. The detector-gap family awaits the upstream fix.

Caution: Changing another rule's entries can hide that rule's findings. Those entries belong to other issues. Leave them unchanged in this work.
