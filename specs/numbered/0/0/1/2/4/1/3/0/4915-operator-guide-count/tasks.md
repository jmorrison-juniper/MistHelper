# Tasks: Operator Guide Operation Count

**Input**: Numeric record `specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count`, from `spec.md` and `plan.md`.

**Available Docs**: `spec.md`, `plan.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/checklists/requirements.md`.

**Tests**: The guard test is required, because FR-007 requires a test that fails before the guide edit.

**Organization**: Tasks follow the user stories. User Story 2 (guard) runs first, because the guard must fail before the guide changes.

## Format

- `[P]`: the task runs in parallel with other `[P]` tasks, because it changes different files.
- `Status`: `open`, `absent`, `partial`, or `verified-present`, measured against remote `main` (R-IDs in `design/research.md`).

## Phase 1: Setup

- [ ] T001 Create the worktree and the environment
  - Requirements: FR-007
  - Files: none. Create the worktree for branch `docs/4915-operator-guide-count` from `main`.
  - Acceptance: Issue #4915 carries the `in-progress` label (R-34). The branch name follows the pattern in R-35. The bootstrap command completes without error (R-54, R-55).
  - Verify: `python -m pytest tests\guardrails\test_destructive_menu_docs.py -q`
  - Status: open

## Phase 2: User Story 2 - Maintainer gets a guard against a repeated count (Priority: P2)

- [ ] T002 Add the guard test before the guide edit
  - Requirements: FR-001, FR-002, FR-007
  - Files: `tests/guardrails/test_destructive_menu_docs.py`
  - Acceptance: The module holds the class `OperatorGuideCountIndex` and the function `test_operator_guide_defers_the_count_to_the_menu_reference`. The test reads `documentation/operator-guide.md` through `pathlib.Path`. Before T003, the test fails. Its failure names `303 operations` and `numbered 1 to 304`. The module docstring gains one paragraph about the guide (D-2, D-3).
  - Verify: `python -m pytest tests\guardrails\test_destructive_menu_docs.py -q` (expect one failure)
  - Status: absent

## Phase 3: User Story 1 - Operator reads a correct pointer to the menu operations (Priority: P1)

- [ ] T003 Remove the stale count sentence from the guide
  - Requirements: FR-001, FR-002, FR-003
  - Files: `documentation/operator-guide.md`
  - Acceptance: Line 13 is deleted in full. Lines 14 and 15 stay unchanged. The guide holds no operation count and no `numbered 1 to N` range. The link `(menu_reference.md)` stays in place. Depends on T002.
  - Verify: `python -m pytest tests\guardrails\test_destructive_menu_docs.py -q` (expect all tests to pass)
  - Status: partial

- [ ] T004 [P] Add the release-note fragment
  - Requirements: FR-005
  - Files: `changelog.d/issue-4915-operator-guide-count.md`
  - Acceptance: The file holds one `###` heading and one bullet that starts with `**Fixed**:`. The bullet ends with `Issue #4915.` The file name follows the issue form that the changelog guard enforces (R-78).
  - Verify: `python -m pytest tests\guardrails\test_changelog_fragment_policy.py -q`
  - Status: absent

- [ ] T005 [P] Copy the record to the route
  - Requirements: FR-008
  - Files: `specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count\spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design\research.md`, `design\data-model.md`, `design\quickstart.md`, `design\checklists\requirements.md`
  - Acceptance: The route folder holds the eight files of this record, with the same content. The route levels hold five children or fewer (R-83, R-85).
  - Verify: `python -m pytest tests\guardrails\test_process_folder_structure.py tests\guardrails\test_spec_route_contract.py -q`
  - Status: absent

## Phase 4: Gates and delivery

- [ ] T-LOCAL-GATES Run each applicable local gate
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008
  - Files: the changed paths from T003, T004, and T005, and the record folder.
  - Acceptance: Each applicable local gate prints its expected result, as Scenarios 4 to 9 in `design/quickstart.md` state. Mypy, pydocstyle, interrogate, and vulture do not apply to the test file, because the CI scopes exclude tests (R-43, R-44, R-45, R-46). The pull request body names each gate that does not apply and gives the reason. Any failure in the guard modules of Scenario 8 is compared with the baseline in issue #4917. A new failure stops the task.
  - Verify: The commands in `design/quickstart.md`, Scenarios 4 to 9.
  - Status: open

- [ ] T-PR Commit, push, and open the pull request
  - Requirements: FR-005, FR-008
  - Files: `documentation/operator-guide.md`, `changelog.d/issue-4915-operator-guide-count.md`, `tests/guardrails/test_destructive_menu_docs.py`, `specs/numbered/0/0/1/2/4/1/3/0/4915-operator-guide-count/`
  - Acceptance: Stage each path by name (R-37). The commit title is `docs(operator-guide): remove the stale operation count`. The commit body holds `Closes #4915` and the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`. Run the test quality ratchet in `.github/copilot-instructions.md` after the commit and before the push (R-69). Push the branch without a force option. The pull request body follows `.github/PULL_REQUEST_TEMPLATE.md` (R-59). It contains `Closes #4915` (R-38) and lists each local gate with its result. Set `$PR_NUMBER` to the number that `gh pr create` prints.
  - Verify: `gh pr view $PR_NUMBER --json title,body,headRefName`
  - Status: open

- [ ] T-REMOTE-CI Watch the continuous integration run
  - Requirements: FR-006
  - Files: none
  - Acceptance: `gh pr checks $PR_NUMBER --watch` ends with each required check in a success state. The check `Conventional Commits PR title` passes. If a check fails, fix it on the same branch with a new commit and push again without a force option.
  - Verify: `gh pr checks $PR_NUMBER`
  - Status: open

- [ ] T-MERGE Merge and close the issue
  - Requirements: SC-005
  - Files: none
  - Acceptance: After the orchestrator authorizes the merge, add the `auto-merge` label (R-72). The label starts the squash merge after each required check passes. After the merge, `gh issue view 4915 --json state` reports `CLOSED` (R-73). Record the result of `gh run list --workflow container-build.yml --branch main --limit 3`. No run matches the merge commit (D-6, R-56). Remove the worktree after the merge.
  - Verify: `gh issue view 4915 --json state`
  - Status: open
  - Warning: delete the local branch only after the merge commit reaches `main`. Deleting an unmerged branch can remove its only local copy of the commits.

## Dependencies and Execution Order

- T001 starts first.
- T002 depends on T001.
- T003 depends on T002.
- T004 and T005 are `[P]`. Each depends on T001 only. They run in parallel with T002 and T003.
- T-LOCAL-GATES depends on T003, T004, and T005.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on the orchestrator authorization.

## Verification Exceptions

- T-PR, T-REMOTE-CI, and T-MERGE verify with GitHub commands. The local gates table has no row for hosting or continuous integration state. The commands come from the workflow rows in `.github/copilot-instructions.md` (R-52, R-53).
