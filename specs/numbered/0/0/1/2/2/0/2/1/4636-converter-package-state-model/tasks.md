# Tasks: Compliant Converter Package and State Model

**Input**: `spec.md`, `plan.md`, and the supporting artifacts under `design/`.

**Prerequisites**: Issue 4633 is closed. Its coordinator decision authorizes offline types and synthetic tests only. Issue 4632 is closed and records the DNS baseline.

**Rules for this list**: Each task names exact repository paths and one verification command from the local gates table. Mark a task done only after its verification passes and its evidence exists. Status values are `open`, `verified-present`, `partial`, or `absent`.

## Format

- `[P]`: The task can run in parallel with other `[P]` tasks. It uses different files and has no shared dependency.
- `FR-###`: The requirement IDs in `spec.md` that the task satisfies.
- `Depends on`: The tasks that must pass first.

## Phase 1: Prerequisites and Layout

- [ ] T001 [P] Verify offline implementation authorization and owner scope.
  - Requirements: FR-018
  - Depends on: None
  - Paths: `specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model/design/research.md`
  - Acceptance: The record cites issue 4633, the coordinator decision on issue 4636, and open PR #4208 as the shared-file owner.
  - Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
  - Status: partial. Offline scope is verified. The integration handover is absent.

- [ ] T002 [P] Run the baseline converter tests before any edit.
  - Requirements: FR-019
  - Depends on: None
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Acceptance: Both files pass on the unchanged `main` tree. Record the counts in `analysis.md`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: open. This drafting pass ran no tests.

- [ ] T003 [P] Record the capacity inventory and replacement layout.
  - Requirements: FR-001, FR-002, FR-023
  - Depends on: None
  - Paths: `specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model/plan.md`
  - Acceptance: `plan.md` lists each touched directory, its child count, and its replacement path. The guard test passes.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py`
  - Status: partial. The inventory is in this record. No source file changed.

## Phase 2: Move and Record Types

- [ ] T004 Replace `models.py` with the `state/` package and update three imports.
  - Requirements: FR-003, FR-019, FR-020
  - Depends on: T002, T003
  - Paths: delete `src/interfaces/portals/cisco_config_converter/models.py`. Add `src/interfaces/portals/cisco_config_converter/state/__init__.py`, `state/intake.py`, and `state/proposal.py`. Modify `src/interfaces/portals/cisco_config_converter/conversion.py`, `src/interfaces/portals/cisco_config_converter/routes.py`, and `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`.
  - Acceptance: The moved names match the symbol map in `plan.md`. No shim exists. Each touched line has an inline comment. Existing behavior is unchanged.
  - Verification: `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Status: absent.

- [ ] T005 [P] Write the record test module before the record code.
  - Requirements: FR-001, FR-004, FR-005, FR-007, FR-008, FR-009, FR-010, FR-017, FR-023
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/state/__init__.py`, `tests/integration/web_portal/cisco_config_converter/state/test_state_records.py`
  - Acceptance: The module holds these eleven tests: `test_digest_matches_existing_review_digest`, `test_digest_changes_when_any_proposal_field_changes`, `test_public_view_redacts_secret_fields`, `test_public_view_omits_source_text`, `test_review_expires_at_fifteen_minutes_utc`, `test_naive_timestamp_is_refused`, `test_approval_refused_without_verified_operator`, `test_approval_refused_for_changed_proposal_or_scope`, `test_backup_manifest_rejects_incomplete_pagination`, `test_backup_manifest_rejects_count_checksum_organization_or_family_defects`, and `test_structure_stays_within_five_children`. The structure test counts the `state/` package, its two subpackages, and the test `state/` folder.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_records.py`
  - Status: absent.

