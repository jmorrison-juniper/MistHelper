# Tasks: Versioned Proposal Review and Safe Export

**Input**: [Specification](spec.md), [plan](plan.md), and the supporting artifacts under `design/`.

**Prerequisites**: Issue #4636 merges before T002. Issues #4637 to #4640 merge before T006 (assumption A-1). Issue #4648 approves the three routes before its own merge (assumption A-2).

**Tests**: The specification requires 21 test functions. Tests 1 to 7 cover assembly, tests 8 to 20 cover routes, and test 21 covers the isolated browser host.

**Organization**: Tasks follow the five user stories. Each task names exact paths and one verification command from the local gates table in `.github/copilot-instructions.md` line 55.

## Format and Status Values

- `[P]` marks a task that can run in parallel with its neighbors. The files do not overlap.
- `[US1]` to `[US5]` name the user story that a task serves.
- Status values are `open`, `verified-present`, `partial`, and `absent`. A `verified-present` status records remote evidence only. The test run is a later task.
- All boxes stay unchecked until the verification command of each task runs and passes.

## Phase 1: Claim and Preconditions

- [ ] T001 [US4] Claim issue #4641 and confirm the version 1 baseline on `main`.
  - Files: `src/interfaces/portals/cisco_config_converter/routes.py`, `src/interfaces/portals/cisco_config_converter/presentation/converter.html`, `src/interfaces/portals/cisco_config_converter/presentation/converter.js`, `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/e2e/web_portal/test_portal_smoke.py`.
  - Requirements: FR-013.
  - Acceptance: Add the `in-progress` label to issue #4641 before the branch exists. Rows 5 to 9, 17 to 22, and 24 match `main` at the recorded blob SHAs.
  - Verification: `python -m py_compile MistHelper.py`
  - Status: partial. The baseline evidence is `verified-present`. The label claim is open.

- [ ] T002 [US5] Confirm that issue #4636 merged and that `state/` exists before any edit.
  - Files: `src/interfaces/portals/cisco_config_converter/state/proposal.py`, created by issue #4636. `src/interfaces/portals/cisco_config_converter/models.py` must no longer exist.
  - Requirements: FR-021. Decision D-14.
  - Acceptance: Rows 4 and 13 change from `absent` and `present` to the state after issue #4636. Branch `feat/4641-proposal-review-export` starts from `main` in its own worktree.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent. The package move does not exist on `main` today (row 4).

## Phase 2: Shared Types, Assembly Tests, and Assembly

- [ ] T003 [P] [US1] Add `StructuredProposal` to `state/proposal.py`.
  - Files: `src/interfaces/portals/cisco_config_converter/state/proposal.py`.
  - Requirements: FR-001, FR-006, FR-007, FR-012.
  - Acceptance: The TypedDict holds the ten keys in `design/contracts/proposal-v2.md`. The module holds five top-level names. Each new line has an inline comment.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_assembly.py`
  - Status: open. Depends on T002.

- [ ] T004 [P] [US1] Write assembly tests 1 to 7.
  - Files: `tests/integration/web_portal/cisco_config_converter/proposals/__init__.py`, `tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_assembly.py`.
  - Requirements: FR-002 to FR-007, FR-016.
  - Acceptance: Each of the seven tests fails before T006 and passes after it. The tests use synthetic sources and no network.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_assembly.py`
  - Status: open. Depends on T002.

- [ ] T005 [P] [US2] [US3] [US5] Write route tests 8 to 20.
  - Files: `tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_routes.py`.
  - Requirements: FR-001, FR-008 to FR-019, FR-023.
  - Acceptance: Each of the thirteen tests fails before T007 and passes after it. The tests block network access and file opening.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_routes.py`
  - Status: open. Depends on T002.

- [ ] T006 [US1] Implement `ProposalAssembler` in `conversion.py`.
  - Files: `src/interfaces/portals/cisco_config_converter/conversion.py`.
  - Requirements: FR-002 to FR-007.
  - Acceptance: `assemble(source, suffix)` returns the StructuredProposal. The class holds four methods named `assemble`, `_scope`, `_object_changes`, and `_omissions`. Each method holds five parameters or fewer and 25 lines or fewer. `IOSDnsConverter` stays unchanged.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_assembly.py`
  - Status: open. Depends on T003, T004, and issues #4637 to #4640 merged.

