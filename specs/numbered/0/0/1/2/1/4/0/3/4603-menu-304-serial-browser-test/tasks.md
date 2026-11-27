# Tasks: Menu 304 serial number browser test

**Input**: Numeric record from `/specs/numbered/0/0/1/2/1/4/0/3/4603-menu-304-serial-browser-test/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, `design/contracts/`.

**Tests**: Required. The spec defines TC-1 (existing test, changed helper) and TC-2 (new negative test).

**Format**: `[ID] [P?] Title`. Each task lists requirements, files, acceptance, verification, and status. Status values: open, verified-present, partial, or absent.

## Phase 1: Evidence

### T001 Document the CI evidence

- **Requirements**: FR-001, FR-011
- **Files**: `design/research.md` (sections R2 and R7)
- **Acceptance**: The record names the test ID, the assertion, the run ID, the job ID, and the versions of each cited run.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py --collect-only -q` lists the test ID of TC-1.
- **Status**: verified-present. Evidence: `design/research.md` sections R2 and R7.

## Phase 2: Helper and negative test

### T002 Wait on the response and the selected title in the helper

- **Requirements**: FR-002, FR-003, FR-006, FR-007, FR-008, FR-009
- **Files**: `tests/e2e/web_portal/test_juniper_menus_browser.py`, function `select_menu` (lines 182 to 187 on main)
- **Acceptance**: The helper registers `page.expect_response` for the parameter path before the click. It requires HTTP 200. It waits until `#selectedOpTitle` reads `Menu` followed by the menu number. It then waits until the loading predicate holds. The fixed sleep at line 187 is removed. No module-level name changes.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -k test_menu_304_waits -q`
- **Status**: open

### T003 Name the failure with the status and the browser errors

- **Requirements**: FR-004, FR-005, FR-009
- **Depends on**: T002
- **Files**: `tests/e2e/web_portal/test_juniper_menus_browser.py`, function `select_menu` only
- **Acceptance**: A failed wait raises `AssertionError`. The message follows `design/contracts/selection-failure-message.md`. The page and console listeners register before the click and detach after the wait. The function stays at 25 lines or fewer.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -k test_menu_304 -q`
- **Status**: open

### T004 Add the negative test for a refused parameter request

- **Requirements**: FR-004, FR-009, FR-015
- **Depends on**: T003
- **Files**: `tests/e2e/web_portal/test_juniper_menus_browser.py`, new method `test_menu_304_names_a_refused_parameter_request` in class `TestTheJuniperMenusAreReadableInTheBrowser`
- **Acceptance**: The test routes `**/api/operations/parameters/304` with `page.route` and fulfills HTTP 503. It asserts that the `AssertionError` names the parameter path and `503`. The test passes only in that case. The method adds no module-level name.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -k test_menu_304_names -q`
- **Status**: open

## Phase 3: Changelog

### T005 Add the changelog fragment [P]

- **Requirements**: FR-012
- **Files**: `changelog.d/issue-4603-menu-304-serial-browser-test.md`
- **Acceptance**: One `###` heading names the change. One `Fixed` bullet names issue 4603 at its end. No index file is added. The file follows the rules in `changelog.d/README.md`.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

## Phase 4: Evidence matrix and conditional repair

### T006 Run the diagnostic matrix

