# Tasks: MSP Profile Lookup Failure

**Input**: Design documents in `specs/numbered/0/0/1/2/2/3/2/3/4713-msp-profile-lookup-failure/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`

**Tests**: The specification requires tests. Write each test task before its implementation task, and see it fail first. Use mocked SDK responses only. Use no API token and no container.

**Status values**: `open` means not started. `absent` means the behavior is not on `main` yet. `verified-present` means the behavior is on `main` and needs no change. `partial` means part of the behavior is on `main`.

## Format

- **[P]**: The task can run in parallel with other [P] tasks, because it edits a different file.
- **Format**: Each code task names a verification command from the Local gates table or a test command from the same repository. Each process task names its process check.
- **Requirements**: The FR and SC IDs from `spec.md`.
- **Files**: The exact repository paths.
- **Acceptance**: The observable result.
- **Verification**: The command or the check.
- **Status**: One status value from the list above.

## Dependencies

- T001 gates T005 and T007.
- T004 runs before T006. T006 runs before T007.
- T005 runs before T007.
- T003, T006, T007, and T008 finish before T009. T006 and T007 finish before T010.
- T011 runs before T-PR, so the pull request names the follow-up issues.

## Phase 1: Coordination and Setup

### T001 Gate: release of the #4708 file hold

- **Requirements**: FR-014
- **Files**: `src/mist/resources/inventory/org_device_inventory_msp.py`, `tests/unit/inventory/test_org_device_inventory_msp.py`
- **Acceptance**: A comment on #4708 or on #4713 names both files and states that the owner releases them. T005 and T007 start only after that comment exists.
- **Verification**: `gh issue view 4708 -R jmorrison-juniper/MistHelper --json comments` shows the release comment. If it does not, stop before T005.
- **Status**: open

### T002 Claim the issue and create the branch

- **Requirements**: Process, `AGENTS.md` Git flow
- **Files**: None
- **Acceptance**: #4713 carries `in-progress`, `bug`, and `MistHelper.py`. The branch `fix/4713-msp-profile-lookup-failure` starts from `origin/main` in a new worktree. The worktree has no unrelated change.
- **Verification**: `git -C <worktree> rev-parse --abbrev-ref HEAD` prints `fix/4713-msp-profile-lookup-failure`. `git -C <worktree> merge-base --is-ancestor origin/main HEAD` exits with code 0.
- **Status**: open

## Phase 2: Tests First

### T003 [P] Changelog fragment

- **Requirements**: FR-017
- **Files**: `changelog.d/issue-4713-msp-profile-lookup-failure.md`
- **Acceptance**: The file holds one `###` heading and one bullet that starts with `- **Fixed**:`. The bullet names Issue #4713. The change does not edit `CHANGELOG.md`.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` passes (RC-89). The guard reads the fragment directory.
- **Status**: absent

### T004 Detector tests

- **Requirements**: FR-001 to FR-007, FR-013, FR-016
- **Files**: `tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py`
- **Acceptance**: Five existing fixtures add `status_code=200`. They sit at lines 404, 412, 446, 452, and 489. Add the 13 new cases below. Each new test imports `lookup_msp_privileges` or `MspPrivilegeLookup` inside its body, so the rest of the module collects before T006.
- **New cases**:
  1. `test_lookup_fails_on_refused_status`, parameters 401, 403, 429, and 503 (4 cases). Asserts: `succeeded` is false, `grants` is empty, and the warning names the status.
  2. `test_lookup_fails_when_status_missing` (1 case).
  3. `test_lookup_fails_when_privileges_not_a_list`, parameters missing, null, and text (3 cases).
  4. `test_lookup_fails_when_body_is_not_object` (1 case).
  5. `test_lookup_succeeds_with_zero_grants` (1 case). Asserts a valid profile with an empty grant list.
  6. `test_lookup_fails_on_exception_and_logs_class_only` (1 case). Asserts that the exception text is absent from the captured log.
  7. `test_lookup_fails_without_session_and_makes_no_call` (1 case).
  8. `test_detect_returns_empty_list_on_refused_status` (1 case). Asserts an empty list and one warning that names the status.
- **Verification**: `python -m pytest tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py -q`. Before T006, cases 1 to 8 fail. After T006, every case passes.
- **Status**: absent

### T005 Dispatch tests

