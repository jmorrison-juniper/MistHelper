# Tasks: Site Request Admission by Organization

**Input**: `plan.md`, `spec.md`, and the design files in `design\`. Paths are repository paths relative to the root of the worktree.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design\research.md`, `design\contracts\site-organization-resolution.md`, and `design\quickstart.md`.

## Format and Status Values

- **[P]**: The task can run in parallel with other [P] tasks. The files differ, and no dependency exists.
- **Requirements**: The `FR-###` and `SC-###` IDs from `spec.md`.
- **Status**: `absent` means the target is not on `main`. `partial` means part of the target exists on `main`. `open` means the task verifies a result that has not run yet.
- Each task names one verification command from the local gates table in `.github\copilot-instructions.md`.

## Phase 1: Attribution Core

**Purpose**: Add the site organization map and the resolution rule to the request ledger.

### T001 - Add the site organization map class

- **Requirements**: FR-002, FR-006
- **Files**: `src\interfaces\wan_performance\collection\request_admission.py` (add the class `SiteOrganizationMap` before `RequestLedger`, near line 20)
- **Acceptance**: The class has one lock, an ordered map, a bound of 50,000 entries, and methods `remember` and `organization`. The oldest entry leaves first.
- **Verification**: `python -m ruff check .` (Lint row)
- **Status**: absent
- **Depends on**: none

### T002 - Add the session organization argument, the learning method, and the site resolution

- **Requirements**: FR-001, FR-003, FR-004, FR-005, FR-009
- **Files**: `src\interfaces\wan_performance\collection\request_admission.py` (`RequestLedger.__init__` line 37, `connect` line 56, `_organization` lines 102 to 109, and the new methods)
- **Acceptance**: A site request resolves in the order map, ledger, session, then refusal. The learning method never raises and writes counts only.
- **Verification**: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` (Types row)
- **Status**: absent
- **Depends on**: T001

### T003 - Call the learning step after the HTTP 429 check

- **Requirements**: FR-001, FR-008
- **Files**: `src\interfaces\wan_performance\collection\request_admission.py` (`AdmittedAdapter.send` lines 139 to 142)
- **Acceptance**: `send` calls `learn_site_organizations` after the 429 check and before `return response`. No new request is sent.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py -q` (Tests row)
- **Status**: absent
- **Depends on**: T002

## Phase 2: Session Wiring and Tests

**Purpose**: Connect the session organization and prove the behavior with unit tests.

### T004 - Pass the session organization from the session configurator

- **Requirements**: FR-004
- **Files**: `src\foundation\support\refactors\initialize_mist_session.py` (`_build_timeout_adapter` lines 67 to 75)
- **Acceptance**: The configurator imports `ConfigUtils` inside the function and passes `session_organization=ConfigUtils.get_cached_org_id` to `RequestLedger.connect`.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py -q` (Tests row, because the module imports the configurator)
- **Status**: absent
- **Depends on**: T002

### T005 - Add the eight new unit tests [P]

- **Requirements**: FR-001 to FR-006, FR-008, SC-001, SC-003, SC-005
- **Files**: `tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py` (class `TestRequestAdmission`, after line 101)
- **Acceptance**: The eight tests are `test_listed_site_uses_the_listing_organization`, `test_worker_thread_admits_a_listed_site_without_a_binding`, `test_unlisted_site_uses_the_session_organization`, `test_unlisted_site_fails_closed_after_other_sites_are_listed`, `test_failed_or_malformed_listing_learns_nothing`, `test_site_map_evicts_the_oldest_entry_at_the_bound`, `test_concurrent_listing_and_site_reads_stay_consistent`, and `test_listing_learning_adds_no_transport_call`.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py -q` (Tests row)
- **Status**: absent
- **Depends on**: T003

### T006 - Update the patched connect lambda

- **Requirements**: FR-004
- **Files**: `tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py` (line 120)
- **Acceptance**: The lambda accepts `session_organization=None` as well as `org_id=None`. The adapter test passes.
- **Verification**: `python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py -q` (Tests row)
- **Status**: absent
- **Depends on**: T004

## Phase 3: Remove the Binding