## Phase 3: Version 2 Routes

- [ ] T007 [US2] [US3] [US5] Implement `ProposalRoutes`, the version 2 rules, and the `version` keyword.
  - Files: `src/interfaces/portals/cisco_config_converter/routes.py`.
  - Requirements: FR-001, FR-008 to FR-019, FR-023.
  - Acceptance: Tests 8 to 20 pass. `ConverterRoutes` keeps its five members. `ConverterInput.action` keeps its version 1 behavior when `version` is 1. Each touched block has inline comments and action logs.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_routes.py`
  - Status: open. Depends on T005 and T006.

- [ ] T008 [US4] Confirm that the version 1 tests pass without an edit.
  - Files: `tests/integration/web_portal/cisco_config_converter/test_routes.py`.
  - Requirements: FR-013. SC-003.
  - Acceptance: `test_routes.py` shows no diff. Every existing test passes.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: open. Depends on T007.

## Phase 4: Structured Review in the Isolated Host

- [ ] T009 [P] [US1] Add the structured review section and its test IDs to the page.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.html`.
  - Requirements: FR-020.
  - Acceptance: Each test ID in `design/contracts/ui-v2.md` appears once. The section loads `proposal_review.js` after `converter.js`. The version 1 test IDs stay in place.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Status: open. Depends on T007.

- [ ] T010 [US1] [US2] Create `CiscoStructuredReview` in the new script.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/proposal_review.js`.
  - Requirements: FR-008, FR-009, FR-011, FR-016, FR-017, FR-020.
  - Acceptance: The script renders with `textContent` only. Each JSON POST sends `X-CSRFToken`. The multipart preview sends the `csrf_token` field. Each function holds 25 lines or fewer. Each line has a comment.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Status: open. Depends on T009.

- [ ] T011 [US1] [US2] Add test 21, `test_structured_review_and_export`, to `TestCiscoOfflinePreview`.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py`.
  - Requirements: FR-020. SC-006.
  - Acceptance: The test previews, reviews, and exports. It compares the download with the preview response as parsed JSON. It checks the file name `cisco-proposal-v2.json`. It checks that a changed name disables review.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Status: open. Depends on T010.

## Phase 5: Structure and Release Note

- [ ] T012 [US4] Confirm the structure counts and the nested package guard.
  - Files: `src/interfaces/portals/cisco_config_converter/`, `src/interfaces/portals/cisco_config_converter/presentation/`, `tests/integration/web_portal/cisco_config_converter/proposals/`, `tests/integration/web_portal/cisco_config_converter/`.
  - Requirements: FR-021. SC-007.
  - Acceptance: The converter root holds five children. `presentation/` holds three. `proposals/` holds three. The integration folder holds four. The guard passes.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py`
  - Status: open. Depends on T011.

- [ ] T013 [P] [US2] Add the changelog fragment for the user-visible behavior.
  - Files: `changelog.d/issue-4641-proposal-review-export.md`.
  - Requirements: FR-022.
  - Acceptance: The fragment holds one `###` heading and one bullet for each change type. The bullet names issue #4641. The file name follows the rule in `.github/copilot-instructions.md` lines 451 and 452.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open. Depends on T007.