- **Requirements**: FR-008 to FR-012, FR-016
- **Files**: `tests/unit/inventory/test_org_device_inventory_msp.py`
- **Acceptance**: Update `test_dispatch_without_privileges_calls_single_directly` (line 123). It patches `lookup_msp_privileges` with a valid zero-grant result and expects one single-organization callback call. Add four cases:
  1. `test_dispatch_stops_when_lookup_fails`. The patched lookup fails. Expects no callback and the failure message.
  2. `test_dispatch_stops_when_lookup_finds_grants`. The patched lookup returns one MSP grant. Expects no callback and the restart message.
  3. `test_dispatch_with_cached_grants_makes_no_lookup`. A regression guard. The patched lookup is not called. It passes before and after the change.
  4. `test_dispatch_without_session_makes_no_lookup`. The session is None. The real lookup returns a failed result without an API call. Expects no callback.
- **Verification**: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py -q -k dispatch`. Before T007, cases 1, 2, and 4 fail. Case 3 passes before and after.
- **Status**: absent

## Phase 3: Implementation

### T006 Detector implementation

- **Requirements**: FR-001 to FR-007, FR-013
- **Files**: `src/foundation/support/refactors/msp_privilege_detection.py`
- **Acceptance**: The module adds the frozen dataclass `MspPrivilegeLookup`. `lookup_msp_privileges` implements `design/contracts/profile-lookup.md`. `_msp_fetch_user_data` checks the status and the `privileges` list. `detect_msp_privileges` returns the grants of the lookup result. The module and function docstrings name both entry points. The except block logs the exception class name only, through the module logger. Each touched line has an inline comment. Each new or touched function keeps 25 lines or fewer.
- **Verification**: `python -m pytest tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py -q` passes.
- **Status**: absent

### T007 Dispatch implementation

- **Requirements**: FR-008 to FR-013
- **Files**: `src/mist/resources/inventory/org_device_inventory_msp.py`
- **Acceptance**: The module imports `lookup_msp_privileges`. It adds `_LOOKUP_FAILED_MSG` and `_RESTART_FOR_GRANTS_MSG` with the exact text in `design/contracts/menu-13-dispatch.md`. It adds `_confirm_no_msp_access`. `dispatch` calls the helper only when the grant list is empty. `dispatch` calls `single_org_fn` only after confirmed absence. No other function changes.
- **Verification**: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py -q` passes.
- **Status**: absent

### T008 Documentation

- **Requirements**: FR-017
- **Files**: `documentation/wiki/MSP-Support.md`, `documentation/operator-guide.md`
- **Acceptance**: The detection bullet at line 116 of `MSP-Support.md` gains one sentence. One paragraph follows line 594 of `operator-guide.md`. The change makes no heading change in `operator-guide.md`. The new text uses no semicolon, no contraction, and no sentence longer than 25 words.
- **Verification**: `python -m pytest tests/guardrails/test_hardware_shell_lock_docs.py -q` passes (RC-34). Read the two new passages against the writing rules in `AGENTS.md`.
- **Status**: absent

## Phase 4: Review and Coordination

### T009 [P] Changed-file manifest

- **Requirements**: FR-014, FR-015, SC-005
- **Files**: The seven paths in the File Change Map of `plan.md`
- **Acceptance**: The branch changes exactly seven paths. Six have status `M`, and one has status `A`. No file under `src/` is new.
- **Verification**: `git -C <worktree> diff --name-status origin/main` lists exactly seven paths.
- **Status**: open

### T010 [P] Redaction review

- **Requirements**: FR-013
- **Files**: `src/foundation/support/refactors/msp_privilege_detection.py`, `src/mist/resources/inventory/org_device_inventory_msp.py`
- **Acceptance**: No new log line or message uses a response body, an exception message, a token, a password, or a session object as an argument.
- **Verification**: `git -C <worktree> diff origin/main -- src` shows no new `%s` argument named `e`, `error`, `body`, `data`, `session`, or `apisession`. Case 6 of T004 passes.
- **Status**: open

### T011 Follow-up issues (orchestrator action)

- **Requirements**: Scope, `spec.md` Out of Scope
- **Files**: None
- **Acceptance**: Two follow-up issues exist, and #4713 links them. Issue (a) carries the lookup result through the `MainEntrypoint` context and the startup, restore, and login messages. Issue (b) covers the `OrgConfigExporter` and the firmware cache, which read an empty grant list as no access.
- **Verification**: `gh issue list -R jmorrison-juniper/MistHelper --search "4713 in:body" --json number,title` lists both issues.
- **Status**: open

## Phase 5: Final Tasks

### T-LOCAL-GATES Run the local gates

