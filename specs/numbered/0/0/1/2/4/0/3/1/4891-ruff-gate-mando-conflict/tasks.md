# Tasks: Ruff (lint) check failure from the mando 0.8.2 pin

**Input**: Record folder `specs\numbered\0\0\1\2\4\0\3\1\4891-ruff-gate-mando-conflict`. Required inputs: `plan.md` and `spec.md`. Supporting artifacts: `design\research.md`, `design\quickstart.md`.

## Conventions

- `[P]` marks a task that can run in parallel with other `[P]` tasks. The tasks change different files and have no shared step.
- Status values: `absent` means the artifact is not on `main` yet. `verified-present` means the artifact is on `main` and its evidence is recorded. `open` means the work has not started.
- Each task names exact paths and one verification command from the local gates table (RV-48). Remote tasks also name the `gh` command that checks the remote state.
- Tests come first. T002 writes the guard cases before T003 adds the entry.

## Phase 1: Verify the pins

### T001 Confirm the mando 0.7.1 pin and lock agreement on main

- **Requirements**: FR-001, FR-007
- **Paths**: `requirements-dev.txt` (line 179), `uv.lock` (line 1301), `pyproject.toml` (line 118). No edit.
- **Acceptance**: `requirements-dev.txt` pins `mando==0.7.1` (RV-01). `uv.lock` locks mando 0.7.1 (RV-05). The Dependency lock and exports job succeeded on `main` (RV-51).
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py`
- **Status**: verified-present

## Phase 2: Guard cases and policy entry

### T002 Write the three guard cases first

- **Requirements**: FR-002, FR-003, FR-004, FR-009
- **Paths**: `tests/guardrails/test_dependency_export.py`
- **Acceptance**: The module docstring names issue #4891. The module imports `yaml`. Class `DependabotPolicy` holds the two helpers described in `plan.md`. Class `TestDependabotMandoIgnore` holds the three cases described in `plan.md`. Each executable line has an inline comment. Each action logs before and after. Before T003, cases 1 and 2 fail on `main`, and case 3 passes.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py`
- **Status**: absent

### T003 Add the mando ignore entry (after T002)

- **Requirements**: FR-002, FR-003, FR-004, SC-004
- **Paths**: `.github/dependabot.yml`. Insert the block after line 11 (`prefix: "chore"`), inside the pip update block.
- **Entry text**:

```yaml
    ignore:
      # Issue #4891: radon 6.0.1 requires mando below 0.8. A mando 0.8 pin makes
      # pip stop with a resolver conflict in each job that installs the dev requirements.
      # Patch updates stay allowed. Remove this entry only after a radon release accepts mando 0.8.
      - dependency-name: "mando"
        update-types: ["version-update:semver-minor"]
```

- **Acceptance**: The YAML parses. The pip block holds one mando entry with `version-update:semver-minor` and no semver-patch entry. Cases 1 and 2 pass, and the output prints the count of entries examined.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py`
- **Status**: absent

## Phase 3: Fragment and record

### T004 [P] Add the changelog fragment

- **Requirements**: FR-005
- **Paths**: `changelog.d/issue-4891-dependabot-mando-ignore.md` (new file)
- **Content**: One `###` heading that names the change. One bullet that starts with `- **Fixed**:` and ends with `Issue #4891.`
- **Acceptance**: The file name uses the issue form (RV-61). The file holds one heading and one bullet. The bullet uses the change type `Fixed` (RV-19). The fragment guard reads the file without error.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent

### T005 [P] Copy the record folder

- **Requirements**: FR-006
- **Paths**: `specs/numbered/0/0/1/2/4/0/3/1/4891-ruff-gate-mando-conflict/` (new folder). It holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`.
- **Acceptance**: No `contracts` folder exists. Each folder holds five children or fewer. The record contains no placeholder token.
- **Verification**: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` (Full tests row, RV-50)
- **Status**: absent

## Final tasks

### T-LOCAL-GATES Run the applicable local gates

- **Requirements**: FR-008, FR-009
- **Paths**: `.github/dependabot.yml`, `tests/guardrails/test_dependency_export.py`, `changelog.d/issue-4891-dependabot-mando-ignore.md`, `specs/numbered/0/0/1/2/4/0/3/1/4891-ruff-gate-mando-conflict/`
- **Steps**:
  1. Stage each path by name. Stage no other file.
  2. Commit the change on the fix branch. The subject is `fix(ci): ignore mando minor updates that radon 6.0.1 blocks`. The body contains `Closes #4891` and the Co-authored-by trailer required by the session policy.
  3. Run the test-quality procedure after the commit (RV-49). The procedure requires committed tests.
  4. Run each applicable local gate listed in `design\quickstart.md`, section 4. Record each result.