## Phase 6: Delivery

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files.
  - Files: every path in the file-by-file change map of `plan.md`.
  - Requirements: FR-001 to FR-023.
  - Acceptance: Each applicable gate in the table below reports its expected result. The pull request body lists each command with its result.
  - Verification: The commands in the table below. They come from `.github/copilot-instructions.md` line 55 and from the CI scope values in rows 45 to 49 of `design/research.md`.
  - Status: open. Depends on T008, T012, and T013.

  | Gate | Command | Expected result | Applies |
  | - | - | - | - |
  | Compile | `python -m py_compile` on each changed Python file | No output | Yes |
  | Lint | `python -m ruff check .` | `All checks passed` | Yes |
  | Format | `python -m black --check .` | No file needs a change | Yes |
  | Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` | Yes |
  | Tests | `python -m pytest` on each changed test file | All tests pass | Yes |
  | Full tests | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` and `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line for each shard | Yes |
  | Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Shards combine to 80 percent or above | Yes |
  | Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` | `gate: 0 new findings vs baseline` | Yes |
  | Complexity | `radon cc src/interfaces/portals/cisco_config_converter -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 | Yes |
  | Security lint | `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q` | No finding at any severity | Yes |
  | Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above | Yes |
  | Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding | Yes |
  | Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v` | No violation and coverage of 90 percent or above | Yes |
  | Symbols | `symbol-diff --base origin/main` on each modified module | `no module-level name changed` | Yes |
  | Dependency audit | `pip-audit -r requirements.txt` | Not applicable. No requirement changes. | No |
  | Menu reference | `python scripts/generate_menu_wiki.py` | Not applicable. No menu changes. | No |
  | Safe sweep | `python MistHelper.py --test` | Not applicable. No menu operation or `MistHelper.py` change. | No |
  | STE | `ste-linter` on the listed Markdown files | Not applicable. The gate lists no spec record (`.github/copilot-instructions.md` line 74). | No |
  | Ops portal and ops platform | npm and pytest commands in `ops-portal/` and `mist-ops-platform/` | Not applicable. No change in those trees. | No |

- [ ] T-PR Commit, push, and open the pull request.
  - Files: `changelog.d/issue-4641-proposal-review-export.md`, renamed to `changelog.d/pr-<number>.md`.
  - Requirements: FR-022. Assumption A-2 is visible in the pull request body.
  - Acceptance: The branch `feat/4641-proposal-review-export` is pushed to `origin`. The commit uses `feat(cisco-converter): add versioned proposal review and export` and includes `Closes #4641`. The pull request title uses the same Conventional Commits form. The body lists the gate results from T-LOCAL-GATES.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI Wait for the CI run on the pull request head.
  - Files: `.github/workflows/ci.yml`, read through the pull request checks.
  - Requirements: FR-001 to FR-023 through the CI copy of each gate.
  - Acceptance: Each required check reports success on the latest commit. A canceled, skipped, or timed-out check counts as unresolved.
  - Verification: `gh pr checks <number> --watch`
  - Status: open. Depends on T-PR.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Files: `.github/workflows/ci.yml`, whose required checks gate the pull request for issue #4641.
  - Requirements: Orchestrator authorization.
  - Acceptance: Auto-merge starts only after T-REMOTE-CI passes and the orchestrator authorizes the merge. The branch is removed after the squash merge.
  - Verification: `gh pr view <number> --json state,mergedAt,autoMergeRequest`
  - Status: open. Depends on T-REMOTE-CI and orchestrator authorization.

## Dependencies and Execution Order

| Task | Prerequisites |
| - | - |
| T001 | None |
| T002 | T001 and issue #4636 merged |
| T003 | T002 |
| T004 | T002 |
| T005 | T002 |
| T006 | T003, T004, and issues #4637 to #4640 merged |
| T007 | T005 and T006 |
| T008 | T007 |
| T009 | T007 |
| T010 | T009 |
| T011 | T010 |
| T012 | T011 |
| T013 | T007 |
| T-LOCAL-GATES | T008, T012, and T013 |
| T-PR | T-LOCAL-GATES |
| T-REMOTE-CI | T-PR |
| T-MERGE | T-REMOTE-CI and orchestrator authorization |

### Parallel Opportunities

- T003, T004, and T005 use separate files after T002.
- T009 and T013 use separate files after T007.
- The three test files (T004, T005, and T011) stay separate, so they can run in parallel.
- T007 owns `routes.py`, and T006 owns `conversion.py`. No task edits both modules at once.

## Requirement Traceability

