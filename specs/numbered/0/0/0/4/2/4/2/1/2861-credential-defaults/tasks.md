# Tasks: Credential default audit

**Input**: [spec.md](spec.md), [plan.md](plan.md), and [design/research.md](design/research.md).

**Tests**: Required. Each batch writes its test before the production edit.

**Status legend**: `open` means ready and not started. `absent` means the outcome is missing and a human decision blocks the task. `partial` means some outcome is on main. `verified-present` means the outcome is on main.

## Phase 1: Batch 0 - Ratchet foundation

**Purpose**: Lock the baseline before any repair.

- [ ] T001 [P] FR-014 Create the nested guard package in `tests/guardrails/credential_default_ratchet/__init__.py`. Acceptance: pytest collects the package. Verify: `.venv\Scripts\python.exe -m pytest tests\guardrails\credential_default_ratchet --collect-only -q`. Status: open.
- [ ] T002 FR-014 Add class `CredentialDefaultScanner` and the repository scan test in `tests/guardrails/credential_default_ratchet/test_credential_default_ratchet.py`. Acceptance: the test prints the stable count line. Verify: `.venv\Scripts\python.exe -m pytest tests\guardrails\credential_default_ratchet -q -s`. Status: open.
- [ ] T003 FR-014 Add the zero-input proof in `tests/guardrails/credential_default_ratchet/test_credential_default_ratchet.py`. Acceptance: a zero-file scan fails with `files=0`. Verify: the same pytest command as T002. Status: open.
- [ ] T004 FR-014 Add the negative fixture proof in `tests/guardrails/credential_default_ratchet/test_credential_default_ratchet.py`. Acceptance: the scanner reports an environment default and a dataclass default. Verify: the same pytest command as T002. Status: open.
- [ ] T005 [P] FR-015 Create `tests/guardrails/credential_default_ratchet/credential_default_baseline.json` with the 64 reviewed candidates from research.md. Acceptance: each entry has path, scope, kind, fingerprint, group, and reason. Verify: the same pytest command as T002. Status: open.
- [ ] T006 FR-015 Add growth and stale-entry checks in `tests/guardrails/credential_default_ratchet/test_credential_default_ratchet.py`. Add `changelog.d/issue-2861-credential-default-ratchet.md` with one heading and one Added bullet. Acceptance: a new candidate fails, a stale entry fails, and the changelog policy test passes. Verify: the same pytest command as T002. Status: open.

## Phase 2: Batch 1 - Wrong identity

**Purpose**: Remove default credentials that select an account.

- [ ] T007 [P] FR-001, FR-002, FR-003 Modify `src/foundation/persistence/db/__init__.py` lines 44, 45, and 48. Add the frozen set `_KNOWN_SAMPLE_CREDENTIALS`, a `__post_init__` check, and `changelog.d/issue-2861-database-sample-credentials.md`. Acceptance: fields default to empty and sample values are rejected. Verify: `.venv\Scripts\python.exe -m pytest tests\unit\test_standalone.py -q`. Status: open.
- [ ] T008 FR-001, FR-002, FR-003 Add tests in `tests/unit/test_standalone.py`. Acceptance: TST-06, TST-07, and TST-08 pass. Verify: the same pytest command as T007. Status: open.
- [ ] T009 [P] FR-004, FR-005 Modify `src/interfaces/portals/upgrade_portal/app/config.py` line 276. Add a helper that requires `ARANGO_USERNAME` when `_is_container_runtime()` is true. Acceptance: container runtime refuses a missing variable. Verify: `.venv\Scripts\python.exe -m pytest tests\unit\upgrade_portal\test_config.py -q`. Status: open.
- [ ] T010 FR-004, FR-005 Add tests in `tests/unit/upgrade_portal/test_config.py`. Acceptance: TST-09 and TST-10 pass. Verify: the same pytest command as T009. Status: open.
- [ ] T011 [P] FR-011 Modify `tests/integration/conftest.py` lines 36 and 93. Read `MIST_API_TOKEN` first. Call `pytest.fail` with both names on a conflict. Add `changelog.d/issue-2861-token-variable-precedence.md`. Acceptance: TST-15 passes. Verify: `.venv\Scripts\python.exe -m pytest tests\integration --collect-only -q`. Status: open.
- [ ] T012 FR-013 Modify `mist-ops-platform/src/shared/mist/session.py` line 90 after D-6 is decided. Acceptance: TST-18 passes for the chosen option. Verify: `mist-ops-platform\.venv\Scripts\python.exe -m pytest mist-ops-platform\tests\unit\mist\token_resolution -q`. Status: absent, blocked by D-6.

