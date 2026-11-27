# Specification Analysis Report: Metrics Gateway Core Modules

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, the `design/` folder, the legacy record in commit `033553b3`, the candidate archive branch, and `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only pass compared the legacy record, the candidate diff, the local working tree, and the remote tree. The pass recounted the nested package totals from the tracked files. No build, test, or repository script ran.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
| - | - | - | - | - | - |
| A1 | Defect | HIGH | Legacy `tasks.md`, tasks T001 to T006 | The legacy tasks carry the `[X]` mark. Main holds none of their artifacts. | Fixed. Each task in `tasks.md` carries its real status. |
| A2 | Defect | HIGH | Candidate `033553b3`, test paths | The candidate edits `tests/unit/metrics_gateway/` and `tests/unit/mib_generator/`. Both paths are absent on main. | Fixed. The spec uses the current paths. Decision D-1 forbids replay. |
| A3 | Defect | HIGH | Candidate `033553b3`, hook catalog | The candidate omits the eight hook rows. The hook guard then reports unresolved rows. | Fixed. Task T018 updates the rows. |
| A4 | Defect | HIGH | Candidate `033553b3`, nested guard | The candidate omits the baseline entry and the totals. The nested guard reports a stale entry. | Fixed. Task T013 removes the entry and sets 32 and 233. |
| A5 | Conflict | HIGH | Open PR #4208 | PR #4208 changes the symbol guard file, which the candidate also changes. | Accepted with a gate. Task T012 waits for task T002. FR-020 blocks publication. |
| A6 | Defect | MEDIUM | Legacy `plan.md`, Technical Context | The legacy plan names Python 3.13. `pyproject.toml` line 23 requires 3.15. | Fixed. The plan names Python 3.15.2. |
| A7 | Defect | MEDIUM | Legacy `plan.md`, menu check | The legacy plan runs `python -m scripts.menu_api_map` without `--check`. CI runs the `--check` form. | Fixed. Task T016 and the quickstart use the CI form. |
| A8 | Coverage | MEDIUM | Legacy `spec.md` | The legacy spec does not record the logger-name change. The repository rules require that record. | Fixed. FR-007 and the module-path contract record the change. |
| A9 | Coverage | MEDIUM | Legacy record | No legacy requirement maps to a test or a command. | Fixed. Each task names one verification command. |
| A10 | Underspecification | MEDIUM | Hook guard | The hook guard reads tracked files only. An unstaged core file leaves rows unresolved. | Fixed. The edge cases and task T018 require staging first. |
| A11 | Risk | MEDIUM | Test-quality baseline | The baseline stores line numbers. The guard file gains lines, so a finding can shift. | Accepted with a gate. The risk table names the mitigation. |
| A12 | Constitution | MEDIUM | Principle VI | The candidate's changed import lines carry no inline comment. | Fixed. FR-022 and task T006 require the comments. |
| A13 | Constitution | LOW | Principle VII | Import-only edits add no action logging. The constitution asks for logging in touched blocks. | Accepted. Decision D-16 records the reason. A reviewer can request more logging. |
| A14 | Ambiguity | LOW | Issue term "public symbol map" | No file has that name. | Fixed. The clarification and decision D-15 map the term to `MODULE_PATHS`. |
| A15 | Inconsistency | LOW | Issue comment of 2026-10-06 | The comment says the candidate is not pushed. The archive branch holds the candidate commit. | Accepted. FR-021 keeps the archive branch unchanged. |
| A16 | Inconsistency | LOW | Folder `specs/2448-misthelper-performance-monitoring` | The folder name uses issue 2448. Issue 2448 is closed, and its title is unrelated. | Accepted. The folder is historical evidence, not an issue link. |
| A17 | Drift | LOW | `documentation/architecture.md` line 227 | The package tree does not show the current layout. The drift predates this change. | Out of scope. The spec names the need for a separate issue. |
| A18 | Defect | LOW | Candidate `core/__init__.py` | The candidate docstring names the content but not the reason. | Fixed. Task T005 requires the reason. |
| A19 | Environment | LOW | Local working tree | Five unrelated files are modified. They include `logger_utils.py` and two test files. | Fixed. Task T003 uses a fresh worktree. Task T-PR stages explicit paths. |
| A20 | Dependency | LOW | MIB regeneration inputs | The MIB regeneration needs three tracked inputs. | Verified. Rows C48 to C50 confirm that the three inputs are tracked on main. |

## Coverage Summary

| Requirement | Has task | Task IDs | Test or command |
| - | - | - | - |
| FR-001 | Yes | T004 | Import smoke on `core.catalog` |
| FR-002 | Yes | T006 | Import smoke on the gateway root |
| FR-003 | Yes | T005 | Import smoke on `core` |
| FR-004 | Yes | T006, T017 | Old-path search |
| FR-005 | Yes | T006, T007, T008, T009, T010 | Targeted unit and contract tests |
| FR-006 | Yes | T006 | Import smoke |
| FR-007 | Yes | T009 | Targeted unit tests |
| FR-008 | Yes | T007, T015 | `--mib-check` and the contract test |
| FR-009 | Yes | T014, T017 | STE gate and old-path search |
| FR-010 | Yes | T016 | Menu drift check |
| FR-011 | Yes | T018 | Hook guard |
| FR-012 | Yes | T019 | Guardrails run |
| FR-013 | Yes | T012 | Symbol guard |
| FR-014 | Yes | T011 | Structure guard |
| FR-015 | Yes | T013 | Nested guard |
| FR-016 | Yes | T-LOCAL-GATES | Changed-file list |
| FR-017 | Yes | T001, T-LOCAL-GATES | Symbol guard and targeted tests |
| FR-018 | Yes | T020 | Changelog policy test |
| FR-019 | Yes | T021 | STE gate on the record |
| FR-020 | Yes | T002, T003, T-PR, T-REMOTE-CI, T-MERGE | Overlap check and coordinator approval |
| FR-021 | Yes | T-PR, T-MERGE | Archive branch check |
| FR-022 | Yes | T005, T006, T007, T011, T012 | Review of changed lines |
| SC-001 | Yes | T006, T011 | Structure guard |
| SC-002 | Yes | T005, T011 | Structure guard |
| SC-003 | Yes | T-LOCAL-GATES | Targeted tests |
| SC-004 | Yes | T012 | Symbol guard |
| SC-005 | Yes | T016 | Menu drift check |
| SC-006 | Yes | T017, T-PR | Old-path search |
| SC-007 | Yes | T015 | `--mib-check` |
| SC-008 | Yes | T013 | Nested guard |

## Constitution Alignment

Principles I, II, III, IV, and V pass after the tasks run. Principle VI passes when task T006 adds the comments. Principle VII passes with the reason in finding A13. The Mist, container, and data rules are not applicable, as the plan records.

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Defects in Existing Work

- The legacy record has five defects: A1, A6, A7, A8, and A9.
- The candidate commit has four defects that block publication: A2, A3, A4, and A5.
- The candidate commit has two lower-severity defects: A12 and A18.
- This change does not reuse the legacy record's text. It reuses only the section layout.

## Convergence After Implementation

- The gateway root holds five structural children, and the core package holds four.
- The nested guard reports 191 directories, 32 violations, and 233 total excess.
- The hook guard resolves each of the eight rows at a core path, and the hook summary stays valid.
- The symbol guard reports no lost name for the four moved modules.
- The two menu pages link `core/collector.py`, and the drift check passes.
- The old-path search prints no line.
- `python MistHelper.py --mib-check` exits with status 0.

## Metrics

| Metric | Value |
| - | - |
| Requirements | 22 |
| Tasks | 25 |
| Remote checks | 66 |
| Legacy claims | 12 |
| Legacy claims verified, stale, and absent | 3, 3, and 6 |
| Decisions | 17 |
| Human decisions | 0 |
| Targeted test modules | 13 |
| Findings | 20 |

## Unresolved Items

- U-1: PR #4208 must release the symbol guard file. The coordinator owns that timing. It blocks task T012 and task T-PR.
- U-2: The full Windows test run takes about 20 minutes. The last recorded unit shard took 1179.3 seconds. Plan the time before the push.
- U-3: The test-quality analyzer result for the edited guard file is not measured in this phase. Task T-LOCAL-GATES measures it.
- U-4: The `symbol-diff` behavior for renamed files is not measured in this phase. The symbol guard test covers renamed files.
