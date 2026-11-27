# Specification Analysis Report: Refactor: isolate audit renderer modules

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/contracts/`, and the repository state of `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Method**: A read-only pass compared the spec, plan, and tasks with the remote tree. It read each cited file through GitHub. It compared each legacy claim with the current `main`. It searched the audit modules for logger use and for `__module__` use. Each finding has a resolution. Each unresolved item names its owner.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| F-01 | Stale premise | HIGH | Issue #4011 body | The issue describes the flat layout with ten children. `main` holds the 3824 layout since PR #4552. | The target is refreshed against `main` (D-1). |
| F-02 | Stale base | HIGH | Commit `5b665c48` | The local commit is 401 commits behind `main`. Its paths predate the 3824 layout. | The change is rebuilt from `main`. The commit is not cherry-picked (D-9, D-10). |
| F-03 | Unmet criteria | MEDIUM | Issue acceptance criteria 4 and 5 | The rendering package holds five children, not two. The helpers package is absent. | The change builds the issue layout (D-1). |
| F-04 | Unneeded edit | MEDIUM | Issue implementation notes | Four consumers already import the canonical renderer path (rows RC-14, RC-16, RC-17, RC-23). | No edit is made. The consumer test still runs (D-5, TS-12). |
| F-05 | Stale mapping | MEDIUM | Symbol guard lines 82 to 87 | The six rows map flat paths that no baseline path matches (row RC-25). | Six rows are replaced with baseline keys (D-2). |
| F-06 | Different method | MEDIUM | Local commit and `main` | The local commit used a six-path map in the hook guard. `main` uses CSV rows and expected rows (row RC-27). | The `main` method is used (D-3). |
| F-07 | Open overlap | MEDIUM | PR #4208 (open) | The open pull request changes the symbol guard file (row RC-25). | The rebase resolves only the `MODULE_PATHS` block. The rerun is task T-PR. |
| F-08 | Historical conflict | MEDIUM | #3824 contract (row RC-40) | The historical contract names the `clusters` layout. | The historical record is not edited (FR-015). This record supersedes the audit layout. |
| F-09 | Stale path | LOW | Legacy tests | The legacy record names `tests/unit/audit/`. That folder is absent (row RC-24). | The current folder `tests/unit/marvis/mist/access/audit/` is used (row RC-19). |
| F-10 | Stale version | LOW | Legacy spec | The legacy record names Python 3.13. The repository requires 3.15 (row RC-57). | Python 3.15 is used. |
| F-11 | Record layout | LOW | Legacy spec FR-012 | The legacy record allows three routed files. The brief layout needs more files. | The brief layout is used (D-9). |
| F-12 | Stale comment | LOW | `renderer.py` line 42 | The comment says "relative import" for an absolute import (row RC-02). | The comment is corrected in the touched block (T011). |
| F-13 | Rule conflict | LOW | Repository instructions line 451 and constitution line 409 | The instructions limit fragments to user-visible changes. The constitution requires one fragment for each change (rows RC-56 and RC-58). | The fragment is added (D-8). Both rules hold. |
| F-14 | Label mismatch | LOW | Repository instructions line 439 | The issue label `src` is not in the scope set. The scope set names six labels, and `src` is not one of them. | The `src` label stays. `in-progress` is added at the start of work. The owner receives this mismatch (unresolved item U-C). |
| F-15 | Gate false positive | LOW | Old-path search | A search for retired paths finds guard keys, the retired-import list, and historical records. | The allowlist is in `design/contracts/structure-guard.md` and `design/checklists/gates.md`. |
| F-16 | Pre-existing item | INFO | `audit_analysis_ops.py` line 55 (row RC-15) | The call forwards `**api_kwargs` into a `mistapi` function. The SDK-compatibility gate may flag it. | Out of scope. A separate issue is opened only if the gate fails. |
| F-17 | Shared worktree | INFO | Main checkout (five modified files) | Five unrelated files are modified in the shared checkout. | The change uses a worktree and stages explicit paths only (T002, T027). |
| F-18 | Count mismatch | LOW | Issue implementation notes | The issue says "six exact old-to-new paths". Five modules move, and the renderer does not move. | Six rows are kept. The renderer row maps to itself (D-2). |

## Coverage summary

Each requirement maps to at least one task and at least one test or check. A check is a command or review in `design/checklists/gates.md`. For this coverage rule, a check counts as a test.