**Purpose**: Delete the per-run workaround after the new rule passes its tests.

### T007 - Delete AdmissionBinding and keep SdkErrorMute

- **Requirements**: FR-007, FR-010
- **Files**: `src\operations\exporting\ex_hardware_inventory\scope\session.py` (module docstring lines 1 to 11, the `MIST_URL` constant, class `AdmissionBinding` lines 25 to 75, and the imports that only it uses)
- **Acceptance**: `AdmissionBinding` and `_find_ledger` are gone. `SdkErrorMute` stays unchanged. The module docstring names no issue.
- **Verification**: `symbol-diff --base origin/main src\operations\exporting\ex_hardware_inventory\scope\session.py` (Symbols row). The only removed name is `AdmissionBinding`.
- **Status**: partial. `SdkErrorMute` is present. `AdmissionBinding` is present on `main`.
- **Depends on**: T005, T006

### T008 - Remove the binding calls from the batch

- **Requirements**: FR-007
- **Files**: `src\operations\exporting\ex_hardware_inventory\run\batch.py` (import line 38, `with AdmissionBinding` at lines 199 and 223)
- **Acceptance**: The import is gone. Each block body runs without the wrapper, and each statement keeps its comment.
- **Verification**: `python -m pytest tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py -q` (Tests row)
- **Status**: partial. The batch imports and wraps `AdmissionBinding` on `main`.
- **Depends on**: T007

### T009 - Delete the binding tests and keep the mute tests

- **Requirements**: FR-007
- **Files**: `tests\unit\ex_hardware_inventory\scope\test_hardware_session.py` (class `TestAdmissionBinding` lines 28 to 86, imports at lines 5 to 15 that only it uses)
- **Acceptance**: `TestAdmissionBinding` is gone. `TestSdkErrorMute` and its imports stay. No unused import remains.
- **Verification**: `python -m pytest tests/unit/ex_hardware_inventory/scope/test_hardware_session.py -q` (Tests row)
- **Status**: partial. The class is present on `main`, at line 28.
- **Depends on**: T007

## Phase 4: Changelog and Documentation

**Purpose**: Record the fix for users and update the code documentation.

### T010 - Add the changelog fragment [P]

- **Requirements**: FR-010
- **Files**: `changelog.d\issue-4921-site-request-admission.md` (add)
- **Acceptance**: The fragment has one `### Fixed` heading and one bullet. The bullet names issue 4921 and describes the attribution change.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` (Tests row)
- **Status**: absent
- **Depends on**: none

### T011 - Update docstrings and inline comments [P]

- **Requirements**: FR-010
- **Files**: `src\interfaces\wan_performance\collection\request_admission.py`, `src\operations\exporting\ex_hardware_inventory\scope\session.py`, `src\operations\exporting\ex_hardware_inventory\run\batch.py`, `src\foundation\support\refactors\initialize_mist_session.py`
- **Acceptance**: Each new class, method, and changed line has a docstring or an inline comment. Each comment names the cause or the purpose.
- **Verification**: `pydocstyle src/ wsgi.py web_portal` (Docstrings row)
- **Status**: absent
- **Depends on**: T002, T007

## Phase 5: Affected Readers and Guards

**Purpose**: Prove that the other site readers and the repository guards still pass.

### T012 - Run the subscription-expiry affected reader

- **Requirements**: FR-003, FR-009
- **Files**: `tests\unit\marvis\mist\intelligence\reports\audits\credentials\subscription_expiry\test_client.py` (read only)
- **Acceptance**: The virtual-chassis read and the report tests pass with the new rule.
- **Verification**: `python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py -q` (Tests row)
- **Status**: open
- **Depends on**: T004

### T013 - Run the process folder guard with the record present

- **Requirements**: FR-010 and the record layout in `plan.md`
- **Files**: `specs\numbered\0\0\1\2\4\1\4\1\4921-site-request-admission\` (read only)
- **Acceptance**: The guard accepts the record folder and its child count. It rejects no direct child.
- **Verification**: `python -m pytest tests/guardrails/test_process_folder_structure.py -q` (Tests row)
- **Status**: open
- **Depends on**: none

## Phase 6: Delivery

**Purpose**: Run every applicable gate, then take the change through the pull request and the merge.

### T-LOCAL-GATES - Run every applicable local gate

- **Requirements**: SC-001 to SC-006
- **Files**: `src\interfaces\wan_performance\collection\request_admission.py`, `src\foundation\support\refactors\initialize_mist_session.py`, `src\operations\exporting\ex_hardware_inventory\scope\session.py`, `src\operations\exporting\ex_hardware_inventory\run\batch.py`, `tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py`, `tests\unit\ex_hardware_inventory\scope\test_hardware_session.py`, `changelog.d\issue-4921-site-request-admission.md`, and `specs\numbered\0\0\1\2\4\1\4\1\4921-site-request-admission\`
- **Acceptance**: Each applicable row of the local gates table passes for the changed files. The symbol gate reports only `AdmissionBinding`. Each row not applicable names its reason in the pull request body.
- **Verification**: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` (Coverage row). The other rows are in `design\quickstart.md`.
- **Status**: absent
- **Depends on**: T008, T009, T010, T011, T012, T013