## Phase 3: Batch 2 - Command-line prompt and token rules

**Purpose**: Implement the owner decision for a missing token.

- [ ] T013 FR-006, FR-007, FR-008 Modify `MistHelper.py` lines 2809-2832, 2847-2866, and 2891-2905. Add a terminal-gated hidden prompt. Refuse without a terminal. Update `README.md` line 63 and `documentation/development-setup.md` line 154. Acceptance: TST-11 to TST-13 pass. Verify: `.venv\Scripts\python.exe -m pytest tests\unit\test_credential_preflight.py -q`. Status: open.
- [ ] T014 FR-008 Modify `src/foundation/support/refactors/initialize_mist_session.py` line 168 only if the stored token needs a new read path. Acceptance: TST-14 passes. Verify: the same pytest command as T013. Status: open.
- [ ] T015 FR-006, FR-007, FR-008 Add tests in `tests/unit/test_credential_preflight.py` and `changelog.d/issue-2861-interactive-token-prompt.md`. Acceptance: TST-11, TST-12, TST-13, and TST-14 pass. Verify: the same pytest command as T013. Status: open.
- [ ] T016 FR-012 Verify token-only session tests in `tests/unit/websocket/test_manager.py`, `tests/unit/device/test_arp_command_manager.py`, and `tests/unit/test_routing_utils.py`. Acceptance: all three files pass unchanged. Verify: `.venv\Scripts\python.exe -m pytest tests\unit\websocket\test_manager.py tests\unit\device\test_arp_command_manager.py tests\unit\test_routing_utils.py -q`. Status: verified-present.
- [x] T017 FR-009, FR-010 Verify the conflict and migration tests in `tests/unit/test_credential_preflight.py` lines 85 to 125 and the conflict check in `MistHelper.py` line 2823. Acceptance: the existing tests pass. Verify: the same pytest command as T013. Status: verified-present (delivered: MistHelper.py, tests/unit/test_credential_preflight.py).

## Phase 4: Batch 3 - Accepted entries

**Purpose**: Record reviewed intentional and display defaults.

- [ ] T018 FR-015, FR-016 Move the 31 group C entries and the 23 group B entries into the accepted section of the baseline with reasons. Acceptance: TST-17 passes. Verify: `.venv\Scripts\python.exe -m pytest tests\guardrails\credential_default_ratchet -q`. Status: open.
- [ ] T019 FR-016 Verify each changed file keeps its `except` clause count. Acceptance: the blind-exception ratchet passes. Verify: `.venv\Scripts\python.exe -m pytest tests\guardrails\test_blind_exception_handler_ratchet.py -q`. Status: open.

## Phase 5: Batch 4 - SDK allowlist and blocked decisions

**Purpose**: Add the SDK guard and wait for the three human decisions.

- [ ] T020 FR-017 Add the allowlist test in `tests/guardrails/credential_default_ratchet/test_credential_default_ratchet.py`. Allowed call sites are `wsgi.py`, `src/interfaces/visualization/maps/maps_manager.py`, and `scripts/probe_pk_strategy.py`. Acceptance: TST-16 passes. Verify: the same pytest command as T002. Status: open.
- [ ] T021 FR-018 Modify `compose.yml` lines 223, 244, and 250 and the SSH default in `container/scripts/start.sh` after D-7 is decided. Acceptance: TST-19 passes for the chosen option. Verify: `.venv\Scripts\python.exe -m pytest tests\guardrails\test_compose_database_settings.py -q`. Status: absent, blocked by D-7.
- [ ] T022 FR-009 Remove the `MIST_APITOKEN` read in `MistHelper.py` lines 2819-2827 and 2873-2881 after D-5 names the release. Update `README.md`, `documentation/development-setup.md`, `documentation/sample.env`, and `deploy/.env.example`. Acceptance: no code reads the legacy name. Verify: `.venv\Scripts\python.exe -m pytest tests\unit\test_credential_preflight.py -q`. Status: absent, blocked by D-5.

