# Tasks: Hold mando below 0.8 for the mypy gate

**Input**: Records `spec.md`, `plan.md`, and `design/research.md` in `specs/numbered/0/0/1/2/4/0/3/3/4893-mando-radon-pin/`.

**Format**: Each task names its requirement IDs, exact repository paths, acceptance statement, one verification command from the local gates table, and status. `[P]` marks a task that is safe in parallel. Status values are `open`, `verified-present`, `partial`, and `absent`.

**Verification row references** point to the Local gates table in `.github/copilot-instructions.md` (research.md, RC-36, header line 55). Row lines: Lint 58, Format 59, Types 60, Tests 61, Full tests 62, Test quality 65, Security lint 67, Symbols 73, STE 74.

## Phase 1: Evidence and pin set

### T001 Confirm the failing check and rule

- **Requirements**: FR-003
- **Files**: `.github/workflows/ci.yml` lines 232-237 (read only, RC-01, RC-02). Also the run 45064243269 log for job 137338084785.
- **Acceptance**: The `mypy (strict)` log shows `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`. Step `Run mypy` shows `skipped`.
- **Verification**: Types row, `python -m mypy $MYPY_PATHS --config-file pyproject.toml`, expected `Success`, after T009 and T-LOCAL-GATES
- **Status**: verified-present

### T002 [P] Confirm the pin set on main

- **Requirements**: FR-001
- **Files**: `requirements-dev.txt` lines 179 and 365 (RC-09, RC-11). `uv.lock` lines 1301 and 2432 (RC-23, RC-24). `pyproject.toml` line 118 (RC-17).
- **Acceptance**: `main` pins `mando==0.7.1` and `radon==6.0.1`. `uv.lock` lists both, and it lists `mando` as a radon dependency.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_dependency_export.py`, expected all tests pass
- **Status**: verified-present

## Phase 2: Control and tests

### T003 [P] Add the Dependabot ignore entry

- **Requirements**: FR-002
- **Files**: `.github/dependabot.yml`, insert after line 11 inside the pip block (RC-25, RC-26)
- **Acceptance**: The pip block holds `ignore:`, then `dependency-name: "mando"`, then `update-types: ["version-update:semver-minor", "version-update:semver-major"]`. A YAML comment gives the radon reason. The npm block and the other blocks stay unchanged.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_dependency_export.py`, expected all tests pass
- **Status**: absent

### T004 Add the guard tests and helpers