- [ ] T006 Implement the digest, seal, redaction, and record types until T005 passes.
  - Requirements: FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-017, FR-020
  - Depends on: T005
  - Paths: add `state/storage/__init__.py`, `state/storage/integrity.py`, `state/storage/redaction.py`, `state/lifecycle/__init__.py`, `state/lifecycle/approval.py`, `state/lifecycle/operation.py`, and `state/lifecycle/backup.py`. Modify `state/intake.py` to add `SourceRecord` and `ReviewRecord`. Modify `state/proposal.py` to add `ProposalRecord`.
  - Acceptance: Each record class holds the fields in `design/data-model.md`. Each module keeps five top-level names or fewer.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_records.py`
  - Status: absent.

## Phase 3: Transitions

- [ ] T007 [P] Write the transition test module before the transition code.
  - Requirements: FR-009, FR-011, FR-012
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/state/test_state_transitions.py`
  - Acceptance: The module holds these four tests: `test_documented_transitions_are_accepted`, `test_undocumented_transitions_are_refused`, `test_indeterminate_operation_cannot_start_execution`, and `test_expired_or_consumed_approval_cannot_start_execution`. The first two tests are parametrized.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_transitions.py`
  - Status: absent.

- [ ] T008 Implement `TransitionTable` until T007 passes.
  - Requirements: FR-011, FR-012
  - Depends on: T006, T007
  - Paths: `src/interfaces/portals/cisco_config_converter/state/lifecycle/transitions.py`
  - Acceptance: The table holds the edges in `design/data-model.md`, section Transition Table. Each refused transition raises `StateRefused`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_transitions.py`
  - Status: absent.

## Phase 4: Private Store

- [ ] T009 [P] Write the store test module before the store code.
  - Requirements: FR-006, FR-007, FR-013, FR-014, FR-015, FR-020, FR-021, FR-022
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/state/test_state_store.py`
  - Acceptance: The module holds these eight tests: `test_write_refused_without_portal_secret`, `test_write_refused_when_data_path_is_a_file`, `test_read_back_mismatch_reports_no_success`, `test_tampered_record_fails_seal_check`, `test_restart_reads_records_and_keeps_expiry`, `test_changed_secret_refuses_existing_records`, `test_default_store_refuses_production_writes`, and `test_write_logs_before_and_after_without_secret`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_store.py`
  - Status: absent.

- [ ] T010 Implement `PrivateStateStore` and `NativeFileLock` until T009 passes.
  - Requirements: FR-006, FR-009, FR-013, FR-014, FR-015, FR-016, FR-020, FR-021
  - Depends on: T006, T009
  - Paths: add `src/interfaces/portals/cisco_config_converter/state/storage/store.py` and `state/storage/locks.py`
  - Acceptance: Each write follows the order in `design/contracts/state-store.md`. Production writes stay disabled by default. Each action logs before and after.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_store.py`
  - Status: absent.

- [ ] T011 Write and run the multiworker test module.
  - Requirements: FR-009, FR-016, FR-022
  - Depends on: T010
  - Paths: `tests/integration/web_portal/cisco_config_converter/state/test_state_multiworker.py`
  - Acceptance: The module holds `test_two_processes_consume_one_approval_once` and `test_lock_holder_exit_releases_ownership`. Each test uses `tmp_path` and bounded timeouts.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/state/test_state_multiworker.py`
  - Status: absent.

## Phase 5: Audit and Guards

- [ ] T012 Audit comments, logs, ASCII output, and function limits.
  - Requirements: FR-001, FR-020
  - Depends on: T008, T010, T011
  - Paths: every file under `src/interfaces/portals/cisco_config_converter/` that T004 or T006 changes
  - Acceptance: Each executable line in a changed file has an inline comment. Each store action has an info line before and a debug line after. Each method uses five parameters or fewer.
  - Verification: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
  - Status: open.

