# Tasks: Dash pytest plugin marker warning

**Input**: Numeric record at `specs/numbered/0/0/1/2/3/3/0/1/4826-dash-pytest-hook-warning/`. Read `spec.md` and `plan.md` first.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`.

**Tests**: Required. FR-001 to FR-004 need the policy tests and the documentation test. The gates in T-LOCAL-GATES run each applicable check.

**Organization**: Tasks group by delivery stage. The upstream dependency blocks user story 3, so stage order replaces story order.

## Format

- `[P]` means the task is safe in parallel with other `[P]` tasks.
- Each task names its requirement IDs, exact paths, acceptance statement, and one verification command.
- Each status is one of: open, verified-present, partial, or absent.
- A remote check ID such as RC-59 points to the table in `design/research.md`.
- Tasks that change code name a command from the local gates table. Tasks that only read remote state name a read command, because no local gate covers a remote read.

## Phase 1: Verification

### T001 [P] Verify branch preservation

- **Requirements**: FR-007
- **Paths**: GitHub branch `fix/4826-dash-pytest-hooks` (read only)
- **Acceptance**: The branch exists at commit `725510a3237623e6c5a0653aea14263f4e51a94e`.
- **Verification**: `gh api repos/jmorrison-juniper/MistHelper/branches/fix/4826-dash-pytest-hooks --jq .commit.sha`
- **Status**: verified-present (RC-59)

### T002 [P] Verify no open pull request overlaps the interim files

- **Requirements**: FR-005
- **Paths**: Open pull requests (read only), `tests/contract/test_pytest_coverage_gate.py`, `documentation/development-setup.md`
- **Acceptance**: No open pull request lists either interim path. Pull request #4888 touches `requirements-dev.txt` (RC-63).
- **Verification**: `gh pr list --state open --json number,headRefName,files`
- **Status**: verified-present (RC-63)

### T003 [P] Verify the warning source and the installed pins

- **Requirements**: FR-001
- **Paths**: `.venv\Lib\site-packages\dash\testing\plugin.py`, `requirements.txt`, `requirements-dev.txt`
- **Acceptance**: Plugin line 104 holds `@pytest.mark.tryfirst`. `requirements.txt` line 45 pins `dash==4.5.1`. `requirements-dev.txt` pins `dash==4.5.1` at line 76 and `pytest==9.2.0` at line 325.
- **Verification**: `Select-String -LiteralPath .venv\Lib\site-packages\dash\testing\plugin.py -Pattern tryfirst`
- **Status**: verified-present (RC-43, RC-09, RC-10, RC-11)

## Phase 2: Interim change

### T004 Add the policy check and the policy tests

- **Requirements**: FR-001, FR-002, FR-003
- **Paths**: modify `tests/contract/test_pytest_coverage_gate.py`
- **Acceptance**: The module adds `import tomllib` and two path constants. Class `DashPytestPluginPolicy` holds three methods. Class `TestDashPytestPluginPolicy` holds five test functions. Those five functions collect six cases. Each executable line has an inline comment. The policy check logs before and after each file read. The module adds no new file.
- **Verification**: `python -m pytest tests/contract/test_pytest_coverage_gate.py -q --no-cov -k DashPytestPluginPolicy` prints `6 passed`.
- **Status**: absent

### T005 [P] Add the known-warning section

- **Requirements**: FR-004
- **Paths**: modify `documentation/development-setup.md`. Insert the section after the paragraph that starts with `tests/conftest.py also checks this` (RC-31) and before `## Where the code lives`.
- **Acceptance**: The section names PytestRemovedIn10Warning, issue #4826, and Dash 4.5.1. It states the upstream state. It gives a Caution statement for `-p no:dash` and for warning filters. It names the upgrade trigger and the warning gate command. The policy test `test_development_setup_names_warning_cause_and_trigger` passes. Each sentence has 25 words or fewer and no semicolon.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation\development-setup.md` scores 80 or above.
- **Status**: absent

### T006 [P] Copy the record into the repository route

