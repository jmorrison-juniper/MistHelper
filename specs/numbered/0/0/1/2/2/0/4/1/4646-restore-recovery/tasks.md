# Tasks: Reviewed Restore and Partial-Operation Recovery

**Input**: [Specification](spec.md), [plan](plan.md), and the supporting artifacts under `design/`.

**Prerequisites**: This record authorizes design only. Each task below describes later work and remains open or absent until its evidence exists.

**Rules for this list**: Each task names exact paths and one verification command from the Local gates table (remote check 6). Mark a task done only after its verification passes and its evidence exists.

## Format

- `[P]`: The task can run in parallel with other `[P]` tasks. It uses different files and has no shared dependency.
- `FR-###`: The requirement IDs in `spec.md` that the task satisfies.
- `Depends on`: The tasks that must finish first. External gates name the issue.
- Status values are `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Prerequisites and Evidence

- [ ] T001 [P] Confirm the prerequisite issues and the open owner decisions.
  - Requirements: FR-011, FR-025
  - Depends on: None
  - Paths: `specs/numbered/0/0/1/2/2/0/4/1/4646-restore-recovery/design/research.md`
  - Acceptance: `research.md` lists each prerequisite issue state. Decisions D-14 and D-20 remain marked HUMAN-DECISION-REQUIRED.
  - Verification: `python -m pytest tests/guardrails`
  - Status: partial. Issue states are verified. Handovers and owner decisions are absent.

- [ ] T002 [P] Record the Mist contract for the twelve restore functions.
  - Requirements: FR-024
  - Depends on: T001
  - Paths: `specs/numbered/0/0/1/2/2/0/4/1/4646-restore-recovery/design/contracts/restore-mist.md`
  - Acceptance: The contract lists each method, path, status mapping, read-only field, and unverified payload rule. Each claim cites a local OpenAPI line or a local SDK line.
  - Verification: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py`
  - Status: partial. Method names and OpenAPI lines are verified. Payload evidence from issue 4634 is absent.

- [ ] T003 [P] Confirm the layout revision R-4636-1 in issue 4636.
  - Requirements: FR-027
  - Depends on: T001
  - Paths: `specs/numbered/0/0/1/2/2/0/4/1/4646-restore-recovery/plan.md`
  - Acceptance: The plan names the moved file and the child counts after the revision. Issue 4636 holds `lifecycle/` at five children after the move.
  - Verification: `python -m pytest tests/guardrails/test_move_module_guidance.py`
  - Status: partial. The plan names the revision. Issue 4636 has not adopted it.

## Phase 2: Shared Test Support and Tests First

- [ ] T004 [P] Add the fake gateway, the fixed clock, and the test package marker.
  - Requirements: FR-024, FR-027
  - Depends on: T002
  - Paths: `tests/integration/web_portal/cisco_config_converter/recovery/__init__.py`, `tests/integration/web_portal/cisco_config_converter/recovery/fakes.py`
  - Acceptance: `FakeMistGateway` records each call and returns scripted responses. It supports success, HTTP 4xx, HTTP 429, timeout, missing ID, and read-back mismatch. `FixedClock` returns a fixed UTC time.
  - Verification: `python -m py_compile tests/integration/web_portal/cisco_config_converter/recovery/fakes.py`
  - Status: absent.

- [ ] T005 [P] Write the decision tests in `test_restore_decisions.py`.
  - Requirements: FR-001 to FR-007, FR-022
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/recovery/test_restore_decisions.py`
  - Acceptance: The module holds these 14 tests: `test_verified_manifest_is_accepted`, `test_damaged_seal_refuses_manifest`, `test_count_or_digest_mismatch_refuses_manifest`, `test_incomplete_pagination_refuses_manifest`, `test_wrong_organization_or_family_refuses_manifest`, `test_absent_object_with_free_name_is_create`, `test_identical_object_is_unchanged`, `test_changed_object_without_override_is_conflict`, `test_override_is_update_and_changes_proposal_digest`, `test_duplicate_name_is_conflict_and_excluded`, `test_unresolved_reference_is_conflict`, `test_failed_lookup_is_never_create`, `test_object_absent_from_backup_is_preserved`, and `test_proposal_lists_identities_conflicts_and_digests`. Each test fails before T009 and T010.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_decisions.py`
  - Status: absent.