## Phase 6: Final validation and delivery

- [ ] T-LOCAL-GATES SC-005 Run each applicable row of the local gates table in `.github/copilot-instructions.md` lines 57 to 76 for every changed file. Acceptance: each row exits 0 or matches its expected result. Verify: the commands in `design/quickstart.md`. Status: open.
- [ ] T-PR SC-005 Commit with a Conventional Commits title. Open one pull request per batch. Body uses `Refs #2861` in batches 0 to 4. The final pull request body uses `Closes #2861`. Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body`. Status: open.
- [ ] T-REMOTE-CI SC-005 Watch the CI run for the pull request with `gh pr checks <number> --watch`. Acceptance: every required check passes, including CodeQL. Verify: `gh pr checks <number> -R jmorrison-juniper/MistHelper`. Status: open.
- [ ] T-MERGE SC-005 Enable auto-merge only after remote checks pass and the orchestrator authorizes the merge. After merge, verify container build and health (constitution IV steps 10 to 12). Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json mergedAt,mergeCommit`. Status: absent, blocked by orchestrator authorization.

## Planned Tests

| ID | Name | Task | Requirement |
| - | - | - | - |
| TST-01 | `test_repository_scan_reports_counts` | T002 | FR-014 |
| TST-02 | `test_zero_input_scan_fails` | T003 | FR-014 |
| TST-03 | `test_negative_fixture_detects_environment_and_dataclass_defaults` | T004 | FR-014 |
| TST-04 | `test_baseline_entries_match_current_scan` | T006 | FR-015 |
| TST-05 | `test_new_candidate_fails_growth_check` | T006 | FR-015 |
| TST-06 | `test_database_fields_have_no_default_credentials` | T008 | FR-001 |
| TST-07 | `test_database_rejects_sample_credential_value` | T008 | FR-002 |
| TST-08 | `test_standalone_mode_allows_empty_credentials` | T008 | FR-003 |
| TST-09 | `test_portal_container_requires_arango_username` | T010 | FR-004 |
| TST-10 | `test_portal_local_uses_image_account_and_logs_variable_name` | T010 | FR-005 |
| TST-11 | `test_prompt_runs_only_with_both_terminals` | T015 | FR-006 |
| TST-12 | `test_no_terminal_refuses_without_prompt` | T015 | FR-007 |
| TST-13 | `test_end_of_file_during_prompt_refuses_without_logging_input` | T015 | FR-007 |
| TST-14 | `test_prompted_token_is_not_logged_or_exported` | T015 | FR-008 |
| TST-15 | `test_integration_helper_prefers_canonical_and_fails_on_conflict` | T011 | FR-011 |
| TST-16 | `test_implicit_api_session_outside_allowlist_fails` | T020 | FR-017 |
| TST-17 | `test_accepted_entries_have_reasons` | T018 | FR-015 |
| TST-18 | `test_configured_token_fallback_follows_decision_d6` | T012 | FR-013 |
| TST-19 | `test_compose_has_no_literal_database_password_fallback` | T021 | FR-018 |

Existing tests cover FR-009 and FR-010 in `tests/unit/test_credential_preflight.py`. Existing tests cover FR-012 in the three token-only session modules. Existing `tests/guardrails/test_blind_exception_handler_ratchet.py` covers FR-016.

## Dependencies

- T001 precedes T002 to T006.
- T005 precedes T006 and T018.
- T007 precedes T008. T009 precedes T010. T013 precedes T014 and T015.
- T012, T021, and T022 wait for decisions D-6, D-7, and D-5.
- T-LOCAL-GATES follows every batch. T-PR follows T-LOCAL-GATES. T-REMOTE-CI follows T-PR. T-MERGE follows T-REMOTE-CI.
- Only one open pull request may change `MistHelper.py` at a time.
