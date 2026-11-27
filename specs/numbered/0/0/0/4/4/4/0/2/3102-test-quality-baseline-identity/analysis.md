# Analysis: Test-quality baseline identity by content

This analysis checks the spec, the plan, the tasks, the contracts, and the remote code against each other. It also records the defects in the issue and in the existing code. Each claim cites a row of `design/research.md`.

## 1. Consistency review

| Check | Expected | Observed | Result |
| - | - | - | - |
| Route | `specs\numbered\0\0\0\4\4\4\0\2` for issue 3102 | Base-5 form of 3102 is `44402`. Padded to eight levels it is `00044402`, which matches the route. | Consistent |
| Spec record path | `specs\numbered\0\0\0\4\4\4\0\2\3102-test-quality-baseline-identity` | Used in the spec header, the plan, the research header, and `STATUS.json`. | Consistent |
| Pin | Pin on main equals the commit that the analysis uses | `requirements-dev.txt` line 197 names `2239e7bd`. Upstream main equals that commit (R-06, R-31). | Consistent |
| Gate command | Same command in CI, documentation, and the guide | The CI step (R-04), the guide line 145, and `quality-gates.md` (R-07) name the same flags. | Consistent |
| Gate output | Lines in the contract match the code | Lines `gate_scope`, `gate_new`, and `gate` exist (R-37, R-42). Lines `gate_removed` and the second prune line are new. | Consistent |
| Remote check count | Table, `remote_checks`, and summary agree | Table has 56 rows (research), 56 entries in `remote_checks`, and the summary states 56. | Consistent |
| Requirement count | 16 functional requirements | Spec lists FR-001 to FR-016. `STATUS.json` lists 16. | Consistent |
| Task count | 21 tasks | Tasks T001 to T017 and four final tasks. `STATUS.json` lists 21. | Consistent |
| Planned tests | 15 new tests | Tasks list 11 upstream and 4 MistHelper tests. `STATUS.json` lists 15. | Consistent |
| Decision count | 15 decisions | Research lists D-1 to D-15. `STATUS.json` lists 15. | Consistent |
| Folder children, spec record | At most five children in each folder | Root holds 5. `design` holds 5. `contracts` holds 2. `checklists` holds 1. | Consistent |
| Folder children, MistHelper | No new file in `tests/guardrails/local_test_quality_loop` | The folder holds five children (R-15). The plan adds the class to `test_scope.py`. | Consistent |
| Folder children, upstream | No new module in the package root | The root holds 12 children (R-55). The plan adds no module. | Consistent |
| Migration floor | At least 46 dropped entries | 12 entries name a missing file (R-24). 34 entries name a blank line (R-21, R-44). | Consistent |

## 2. Defects in the issue and in the existing code