- [ ] T006 [P] Write the approval, execution, and output tests in `test_restore_execution.py`.
  - Requirements: FR-007, FR-008 to FR-018, FR-023, FR-025, FR-028
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/recovery/test_restore_execution.py`
  - Acceptance: The module holds these 15 tests: `test_expired_approval_refused_at_boundary`, `test_changed_proposal_or_scope_refused`, `test_unverified_operator_refused`, `test_missing_scope_confirmation_refused`, `test_wrong_confirm_word_refused`, `test_consumed_approval_refused_on_second_use`, `test_disabled_gate_returns_not_found`, `test_success_verifies_recovery_backup_then_writes_in_order`, `test_changed_target_before_write_stops_operation`, `test_partial_apply_stops_later_writes`, `test_timeout_is_indeterminate_and_not_retried`, `test_rate_limited_create_reconciles_before_next_write`, `test_reconciliation_finds_unique_created_object`, `test_unrelated_objects_unchanged_in_success_and_failure`, and `test_logs_and_responses_hold_no_backup_bodies`. Each refusal test asserts zero write calls.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_execution.py`
  - Status: absent.

- [ ] T007 [P] Write the recovery tests in `test_recovery.py`.
  - Requirements: FR-007, FR-018 to FR-021
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/recovery/test_recovery.py`
  - Acceptance: The module holds these seven tests: `test_reverse_update_requires_matching_after_digest`, `test_changed_by_another_operator_blocks_reverse`, `test_created_objects_are_kept_by_default`, `test_recovery_delete_requires_owner_permission`, `test_failed_recovery_reports_failed_not_atomic`, `test_recovery_requires_fresh_approval`, and `test_absent_from_backup_never_deleted`. Each test fails before T010 and T013.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_recovery.py`
  - Status: absent.

## Phase 3: Records, Planning, and Gateway

- [ ] T008 Add `DecisionKind`, `ObjectDecision`, and the new `OperationRecord` fields.
  - Requirements: FR-003, FR-012, FR-022
  - Depends on: T005, T003 (external gate R-4636-1)
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/operation.py`
  - Acceptance: `operation.py` holds four top-level names or fewer. `OperationRecord` adds `object_decisions`, `recovery_actions`, and `write_count`. Each new line has an inline comment.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_decisions.py`
  - Status: absent.

- [ ] T009 Move `BackupManifest` into `lifecycle/recovery/backup.py` and add the private `objects` mapping.
  - Requirements: FR-001, FR-002, FR-023
  - Depends on: T005, T003 (external gate R-4636-1)
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/__init__.py`, `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/backup.py`
  - Acceptance: `backup.py` keeps the verification rules of issue 4636 and adds `objects`. The public view omits `objects`. No file remains at `state/lifecycle/backup.py`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_decisions.py`
  - Status: absent.

- [ ] T010 Add `RestorePlanner`, `RecoveryPlanner`, and `RecoveryAction` in `planning.py`.
  - Requirements: FR-003 to FR-007, FR-019, FR-021, FR-022
  - Depends on: T008, T009
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/planning.py`
  - Acceptance: The planner assigns one decision per object with the rules in `design/contracts/restore-decisions.md`. The recovery planner lists a reverse update only when the current digest equals the recorded after-digest.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_decisions.py`
  - Status: absent.

- [ ] T011 Add `MistRestoreGateway` in `gateway.py`.
  - Requirements: FR-024
  - Depends on: T002, T009
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/gateway.py`
  - Acceptance: The class holds five members or fewer. It calls the twelve functions from `design/contracts/restore-mist.md` with explicit arguments. It contains no `*args` or `**kwargs` forwarding. It logs before and after each call without a body.
  - Verification: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py`
  - Status: absent.

## Phase 4: Execution, Recovery, and Portal

