# Specification Analysis Report: Windows Path and Symlink Guardrails

This review checks the spec, the plan, the tasks, and the remote code on `main`. Row IDs such as R-15 refer to `design\research.md`.

## Findings: Defects in Existing Work

| ID | Finding | Evidence | Resolution |
| - | - | - | - |
| A-1 | The issue calls the message mismatch "another form of the same path." The inspector formats a Python list, so each backslash appears doubled. The pattern escapes one form only. | R-18, R-19, R-20 | D-5 changes both sides to `as_posix()`. |
| A-2 | Three changelog rules disagree. The constitution requires one fragment for each change. The copilot instructions require one only for a user-visible change. The changelog README exempts an internal change. | R-32, R-42, R-54 | D-8 applies the strictest rule. Unresolved item U-3 aligns the three documents. |
| A-3 | The repository's missing-`pwsh` checks call `pytest.fail`. The issue asks for a skip on the symlink privilege. | R-12, S-3 | D-2 skips only on error 1314. The `pytest.fail` behavior stays unchanged. |
| A-4 | The test module holds more than five top-level names. The constitution forbids a new direct child under a noncompliant parent. | R-10, R-24 | D-7 adds no top-level test name. Unresolved item U-2 records the grandfathered debt. |
| A-5 | The skip branch cannot run on Linux CI, because Linux creates the link. | R-03, R-05 | D-7 and the one-off check in quickstart section 2.3 cover the branch. Unresolved item U-1 records the gap. |
| A-6 | The issue says the three failures occur on a pristine export of `origin/main`. This review cannot run tests (rule 2). | S-10 | Task T001 records the failures on the reporter host. Unverified item UV-1 records the gap. |
| A-7 | The constitution lists the container build as a release step. The workflow runs on pushes that change product files, or on manual dispatch. A test-only merge does not start the build. | R-27, R-43 | The pull request body records that the trigger did not start. |
| A-8 | The local checkout holds five modified files outside this issue. | L-2 | Each file is staged by its explicit path. Unresolved item U-4 records the owner decision. |
| A-9 | A skip can count as a pass in summaries. Issue #2241 recorded 11 test files that covered nothing while a gate stayed green. | R-76 | D-2 keeps the skip narrow. The skip reason prints under `-rs` (quickstart section 2.1). Task T-REMOTE-CI checks the Linux run. Unresolved item U-1 covers the gap. |

## Consistency Review

- The spec, plan, and tasks name the same method, `SpecCommandFixture.symlink`. The plan places it after `feature` (R-08). Task T002 names the same placement.
- FR-005 and FR-006 match the plan's target shapes, and each has one task (T003, T004).
- FR-010 names the fragment file that task T005 creates. The name follows the issue form that the guard accepts (R-56).
- FR-011 names the route that the plan and task T006 use. The route follows the base-5 formula (R-22, R-23, L-9).
- SC-005 matches the test-quality gate row in the copilot instructions (R-49).
- The plan places no new module-level name (D-6, D-7). The Symbols gate row (R-51) matches that claim.

## Coverage Summary

Each FR maps to at least one task. The self-review rule (a) requires a repository test for each FR. FR-003, FR-004, FR-011, and FR-012 do not map to a new repository test. D-7 forbids the new test. The verification column names the command that proves each FR.

| FR | Tasks | Test or verification |
| - | - | - |
| FR-001 | T002 | Existing `test_unsafe_feature_selection_fails[symlink]` on Windows (SC-001) |
| FR-002 | T002 | Existing `test_unsafe_feature_selection_fails[symlink]` on Linux CI (SC-003) |
| FR-003 | T002 | One-off check, quickstart section 2.3. Not a repository test (D-7, U-1) |
| FR-004 | T002 | Log capture, quickstart section 2.2 |
| FR-005 | T003 | `test_git_ignores_poisoned_locations` (test set row 4) |
| FR-006 | T004 | `test_missing_root_fails_with_path_and_cause` (test set row 5) |
| FR-007 | T004 | `test_missing_root_fails_with_path_and_cause` (wording) |
| FR-008 | T-LOCAL-GATES | Symbols gate (R-51) and review of the `src` diff |
| FR-009 | T-LOCAL-GATES | Lint gate and line length (R-46, R-66) and review |
| FR-010 | T005 | `test_changelog_fragment_policy.py` (test set rows 10 to 12) |
| FR-011 | T006 | Quickstart section 4. The route formula test pins the formula, not this folder (R-11). |
| FR-012 | T-PR | Pull request body check (R-68) |

## Unresolved Items

- Remediation: a follow-up issue moves the guard into a compliant test package and adds a unit test.
- U-2: The three guard modules exceed the Five-Item limit, and that debt is grandfathered (R-10). Remediation: a follow-up issue splits the modules.
- U-3: The three changelog rules disagree (A-2). Remediation: a documentation issue aligns the constitution, the copilot instructions, and the changelog README.
- U-4: The local checkout holds five modified files outside this issue (L-2). Owner: the operator decides whether to commit or keep them. This change does not touch them.
- U-5: Issues #4877 and #4879 stay out of scope (S-11).
- U-6: The reporter-host baseline is not yet recorded (task T001 is open).

## Metrics

- Functional requirements: 12
- Success criteria: 5
- Tasks: 10
- Decisions: 11, with no human decision required
- Remote checks: 76
- Named tests in the test set: 12
