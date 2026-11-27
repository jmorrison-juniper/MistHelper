# Tasks: Radon Job Mando Pin Conflict

## Format: `[ID] [P?] Requirement IDs Description`

- `[P]` marks a task that is safe to run in parallel.
- Each task lists its files, its acceptance statement, its verification command, and its status.
- Status values are open, verified-present, partial, or absent.
- Verification commands come from the local gates table in `.github/copilot-instructions.md` (R-39).

## Phase 1: Verify and Reproduce

- [ ] T001 [P] FR-002, FR-010 Confirm the pins that the fix keeps.
  - Files: `requirements-dev.txt` (line 179 `mando==0.7.1`, line 365 `radon==6.0.1`) and `uv.lock` (line 1301 `0.7.1`).
  - Acceptance: Remote checks R-09, R-10, and R-16 show the same values on `main`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row).
  - Status: verified-present.

- [ ] T002 [P] FR-008 Reproduce the radon job failure from run 45064243269.
  - Files: `.github/workflows/ci.yml` (lines 531 to 549).
  - Acceptance: The record names job 137336719006, the install step, and the resolution conflict (R-05, R-06, R-07).
  - Verification: `python -m pytest tests/guardrails/test_complexity_gate_limit.py` (Tests row) confirms that the radon job keeps its install-before-gate order.
  - Status: verified-present.

## Phase 2: Implement

- [ ] T003 FR-005, FR-006 Add the label `in-progress` to issue 4898 before the branch exists.
  - Files: none. The GitHub issue #4898 is the only object.
  - Acceptance: The issue shows the labels bug, ci, quality-gate, and in-progress.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row) on the base tree.
  - Status: open.

- [ ] T004 FR-005 Create the branch `fix/4898-radon-mando-conflict` from `main` in a new worktree.
  - Files: none. The worktree sits outside the shared checkout.
  - Acceptance: The branch starts from `main`. The shared checkout stays unchanged.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row) in the new worktree.
  - Status: open. Depends on T003.

- [ ] T005 [P] FR-001 Add the pip ignore rule for mando.
  - Files: `.github/dependabot.yml` (insert after line 11, in the pip entry).
  - Acceptance: `yaml.safe_load` returns the pip entry with an ignore rule. The rule names dependency `mando` and versions `>=0.8.0`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row), run after T006.
  - Status: open. Depends on T004.

- [ ] T006 FR-002, FR-003 Add the two real-file guard tests and their helper classes.
  - Files: `tests/guardrails/test_dependency_lock_file.py`.
  - Acceptance: `test_pinned_mando_satisfies_the_radon_requirement` and `test_dependabot_ignores_the_mando_release_that_radon_rejects` pass on the fix branch.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row).
  - Status: open. Depends on T005.

- [ ] T007 FR-002, FR-003 Add the two negative tests.
  - Files: `tests/guardrails/test_dependency_lock_file.py`.
  - Acceptance: `test_radon_rule_reports_a_mando_release_that_radon_rejects` and `test_dependabot_without_the_mando_rule_allows_the_rejected_release` pass.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row).
  - Status: open. Depends on T006.

- [ ] T008 [P] FR-007 Add the changelog fragment.
  - Files: `changelog.d/issue-4898-radon-mando-conflict.md`.
  - Acceptance: One `###` heading and one `**Fixed**` bullet. The bullet ends with `Issue #4898.`
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4898-radon-mando-conflict.md` (STE row, with the fragment path in place of the listed files).
  - Status: open. Depends on T004.

## Phase 3: Final Tasks

- [ ] T-LOCAL-GATES FR-008, FR-009, FR-010 Run each applicable local gate in the fix worktree.
  - Files: `.github/dependabot.yml`, `tests/guardrails/test_dependency_lock_file.py`, and `changelog.d/issue-4898-radon-mando-conflict.md`.
  - Acceptance: The gates in `design/quickstart.md` show the expected result. Each mutation run in SC-003 fails as expected, and the file is restored. The diff lists only the allowed files.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row).
  - Status: open. Depends on T005, T006, T007, and T008.

- [ ] T-PR FR-005, FR-006, FR-007 Commit, push, and open the fix PR.
  - Files: `.github/dependabot.yml`, `tests/guardrails/test_dependency_lock_file.py`, `changelog.d/issue-4898-radon-mando-conflict.md`, and the record folder.
  - Acceptance: The commit title is `fix(ci): ignore mando releases that radon 6.0.1 rejects`. The branch is `fix/4898-radon-mando-conflict`. The body holds `Closes #4898` (R-36), the labels bug, ci, and tests, the local gate results, and rollback notes that link to `plan.md`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row) on the committed tree.
  - Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI FR-008 Watch the remote checks of the fix PR.
  - Files: none.
  - Acceptance: SC-001 and SC-002 hold. The check `Radon (complexity)` succeeds with its complexity step run. No job log shows a resolution conflict.
  - Verification: `python -m pytest tests/guardrails/test_complexity_gate_limit.py` (Tests row) locally, and `gh pr checks $env:FIX_PR -R jmorrison-juniper/MistHelper --watch` remotely.
  - Status: open. Depends on T-PR.

- [ ] T-MERGE FR-004 Merge after authorization, then close PR #4888.
  - Files: none.
  - Acceptance: The orchestrator authorizes the merge. The squash merge lands on main. Add the auto-merge label only after all checks are green (R-33). PR #4888 closes with a note that cites `requirements-dev.txt` line 179 (blob `9a528bfe03a10f7bc903f5768ef26de765bbff43`, R-09) and `uv.lock` line 1301 (R-16). The sibling issues close only when the orchestrator authorizes it (D-8).
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py` (Tests row) on main after the merge.
  - Status: open. Depends on T-REMOTE-CI and orchestrator authorization.

## Dependencies and Execution Order

- T001 and T002 run in parallel. Both are read-only.
- T003 runs first in Phase 2, then T004.
- T005 and T008 run in parallel after T004.
- T006 runs after T005. T007 runs after T006.
- T-LOCAL-GATES runs after T005, T006, T007, and T008.
- T-PR, T-REMOTE-CI, and T-MERGE run in that order.

## Notes

- Run every command in the fix worktree. The shared checkout holds five modified files that this change does not include.
- Set `FIX_PR` to the number of the fix PR before the remote commands run.
- Keep one commit for the change and the record. A later commit to the merged branch creates an orphan pull request.