- **Requirements**: Delivery pipeline (constitution Principle IV). No functional requirement.
- **Paths**: add `specs/numbered/0/0/1/2/3/3/0/1/4826-dash-pytest-hook-warning/` from the draft folder
- **Acceptance**: The folder holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` with `research.md`, `data-model.md`, `quickstart.md`, and `checklists/requirements.md`. The folder root holds five children or fewer.
- **Verification**: `python -m pytest tests/guardrails/test_process_folder_structure.py -q --no-cov` prints no failure.
- **Status**: absent

### T007 Confirm the interim diff has no manifest change

- **Requirements**: FR-005, SC-005
- **Paths**: Git diff of the branch (read only)
- **Acceptance**: The diff lists only `tests/contract/test_pytest_coverage_gate.py`, `documentation/development-setup.md`, and the record folder. It lists no `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, or `uv.lock`.
- **Verification**: `git diff --name-only $(git merge-base origin/main HEAD) HEAD`
- **Status**: absent. Run after T004, T005, and T006.

## Phase 3: Deferred upgrade and cleanup

### T008 [P] Watch the upstream Dash release

- **Requirements**: FR-006 (upgrade trigger)
- **Paths**: GitHub release and contents API for `plotly/dash` (read only). PyPI project page for `dash` (read only).
- **Acceptance**: The check records the latest release tag. It also records whether `dash/testing/plugin.py` at that tag uses `pytest.hookimpl` at line 104. The check posts its result as a new comment on issue #4826. It does not edit an earlier comment.
- **Verification**: `gh api repos/plotly/dash/releases/latest --jq .tag_name`, then read the plugin file at that tag as described in `design/quickstart.md`.
- **Status**: open. Release v4.5.1 still holds the old marker (RC-48, RC-53). The upstream `dev` branch holds the fix (RC-49).

### T009 Upgrade Dash after a release contains the fix

- **Requirements**: FR-005, FR-006
- **Paths**: modify `requirements.txt` (line 45), `requirements-dev.txt` (line 76), `uv.lock` (Dash entries), and `documentation/development-setup.md` (known-warning section)
- **Acceptance**: Both pins name the new release. The warning gate exits with code 0. The integration journey test passes. The known-warning section names the new state. The change adds no suppression entry.
- **Verification**: `python -m pytest tests/unit/refactors/test_app_context_session_state.py -q --no-cov -W error::pytest.PytestRemovedIn10Warning` exits with code 0.
- **Status**: absent. Blocked until a Dash release contains the fix. Also wait for the manifest owner handover and for pull request #4888 (RC-63).

### T010 Decide the branch disposition after the replacement merges

- **Requirements**: FR-007
- **Paths**: GitHub branch `fix/4826-dash-pytest-hooks` and closed PR #4831 (read and comment only)
- **Acceptance**: A comment on issue #4826 records a preservation proof. The proof names the merged replacement pull request and each interim file that the proof examined on `main`. The branch is removed only after that comment exists.
- **Verification**: `gh api repos/jmorrison-juniper/MistHelper/branches/fix/4826-dash-pytest-hooks --jq .commit.sha` before any removal.
- **Status**: absent. Depends on T-MERGE.

Caution: Deleting the branch removes its name. The pull request reference `refs/pull/4831/head` keeps the commits.

### T011 Move the policy check to a compliant package

- **Requirements**: FR-001 (the rule stays in force after the move)
- **Paths**: move `DashPytestPluginPolicy` and `TestDashPytestPluginPolicy` to a new module in a compliant nested package under `tests/`
- **Acceptance**: The moved tests collect the same six cases and pass. Each directory on the new path holds five children or fewer.
- **Verification**: `python -m pytest <new module path> -q --no-cov -k DashPytestPluginPolicy` prints `6 passed`.
- **Status**: absent. Depends on T-MERGE.

## Phase 4: Delivery

### T-LOCAL-GATES Run each applicable local gate

- **Requirements**: FR-001 to FR-004, SC-001 to SC-006
- **Paths**: the changed files and the record folder
- **Acceptance**: Each applicable gate exits with code 0 and prints the expected result. Each non-applicable gate has a reason in the pull request body. The warning evidence run records the warning line in the pull request. Any failure appears in the pull request with its full output.
- **Verification**: Run the commands in the table below.
- **Status**: absent

