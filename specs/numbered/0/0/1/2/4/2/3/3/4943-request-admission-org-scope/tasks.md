# Tasks: Ship the preserved admission scope work

**Input**: Numeric record `specs/numbered/0/0/1/2/4/2/3/3/4943-request-admission-org-scope/`. Read `spec.md` and `plan.md` first.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`.

## Format and Rules

- **[P]**: The task touches files that no other open task touches, so it can run in parallel.
- **[US1]**, **[US2]**, **[US3]**: The user story of the task. Setup and final tasks carry no story tag.
- **Requirements**: The `FR-###` identifiers from `spec.md`.
- **Files**: Exact repository paths, forward slashes, relative to the repository root.
- **Acceptance**: The observable result that closes the task.
- **Verification**: One command. A file edit names one row of the local gates table in `.github/copilot-instructions.md`. A process task names one read-only command, because that table covers file content only.
- **Status**: `open`, `verified-present`, `partial`, or `absent`. The status reflects the preservation branch and `main` at the time of this record.

The test names in this file match the names in `spec.md` and `plan.md`.

## Phase 1: Verify inputs and sequencing

### T001 [P] Verify the five preserved blobs against the local files

- **Requirements**: FR-001
- **Files**: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`, `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- **Acceptance**: Each local file hashes to the blob that commit `5213149d63be00d4c47c0fe8194d4cbf0eca1f1f` lists. The research table lists the five rows.
- **Verification**: `git --no-pager --no-optional-locks -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object --no-filters` followed by each path in Files. This process task uses a read-only command.
- **Status**: verified-present

### T002 Confirm the PR #4208 gate before any edit

- **Requirements**: FR-002
- **Files**: `src/interfaces/wan_performance/collection/request_admission.py` and `tests/unit/wan_performance/test_request_admission.py` on the head of PR #4208
- **Acceptance**: PR #4208 is closed or merged. Its head no longer changes `request_admission.py` or the admission test. Otherwise the task stays open, and no later task starts.
- **Verification**: `gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,mergedAt,files`. This process task uses a read-only command.
- **Status**: open

### T003 Create the worktree and the branch from main

- **Requirements**: FR-001
- **Files**: None. The task changes git metadata only.
- **Acceptance**: The worktree `../MistHelper-request-admission-org-scope` holds branch `fix/4943-request-admission-org-scope`, based on the `main` commit that T002 records.
- **Verification**: `git -C ../MistHelper-request-admission-org-scope rev-parse --abbrev-ref HEAD` prints `fix/4943-request-admission-org-scope`.
- **Status**: open

### T004 Commit the record as the first commit

- **Requirements**: FR-029
- **Files**: `specs/numbered/0/0/1/2/4/2/3/3/4943-request-admission-org-scope/` (the record folder)
- **Acceptance**: The first commit changes only paths under the record folder. The commit subject follows Conventional Commits.
- **Verification**: `git -C ../MistHelper-request-admission-org-scope show --stat --format=%s HEAD`. This process task uses a read-only command.
- **Status**: open

## Phase 2: Tests first

### T005 [US1] Write the admission tests with the branch names

- **Requirements**: FR-006, FR-007, FR-008, FR-013, FR-022, FR-024
- **Files**: `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- **Acceptance**: Line 141 tests the traceback type with `isinstance`. The file holds four new tests: `test_nested_organization_scope_restores_outer_value`, `test_organization_scope_resets_after_exception`, `test_organization_scope_rejects_empty_identifier`, and `test_console_renderer_output_has_no_ansi_on_non_terminal`. The new tests use the branch names `organization_scope` and `RequestLedger`.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- **Status**: partial. The branch holds `test_site_request_uses_the_scoped_organization`, `test_organization_scope_ends_with_its_block`, `test_credential_never_appears_in_exception_locals`, and `test_console_renderer_hides_frame_locals`. Line 141 holds `assert frame is not None`.

### T006 [US3] Write the client tests with the branch names

- **Requirements**: FR-018, FR-020, FR-024
- **Files**: `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`
- **Acceptance**: The file holds `test_transport_failure_keeps_the_client_error_line`, which expects one ERROR record from the client logger and no ERROR record from `mistapi`. It also holds `test_msp_listing_logs_info_before_and_debug_after`, which expects an INFO record before the MSP call and a DEBUG record after it.
- **Verification**: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`
- **Status**: partial. The branch holds `test_virtual_chassis_read_is_admitted_under_its_organization` and `test_failed_msp_listing_logs_one_outcome_and_no_sdk_error_lines`. The two new tests are absent.

### T007 Run the red run on the branch code

- **Requirements**: FR-024
- **Files**: None changed. The task runs the tests from T005 and T006.
- **Acceptance**: `test_organization_scope_rejects_empty_identifier`, `test_console_renderer_output_has_no_ansi_on_non_terminal`, and `test_msp_listing_logs_info_before_and_debug_after` fail. The other new tests pass, because they guard behavior that the branch already has. The pull request body records each failure line.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`
- **Status**: open

## Phase 3: Repairs

### T008 [US1] Restructure request_admission.py into OrganizationScope

- **Requirements**: FR-004, FR-005, FR-006, FR-008, FR-009, FR-010, FR-011, FR-021
- **Files**: `src/interfaces/wan_performance/collection/request_admission.py`, `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` (rename only)
- **Acceptance**: The module holds four top-level names: `logger`, `OrganizationScope`, `RequestLedger`, and `AdmittedAdapter`. `OrganizationScope.block("")` raises `ValueError`. A site request with no ledger organization takes its organization from `OrganizationScope.current()`. Each changed line has an inline comment.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- **Status**: partial. The branch holds the scope behavior in module-level functions. It has seven top-level names, and it lacks the empty identifier refusal.

### T009 [P] [US2] Repair the traceback renderer in logger_utils.py

- **Requirements**: FR-012, FR-013
- **Files**: `src/foundation/support/utils/logger_utils.py`
- **Acceptance**: `console_formatter` passes `show_locals=False` and `color_system="truecolor" if supports_color else None` to `RichTracebackFormatter`. The function holds 25 lines or fewer.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`
- **Status**: partial. The branch holds `show_locals=False` at line 152. It lacks the `color_system` argument.