| Requirement | Tasks | Tests and checks |
|-------------|-------|------------------|
| FR-001 | T001, T023 | TS-01 |
| FR-002 | T004 to T010, T023 | TS-01 |
| FR-003 | T004 to T009, T022 | TS-01, TS-03, TS-06 |
| FR-004 | T010 | TS-01, C-03 |
| FR-005 | T011 | TS-06, TS-11 |
| FR-006 | T011 to T017 | TS-02, TS-05, C-02, C-03 |
| FR-007 | T010, T011 | TS-02, TS-07, C-03 |
| FR-008 | T018 | TS-09 |
| FR-009 | T019 to T021 | TS-08, TS-15 |
| FR-010 | T022 | TS-06, TS-07 |
| FR-011 | T023, T024 | TS-01, TS-03, TS-04, TS-05, TS-13 |
| FR-012 | T018, T028 | TS-09, C-04 |
| FR-013 | T026 | TS-11, C-09 |
| FR-014 | T025 | TS-14, C-07 |
| FR-015 | T021, T027 | TS-15, C-01 |
| FR-016 | T027 | C-01 |
| FR-017 | T017 | TS-12 |
| FR-018 | T003, T028 | TS-10 |
| FR-019 | T009, T011 to T013, T023 | C-05 |
| FR-020 | T002, T-PR, T-REMOTE-CI, T-MERGE | C-08 |
| FR-021 | T026 | C-06, C-07 |

## Test catalog

The pytest identifiers below cover the new and changed tests. The existing tests keep their names.

| ID | Test | Status | Covers |
|----|------|--------|--------|
| TS-01 | `tests/guardrails/test_audit_rendering_structure.py::test_audit_levels_hold_the_exact_child_counts` | New | FR-001 to FR-004, SC-001 |
| TS-02 | `tests/guardrails/test_audit_rendering_structure.py::test_retired_renderer_paths_are_absent_from_active_files` | New | FR-006, FR-007, SC-002 |
| TS-03 | `tests/guardrails/test_audit_rendering_structure.py::test_over_limit_helpers_package_fails` | New failure proof | FR-003, FR-011 |
| TS-04 | `tests/guardrails/test_audit_rendering_structure.py::test_unreadable_audit_root_fails` | New failure proof | FR-011 |
| TS-05 | `tests/guardrails/test_audit_rendering_structure.py::test_active_retired_path_fails` | New failure proof | FR-006, FR-011 |
| TS-06 | `tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py::test_new_renderer_module_imports` | Changed list | FR-003, FR-005, FR-010 |
| TS-07 | `tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py::test_legacy_renderer_module_import_fails` | Changed list | FR-007, FR-010 |
| TS-08 | `tests/guardrails/test_performance_hook_catalog.py::TestPerformanceHookCatalog::test_audit_renderer_hook_rows_use_current_paths_and_symbols` | Changed rows | FR-009 |
| TS-09 | `tests/guardrails/test_src_public_symbol_preservation.py::test_moved_modules_lose_no_module_level_symbol` | Existing, changed rows | FR-008, FR-012, SC-005 |
| TS-10 | `tests/test_audit_renderer.py`, `tests/unit/marvis/mist/access/audit/test_renderer_format_wave9.py`, and `tests/unit/marvis/mist/access/audit/test_renderer_time_wave9.py` | Existing, import edits | FR-018, SC-004 |
| TS-11 | `tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py::test_renderer_class_reports_its_canonical_module` | Existing | FR-005, FR-013 |
| TS-12 | `tests/unit/marvis/mist/access/audit/test_audit_analysis_ops.py` | Existing consumer test | FR-017, SC-004 |
| TS-13 | `tests/guardrails/test_nested_package_structure.py::test_nested_package_ratchet_matches_main` | Existing | FR-011, SC-003 |
| TS-14 | `tests/guardrails/test_changelog_fragment_policy.py` | Existing guard | FR-014 |
| TS-15 | `tests/guardrails/test_performance_hook_catalog.py::TestPerformanceHookCatalog::test_inventory_paths_exist_at_the_recorded_source_revision` | Existing | FR-015 |

Counts: New tests are TS-01 to TS-05, which is five. Changed tests are TS-06, TS-07, and TS-08, which is three. The planned test count is eight.

## Check catalog