| ID | Source | Claim | Observed | Effect | Handling |
| - | - | - | - | - | - |
| DEF-01 | Issue body | The baseline path is `tools/test_quality_analyzer/baseline.json`. | That path is absent (R-25). The baseline is `.github/test-quality-baseline.json` (R-01). | The issue cites a wrong path. | The spec uses R-01. |
| DEF-02 | Issue body | The baseline holds 1,097 entries. | Main holds 733 entries (R-01). The base of pull request 4358 also holds 733. | The migration count in the issue is wrong. | The migration counts from main. |
| DEF-03 | Issue body | Six example rows name baseline lines 631, 1310, 506, 520, 153, and 122. | No explanation names `test_write_function_handles_empty`. Line 153 is blank (R-21). Line 631 names another test (R-23). | The example rows are stale. | D-15 uses a live report file. |
| DEF-04 | Issue body | Most findings name the test function in their explanation. | 557 of 733 entries do (76 percent). 176 entries do not. | The statement is true only for most entries. | D-2 uses a content anchor. |
| DEF-05 | Issue body | The key `(rule_id, file_path, test_function_name)` survives a line move. | The test name is missing for 176 entries. | The proposed key cannot be built from the record. | D-2 rejects the key. |
| DEF-06 | Issue body | The contributor guide forbids regenerating the baseline on a feature branch. | The guide forbids a rewrite that hides a new finding (R-10). It names no feature-branch rule. | The claim is unsupported. | The migration rule in the spec relies on R-10 only. |
| DEF-07 | Issue acceptance 3 | `--prune-baseline` still drops the stale entry. | The pinned prune drops only entries of unscanned files (R-35, R-36). Removed findings in scanned files remain. | Acceptance 3 is unmet by the pinned code. | D-6 and FR-005. |
| DEF-08 | Pinned analyzer | The prune rule keeps entries for files it scans. | Parse-error files are missing from the scanned set (R-39, R-40). The prune drops their entries. | Accepted entries are lost after a syntax error. | D-6 and FR-006. |
| DEF-09 | Pinned analyzer | The diff compares findings by dictionary and set (R-33, R-34). | Identical keys collapse to one. | A second identical finding passes. | D-4 and FR-002. |
| DEF-10 | Issue comment, 2026-10-20 | Pull request 4358 is an open draft and reserves the baseline file. | Pull request 4358 merged on 2026-11-13. | The reservation no longer applies. | The spec does not depend on the reservation. |
| DEF-11 | Issue comments, 2026-10-19 and 2026-10-20 | The pin is v0.6.3 at `e8e093d`. | The pin is `2239e7bd`, which is five commits after v0.6.4 (R-06 and the compare API). | The comment names a stale pin. | The plan uses R-06. |
| DEF-12 | Issue body | Pull request 3090 carries the register repair. | Its script and test are absent on main (R-28, R-29). | The precedent code cannot be read on main. | The plan uses the issue text as the precedent. |
| DEF-13 | Baseline on main | Entries record their findings. | 34 entries name blank lines, and 12 name a missing file (R-21, R-24). | At least 46 entries cannot match any finding. | D-8 drops them through the migration. |
| DEF-14 | Multiset comparison | A stale occurrence keeps one unit of count. | One later identical finding then passes with no review. | A hidden new finding. | FR-005, D-6, and the prune in T005. |
| DEF-15 | Untested finding | The finding names the analyzed module. | The `file_path` is the source module (R-46). | An anchor for this finding reads a source file outside the test set. | T004 reads the source module. |
| DEF-16 | Existing upstream tests | The differ test builds keys from line numbers. | `test_baseline_differ.py` line 62 uses `line_number` in the key (R-47). | The existing tests encode the defect. | T003 and T007 update them. |
| DEF-17 | Issue acceptance 4 | The gate must report counts and must not pass after reading nothing. | `gate_scope` exists (R-37, R-38). The empty scope prints zeros (R-51). | Part of acceptance 4 is present. | FR-008 and SC-005 keep the output. |
| DEF-18 | Issue table | Every row drifted by exactly one line. | The CI log of pull request 3101 was not read. | The claim is unverified. | Unverified item 1 in the research. |
| DEF-19 | Pull request 4358 | Pull request 4358 changed 586 baseline lines. | The change moved 293 entries to other file paths. Each entry kept its line number. | File moves change the identity, so they cause drift. | Plan risk: file moves. Issue 4142 coordinates the work. |

## 3. Requirement coverage