- **Requirements**: FR-010, FR-011, SC-002, SC-003
- **Depends on**: T002, T003, T004
- **Files**: `design/research.md` (add a results section after R13)
- **Acceptance**: Combination D passes 20 of 20 runs. Combination A runs 20 times. Combinations B and C run 10 times each. The results record Python version, Dash version, pass count, and failure count. Each failure message from combination A is copied into `analysis.md`. Stop rule: when combination A passes 20 of 20, record the result and skip T007.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -k test_menu_304_waits -q`, repeated as described in `design/quickstart.md`, scenario 3.
- **Status**: open

### T007 Repair the production cause (conditional)

- **Requirements**: FR-013
- **Depends on**: T006
- **Trigger**: Combination A fails, and the failure message shows no parameter request or a page error. Decision D-7 defines the trigger.
- **Files**: `web_portal/static/js/operations.js`, and a regression case in `tests/e2e/web_portal/test_juniper_menus_browser.py`
- **Acceptance**: The repaired code passes combination A in 20 of 20 runs. TC-1 and TC-2 keep passing. Each changed line carries an inline comment. Each action carries a log line where the file uses logging.
- **Verification**: `python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py -q`
- **Status**: open. When the trigger does not occur, skip this task and record the reason in `analysis.md`.

## Final tasks

### T-LOCAL-GATES

- **Depends on**: T002, T003, T004, T005
- **Requirements**: FR-008, FR-012, FR-014, SC-005
- **Files**: `tests/e2e/web_portal/test_juniper_menus_browser.py`, `changelog.d/issue-4603-menu-304-serial-browser-test.md`
- **Acceptance**: Each applicable gate prints its expected result. The browser module passes 19 of 19 tests. Run the test quality gate after the local commit, because the gate reads the committed diff.
- **Applicable gates**:
  - Compile: `python -m py_compile MistHelper.py` (no output). Expected result from `.github/copilot-instructions.md` line 57.
  - Lint: `python -m ruff check .` (`All checks passed`). Line 58.
  - Format: `python -m black --check .` (no file needs a change). Line 59.
  - Tests: `python -m pytest tests/e2e/web_portal/test_juniper_menus_browser.py` (all pass). Line 61.
  - Test quality: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` (`gate: 0 new findings vs baseline`). Line 65 and the ratchet section at line 95.
  - Symbols: `symbol-diff --base origin/main tests/e2e/web_portal/test_juniper_menus_browser.py` (`no module-level name changed`, exit code 0). Line 73.
  - Shard guard: `python -m pytest tests/guardrails/test_e2e_shard_partition.py`.
  - Changelog guard: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`.
- **Not applicable**: Types (the `MYPY_PATHS` value on `ci.yml` line 93 excludes `tests/`). Complexity and security lint (no `src/` package change). Dead code and docstrings (no `src/`, `wsgi.py`, or `web_portal` Python change). Menu reference (no menu change). STE (no listed Markdown file changes). Safe sweep and coverage (no product code change).
- **Status**: open

### T-PR

- **Depends on**: T-LOCAL-GATES
- **Requirements**: FR-009, FR-012, SC-004
- **Files**: each changed file, and the record folder `specs/numbered/0/0/1/2/1/4/0/3/4603-menu-304-serial-browser-test/`
- **Acceptance**: The `in-progress` label is added to issue #4603 before the branch is created. The branch is `fix/4603-menu-304-serial-browser-test`. The commit subject is `test(e2e): prove the menu 304 selection before the control check`. The commit body contains `Closes #4603` and ends with the Copilot co-author trailer. The pull request title equals the commit subject. The pull request body lists each gate result and the matrix counts.
- **Verification**: `python -m py_compile MistHelper.py` (no output), run before the push.
- **Status**: open

### T-REMOTE-CI

- **Depends on**: T-PR
- **Requirements**: SC-004
- **Acceptance**: The web-portal E2E job on the pull request head is green. The first main run after merge shows the web-portal E2E job green. A red job stops T-MERGE and sends the work back to T002 to T004.
- **Verification**: `gh pr checks --watch` for the pull request branch. GitHub runs this check, so the local gates table has no equivalent command.
- **Status**: open

### T-MERGE

- **Depends on**: T-REMOTE-CI, and the orchestrator authorizes the merge
- **Requirements**: SC-004
- **Acceptance**: The `auto-merge` label is added only after each required check is green, and only after the orchestrator authorizes the merge. The squash merge creates one commit on main. The branch and the worktree are removed after the merge.
- **Verification**: `gh pr view --json state,mergedAt` for the pull request branch reports `MERGED`. GitHub reports this state, so the local gates table has no equivalent command.
- **Status**: open
