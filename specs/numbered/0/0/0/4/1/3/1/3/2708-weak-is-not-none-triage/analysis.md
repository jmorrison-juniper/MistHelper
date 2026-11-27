# Specification Analysis Report: Test quality: triage weak_is_not_none findings

This report checks the spec, the plan, the tasks, and the remote code against each other. It lists each defect in existing work and each unresolved item.

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-1 | High | The issue acceptance command `python -m tools.test_quality_analyzer` has no target. | Main has no `tools/` folder. The root listing and the tree of 11,404 entries show none. The documented command is `test-quality-analyzer --gate` (`.github/copilot-instructions.md` line 95 and `.github/workflows/ci.yml` line 632). | Decision D-8. The record uses the documented command. |
| A-2 | High | The config key does not match the emitted rule ID. | `.github/test-quality-config.toml` line 21 sets `weak_assert_not_none`. The emitted rule ID is `weak_is_not_none` (`weak_assertion.py` line 310, installed). The installed `config.py` line 31 lists the config key. | Decision D-4 and task T018. The effect on the gate is unverified. |
| A-3 | Medium | 19 of 84 baseline entries are stale on main. | The per-line check on main finds no weak guard at these lines (research rows 52 to 135). | Tasks T002 and T017. |
| A-4 | Medium | Seven candidate blobs and one candidate commit are absent from GitHub. | Research rows 36 and 43 to 49. | Decision D-6. Each repair is derived again from main. |
| A-5 | Medium | Local commit `fd7896f` repeats a repair that main already has. | Pull request #3783 merged on 2026-10-04 and changed `mist-ops-platform/tests/unit/mist/test_api_result.py`. Recovery branch `recovery/2708-handoff-20261004` holds only that file. | Drop the candidate. Line 59 is stale (F-10). |
| A-6 | Medium | A comment says pull request #4358 renames `test_ui_geocoder_profile_cleanup.py`. | Comment dated 2026-11-10T05:17:03Z. Pull request #4358 changed 410 files and does not include that file. The destination path is absent on main. | The file keeps its original path. Task T010 edits it. |
| A-7 | Low | A comment says pull request #4385 holds the serial publication slot. | Pull request #4385 merged on 2026-10-21T03:53:43Z. | Decision D-10 sets the slice order in this record. |
| A-8 | High | A merged pull request closed issue #2708 automatically. | Comment dated 2026-10-22T12:16:17Z from `github-actions`. The issue reopened later, and its state is open. | Decision D-9. Each slice closes its own child issue. |
| A-9 | Medium | A local commit has no issue reference. | Comment dated 2026-11-10T02:55:18Z says commit `8e67300160731232298e307d29531bf3e0c4e28f` has no issue-reference trailer. | Requirement FR-009. |
| A-10 | Medium | The hook directory resolves inside the main checkout. | Comment dated 2026-11-11T03:48:37Z. | Risk R-7 in `plan.md`. Task T-PR forbids bypassing hooks. |
| A-11 | Low | The installed analyzer commit is unverified. | `requirements-dev.txt` line 197 pins commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. The installed `misthelper_devtools_0.6.4.dist-info` folder has no `direct_url.json`. | Unverified list in `design/research.md`. |
| A-12 | Medium | The constitution and the changelog README conflict. | Constitution line 409 requires one fragment for each change. `changelog.d/README.md` line 58 exempts internal-only changes. | Decision D-12. A maintainer reviews the conflict. |
| A-13 | Medium | The comments give three different counts. | Comments report 369 (2026-09-18), 79 (2026-10-01), and 67 (2026-11-10). The untracked local report from 2026-11-10 holds 67. The remote tree shows no tracked report. | Decision D-1. |
| A-14 | Medium | The 2026-11-10 report uses paths that moved. | 13 report entries name paths that are absent on main (research rows 52 to 135 use the moved paths). | Decision D-1 uses the baseline paths on main. |
| A-15 | High | The gate identity uses the line number. | Installed `baseline.py` lines 5 to 6 and 48 to 55 define the five-field identity. | Requirement FR-003, decision D-2, and risk R-1. |
| A-16 | Low | The compose test skips without services. | Local view of `tests/integration/test_compose_deploy.py` lines 16 and 23. Line 36 matches the remote check (research row 81). | Decision D-14 and task T015. |
| A-17 | Low | Comments cite Mac session paths. | Comments cite `/Users/jmorrison/.copilot/session-state/` paths. Those paths do not exist in this environment. | This record does not reuse them. |
| A-18 | High | The constitution requires a closing reference in each pull request. | Constitution line 519 (research row 136). A `Part of` reference alone breaks that rule. | Decision D-9. Each slice closes its child issue. |
| A-19 | Medium | The constitution names Principles VI and VII as review gates. | Constitution line 553 (research row 137). | Principle VII covers production actions, and assertion edits perform none. The maintainer confirms that reading. |