Each functional requirement maps to at least one task and one test. FR-012 uses a manual migration proof, because the proof compares two baseline files. The proof is quickstart Step 7.

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T001, T003, T004 | `test_line_number_shift_is_not_new` (T003) and `test_blank_line_above_finding_keeps_gate_green` (T015) |
| FR-002 | T003 | `test_second_identical_occurrence_is_new` (T003) |
| FR-003 | T001, T004, T007 | `test_changed_flagged_line_is_new` (T004) and `test_three_configurations_isolate_the_identity_change` (T007) |
| FR-004 | T003 | `test_removed_occurrence_is_not_new` (T003) |
| FR-005 | T005 | `test_prune_removes_unmatched_occurrences_in_analyzed_files` (T005) |
| FR-006 | T005 | `test_prune_keeps_entries_of_parse_error_files` (T005) |
| FR-007 | T006 | `test_missing_content_anchor_exits_two` (T006) |
| FR-008 | T011 | `test_full_gate_reports_scope_counts` (T015) |
| FR-009 | T005 | `test_gate_prints_removed_count_for_analyzed_files` (T005) |
| FR-010 | T002 | `test_file_level_finding_carries_sentinel` (T002) |
| FR-011 | T014 | `test_baseline_entries_carry_content_anchors` (T015) and a manual migration proof |
| FR-012 | T014, T-PR | Manual migration proof in quickstart Step 7 |
| FR-013 | T015, T-LOCAL-GATES | `test_added_weak_assertion_fails_gate` (T015) and `test_blank_line_above_finding_keeps_gate_green` (T015) |
| FR-014 | T008, T009, T013, T-MERGE | Full-suite gate on main after the merge (T-MERGE) |
| FR-015 | T016, T017 | STE gate on the changed documents (T016, T017) |
| FR-016 | T010, T-LOCAL-GATES, T-REMOTE-CI | `test_guidance.py::TestLiveGuides` preflight |

Edge cases with a test: duplicates (T003), file-level headers (T002), changed lines (T004), missing anchors (T006), unreadable sources (T004), and parse errors (T005). The edge case of a changed-scope pull request with no test file has no new test. Decision D-10 keeps the existing behavior.

## 4. Detector inventory for the anchor

The anchor needs a flagged line for each finding. The table lists the detectors that this record inspected.

| Detector | Rule group | Line source | Anchor rule | Evidence |
| - | - | - | - | - |
| `weak_assertion.py` | `weak_is_not_none` | `sub.lineno` at line 207 | Digest of the flagged line | R-54 |
| `weak_assertion.py` | `weak_zero_assertions` | `func.lineno` at line 248 | Digest of the `def` line | R-44 |
| `missing_failure_mode.py` | `missing_fm_*` | Line 1 from the `_finding` helper at line 760 | Sentinel `file-level` | R-45 |
| `untested.py` | `untested_public_function` | Node line and file path at line 151 | Digest of a line in the source module | R-46 |

The detectors `tautological.py` and `missing_edge_case.py` were not read in this record. Task T002 checks them before the change lands. Unverified item 8 in the research lists them.

## 5. Unresolved items

| ID | Item | Owner | Task |
| - | - | - | - |
| U-1 | The upstream issue, release, and pin do not exist yet. | Owner | T001 to T009 |
| U-2 | The number of live findings and stale entries needs an analyzer run. | Implementer | T014 |
| U-3 | `tautological.py` and `missing_edge_case.py` need a line check. | Implementer | T002 |
| U-4 | Issue 4142 may move files before this change merges. | Owner | Plan risk table |
| U-5 | The CI log of pull request 3101 was not read. | Owner | None. The claim is historical. |
| U-6 | The origin of the 1,097 count is unknown. | Owner | None. The migration uses main. |

## 6. Self-review results

- Requirement mapping: all 16 requirements map to at least one task and one test or manual check (section 3).
- Verification commands: each task names one command. Upstream tasks use the Tests pattern. MistHelper tasks use the Test quality, Tests, and STE rows.
- Forbidden tokens: the final scan found no semicolon, ellipsis, contraction, Latin abbreviation, unfinished marker, or human decision marker in the record.
- Folder children: the record root holds 5 children, `design` holds 5, `contracts` holds 2, and `checklists` holds 1.
- Sentence length: the final scan found no sentence above 25 words.
- Remote checks: the research table, `remote_checks`, and the summary each state 56.
- Fixes made during review: 13 semicolons, 7 sentences above 25 words, and about a dozen line citations without a matching research row were corrected.

