# Specification Analysis Report: Entry-point test quality for HTTP status scope

## Findings

| ID | Type | Finding | Evidence | Action |
| - | - | - | - | - |
| A-01 | Defect in existing work | The body of pull request 4833 lists two bootstrap modules with baseline findings. Three modules carry them. The third module is `test_fast_mode_small_seams.py`. | RC-11, RC-13, RC-14, RC-15, RC-16, RC-17 | Name all three modules in the final pull request body (T-PR). |
| A-02 | Defect in existing work | The body of pull request 4833 says `--prune-baseline` removes the two stale entries. The analyzer prunes only entries for paths that the scan does not reach. The stale entries name a scanned file. | RC-37 (line 160), RC-38 (line 352) | Use `--write-baseline` on the full suite (decision D-4). |
| A-03 | Gate limitation | Baseline keys include the line number (RC-52). The bootstrap findings use line 1 (RC-15 to RC-17). A new bootstrap-importing test in those modules creates no new finding. | RC-52, RC-15, RC-16, RC-17 | Review each test diff in the three modules (risk R-6). |
| A-04 | Traceability gap | The help-test repair landed in commit `aa8d12e90f`, titled "fix: resolve strict Pyright diagnostics (#4853)". The title does not name the entry-point repair. | RC-04 | Name commit `aa8d12e90f` in the final pull request body. |
| A-05 | Pending defect | `pyproject.toml` line 122 says "Full commit of devtools release v0.6.4". The pin change makes that comment stale. | RC-29 | Update line 122 in T006. |
| A-06 | Known drift | The shared workflow pins in `ci.yml` line 681 name commit `79a5e459` (v0.6.4). The requirement pin names commit `2239e7bd`. | RC-27, RC-28 | Keep the workflow pins unchanged in this record. Note the drift in the pull request. |
| A-07 | Analyzer defect in another repository | For a class symbol, the analyzer inspects the whole class body (RC-32). Any `mistapi` root counts as HTTP risk (RC-33, RC-34). | RC-32, RC-33, RC-34 | Tasks T004 and T005. |
| A-08 | Scope check | The issue names the help test. At revision `838046104` the file imports `ApplicationBootstrap` (RC-02). On `main` the file does not (RC-01). Revision `838046104` diverged from `main`. `main` holds 42 commits that the revision lacks. The revision holds 4 commits that `main` lacks. | RC-01, RC-02 | No change. Record the divergence (research, Sources). |
| A-09 | Gate limitation | Stale entries produce no gate output. The stale advisory covers entries for absent files only (RC-37, and the module notes at baseline.py lines 10 to 13). | RC-18, RC-19, RC-37 | Remove the stale entries in T007. |
| A-10 | Pipeline impact | `pyproject.toml` and `uv.lock` trigger `container-build.yml` (RC-41). The pin change therefore starts a container build after the merge. | RC-41 | Follow Principle IV steps 10 to 12 (RC-59, T-MERGE). |

## Coverage Summary

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T001 | Help file: `test_help_stops_before_startup` (6 cases) and `test_invalid_help_variants_fail_before_startup` (3 cases). |
| FR-002 | T002 | Reject-flag file: `test_hyphenated_test_flag_uses_standard_argparse_error`. |
| FR-003 | T003 | Pytest on `test_main_entrypoint.py`. Search for `ApplicationBootstrap(argv` (SC-003). |
| FR-004 | T-LOCAL-GATES, T007 | Full gate output. Baseline diff shows zero added lines. |
| FR-005 | T005 | Good fixture and bad fixture in `misthelper-devtools` (external). Full gate after the pin. |
| FR-006 | T006 | `uv lock --check`. `tests/guardrails/test_dependency_export.py` (RC-25). |
| FR-007 | T007 | Full gate output. Baseline diff review. |
| FR-008 | T-LOCAL-GATES, T-REMOTE-CI | Local gate output. Remote check `Test quality ratchet (gate)` (RC-26). |
| FR-009 | T004, T-PR, T-MERGE | Pull request body contains `Closes #4828`. Issue state after merge. |

Each requirement has at least one task and at least one test or check.

## Consistency Review

- **Spec and plan**: The plan lists the three bootstrap modules as grandfathered debt. User Story 5 in the spec states the same debt.
- **Spec and tasks**: SC-002 gives 15 help cases and 3 reject-flag tests. T001 and T002 state the same counts.
- **Plan and tasks**: The change map lists `test_main_entrypoint.py` lines 158 to 166. T003 names the same lines. Each pin file in the map appears in T006.
- **Tasks and remote code**: T003 targets the test that RC-12 locates at line 162. The function spans lines 158 to 165 on `main`. Line 166 is the blank line after it.
- **Decision D-5 and the template**: The final pull request uses `Closes #4828`. Earlier work would use `Refs`. The plan contains no earlier pull request.
- **Constitution and plan**: The plan states the seven principles and the spec-specific rules. Principle IV steps 10 to 12 appear in the plan because of A-10.
- **Counts**: 9 requirements, 12 tasks, 20 planned tests, 66 remote check rows, and 8 decisions. The STATUS file and the summary use the same values.

## Defects in Existing Work

- A-01: The body of pull request 4833 omits one module.
- A-02: The body of pull request 4833 names a command that does not remove the two entries.
- A-04: The help-test repair has no title that names it.
- A-05: The comment on `pyproject.toml` line 122 becomes wrong after the pin change.

No defect in the merged code changes the test outcome on `main`. The gate result for `main` is success on the latest checked head (RC-26). The gate itself was not run in this record (Unverified U-01).

## Unresolved Items

- The owner of misthelper-devtools must accept and merge the analyzer fix (T004, T005).
- The analyzer fix may not clear all three modules (Unverified U-02). If it does not, the debt stays and the issue stays open.
- The shared workflow pin drift remains (A-06). No owner decision is needed for this record.
- The gate cannot see growth in the baselined modules (A-03). The review rule in risk R-6 covers this gap.