| Gate | Command | Expected result |
| - | - | - |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Policy tests | `python -m pytest tests/contract/test_pytest_coverage_gate.py -q --no-cov` | All tests pass |
| Process records | `python -m pytest tests/guardrails/test_process_folder_structure.py -q --no-cov` | All tests pass |
| Spec route | `python -m pytest tests/guardrails/test_spec_route_contract.py -q --no-cov` | All tests pass with PowerShell 7 installed |
| Journey test | `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py -q --no-cov` | All tests pass |
| Warning evidence | `python -m pytest tests/unit/refactors/test_app_context_session_state.py -q --no-cov` | Exit code 0, with PytestRemovedIn10Warning in the summary |
| Complexity | `radon cc tests\contract\test_pytest_coverage_gate.py -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 |
| Symbols | `symbol-diff --base origin/main tests\contract\test_pytest_coverage_gate.py` | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 documentation\development-setup.md` | Score 80 or above |
| Test quality | Preflight, then `test-quality-analyzer --gate` with the options in `.github/copilot-instructions.md` | `gate: 0 new findings vs baseline` |

Not applicable with reason:

- Compile: no `MistHelper.py` change.
- Safe sweep: no product change.
- Mypy, vulture, pydocstyle, and interrogate: the changed file lies outside their paths.
- Bandit: no product package change.
- Pip-audit: no manifest change.
- Pylint: no `src/` change.
- Coverage: no `src/` change. CI runs the coverage shards.
- Menu reference, ops portal, and ops platform: not affected by the change.

### T-PR Commit and open the pull request

- **Requirements**: FR-008, FR-005, FR-007
- **Paths**: the changed files and the record folder on branch `chore/4826-dash-pytest-hook-warning`
- **Acceptance**: The commit subject is `test(tests): keep the Dash pytest warning visible`. The commit message ends with the `Co-authored-by: Copilot App` trailer. The pull request title uses the same subject. The pull request body contains `Refs #4826` and does not contain `Closes #4826`. The body gives the reason for `Refs` (decision D-4). The body lists each gate result and each non-applicable gate with its reason.
- **Verification**: `gh pr view <number> --json body --jq .body` shows `Refs #4826` and no `Closes #4826`.
- **Status**: absent. Deviates from the AGENTS default because the owner keeps the issue open (D-4).

### T-REMOTE-CI Watch the remote checks

- **Requirements**: SC-001, FR-008
- **Paths**: remote checks on the pull request (read only)
- **Acceptance**: Each required check shows success. The required checks include the Conventional Commits title check, the STE compliance check, and the pytest gate.
- **Verification**: `gh pr checks <number> --watch`
- **Status**: absent. Depends on T-PR.

### T-MERGE Squash merge after authorization

- **Requirements**: FR-008
- **Paths**: the pull request and its branch
- **Acceptance**: The orchestrator authorizes the merge. The `auto-merge` label is added only after each check passes. The squash merge creates one commit on `main`. The new branch is removed after the merge. Branch `fix/4826-dash-pytest-hooks` remains (T010).
- **Verification**: `gh pr view <number> --json state --jq .state` prints `MERGED`.
- **Status**: absent. Depends on T-REMOTE-CI and the orchestrator authorization.

Warning: Do not push a commit after the squash merge. The commit becomes an orphan that nobody merges. Open a new issue and branch from `main` instead.

## Dependencies and Execution Order

- T001, T002, and T003 run in parallel.
- T004, T005, and T006 run in parallel after Phase 1.
- T007 runs after T004, T005, and T006.
- T-LOCAL-GATES runs after T007.
- T-PR runs after T-LOCAL-GATES. T-REMOTE-CI runs after T-PR. T-MERGE runs after T-REMOTE-CI and the orchestrator authorization.
- T008 runs at each dependency review. It has no prerequisite.
- T009 runs after T008, a manifest owner handover, and the merge or rebase after pull request #4888.
- T010 and T011 run after T-MERGE.

## Guard Rules

- Each policy test fails for one forbidden entry. Each failure names the entry.
- Each gate prints the count of files or cases it examined.
- A gate that cannot read its input fails. It does not skip.
