# Tasks: Interrogate Gate Failure on PR #4888

**Input**: Numeric record `specs\numbered\0\0\1\2\4\1\0\1\4901-interrogate-mando-pin-conflict`. Sources: `spec.md`, `plan.md`, and `design/research.md`.

**Format**: `- [ ] ID [P] [requirement] Instruction. Status: value.` The status values are `open`, `verified-present`, `partial`, and `absent`. Tick a task only after its verification passes. The tag `[process]` marks a task that follows a repository rule and maps to no requirement.

## Phase 1: Claim and branch

- [ ] T001 [process] Add the label `in-progress` to issue #4901 before any branch exists. Status: open.
  - Acceptance: The issue lists the `in-progress` label. The repository requires the claim first (RV-41).
  - Verify: `gh issue view 4901 -R jmorrison-juniper/MistHelper --json labels`

- [ ] T002 [process] Create the worktree `..\MistHelper-4901` on branch `fix/4901-interrogate-mando-pin-conflict`. Status: open.
  - Acceptance: The worktree starts from `origin/main`. The main checkout keeps its files.
  - Verify: `git -C ..\MistHelper-4901 rev-parse --abbrev-ref HEAD` prints `fix/4901-interrogate-mando-pin-conflict`.

## Phase 2: Verify the baseline

- [X] T003 [FR-001] Confirm that `requirements-dev.txt` pins `mando==0.7.1` at line 179 and `radon==6.0.1` at line 365. Status: verified-present.
  - Evidence: RV-01 and RV-02, blob `9a528bfe03a10f7bc903f5768ef26de765bbff43`.
  - Verify: `Select-String -Path requirements-dev.txt -Pattern '^mando==0.7.1$','^radon==6.0.1$'` returns two lines.

- [ ] T004 [FR-001] Run the export guard that compares the exports with `uv.lock`. Status: open.
  - Acceptance: The guard passes. A failure names the export file and the drift.
  - Verify: `python -m pytest tests/guardrails/test_dependency_export.py -q`

## Phase 3: Tests first

- [ ] T005 [P] [FR-002] [FR-003] Add three parametrized cases to `TestDependabotPolicy` in `tests/guardrails/test_pr_title_workflow.py`. Status: absent.
  - Acceptance: The rule ignores version 0.8.2 and version 0.9.0. The rule allows version 0.7.2.
  - Acceptance: Each case logs before and after its check. Each new line carries an inline comment.
  - Verify: `python -m pytest tests/guardrails/test_pr_title_workflow.py::TestDependabotPolicy -q` fails the three new cases before T007.
  - Evidence: Copy the failing summary line into the PR body (RV-62).

- [ ] T006 [FR-004] Add the same ignore list to `POLICY_SNAPSHOTS["dependabot"]["updates"][0]` after line 29. Status: absent.
  - Acceptance: The snapshot holds the ignore list for the pip stream (RV-20, RV-21).
  - Verify: `python -m pytest tests/guardrails/test_pr_title_workflow.py::TestDependabotPolicy::test_complete_policy -q` fails before T007.

## Phase 4: Implementation

- [ ] T007 [FR-002] [FR-003] [FR-004] Add the ignore list to the pip stream of `.github/dependabot.yml` after line 11. Status: absent.
  - Acceptance: The list names `mando` with `versions: [">= 0.8"]`. A comment block gives the radon limit and the removal condition.
  - Acceptance: Each new line carries an inline comment. Do not edit `requirements-dev.txt` by hand.
  - Verify: `python -m pytest tests/guardrails/test_pr_title_workflow.py::TestDependabotPolicy -q` passes all cases.

- [ ] T008 [P] [FR-008] Add `changelog.d/issue-4901-interrogate-mando-pin-conflict.md`. Status: absent.
  - Acceptance: One `###` heading and one `Changed` bullet. The bullet names issue #4901 at its end.
  - Verify: `Get-ChildItem changelog.d -Filter 'issue-4901-*'` returns one file.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d\issue-4901-interrogate-mando-pin-conflict.md` scores 80 or above (quickstart, STE row).

- [ ] T009 [P] [FR-009] [FR-010] Copy the record from the draft folder into `specs\numbered\0\0\1\2\4\1\0\1\4901-interrogate-mando-pin-conflict`. Status: partial.
  - Acceptance: The record holds the same files as the draft folder. The route guard passes.
  - Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py -q`

## Phase 5: Final tasks

- [ ] T-LOCAL-GATES [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-008] Run each applicable local gate. Status: open.
  - Acceptance: Each applicable gate exits 0. Record each command, exit code, and summary in the PR body.
  - Acceptance: Run the test quality step after the local commit and before the push (RV-36).
  - Verify: Follow the table in `design\quickstart.md`, section "Local gates".

- [ ] T-PR [FR-007] [FR-008] Commit, rebase onto `origin/main`, push, and open the pull request. Status: open.
  - Acceptance: The title is `fix(deps): ignore mando 0.8 updates that radon rejects` (RV-38).
  - Acceptance: The body holds `Closes #4901`, the template checklist, and the gate results (RV-44, RV-62).
  - Acceptance: Labels are `bug` and `ci` (RV-37). Name the 14 sibling issues with `Refs` only (research R10).
  - Acceptance: The commit message ends with `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
  - Verify: `gh pr list -R jmorrison-juniper/MistHelper --head fix/4901-interrogate-mando-pin-conflict --json number,title,state`

- [ ] T-REMOTE-CI [FR-005] [FR-006] Watch the Quality Gates run on the pull request until every check ends. Status: open.
  - Acceptance: `Interrogate (docstring coverage)` shows success. The 15 required contexts show success.
  - Acceptance: No job that failed in run 45064243269 fails again on the fix head.
  - Verify: Run `gh pr checks --watch` in `..\MistHelper-4901`.

- [ ] T-MERGE [FR-007] [FR-001] Enable auto-merge after the orchestrator authorizes the merge. Close PR #4888 after the merge. Status: open.
  - Acceptance: Auto-merge starts only after T-REMOTE-CI passes. Add the `auto-merge` label only after each check is green (RV-45).
  - Acceptance: `main` keeps `mando==0.7.1` at line 179 (RV-01).
  - Acceptance: PR #4888 reads `CLOSED`. Its closing comment names the merged fix, commit `e86098c`, and the main blob SHA (RV-47, RV-01).
  - Caution: Deleting the Dependabot branch removes its name. Delete it only after the closing comment exists.
  - Acceptance: Dispatch `container-build.yml` on `main`. Verify the revision label (RV-51, RV-52, RV-61). Update the stack (RV-60).
  - Verify: `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,mergedAt`
  - Verify: Decode `contents/requirements-dev.txt?ref=main` with `gh api`. Line 179 reads `mando==0.7.1`.

## Dependencies and execution order

- T001, then T002.
- T002, then T003 and T004.
- T002, then T005, then T006, then T007.
- T002 allows T008 and T009 in parallel with T005. They use other files.
- T004, T007, T008, and T009, then T-LOCAL-GATES, then T-PR, then T-REMOTE-CI, then T-MERGE.

## Notes

- T001 and T002 are process tasks. No local gate applies to them.
- T005 and T006 edit one file, so they run in order.
- Warning: do not push to `dependabot/pip/mando-0.8.2`. Dependabot owns that branch.
- Do not edit `requirements-dev.txt` or `uv.lock` in this change.