| ID | Check | Covers |
|----|-------|--------|
| C-01 | `git diff --name-only origin/main` lists only the paths in `plan.md`, section "File change map". | FR-015, FR-016 |
| C-02 | A search for each retired path finds only allowlisted files. The allowlist is in `design/contracts/structure-guard.md`. | FR-006, SC-002 |
| C-03 | An import smoke command imports each canonical module. A second command proves that each retired import fails. | FR-004, FR-006, FR-007 |
| C-04 | `symbol-diff --base origin/main src/mist/access/audit/rendering/renderer.py` prints `no module-level name changed` and exits 0. | FR-012 |
| C-05 | A reviewer reads each changed line and each new file. Each executable line has an inline comment. | FR-019 |
| C-06 | The record folder holds five children at its root, and `design/` holds five children. | FR-021 |
| C-07 | `ste-linter --config .ste-linter.toml --min-score 80` and `markdown-link-check` pass on the new Markdown files. | FR-014, FR-021 |
| C-08 | The coordinator confirms the serial slot in writing before the pull request opens. | FR-020 |
| C-09 | The record `plan.md` and `design/contracts/python-imports.md` state the `__module__` changes and the unchanged logger set. | FR-013 |

## Legacy record review

The local commit `5b665c48` holds a record folder at `specs/numbered/0/0/1/1/2/0/2/1/4011-audit-rendering/`. The folder holds `spec.md` (115 lines), `plan.md`, and `tasks.md`. The working tree and `main` do not hold this folder. The brief requires a review before any reuse. Each claim in the legacy record was checked against `main`.

| ID | Status | Legacy claim | Evidence |
|----|--------|--------------|----------|
| L-01 | verified | The canonical renderer path exists. | RC-01 |
| L-02 | verified | Three consumers import the canonical renderer path. | RC-14, RC-16, RC-17 |
| L-03 | verified | The symbol guard and the hook guard exist. | RC-25, RC-27 |
| L-04 | verified | The legacy commit exists on GitHub. | RC-60 |
| L-05 | stale | The audit root holds ten children. `main` holds five. | RC-08, RC-11 to RC-14 |
| L-06 | stale | `renderer.py` must move out of the audit root. `main` holds it in the rendering package. | RC-01 |
| L-07 | stale | Three consumers need import edits. `main` already uses the canonical imports. | RC-14, RC-16, RC-17 |
| L-08 | stale | The wave tests live under `tests/unit/audit/`. `main` uses the marvis folder. | RC-19, RC-20, RC-24 |
| L-09 | stale | The base is the current `main`. The commit is 401 commits behind `main`. | RC-60 |
| L-10 | stale | The repository requires Python 3.13 or newer. The repository requires 3.15. | RC-57 |
| L-11 | absent | The helpers package exists. It does not exist on `main`. | RC-10 |
| L-12 | absent | The structure guard file exists. It does not exist on `main`. | RC-32 |
| L-13 | absent | The changelog fragment exists. It does not exist on `main`. | RC-36 |
| L-14 | absent | The routed record folder exists. It does not exist on `main`. | RC-38 |

Counts for the STATUS file: verified 4, stale 6, absent 4.

## Searches

- The audit package holds one logger. It is in `audit_analysis_ops.py` line 26 (`logging.getLogger(__name__)`). The moved modules hold no logger, so no logger name changes.
- A search of `src` and `tests` for `__module__` next to the helper symbol names returned no match. No code or test reads the `__module__` of a helper symbol. `AuditReportRenderer.__module__` is checked by TS-11, and its path does not change.

## Consistency review

- The spec holds 21 functional requirements and 6 success criteria. The plan and the tasks use the same identifiers.
- The six symbol rows appear in the spec (FR-008), the plan (file change map), and the tasks (T018). The count is six in each place.
- The seven hook rows appear in the spec (FR-009), the plan, and the tasks (T019 and T020). The count is seven in each place.
- The three failure proofs of the structure guard appear in the spec (FR-011), the plan (test catalog), and the tasks (T023). The count is three in each place.
- The remote verification table in `design/research.md` holds 61 rows. The STATUS file holds 61 `remote_checks` entries. The summary states the same count.
- The task count is 32. The tasks file states the same count.
- The decision count is 11. The research file holds D-1 to D-11. The STATUS file holds the same 11 decisions.

## Unresolved items

- U-A: The coordinator assigns the serial slot. The implementation waits until then. Owner: coordinator.
- U-B: The owner decides whether issue #4011 stays open after this refreshed target lands. The change does not close the issue. Owner: issue owner.
- U-C: The issue label `src` is not in the scope set of the repository instructions. The owner decides whether to change the label set. Owner: repository owner.
- U-D: Pull request #4208 changes the symbol guard file. The coordinator decides the merge order. Owner: coordinator.
- U-E: The results of the local gates and the shard runs. The implementation records them in the pull request body. Owner: implementation agent.