- [ ] T012 Add `RestoreExecutor` and `OutcomeReconciler` in `execution.py`.
  - Requirements: FR-007, FR-008 to FR-018, FR-028
  - Depends on: T006, T008, T010, T011 (external gates: issue 4636 store, issue 4644 apply path)
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/execution.py`, `src/interfaces/portals/cisco_config_converter/state/storage/store.py`, `src/interfaces/portals/cisco_config_converter/state/lifecycle/transitions.py`
  - Acceptance: The executor verifies the approval, writes the recovery backup, and writes each object in order. It stops at the first failed, partial, or indeterminate outcome. It waits at most 60 seconds per write. It never repeats an indeterminate write. A lock timeout refuses execution with code `lock_busy`. `transitions.py` adds the edge `reconciled` to `verified`. `store.py` adds `acquire_scope_lock`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_restore_execution.py`
  - Status: absent.

- [ ] T013 Add the five commands and route them to the handlers in `planning.py` and `execution.py`.
  - Requirements: FR-009, FR-010, FR-020, FR-021, FR-022, FR-025
  - Depends on: T007, T012
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/execution.py`, `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/planning.py`
  - Acceptance: `RestoreCommandDispatcher` maps the commands `propose`, `approve`, `execute`, `reconcile`, and `recovery-propose` to the handlers. Each class holds five methods or fewer, including `__init__`. Each command validates its input before use. Decision D-14 refuses `approve` while the identity is unverified.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery/test_recovery.py`
  - Status: absent.

- [ ] T014 Add `restore_route` to `routes.py`.
  - Requirements: FR-023, FR-025, FR-026
  - Depends on: T013 (external gate: issue 4645 administrative gate)
  - Paths: `src/interfaces/portals/cisco_config_converter/routes.py`
  - Acceptance: `routes.py` adds one import line and one function. `GET` returns the status of one operation. `POST` passes the command to the dispatcher. Responses use `Cache-Control: no-store` and the safe error shape. The gate returns not found when closed. A test proves the CSRF failure shape for each `POST`. Existing routes keep their responses.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent.

