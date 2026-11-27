# Tasks: Vulture Gate Mando Radon Conflict

**Input**: `plan.md`, `spec.md`, `design/research.md`, and `design/quickstart.md`.

**Format**: `T-ID [P?] Requirements`. Each task names its paths, acceptance, verification, and status.

**Status values**: `open`, `verified-present`, `partial`, or `absent`. Status `absent` means the change is not in the repository yet.

## Requirement Coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T-REMOTE-CI | TEST-006 |
| FR-002 | T-LOCAL-GATES, T-PR | TEST-008, TEST-010 |
| FR-003 | T001, T003 | TEST-002, TEST-003 |
| FR-004 | T001, T002 | TEST-001 |
| FR-005 | T003 | TEST-002, TEST-003 |
| FR-006 | T-LOCAL-GATES | TEST-006, TEST-010 |
| FR-007 | T004 | TEST-005 |
| FR-008 | T005 | TEST-004 |
| FR-009 | T-PR | TEST-009 |
| FR-010 | T-MERGE | TEST-011 |
| FR-011 | T003, T-LOCAL-GATES | TEST-010 |
| FR-012 | T-REMOTE-CI | TEST-007 |

## Tasks

- **T001** [P] FR-003, FR-004. Path: `.github/dependabot.yml`. Add the ignore rule from `plan.md` below the pip stream. Acceptance: the pip stream holds one rule for `mando` with versions `>= 0.8`. Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`, run after T003. Status: absent.

- **T002** FR-004. Depends on T001. Path: `tests/guardrails/test_pr_title_workflow.py`. Add the same rule to the pip stream of `POLICY_SNAPSHOTS["dependabot"]`. Acceptance: `test_complete_policy` passes (TEST-001). Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`. Status: absent.

- **T003** FR-003, FR-005, FR-011. Depends on T002. Path: `tests/guardrails/test_pr_title_workflow.py`. Add the two cases from `plan.md` to `test_unrelated_changes_fail`. Acceptance: each case fails the policy assertion with a Dependabot message (TEST-002, TEST-003). Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`. Status: absent.

- **T004** [P] FR-007. Path: `documentation/quality-gates.md`. Add the paragraph from `plan.md` after the job table and before the warning at line 74. Acceptance: the paragraph names the install step and the removal condition. The sentence "No block above cyclomatic complexity 10" stays unchanged (TEST-005). Verification: `python -m pytest tests/guardrails/test_complexity_gate_limit.py`. Status: absent.

- **T005** [P] FR-008. Path: `changelog.d/issue-4899-mando-radon-pin.md`. Create the fragment from `plan.md`. Acceptance: the name, heading, bullet, and change type pass the fragment guard (TEST-004). Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Status: absent.

- **T-LOCAL-GATES** FR-002, FR-006, FR-011. Depends on T001 to T005. Paths: the four changed files. Run each applicable gate from the local gates table: Compile, Lint, Format, Tests, Test quality, Security lint, Symbols, Dead code, and STE. Acceptance: each gate meets its expected result in `design/quickstart.md`. Record each output line in the pull request body. Verification: the commands in `design/quickstart.md`. Status: open.

- **T-PR** FR-002, FR-009. Depends on T-LOCAL-GATES. Create branch `fix/4899-vulture-gate-mando-radon-conflict`. Commit with the title from decision D-7. Open a pull request whose body contains `Closes #4899`, run 45064243269, and job 137336718674. Add the record folder in a separate commit. Acceptance: the diff names the four changed files and the record folder only (TEST-010). Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`, plus the remote check named `Conventional Commits PR title`. Status: open.

- **T-REMOTE-CI** FR-001, FR-012. Depends on T-PR. Watch the checks of the fix pull request with `gh pr checks --watch`. Acceptance: TEST-006, TEST-007, and TEST-008 pass. Verification: the Dead code row of the local gates table. The remote Vulture job runs `vulture $VULTURE_PATHS --min-confidence 70`, and its step concludes success. Status: open.

- **T-MERGE** FR-010. Depends on T-REMOTE-CI. After remote CI passes and the orchestrator authorizes the merge, enable auto-merge and squash-merge the fix pull request. Then close pull request #4888 with a comment that names the fix pull request. Acceptance: TEST-011 passes. Verification: the Dead code row on the next run on `main`. The Vulture job concludes success. Status: open.

Caution: closing pull request #4888 is recoverable. Reopen the pull request on GitHub when a reviewer needs its thread.

## Test Register

| ID | Kind | Check | Source |
| - | - | - | - |
| TEST-001 | Local guard | `test_complete_policy` passes with the new snapshot | `tests/guardrails/test_pr_title_workflow.py` |
| TEST-002 | Local guard | Removing the mando rule fails the policy guard | `tests/guardrails/test_pr_title_workflow.py` |
| TEST-003 | Local guard | Moving the lower bound to 0.9 fails the policy guard | `tests/guardrails/test_pr_title_workflow.py` |
| TEST-004 | Local guard | The changelog guard passes for the new fragment | `tests/guardrails/test_changelog_fragment_policy.py` |
| TEST-005 | Local guard | The complexity guard passes after the guide edit | `tests/guardrails/test_complexity_gate_limit.py` |
| TEST-006 | Remote check | The `Detect dead code` step concludes success on the fix pull request | Quality Gates run of the fix pull request |
| TEST-007 | Remote check | The fix pull request run holds no `ResolutionImpossible` line | Failed logs of the Quality Gates run |
| TEST-008 | Remote check | The `Dependency lock and exports` job concludes success | Quality Gates run of the fix pull request |
| TEST-009 | Record check | The record holds the check name, job ID, run ID, step name, and resolver text | `design/research.md` and `spec.md` |
| TEST-010 | Diff check | The changed paths equal the four changed files and the record folder | Diff of the fix branch against `origin/main` |
| TEST-011 | Remote check | Pull request #4888 is closed after the merge | GitHub pull request state |

## Dependencies and Order

- T001 comes first for the Dependabot file. T002 and T003 depend on it in that order.
- T004 and T005 run in parallel with T001.
- T-LOCAL-GATES waits for T001 to T005.
- T-PR waits for T-LOCAL-GATES. T-REMOTE-CI waits for T-PR. T-MERGE waits for T-REMOTE-CI.