- **Acceptance**: Each command reports the expected result in `quickstart.md`, section 4. The test-quality gate reports `gate: 0 new findings vs baseline`. No applicable gate is skipped.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py`
- **Status**: open

### T-PR Push the fix branch and open the fix pull request

- **Requirements**: FR-007, FR-008
- **Paths**: The branch `fix/4891-dependabot-mando-ignore`, branched from `origin/main`.
- **Steps**:
  1. Add the `in-progress` label to issue #4891 before the branch exists (RV-55). Run `gh issue edit 4891 -R jmorrison-juniper/MistHelper --add-label in-progress`.
  2. Create a worktree outside the repository path (RV-56). Run `git worktree add ..\MistHelper-fix-4891 -b fix/4891-dependabot-mando-ignore origin/main`.
  3. Rebase the committed branch onto `origin/main`. Rerun each local gate that the rebase affects.
  4. Push the branch with `git push -u origin fix/4891-dependabot-mando-ignore`. Do not use force push. The branch belongs to this change only, so RV-54 does not apply to it.
  5. Open the pull request with `gh pr create -R jmorrison-juniper/MistHelper --base main --head fix/4891-dependabot-mando-ignore --title "fix(ci): ignore mando minor updates that radon 6.0.1 blocks"`. Pass the body with `--body`. The body names `Closes #4891` (RV-57). It lists the changed files and the local gate results. It states that Principle IV steps 10 to 12 do not trigger. It states that PR #4888 stays open.
  6. Add the labels `bug` and `ci`. Store the pull request number in `$FIX_PR`.
- **Acceptance**: The pull request targets `main`. Its title uses the Conventional Commit form. Its body contains `Closes #4891`. Its changed files match the file change map in `plan.md`.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py` (run again on the pushed tree before the pull request opens)
- **Status**: open

### T-REMOTE-CI Watch the required checks

- **Requirements**: FR-008, SC-001, SC-002
- **Command**: `gh pr checks $FIX_PR -R jmorrison-juniper/MistHelper --watch`
- **Acceptance**: The Ruff (lint) check reports success, and its step 5 and step 6 succeed (SC-001). The Dependency lock and exports check reports success (SC-002). Each pytest coverage shard reports success. The Conventional Commits PR title check reports success. The CodeQL check reports success.
- **If a check fails**: Record the failure on issue #4891 and stop. Do not change the pins to hide the failure.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py` (the local output is attached to the pull request)
- **Status**: open

### T-MERGE Enable auto-merge after authorization and check the merged main

- **Requirements**: FR-007, SC-005
- **Preconditions**: T-REMOTE-CI passes. The orchestrator authorizes the merge.
- **Steps**:
  1. Add the `auto-merge` label to the fix pull request. Run `gh pr edit $FIX_PR -R jmorrison-juniper/MistHelper --add-label auto-merge`. Add it only after each check shows green (RV-58).
  2. After the merge, confirm that the merge commit on `main` shows the Ruff (lint) check as success.
  3. Confirm that issue #4891 is closed by the `Closes #4891` line (RV-57).
  4. Record the state of PR #4888 on issue #4891. This step only observes the state. Do not close PR #4888, comment on it, or push to its branch (RV-22, RV-54).
  5. Remove the worktree with `git worktree remove ..\MistHelper-fix-4891`. Remove the local branch with `git branch -D fix/4891-dependabot-mando-ignore`.
- Caution: The `-D` flag deletes the branch even when Git cannot see it as merged. Run it only after the squash merge shows MERGED.
- **Acceptance**: The fix pull request state is MERGED. Issue #4891 is CLOSED. The state of PR #4888 is recorded, and PR #4888 is not changed by this change. The worktree and the local branch are removed.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py` on the updated `main` checkout
- **Status**: open

## Dependencies and execution order

- T001 and T002 can run in parallel. T001 makes no edit.
- T003 depends on T002. The guard cases must exist before the entry.
- T004 and T005 are `[P]` tasks. Each one runs in parallel with the other and with T003.
- T-LOCAL-GATES depends on T002, T003, T004, and T005.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on the orchestrator authorization.

## Requirement coverage

| Requirement | Tasks |
| --- | --- |
| FR-001 | T001 |
| FR-002 | T002, T003 |
| FR-003 | T002, T003 |
| FR-004 | T002, T003 |
| FR-005 | T004 |
| FR-006 | T005 |
| FR-007 | T001, T-PR, T-MERGE |
| FR-008 | T-LOCAL-GATES, T-PR, T-REMOTE-CI |
| FR-009 | T002, T-LOCAL-GATES |

Task count: 9.