### T010 [P] [US3] Add sdk_error_lines.py with SdkErrorLineMute

- **Requirements**: FR-016, FR-017, FR-021
- **Files**: `src/mist/intelligence/reports/subscription_expiry/sdk_error_lines.py`
- **Acceptance**: The module holds one class, `SdkErrorLineMute`, with `SDK_LOGGER_NAME = "mistapi"` and the static method `muted()`. Inside the block, the method drops ERROR records from the `mistapi` logger. It removes the filter on exit, including when the block raises.
- **Verification**: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`
- **Status**: absent

### T011 [US3] Repair client.py: scope, MSP fetch, logs, and class attribute

- **Requirements**: FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021
- **Files**: `src/mist/intelligence/reports/subscription_expiry/client.py`
- **Acceptance**: `_fetch_msp_listing(msp_id)` writes one INFO line before the SDK call and one DEBUG line after it. It holds the `SdkErrorLineMute.muted()` block. `HTTP_FORBIDDEN` is a class attribute. The VC read runs inside `OrganizationScope.block`. The module holds five top-level names: `logger`, `HTTP_BAD_REQUEST`, `JsiAccountNotLinkedError`, `SubscriptionExpiryClientError`, and `SubscriptionExpiryClient`.
- **Verification**: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`
- **Status**: partial. The branch holds the VC scope at line 672 and the mute at line 208. It lacks the info and debug lines. It holds nine top-level names.

### T012 [P] Align the operator guide sentence

- **Requirements**: FR-026
- **Files**: `documentation/operator-guide.md` (lines 502 and 503)
- **Acceptance**: Lines 502 and 503 state that a denied MSP organization list continues with direct organizations. No sentence in the step says that the menu uses one organization.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`. The score on main is recorded before the edit. The threshold stays at 80.
- **Status**: open

### T013 [P] Add the changelog fragment

- **Requirements**: FR-027
- **Files**: `changelog.d/issue-4943-request-admission-org-scope.md` (new)
- **Acceptance**: The file holds one `###` heading. It holds one bullet for `Fixed` and one bullet for `Security`. Each bullet names issue #4943, and the `Fixed` bullet names issue #4921. The file name stays unchanged after the pull request opens.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: open

## Phase 4: Final tasks

### T-LOCAL-GATES Run every applicable local gate

- **Requirements**: FR-023, FR-025
- **Files**: The five changed source and test files, the operator guide, the changelog fragment, and the record
- **Acceptance**: Each applicable row of the local gates table passes, with the output recorded. The row for the test quality ratchet reports `gate: 0 new findings vs baseline`. The row for symbols reports the names that moved into classes, listed in the pull request body. The row for the mistapi SDK compatibility test passes.
- **Verification**: The gate rows named in `design/checklists/gates.md`.
- **Status**: open

### T-PR Commit, rebase, push, and open the pull request

- **Requirements**: FR-001, FR-028
- **Files**: The branch `fix/4943-request-admission-org-scope`
- **Acceptance**: The commits follow Conventional Commits. The branch rebases onto `origin/main`, and the affected gates run again after the rebase. The pull request body contains `Closes #4921` and `Closes #4943`. Its title passes the `Conventional Commits PR title` check. The body names the path move of the admission test and the moved symbols.
- **Verification**: `gh pr view --json title,body`, run in the worktree that holds the pull request branch. This process task uses a read-only command.
- **Status**: open

### T-REMOTE-CI Watch the remote checks

- **Requirements**: FR-023
- **Files**: None. The task reads check results.
- **Acceptance**: Every required check passes on the latest commit, including CodeQL. The test quality job reports zero new findings. The pull request has no auto-merge label yet.
- **Verification**: `gh pr checks --watch`, run in the worktree that holds the pull request branch. This process task uses a read-only command.
- **Status**: open

### T-MERGE Merge after the orchestrator authorizes

- **Requirements**: FR-003
- **Files**: None. The task changes pull request state after authorization.
- **Acceptance**: The orchestrator authorizes the merge. The auto-merge label is added after every check passes. The squash commit lands on `main`. The issues #4921 and #4943 close. The `container-build.yml` run on the merged commit passes, and its image revision label equals the merged commit SHA. The preservation branch still exists.
- **Verification**: `gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/chore/4943-preserve-wip-2026-11-24 --jq .object.sha`. This process task uses a read-only command.
- **Status**: open

Warning: deleting the preservation branch removes the only remote copy of the five files. Do not delete the branch in this task.

## Dependencies and Execution Order

- T001 has no dependency. T002 starts first among the code-facing tasks.
- Chain: T002, then T003, then T004.
- After T004, the tasks T005, T006, T012, and T013 run in parallel with each other, because they touch different files.
- T007 runs after T005 and T006.
- T008 runs after T007. T009 and T010 run after T007 and in parallel with T008.
- T011 runs after T010, because it imports `SdkErrorLineMute`.
- The final tasks run in the order T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.

## Coverage Summary

- Requirements: 29 (FR-001 to FR-029).
- Tasks: 17 (T001 to T013, and the four final tasks).
- Test functions: 12. Six exist on the branch: four in the admission module and two in the client module. Six are new, and T005 and T006 add them.