### T-PR - Commit, push, and open the pull request

- **Requirements**: IV in the constitution, and the `AGENTS.md` Git flow
- **Files**: `src\interfaces\wan_performance\collection\request_admission.py`, `src\foundation\support\refactors\initialize_mist_session.py`, `src\operations\exporting\ex_hardware_inventory\scope\session.py`, `src\operations\exporting\ex_hardware_inventory\run\batch.py`, `tests\unit\wan_dashboard\wan_performance\collection\test_request_admission.py`, `tests\unit\ex_hardware_inventory\scope\test_hardware_session.py`, `changelog.d\issue-4921-site-request-admission.md`, and `specs\numbered\0\0\1\2\4\1\4\1\4921-site-request-admission\`. Stage by explicit path. Do not stage the five local working-copy files (`research.md` section 4).
- **Acceptance**: The commit subject is `fix(admission): attribute site requests to their organization`. The body holds `Closes #4921`. The branch is `fix/4921-site-request-admission`, and it starts from `main`. The pull request body names the intended removal.
- **Verification**: `symbol-diff --base origin/main <file>` for each changed file (Symbols row)
- **Status**: absent
- **Depends on**: T-LOCAL-GATES

### T-REMOTE-CI - Watch the remote checks

- **Requirements**: IV in the constitution
- **Files**: `.github\workflows\ci.yml` (the required checks), and the pull request of T-PR.
- **Acceptance**: Each required check of the pull request reports success. The orchestrator reads each result. No check is skipped.
- **Verification**: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` (Coverage row, run locally before the push)
- **Status**: absent
- **Depends on**: T-PR

### T-MERGE - Enable auto-merge after the orchestrator authorizes it

- **Requirements**: IV in the constitution
- **Files**: No file changes in this task. The files of T-PR stay as they are.
- **Acceptance**: Auto-merge starts only after T-REMOTE-CI passes and the orchestrator authorizes it. The branch and worktree are removed after the squash merge.
- **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` (Test quality row, full-suite check)
- **Status**: absent
- **Depends on**: T-REMOTE-CI

## Dependencies and Execution Order

- Phase 1 runs in order: T001, then T002, then T003.
- T004 depends on T002. T005 depends on T003. T006 depends on T004.
- T007 depends on T005 and T006. T008 and T009 depend on T007.
- T010 and T011 run in parallel with the other phases after their own dependencies.
- T012 and T013 verify the change before the delivery phase starts.
- The delivery phase runs in order: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.

## Parallel Opportunities

- T004 and T005 touch different files. They can run in parallel after T003.
- T010 can run at any time, because it touches only the changelog folder.
- T011 can run after T007, in parallel with T008 and T009.

## Implementation Strategy

1. Build the attribution core first, then prove it with tests (T001 to T006).
2. Remove the binding only after the tests pass (T007 to T009).
3. Record the fix and update the docs (T010 and T011).
4. Verify the affected readers and the guards (T012 and T013).
5. Deliver the change through the gates, the pull request, and the merge (delivery phase).
