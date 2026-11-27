# Specification Analysis Report: Split the Juniper RMA and export packages

## Findings

| ID | Category | Severity | Location | Finding | Recommendation |
| - | - | - | - | - | - |
| A-1 | Defect in existing work | High | `specs/numbered/0/0/1/1/3/1/3/3/4168-org-auto-upgrade-policy/plan.md`, line 5 (remote blob `5b45f62c9eee1591967d3d7d936a54643c40a8a2`) | The folder uses number 4168 for issue #4217, and pull request #4219 merged it under this route. Issue #4217 maps to route `0/0/1/1/3/3/3/2` (base 5: 1x5^5 + 1x5^4 + 3x5^3 + 3x5^2 + 3x5^1 + 2 = 4217). | Open a new issue to renumber the folder to route `0/0/1/1/3/3/3/2`. This change does not edit the folder. |
| A-2 | Stale state | Medium | GitHub issue #4168, comment created 2026-11-08T23:42:18Z | The comment says pull request #4607 blocks `MistHelper.py`. Pull request #4607 merged at 2026-11-13T07:14:03Z. No open pull request names `MistHelper.py` at query time. | A maintainer posts an updated comment. This change posts nothing on GitHub. |
| A-3 | Stale measurement | Low | GitHub issue #4168 body, measured 2026-10-10 | The body reports 243 total excess and 36 violations. Remote `main` reports 236 total excess and 33 violations. The child counts 48, 6, and 7 match. | Use the remote measure in `design/research.md`. |
| A-4 | Shared file ownership | High | Open pull request #4813 | It changes `src/operations/exporting/export/data_exporter.py`, `tests/unit/export/test_data_exporter.py`, and `tests/unit/export/test_endpoint_family_exporter.py`. This change edits only the last of these test files. | Wait for the merge (`T001`). Keep `data_exporter.py` in place (D-2). |
| A-5 | Shared file ownership | Low | Open pull request #4208 | It changes `tests/guardrails/test_src_public_symbol_preservation.py`. This change does not edit that file. | No action. |
| A-6 | Stale and absent legacy citations | Medium | Legacy folder `4168-org-auto-upgrade-policy` | Of 30 cited paths, 1 is stale and 2 are absent. The details appear in `design/research.md`, section Legacy record verification. | Record the counts in `META_DIR\4168-STATUS.json`. Do not reuse the folder (D-16). |
| A-7 | Conflicting version pins | Low | `.specify/memory/constitution.md` (Technology section) and `.github/copilot-instructions.md` | The constitution states mistapi 0.59 or later. The repository file pins `mistapi>=0.64.0,<0.65`. | Out of scope. Record it in a separate issue. |
| A-8 | Unverified tool behavior | Medium | `pyproject.toml` line 449 and mypy | The wildcard should cover nested packages. No mypy run has verified it. | `T-LOCAL-GATES` runs mypy (U-2 in `design/research.md`). |
| A-9 | Local working tree differences | Low | Local `git status` (five modified files) | Five modified files exist outside this change. | Do not stage them. Use remote blobs for each claim. |
| A-10 | Review size | High | Change scope | The change edits 194 existing files, adds 17 package files, and moves 59 modules in one pull request. | Run each guard after each phase in `tasks.md`. Use phase commits. Keep one pull request (D-11). |
| A-11 | Documentation drift | Medium | `documentation/api/` (46 files) | These files name old export module paths. | Update each file in `T020`. |
| A-12 | Shared test files | Medium | Issue #4142 | Its scope moves Juniper RMA test folders. This change edits imports in those folders. | Rebase after #4142 merges, or merge this change first and rebase #4142 (D-15). |
| A-13 | Stale issue measurement | Low | GitHub issue #4168 comment, 2026-11-06 | The comment reports 181 directories examined. The measure on remote `main` gives 190. | Use the measure in `design/research.md`. |

## Coverage Summary

| Requirement | Tasks | Verification |
| - | - | - |
| FR-001 | T000, T017, T024 | Guard run in `design/quickstart.md`, steps 1 and 2 |
| FR-002 | T002 to T007, T024 | Guard run |
| FR-003 | T023 | Old-path search excludes `data_exporter.py` |
| FR-004 | T003 to T005, T025 | Import smoke in `design/quickstart.md`, step 5 |
| FR-005 | T006, T025 | Import smoke |
| FR-006 | T007, T025 | Import smoke |
| FR-007 | T018, T023 | Old-path search and the new test in `tests/guardrails/test_nested_package_structure.py` |
| FR-008 | T008 to T016, T019 to T021, T023 | Old-path search |
| FR-009 | T008 to T013, T-LOCAL-GATES | `symbol-diff` in `design/quickstart.md`, step 7 |
| FR-010 | T-LOCAL-GATES | `tests/guardrails/test_move_module_guidance.py` |
| FR-011 | T014 to T016 | `git status` shows no move under `tests/unit/` |
| FR-012 | T023 | Old-path search exclusions in `design/quickstart.md`, step 3 |
| FR-013 | T022, T-PR | Changelog naming rule |
| FR-014 | T001, T-MERGE | `gh pr view 4813` |
| FR-015 | T018, T024 | Guard run |
| FR-016 | T018 | `tests/guardrails/test_nested_package_structure.py` |
| FR-017 | T023 | Logger search in `design/quickstart.md`, step 4, and the plan section Logger and class module changes |
| FR-018 | T-LOCAL-GATES, T-REMOTE-CI | Safe sweep and remote checks |

Each requirement maps to at least one task. No requirement lacks a task.

## Constitution Alignment

- Rule I (Five-Item Rule): pass. Each new directory holds five children or fewer. The guard covers this.
- Rule II (Class-Based Architecture): pass. The change moves classes and adds no wrapper (D-7).
- Rule V (Observability): pass with change. Logger names change, and the plan records each change.
- Rule VI (Inline Comments): pass with a condition. Each changed import line keeps its comment. A reviewer checks each changed line.
- Rule VII (Action Logging): pass. The change adds no action.
- Move a module table: pass. The table stays unchanged (FR-010).
- No compatibility shim: pass. Old paths have no alias (D-7).

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Metrics

| Metric | Value |
| - | - |
| Requirements | 18 |
| Success criteria | 7 |
| Tasks | 30 (26 implementation and verification tasks, 4 final gate tasks) |
| Decisions | 17 |
| Remote checks | 26 |
| Moved modules | 59 |
| New package markers | 16 |
| Moved package markers | 1 |
| Existing files modified | 194 (187 from the old-path search, 7 manual) |
| Test files modified | 91 |
| New tests planned | 2 |

## Convergence After Implementation

- SC-001 (guard counts) is measured by `T024`.
- SC-003 (old-path search) is measured by `T023`.
- SC-006 (generated references) is measured by `T021`.
- Each item listed under Unverified in `design/research.md` is closed by its named task.