## Coverage Summary

| Requirement | Tasks | Evidence |
| - | - | - |
| FR-001 Classify each entry | T001, T002, T003 to T010, T011 to T014, T015, T016 | Research rows 52 to 135 |
| FR-002 Exact check on the same line | T003 to T010 | Acceptance statements |
| FR-003 Keep the line count | T003 to T010, T017 | Decision D-2 and risk R-1 |
| FR-004 Controlled failing run | T003 to T010, T-PR | Pull request body rule |
| FR-005 No scope reduction | T018, T-LOCAL-GATES | Decision D-4 |
| FR-006 Stale entries leave after confirmation | T002, T017 | Analyzer report |
| FR-007 Documented baseline command | T017 | Decision D-7 |
| FR-008 Holds | T011 to T014 | Decision D-5 |
| FR-009 Closing keywords | T-PR | Decision D-9 |
| FR-010 Inline comments and ASCII messages | T003 to T010 | Constitution line 204 |
| FR-011 Local gates | T-LOCAL-GATES | Decision D-13 |
| FR-012 Serial merges | T-REMOTE-CI, T-MERGE | Decision D-10 |
| FR-013 GitHub evidence | T-PR, research rows 35 to 51 | Remote checks |

Each task maps to at least one requirement. No task lacks a requirement.

## Constitution Alignment

- Principle I (five-item rule): Pass. The record folder holds five children at the feature root and four children under `design/`.
- Principle IV (deployment pipeline): Pass with an exception. Steps 10 to 12 do not apply (decision D-11).
- Principle VI (inline comments): Pass by requirement FR-010.
- Principle VII (action logging): Not applicable. No production action changes.
- Release notes: Conflict. Decision D-12 records the choice and the conflict.

## Metrics

| Measure | Value |
| - | - |
| Baseline entries for `weak_is_not_none` on main | 84 |
| Present weak guards on main | 65 |
| Stale entries on main | 19 |
| Present, redundant guard (S) | 35 |
| Present, archived or local candidate (RC) | 12 |
| Present, confirmed gap without candidate (R) | 5 |
| Present, held by an owner (H) | 11 |
| Present, unclassified (U) | 2 |
| Slices | 8 |
| Holds | 4 |
| Tasks | 22 |
| Remote checks | 139 |
| Decisions | 16 |
| Human decisions | 1 |

The counts add up. Present categories total 65 (35 + 12 + 5 + 11 + 2). Present plus stale total 84.

## Unmapped Tasks

None. Each task maps to at least one requirement in the coverage table.

## Unresolved Items

1. The analyzer count on main is unverified. Task T001 decides it.
2. The config key mismatch (A-2) changes no gate result until task T018 and an upstream fix.
3. Eleven stale entries have no attributed merged pull request. Task T002 decides them.
4. The compose test (T015) and the WAN launcher test (T016) need a decision after the analyzer run.
5. The credential session hold (T014) needs the human decision in D-16.
6. The changelog conflict (A-12) needs maintainer review.
7. The reading of Principle VII for assertion-only edits (A-19) needs maintainer confirmation.