| Requirement | Tasks | Tests or guards |
| - | - | - |
| FR-001 | T003, T005, T007 | 1, 8 |
| FR-002 | T004, T006 | 3 |
| FR-003 | T004, T006 | 4 |
| FR-004 | T004, T006 | 6 |
| FR-005 | T004, T006 | 6 |
| FR-006 | T003, T004, T006 | 2 |
| FR-007 | T003, T004, T006 | 2 |
| FR-008 | T005, T007, T010 | 10, 11 |
| FR-009 | T005, T007, T010 | 9, 10 |
| FR-010 | T005, T007 | 12 |
| FR-011 | T005, T007, T010 | 11, 13 |
| FR-012 | T003, T005, T007 | 14 |
| FR-013 | T001, T008 | Existing tests in `test_routes.py` |
| FR-014 | T005, T007 | 16 |
| FR-015 | T005, T007 | 16 |
| FR-016 | T004, T005, T007, T010 | 7, 17 |
| FR-017 | T005, T007 | 15 |
| FR-018 | T005, T007 | 18 |
| FR-019 | T005, T007 | 8, 10 |
| FR-020 | T009, T010, T011 | 21 |
| FR-021 | T002, T012 | `tests/guardrails/test_nested_package_structure.py` |
| FR-022 | T013, T-PR | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-023 | T005, T007 | 19 |

## Test Inventory

| Test | File | Requirement |
| - | - | - |
| 1 `test_v2_shape_keys_match_contract` | `proposals/test_proposal_assembly.py` | FR-001, FR-012 |
| 2 `test_scope_and_scope_digest_match_fields` | `proposals/test_proposal_assembly.py` | FR-006, FR-007 |
| 3 `test_object_change_describes_gateway_template` | `proposals/test_proposal_assembly.py` | FR-002 |
| 4 `test_omissions_list_unsupported_lines_and_known_gaps` | `proposals/test_proposal_assembly.py` | FR-003 |
| 5 `test_no_supported_command_adds_no_dns_servers` | `proposals/test_proposal_assembly.py` | Edge case |
| 6 `test_verification_and_unresolved_mappings_for_dns_subset` | `proposals/test_proposal_assembly.py` | FR-004, FR-005 |
| 7 `test_unknown_secret_value_absent_from_proposal` | `proposals/test_proposal_assembly.py` | FR-016 |
| 8 `test_v2_preview_returns_structured_proposal` | `proposals/test_proposal_routes.py` | FR-001, FR-019 |
| 9 `test_v2_export_requires_review` | `proposals/test_proposal_routes.py` | FR-009 |
| 10 `test_v2_review_then_export_is_exact` | `proposals/test_proposal_routes.py` | FR-008, FR-009, FR-019 |
| 11 `test_v2_edited_proposal_rejected` | `proposals/test_proposal_routes.py` | FR-008, FR-011 |
| 12 `test_new_preview_clears_v1_and_v2_review` | `proposals/test_proposal_routes.py` | FR-010 |
| 13 `test_scope_change_invalidates_review` | `proposals/test_proposal_routes.py` | FR-011 |
| 14 `test_version_integrity_rejects_wrong_version_and_keys` | `proposals/test_proposal_routes.py` | FR-012 |
| 15 `test_v2_csrf_required` | `proposals/test_proposal_routes.py` | FR-017 |
| 16 `test_v2_offline_no_network_or_file_write_and_no_data_exporter` | `proposals/test_proposal_routes.py` | FR-014, FR-015 |
| 17 `test_v2_logs_and_session_exclude_source_text` | `proposals/test_proposal_routes.py` | FR-016 |
| 18 `test_v2_actions_log_before_and_after` | `proposals/test_proposal_routes.py` | FR-018 |
| 19 `test_v2_review_and_export_expire_at_fifteen_minutes` | `proposals/test_proposal_routes.py` | FR-023 |
| 20 `test_v2_request_bound_follows_converter_prefix` | `proposals/test_proposal_routes.py` | Edge case |
| 21 `test_structured_review_and_export` | `tests/e2e/web_portal/test_portal_smoke.py` | FR-020 |

Notes: The test inventory counts 21 test functions. Parametrized cases do not add test functions. Test 14 covers four cases and test 15 covers three routes.