- **Requirements**: FR-001, FR-002
- **Depends on**: T003
- **Files**: `tests/guardrails/test_dependency_export.py` (RC-28, RC-29). Add class `DependencyPinPolicy` and class `TestDependencyPinPolicy`. Update the module docstring.
- **Acceptance**: Four tests pass. The real pin satisfies the radon requirement. A fixture pin of `mando==0.8.2` fails. The real Dependabot config holds minor updates. A fixture config without the entry fails. Each helper keeps five parameters or fewer, five blocks or fewer, and 25 lines or fewer. Each executable line has an inline comment. Each file read logs `info` before and `debug` after. All messages use ASCII.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_dependency_export.py`, expected all tests pass
- **Status**: absent

### T005 [P] Add the changelog fragment

- **Requirements**: FR-004
- **Files**: `changelog.d/issue-4893-mando-radon-pin.md` (rule RC-37 and RC-46. Guard RC-31.)
- **Acceptance**: The file has one `### Fixed` heading and one bullet. The bullet names issue #4893 and has 25 words or fewer. The file follows the naming pattern in `changelog.d/README.md` (RC-32).
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`, expected all tests pass
- **Status**: absent

## Phase 3: Local gates on the changed files

### T006 Lint the changed Python file

- **Requirements**: FR-005
- **Depends on**: T004
- **Files**: `tests/guardrails/test_dependency_export.py`
- **Acceptance**: Ruff reports no violation.
- **Verification**: Lint row, `python -m ruff check .`, expected `All checks passed`
- **Status**: open

### T007 Format the changed Python file

- **Requirements**: FR-005
- **Depends on**: T004
- **Files**: `tests/guardrails/test_dependency_export.py`
- **Acceptance**: Black reports that no file needs a change.
- **Verification**: Format row, `python -m black --check .`, expected no file needs a change
- **Status**: open

### T008 [P] Grade the Markdown files

- **Requirements**: FR-005
- **Files**: `specs/numbered/0/0/1/2/4/0/3/3/4893-mando-radon-pin/` (each Markdown file), `changelog.d/issue-4893-mando-radon-pin.md`
- **Acceptance**: Each file scores 80 or above.
- **Verification**: STE row, `ste-linter --config .ste-linter.toml --min-score 80` on each record Markdown file and the changelog fragment, expected each file scores 80 or above
- **Status**: open

### T009 [P] Confirm the install and the type check

- **Requirements**: FR-001, FR-003
- **Files**: `requirements-dev.txt` (read only, unchanged). The install command is in `documentation/development-setup.md` line 137 (RC-51).
- **Acceptance**: `python -m pip install -r requirements.txt -r requirements-dev.txt` completes with no resolution error. The type check then reports no errors.
- **Verification**: Types row, `python -m mypy $MYPY_PATHS --config-file pyproject.toml`, expected `Success`
- **Status**: open

### T010 Run the test quality ratchet

- **Requirements**: FR-005
- **Depends on**: T004
- **Files**: `tests/guardrails/test_dependency_export.py`. Do not edit `.github/test-quality-baseline.json`.
- **Acceptance**: The analyzer prints `gate: 0 new findings vs baseline`.
- **Verification**: Test quality row, `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`, expected `gate: 0 new findings vs baseline`
- **Status**: open

## Phase 4: Final gates, pull request, remote CI, and merge

### T-LOCAL-GATES Run each applicable local gate

- **Requirements**: FR-003, FR-005
- **Depends on**: T003, T004, T005, T009
- **Applicable gates and files**:
  - Lint, Format, Types, and Tests on `tests/guardrails/test_dependency_export.py` and `tests/guardrails/test_changelog_fragment_policy.py`.
  - Full tests. The second `pytest-chunks` command includes `tests\guardrails`.
  - Test quality on the changed test module.
  - Security lint with `bandit -c pyproject.toml -r tests\guardrails -q` (research.md, U-6).
  - Symbols with `symbol-diff --base origin/main tests/guardrails/test_dependency_export.py` (research.md, U-7).
  - STE on the record Markdown files and the changelog fragment.
- **Not applicable**: Compile, Dependency audit, Coverage, Safe sweep, Menu reference, Ops portal, and Ops platform cover paths that this change does not touch. Complexity, Docstrings, Code quality, and Dead code scan source paths only (RC-70, RC-71).
- **Acceptance**: Each applicable gate reports its expected result. The results go into the PR body.
- **Verification**: Full tests row, the two `pytest-chunks` commands in `.github/copilot-instructions.md` (line 62), expected one summary line for each shard
- **Status**: open

### T-PR Commit, push, and open the pull request

- **Requirements**: FR-004, FR-005
- **Depends on**: T-LOCAL-GATES
- **Steps**:
  1. Add `in-progress` to issue #4893. Add the type label `bug` and the scope labels `ci` and `tests` (AGENTS.md Git flow, RC-41).
  2. Create branch `fix/4893-mando-radon-pin` from `main` in a separate worktree. Do not run `git checkout` in a shared checkout.
  3. Add each changed file by explicit path. The file list is the change map in `plan.md`, plus this record folder.
  4. Commit with the message `fix(deps): keep mando below 0.8 for radon 6.0.1`. The body holds `Closes #4893` and the Co-authored-by trailer from the session instructions.
  5. Push the branch without force.
  6. Open the PR with the same title and the template at `.github/PULL_REQUEST_TEMPLATE.md` (RC-33). The body lists the gate results and the changed files.
  7. Rename the fragment to the pull request number form that `.github/copilot-instructions.md` line 451 names, in a follow-up commit.
- **Acceptance**: The PR title passes the Conventional Commits PR title check. The PR body holds `Closes #4893`. The branch holds no unrelated file.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_dependency_export.py`, expected all tests pass
- **Status**: open

### T-REMOTE-CI Watch the remote CI

- **Requirements**: FR-003
- **Depends on**: T-PR
- **Command**: `gh pr checks fix/4893-mando-radon-pin -R jmorrison-juniper/MistHelper --watch`
- **Acceptance**: Every job in the `Quality Gates` run reports success. The jobs `mypy (strict)`, `Dependency lock and exports`, `Radon (complexity)`, and `Test quality ratchet (gate)` report success. CodeQL reports success before the `auto-merge` label is added. If another job fails, record its cause and open its own issue. Do not merge.
- **Verification**: Types row on the same revision, with the remote `mypy (strict)` result as the acceptance evidence
- **Status**: open

### T-MERGE Merge the fix and close PR #4888

- **Requirements**: FR-002, FR-006
- **Depends on**: T-REMOTE-CI and orchestrator authorization
- **Steps**:
  1. Add the `auto-merge` label only after every check is green.
  2. Squash merge the PR. Warning: a commit pushed after the squash merge orphans the PR. Open a new issue for later changes.
  3. Run `gh run list -R jmorrison-juniper/MistHelper --workflow container-build.yml --branch main --limit 3`. Expect no run for the merged revision (RC-38).
  4. After the next weekly pip cycle, confirm that Dependabot opened no `mando` 0.8.x PR (SC-003).
  5. Comment on PR #4888. The comment names the merged PR and the record path. This is the preservation proof.
  6. Close PR #4888. Caution: deleting the Dependabot branch removes the only remote reference to its commit. Delete the branch after the close.
  7. Remove the worktree and the local branch after the merge (AGENTS.md Git flow, RC-41).
- **Acceptance**: PR #4888 shows state `CLOSED` with the closing comment. The fix PR shows state `MERGED`. No run starts for `container-build.yml` on the merged revision.
- **Verification**: Tests row, `python -m pytest tests/guardrails/test_dependency_export.py`, run on the merged `main` revision, expected all tests pass
- **Status**: open