- **Requirements**: FR-016, SC-002, SC-004
- **Files**: All changed files
- **Acceptance**: Each gate that applies to the changed files passes. A gate that does not apply names its reason in the pull request body. The safe sweep output records the menu 13 line.
- **Verification**: Run each command below in the worktree. Record the output line of each gate.
  1. Compile: `python -m py_compile MistHelper.py`, then `python -m py_compile src/foundation/support/refactors/msp_privilege_detection.py src/mist/resources/inventory/org_device_inventory_msp.py`. Expected: no output.
  2. Lint: `python -m ruff check .`. Expected: `All checks passed`.
  3. Format: `python -m black --check .`. Expected: no file needs a change.
  4. Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. Expected: `Success`. The paths come from `MYPY_PATHS` (RC-73).
  5. Tests: `python -m pytest tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py tests/unit/inventory/test_org_device_inventory_msp.py tests/unit/export/test_msp_inventory_exporter.py tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py tests/unit/marvis/mist/access/auth/test_interactive_session.py tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py -q`. Expected: all pass. These modules read the detector or the grant list.
  6. Full tests: the two `pytest-chunks` commands in the Local gates section of `.github/copilot-instructions.md`. Expected: one summary line for each shard, with no failure.
  7. Safe sweep: `python MistHelper.py --test`. Expected: each safe operation completes. Record the menu 13 output in the pull request body.
  8. Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`. Expected: 80 percent or above, combined as the CI shards combine it.
  9. Test quality: run the required input preflight, then the gate command in the Test quality ratchet section of `.github/copilot-instructions.md`. Expected: `gate: 0 new findings vs baseline`.
  10. Complexity: `radon cc src/foundation/support/refactors -j | complexity-gate --max 10` and `radon cc src/mist/resources/inventory -j | complexity-gate --max 10`. Expected: no block above complexity 10.
  11. Security lint: `bandit -c pyproject.toml -r src/foundation/support/refactors -q` and `bandit -c pyproject.toml -r src/mist/resources/inventory -q`. Expected: no finding.
  12. Dependency audit: not applicable. No requirements file changes.
  13. Code quality: `pylint src/ --fail-under=9.5`. Expected: score 9.5 or above.
  14. Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`. Expected: no finding. The paths come from `VULTURE_PATHS` (RC-74), and the confidence from `VULTURE_CONFIDENCE` (RC-77).
  15. Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v`. Expected: no violation, and coverage at 90 percent or above.
  16. Menu reference: `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`. Expected: no changed file after the run. If a file changes, commit the regenerated page in the same pull request.
  17. Symbols: `symbol-diff --base origin/main src/foundation/support/refactors/msp_privilege_detection.py` and `symbol-diff --base origin/main src/mist/resources/inventory/org_device_inventory_msp.py`. Expected: exit code 0. Record any added name in the output. No existing module-level name may change or disappear.
  18. STE: the STE command covers five listed files only. The two operator pages are not in that list. T008 reviews them by hand.
  19. Ops portal and Ops platform: not applicable. No file under `ops-portal/` or `mist-ops-platform/` changes.
- **Status**: open

### T-PR Commit and open the pull request

- **Requirements**: FR-017, Process
- **Files**: All changed files
- **Acceptance**: One commit has the subject `fix(msp): stop menu 13 after a refused profile lookup` and a body line `Closes #4713`. One pull request has the same title. Its body holds `Closes #4713`, the file list, each gate result from T-LOCAL-GATES, the redaction statement from T010, and the sentence `No container was started.` The pull request carries the labels `bug` and `MistHelper.py`. Stage files by explicit path only. The branch is rebased onto `origin/main`.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body,headRefName` shows the title and `Closes #4713`.
- **Status**: open

### T-REMOTE-CI Watch the remote checks

- **Requirements**: SC-004
- **Files**: None
- **Acceptance**: Every required check reports success on the latest commit. A failed job never counts as skipped. Read the job table of each failed run, and file an issue for each failure.
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch` reports success for each required check.
- **Status**: open

### T-MERGE Squash merge

- **Requirements**: Process
- **Files**: None
- **Acceptance**: The orchestrator authorizes the merge. The `auto-merge` label is added only after every check shows green. The pull request squashes into `main`. The branch is removed after the merge. Issue #4713 closes.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,mergedAt` shows `MERGED`. `gh issue view 4713 -R jmorrison-juniper/MistHelper --json state` shows `CLOSED`.
- Warning: A squash merge cannot be undone in place. A later fix needs a new issue, a new branch from `main`, and a new pull request.
- **Status**: open