- [ ] T015 Audit comments, action logging, complexity, and function limits in each touched file.
  - Requirements: FR-027, FR-028
  - Depends on: T014
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/backup.py`, `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/planning.py`, `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/execution.py`, `src/interfaces/portals/cisco_config_converter/state/lifecycle/recovery/gateway.py`, `src/interfaces/portals/cisco_config_converter/routes.py`
  - Acceptance: Each executable line in a touched file has an inline comment. Each write, read-back, and reconciliation step has an info line and a debug line. Each function has five parameters or fewer.
  - Verification: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
  - Status: open.

- [ ] T016 Confirm the guards, the old module path, and the symbols.
  - Requirements: FR-026, FR-027
  - Depends on: T015
  - Paths: `tests/guardrails/test_nested_package_structure.py`, `tests/guardrails/test_move_module_guidance.py`, `src/interfaces/portals/cisco_config_converter/state/lifecycle/backup.py`
  - Acceptance: The guards pass. A search for the old path `state/lifecycle/backup.py` returns no match. The symbol gate reports no lost module-level name in `routes.py` or `operation.py`.
  - Verification: `python -m pytest tests/guardrails`
  - Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run each applicable gate from the Local gates table.
  - Requirements: FR-001 to FR-028
  - Depends on: T016
  - Paths: Every changed file from T004 through T016, and `changelog.d/issue-4646-restore-recovery.md`
  - Acceptance: Run each applicable gate below. Record each exact result in the pull request body.
  - Applicable gates, one per line:
    - Compile: `python -m py_compile` on each changed Python file.
    - Lint: `python -m ruff check .`
    - Format: `python -m black --check .`
    - Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`. `MYPY_PATHS` is on line 93 of `.github/workflows/ci.yml` (remote check 10).
    - Tests: `python -m pytest tests/integration/web_portal/cisco_config_converter/recovery`
    - Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`, section Local gates.
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
    - Test quality: the ratchet procedure in `.github/copilot-instructions.md`, section Test quality ratchet. The two required input files are named in that procedure. Their presence is unverified (unverified item U-13).
    - Complexity: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
    - Security lint: `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q`
    - Code quality: `pylint src/ --fail-under=9.5`
    - Dead code: `vulture $VULTURE_PATHS --min-confidence 70`. `VULTURE_PATHS` is on line 101 of `ci.yml` (remote check 11).
    - Docstrings: `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90`. The variables are on lines 104 and 107 of `ci.yml` (remote checks 12 and 13).
    - Symbols: `symbol-diff --base origin/main <file>` for `routes.py` and `operation.py`.
    - SDK compatibility: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py`
    - Guardrails: `python -m pytest tests/guardrails`
  - Not applicable, one reason per line:
    - Safe sweep: no menu operation changes.
    - Menu reference: no menu operation changes.
    - STE: no file listed in the STE gate changes.
    - Dependency audit: no dependency changes.
    - Ops portal: no file in `ops-portal/` changes.
    - Ops platform: no file in `mist-ops-platform/` changes.
  - Verification: Each command in the applicable list exits with the expected result.
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-001 to FR-028
  - Depends on: T-LOCAL-GATES
  - Paths: The branch `feat/4646-restore-recovery`
  - Acceptance: The commit subject is `feat(web-portal): add reviewed restore and recovery`. The pull request title uses the same form. The body contains `Closes #4646`, the gate results, and the layout note R-4636-1. Add the `auto-merge` label only after T-REMOTE-CI passes.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body` shows the title and the closing line. This check is remote.
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks until each one finishes.
  - Requirements: FR-001 to FR-028
  - Depends on: T-PR
  - Paths: The pull request from T-PR
  - Acceptance: Each required check reports success. CodeQL reports success before the `auto-merge` label is added.
  - Verification: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`. This check is remote.
  - Status: open.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-001 to FR-028
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Paths: The pull request from T-PR
  - Acceptance: Add the `auto-merge` label only after T-REMOTE-CI passes. Use a squash merge. After the merge, wait for `container-build.yml` on the merged revision and check the image revision label. Deployment needs separate owner approval.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json autoMergeRequest,state`. This check is remote.
  - Status: open.

## Dependencies and Execution Order

| Task | Depends on | Parallel group |
| --- | --- | --- |
| T001 | None | A |
| T002 | T001 | A |
| T003 | T001 | A |
| T004 | T002 | None |
| T005 | T004 | B |
| T006 | T004 | B |
| T007 | T004 | B |
| T008 | T005 and external gate R-4636-1 | None |
| T009 | T005 and external gate R-4636-1 | None |
| T010 | T008, T009 | None |
| T011 | T002, T009 | None |
| T012 | T006, T008, T010, T011 | None |
| T013 | T007, T012 | None |
| T014 | T013 and external gate issue 4645 | None |
| T015 | T014 | None |
| T016 | T015 | None |
| T-LOCAL-GATES | T016 | None |
| T-PR | T-LOCAL-GATES | None |
| T-REMOTE-CI | T-PR | None |
| T-MERGE | T-REMOTE-CI and orchestrator authorization | None |

Parallel group A holds the three prerequisite checks. Parallel group B holds three test modules. Each module is a different file. No task in group B edits a shared file.

## Test Plan Summary

The plan names 36 test functions in three modules and one support module.

| Module | Functions | Requirements covered |
| --- | --- | --- |
| `test_restore_decisions.py` | 14 | FR-001 to FR-007, FR-022 |
| `test_restore_execution.py` | 15 | FR-007, FR-008 to FR-018, FR-023, FR-025, FR-028 |
| `test_recovery.py` | 7 | FR-007, FR-018 to FR-021 |

The existing tests cover FR-026 in `test_routes.py`. The nested package guard covers FR-027 in `tests/guardrails/test_nested_package_structure.py`. The SDK compatibility guard covers FR-024 in `tests/integration/test_mistapi_sdk_compatibility.py`.

## Implementation Strategy

1. Complete the three prerequisite checks in group A.
2. Write the support module and the three test modules. Confirm that each test fails for the missing code.
3. Add the state records, the planner, and the gateway. Confirm the decision tests pass.
4. Add the executor, the dispatcher, and the route. Confirm the execution and recovery tests pass.
5. Run the local gates and the remote checks. Stop before the merge until the orchestrator authorizes it.
