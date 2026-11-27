# Tasks: Mando Pin Conflict Behind the pydocstyle Gate Failure

**Input**: Design documents in `specs/numbered/0/0/1/2/4/1/0/0/4900-mando-radon-pin-conflict/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/quickstart.md`, and `design/checklists/requirements.md`

**Tests**: Five existing or updated test cases cover the requirements. Run each test before the commit. The cases are `TestDependabotPolicy::test_complete_policy`, `TestDependencyExport::test_requirements_exports_match_the_lock`, `TestFragmentNaming::test_every_fragment_uses_an_allowed_name`, `TestFragmentContent::test_every_fragment_holds_a_heading_and_a_bullet`, and `test_numeric_feature_route_remains_stable`.

**Format**: Each task has a requirement list, the exact files, an acceptance statement, one verification command from the local gates table, and a status. The status is `open`, `verified-present`, `partial`, or `absent`. The `[P]` marker means the task can run in parallel with other `[P]` tasks of its phase.

## Phase 1: Setup and Baseline

- [ ] T001 [FR-002, FR-010] Claim issue 4900 and verify the baseline on main.
  - Files: `requirements-dev.txt` and `uv.lock` (read only).
  - Acceptance: Issue 4900 carries the label `in-progress`. A worktree holds the branch `fix/4900-mando-radon-pin-conflict` from `origin/main`. Line 179 of `requirements-dev.txt` reads `mando==0.7.1`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_export.py` (Tests row). The test passes.
  - Status: verified-present (design/research.md rows 6, 9, and 10).

## Phase 2: Dependency Policy and Changelog

- [ ] T002 [FR-003, FR-004] Add the mando ignore block to the pip entry in `.github/dependabot.yml`, after line 11. Depends on T001.
  - Files: `.github/dependabot.yml`.
  - Acceptance: The pip entry holds `ignore`. The block names `mando` and lists the update types `version-update:semver-minor` and `version-update:semver-major`. The npm and GitHub Actions entries do not change. Each new line carries an inline comment.
  - Verification: Run T003 first. Then run `python -m pytest tests/guardrails/test_pr_title_workflow.py` (Tests row).
  - Status: absent (design/research.md row 12).

- [ ] T003 [FR-003, FR-004] Add the same block to the pip entry of `POLICY_SNAPSHOTS["dependabot"]` in `tests/guardrails/test_pr_title_workflow.py`, after line 29. Depends on T002.
  - Files: `tests/guardrails/test_pr_title_workflow.py`.
  - Acceptance: `TestDependabotPolicy::test_complete_policy` passes. The snapshot lists the update types in the same order as the YAML. Each new line carries an inline comment.
  - Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py` (Tests row).
  - Status: absent (design/research.md row 13).

- [ ] T004 [P] [FR-007] Create the fragment `changelog.d/issue-4900-mando-radon-pin-conflict.md`.
  - Files: `changelog.d/issue-4900-mando-radon-pin-conflict.md`.
  - Acceptance: The file holds one `###` heading and one `Fixed` bullet that names issue 4900. The file name follows the issue form. The file holds no version stamp.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (Tests row).
  - Status: absent (no file with this name exists in `changelog.d/`).

## Phase 3: Record

- [ ] T005 [P] [FR-008, FR-011] Copy the record files from the draft folder into the managed route.
  - Files: `specs/numbered/0/0/1/2/4/1/0/0/4900-mando-radon-pin-conflict/` with `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` (`research.md`, `data-model.md`, `quickstart.md`, `checklists/requirements.md`).
  - Acceptance: The folder holds five children or fewer at each level. The route matches design/research.md row 19.
  - Verification: `python -m pytest tests/guardrails/test_spec_route_contract.py` (Tests row).
  - Status: absent (design/research.md row 18).

## Phase 4: Gates and Delivery

- [ ] T-LOCAL-GATES [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008] Run each local gate that applies to the changed files. Depends on T002, T003, T004, and T005.
  - Files: `.github/dependabot.yml`, `tests/guardrails/test_pr_title_workflow.py`, `changelog.d/issue-4900-mando-radon-pin-conflict.md`, and each Markdown file of the record.
  - Acceptance: Ruff prints `All checks passed`. Black reports that no file needs a change. Each Tests row command passes. The Docstrings command prints no violation. Interrogate passes at 90 percent or above. Symbol-diff prints `no module-level name changed`. The STE linter scores each Markdown file at 80 or above.
  - Verification: The Lint, Format, Tests, Docstrings, Symbols, and STE rows of the local gates table. The exact commands are in design/quickstart.md, Scenario 3.
  - Status: open.

- [ ] T-PR [FR-006, FR-007, FR-010] Commit the changes, run the test quality gate, push the branch, and open the pull request. Depends on T-LOCAL-GATES.
  - Files: The files of T002 through T005.
  - Acceptance: The commit title is `fix(ci): block mando updates that radon cannot resolve`. The commit message ends with the Co-authored-by trailer. The pull request body holds `Closes #4900`, the local gate results, the changed-file list, and the rollback steps. The changed-file list holds no path that FR-006 forbids.
  - Verification: The Test quality row. Run the `test-quality-analyzer --gate` command with `--changed-from "origin/main"`. The output reads `gate: 0 new findings vs baseline`.
  - Status: open.

- [ ] T-REMOTE-CI [FR-001, FR-002, FR-005] Watch the remote checks of the pull request that T-PR opens. Depends on T-PR.
  - Files: None changed.
  - Acceptance: All 28 directly failing jobs and both downstream jobs conclude success. The pydocstyle job shows `Check docstring conventions` with success. If a job fails, open a new issue with its log, and do not merge.
  - Verification: The Docstrings row, run locally first. Then `gh pr checks --watch` for the branch.
  - Status: open.

- [ ] T-MERGE [FR-009] After the orchestrator authorizes the merge, merge the fix, then close pull request 4888. Depends on T-REMOTE-CI.
  - Files: None changed. The GitHub pull request 4888 and its branch.
  - Acceptance: The fix merges as one squash commit. The `auto-merge` label is added only after every check passes. Pull request 4888 reads CLOSED. The closing comment names commit e86098cd, the fix pull request, and blob 9a528bfe for `requirements-dev.txt` on main. The branch `dependabot/pip/mando-0.8.2` no longer exists.
  - Caution: Deleting the branch removes the ref only. Commit e86098cd stays recoverable by its SHA.
  - Verification: The Tests row. Run `python -m pytest tests/guardrails/test_pr_title_workflow.py` on the merged main revision.
  - Status: open.

## Dependencies and Execution Order

- T001 comes first.
- T002 starts after T001. T003 starts after T002.
- T004 and T005 can run in parallel with T002 and T003.
- T-LOCAL-GATES starts after T002, T003, T004, and T005 finish.
- T-PR starts after T-LOCAL-GATES. T-REMOTE-CI starts after T-PR. T-MERGE starts after T-REMOTE-CI.