- [ ] T013 Confirm the guards, the old-path search, and the shared-file rule.
  - Requirements: FR-001, FR-003, FR-018, FR-023
  - Depends on: T012
  - Paths: `tests/guardrails/test_move_module_guidance.py`, `tests/guardrails/test_nested_package_structure.py`
  - Acceptance: The guards pass. `git grep -n "cisco_config_converter.models"` returns no match. `web_portal/app.py` and `web_portal/templates/base.html` have no diff.
  - Verification: `python -m pytest tests/guardrails/test_move_module_guidance.py`
  - Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files.
  - Requirements: FR-001 through FR-023
  - Depends on: T013
  - Paths: every changed file from T004 through T013
  - Acceptance: Run each applicable gate from the local gates table in `.github/copilot-instructions.md`. Record each exact result in the pull request body.
  - Acceptance: Run each applicable gate below. Record each exact result in the pull request body.
  - Applicable gates, one per line:
    - Compile: `python -m py_compile` on each changed Python file.
    - Lint: `python -m ruff check .`
    - Format: `python -m black --check .`
    - Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`
    - Tests: each new test file. Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
    - Test quality: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
    - Complexity: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
    - Security lint: `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q`
    - Code quality: `pylint src/ --fail-under=9.5`
    - Dead code: `vulture $VULTURE_PATHS --min-confidence 70`
    - Docstrings: `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90`
    - Symbols: `symbol-diff --base origin/main` for `models.py`, `state/intake.py`, and `state/proposal.py`
    - Guardrails: `python -m pytest tests/guardrails`
  - Not applicable, one reason per line:
    - Safe sweep and Menu reference: no menu changed.
    - STE: no listed Markdown file changed.
    - Dependency audit: no dependency changed.
    - Ops portal and Ops platform: no change in those trees.
  - Verification: Each command in the Applicable gates list exits with the expected result.
  - Status: open.

- [ ] T-PR Commit, rebase, push, and open the pull request.
  - Requirements: FR-001 through FR-023
  - Depends on: T-LOCAL-GATES
  - Paths: the branch `feat/4636-converter-state-model`
  - Acceptance: The commit subject is `feat(web-portal): define compliant converter state model`. The pull request title uses the same form. The body contains `Closes #4636`. The body lists each gate result and the symbol-gate exception from `plan.md`.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body` shows the title and the closing line. This check is remote, because no local gate covers a pull request body.
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks until each one finishes.
  - Requirements: FR-001 through FR-023
  - Depends on: T-PR
  - Paths: the pull request from T-PR
  - Acceptance: Each required check reports success. CodeQL reports success before the `auto-merge` label is added.
  - Verification: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`. This check is remote.
  - Status: open.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-001 through FR-023
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Paths: the pull request from T-PR
  - Acceptance: Add the `auto-merge` label only after T-REMOTE-CI passes. The merge is a squash merge. The branch and worktree are removed after the merge.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json autoMergeRequest,state`. This check is remote.
  - Status: open.

## Dependencies and Execution Order

| Task | Depends on | Parallel group |
| --- | --- | --- |
| T001 | None | A |
| T002 | None | A |
| T003 | None | A |
| T004 | T002, T003 | None |
| T005 | T004 | B |
| T006 | T005 | None |
| T007 | T004 | B |
| T008 | T006, T007 | None |
| T009 | T004 | B |
| T010 | T006, T009 | None |
| T011 | T010 | None |
| T012 | T008, T010, T011 | None |
| T013 | T012 | None |
| T-LOCAL-GATES | T013 | None |
| T-PR | T-LOCAL-GATES | None |
| T-REMOTE-CI | T-PR | None |
| T-MERGE | T-REMOTE-CI and orchestrator authorization | None |

Parallel group B holds three test modules. Each module is a different file. The three groups do not share a file.

## Test Plan Summary

The plan names 25 test functions. The four modules hold 11, 4, 8, and 2 functions. Each parametrized case counts once.

| Module | Functions | Requirements covered |
| --- | --- | --- |
| `test_state_records.py` | 11 | FR-001, FR-004, FR-005, FR-007, FR-008, FR-009, FR-010, FR-017, FR-023 |
| `test_state_transitions.py` | 4 | FR-009, FR-011, FR-012 |
| `test_state_store.py` | 8 | FR-006, FR-007, FR-013, FR-014, FR-015, FR-020, FR-021, FR-022 |
| `test_state_multiworker.py` | 2 | FR-009, FR-016, FR-022 |

The existing tests cover FR-018 and FR-019. `test_complete_offline_journey` in `test_routes.py` blocks sockets and file opens during the offline journey. The unit test file covers the moved `SourceConfiguration` behavior.
