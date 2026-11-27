# Tasks: Safe Cisco Input and Structured Review

**Input**: `spec.md`, `plan.md`, and the supporting artifacts under `design/`.

**Prerequisites**: Issue 4636 must land before task T004. Issue 4636 defines the `state/` package and the `models.py` move that this list extends.

**Rules for this list**: Each task names exact repository paths and one verification command. A task gets the status `verified-present` only after its verification passes and its evidence exists. The status column reflects the repository on `main` on 2026-11-26.

## Format

- `[P]`: The task runs in parallel with other `[P]` tasks. It touches different files and has no shared prerequisite.
- `FR-###`: The requirement IDs in `spec.md` that the task satisfies.
- `Depends on`: The tasks that must pass before this task starts.
- Status values: `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Prerequisites and Layout

- [ ] T001 [P] Verify that issue 4636 landed and that its file map matches this record.
  - Requirements: FR-021
  - Depends on: None
  - Paths: `src/interfaces/portals/cisco_config_converter/state/intake.py`, `specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model/plan.md`
  - Acceptance: The module `state/intake.py` exists, and the symbol map in `plan.md` matches it.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py`
  - Status: absent. Issue 4636 is a draft, and `state/intake.py` is not on `main`.

- [ ] T002 [P] Run the baseline converter tests before any edit.
  - Requirements: FR-016
  - Depends on: None
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Acceptance: Both files pass on the unchanged tree. Record the pass counts in `analysis.md`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Status: open. This drafting pass ran no tests.

- [ ] T003 [P] Record the capacity inventory and the converted layout in `plan.md`.
  - Requirements: FR-021
  - Depends on: None
  - Paths: `specs/numbered/0/0/1/2/2/0/2/2/4637-safe-cisco-input-review/plan.md`
  - Acceptance: `plan.md` lists each touched directory, its child count, and its converted path.
  - Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
  - Status: partial. The inventory exists in the draft. No repository file exists yet.

## Phase 2: Move and Test-First Modules

- [ ] T004 Convert `state/intake.py` into the `intake/` package and update three import lines.
  - Requirements: FR-016, FR-021
  - Depends on: T001, T002, T003
  - Paths: delete `src/interfaces/portals/cisco_config_converter/state/intake.py`. Add `state/intake/__init__.py`, `state/intake/source.py`, and `state/intake/review.py`. Modify `src/interfaces/portals/cisco_config_converter/conversion.py`, `src/interfaces/portals/cisco_config_converter/routes.py`, and `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`.
  - Acceptance: The moved names match the symbol map. No shim remains. Each touched line has an inline comment.
  - Verification: `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent.

- [ ] T005 [P] Write the input contract tests before the source and storage code.
  - Requirements: FR-003, FR-004, FR-005, FR-006, FR-020, FR-021
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/input/__init__.py`, `tests/integration/web_portal/cisco_config_converter/input/test_input_contract.py`
  - Acceptance: The module holds these ten functions: `test_supported_suffixes_are_accepted`, `test_unsupported_suffixes_are_refused`, `test_exact_size_limit_is_accepted`, `test_one_extra_byte_is_refused_before_decoding`, `test_invalid_utf8_is_refused`, `test_empty_or_null_text_is_refused`, `test_path_like_and_control_names_are_refused`, `test_client_path_is_never_accepted_as_stored_identifier`, `test_symlink_escape_is_refused_for_stored_selection`, and `test_intake_package_stays_within_five_children`. Run the module before T007, and each new behavior test fails.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/input/test_input_contract.py`
  - Status: absent.

- [ ] T006 [P] Write the catalog, retention, and route tests before the storage and route code.
  - Requirements: FR-001, FR-002, FR-006, FR-007, FR-008, FR-009, FR-015, FR-017, FR-020
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/input/test_catalog_and_retention.py`, `tests/integration/web_portal/cisco_config_converter/input/test_input_routes.py`
  - Acceptance: `test_catalog_and_retention.py` holds eight functions: `test_catalog_lists_only_contained_supported_files`, `test_catalog_ignores_symlinks_and_non_regular_entries`, `test_catalog_reports_only_safe_metadata`, `test_retention_refused_when_disabled_creates_no_file`, `test_retention_uses_exclusive_creation_and_owner_mode`, `test_retention_refuses_collision_without_overwrite`, `test_retention_refuses_symlinked_or_file_root`, and `test_unknown_or_malformed_identifier_is_refused`. `test_input_routes.py` holds nine functions: `test_inputs_route_lists_catalog_without_paths`, `test_observations_route_requires_csrf_and_keeps_review_state`, `test_preview_rejects_file_and_stored_identifier_together`, `test_retain_saves_only_when_retention_is_enabled`, `test_stored_selection_change_revokes_review`, `test_preview_collision_keeps_review_revoked`, `test_existing_export_shape_is_unchanged`, `test_observation_response_is_no_store`, and `test_logs_omit_source_text_and_original_names`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/input/test_catalog_and_retention.py tests/integration/web_portal/cisco_config_converter/input/test_input_routes.py`
  - Status: absent.

- [ ] T007 Implement the source rules, containment, catalog, retention, and the preview changes until T005 and T006 pass.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-015, FR-017, FR-020, FR-021
  - Depends on: T005, T006
  - Paths: modify `src/interfaces/portals/cisco_config_converter/state/intake/source.py`. Add `src/interfaces/portals/cisco_config_converter/state/intake/private_files.py`. Modify `src/interfaces/portals/cisco_config_converter/routes.py`.
  - Acceptance: Each save follows `design/contracts/private-input-store.md`. Each route follows `design/contracts/input-routes.md`. Each action logs before and after.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/input/test_input_contract.py tests/integration/web_portal/cisco_config_converter/input/test_catalog_and_retention.py tests/integration/web_portal/cisco_config_converter/input/test_input_routes.py`
  - Status: absent.

- [ ] T008 [P] Write the observation tests before the observation code.
  - Requirements: FR-011, FR-012, FR-013, FR-014, FR-022
  - Depends on: T004
  - Paths: `tests/integration/web_portal/cisco_config_converter/input/test_observations.py`
  - Acceptance: The module holds these eleven functions: `test_each_family_reports_its_positive_case`, `test_each_family_omits_absent_family_items`, `test_identity_values_are_omitted`, `test_credential_values_are_omitted`, `test_banner_body_is_unsupported_not_observed`, `test_malformed_mask_and_ambiguous_interface_have_status`, `test_duplicate_directive_has_duplicate_status`, `test_unknown_syntax_is_listed_with_line_number`, `test_missing_identity_section_reports_not_observed`, `test_observation_review_makes_no_socket_or_cloud_call`, and `test_observation_output_contains_no_conversion_fields`. The first function is parametrized over the eleven families.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/input/test_observations.py`
  - Status: absent.

- [ ] T009 Implement `ObservationReview`, the `/observations` route, and the converter page changes.
  - Requirements: FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-019, FR-021
  - Depends on: T007, T008
  - Paths: add `src/interfaces/portals/cisco_config_converter/state/intake/observations.py`. Modify `src/interfaces/portals/cisco_config_converter/routes.py`, `src/interfaces/portals/cisco_config_converter/presentation/converter.html`, and `src/interfaces/portals/cisco_config_converter/presentation/converter.js`.
  - Acceptance: The eleven families follow `design/contracts/observation-families.md`. Each new control has a `data-testid`. The script writes text with `textContent` only.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/input tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent.

- [ ] T010 Extend the isolated browser journey in the existing end-to-end file.
  - Requirements: FR-010, FR-016, FR-019, FR-022
  - Depends on: T009
  - Paths: modify `tests/e2e/web_portal/test_portal_smoke.py`
  - Acceptance: Two new functions exist in `TestCiscoOfflinePreview`: `test_stored_selection_and_sectioned_review_journey` and `test_changed_selection_invalidates_sections_and_review`. They cover a stored selection with sectioned review, and a changed selection that revokes the sections and the review.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k Cisco` with the environment variable `UPGRADE_PORTAL_E2E_STRICT` set to `1`.
  - Status: absent.

## Phase 3: Audit and Guards

- [ ] T011 Audit comments, logs, ASCII output, names, method size, and complexity.
  - Requirements: FR-017, FR-021
  - Depends on: T009
  - Paths: each file under `src/interfaces/portals/cisco_config_converter/` that T004, T007, or T009 changed
  - Acceptance: Each executable line in a changed file has an inline comment. Each action logs before and after. Each method has five parameters or fewer and 25 lines or fewer.
  - Verification: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
  - Status: absent.

- [ ] T012 Confirm the guards, the old-path search, and the shared-file rule.
  - Requirements: FR-018, FR-021
  - Depends on: T011
  - Paths: `tests/guardrails/test_move_module_guidance.py`, `tests/guardrails/test_nested_package_structure.py`, `web_portal/app.py`, `web_portal/templates/base.html`
  - Acceptance: The guards pass. `git grep -n "cisco_config_converter.models"` prints no match. `git diff --name-only origin/main -- web_portal/app.py web_portal/templates/base.html` prints nothing.
  - Verification: `python -m pytest tests/guardrails`
  - Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run each applicable local gate on the changed files.
  - Requirements: FR-001 through FR-022
  - Depends on: T012
  - Paths: every file that T004 through T012 changed, plus each Markdown file under the record folder
  - Acceptance: Run each applicable gate below. Record each exact result in the pull request body.
  - Applicable gates:
    - Compile: `python -m py_compile` on each changed Python file.
    - Lint: `python -m ruff check .`
    - Format: `python -m black --check .`
    - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
    - Tests: the four modules in `tests/integration/web_portal/cisco_config_converter/input/` and `tests/integration/web_portal/cisco_config_converter/test_routes.py`.
    - Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`, section Local gates.
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
    - Test quality: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
    - Complexity: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
    - Security lint: `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q`
    - Code quality: `pylint src/ --fail-under=9.5`
    - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`
    - Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`
    - Symbols: `symbol-diff --base origin/main` for `state/intake.py`, `state/intake/source.py`, and `state/intake/review.py`.
    - Guardrails: `python -m pytest tests/guardrails`
    - Writing: `ste-linter --config .ste-linter.toml --min-score 80` on each Markdown file in the record folder and on `changelog.d/issue-4637-safe-cisco-input-review.md`.
  - Not applicable, with one reason for each item:
    - Safe sweep and Menu reference: no menu changed.
    - Dependency audit: no dependency changed.
    - Ops portal and Ops platform: no file in those trees changed.
  - Verification: Each command in the applicable list exits with its expected result.
  - Status: open.

- [ ] T-PR Commit, rebase, push, and open the pull request.
  - Requirements: FR-001 through FR-022
  - Depends on: T-LOCAL-GATES
  - Paths: the branch `feat/4637-cisco-input-review`
  - Acceptance: The commit subject is `feat(web-portal): add safe Cisco input and structured review`. The pull request title uses the same form. The body contains `Closes #4637`. The body lists each gate result and the symbol-gate result for `state/intake.py`.
  - Verification: Run `gh pr view --json title,body` on the new pull request. Confirm the title and the closing line.
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks until each one finishes.
  - Requirements: FR-001 through FR-022
  - Depends on: T-PR
  - Paths: the pull request from T-PR
  - Acceptance: Each required check reports success. CodeQL reports success before the `auto-merge` label is added.
  - Verification: Run `gh pr checks --watch` on the new pull request.
  - Status: open.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-001 through FR-022
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Paths: the pull request from T-PR
  - Acceptance: Add the `auto-merge` label only after T-REMOTE-CI passes. The merge is a squash merge. Remove the branch and the worktree after the merge.
  - Verification: Run `gh pr view --json autoMergeRequest,state` on the new pull request.
  - Status: open.

## Dependencies and Execution Order

| Task | Depends on | Parallel group |
| --- | --- | --- |
| T001 | None | A |
| T002 | None | A |
| T003 | None | A |
| T004 | T001, T002, T003 | None |
| T005 | T004 | B |
| T006 | T004 | B |
| T007 | T005, T006 | None |
| T008 | T004 | B |
| T009 | T007, T008 | None |
| T010 | T009 | None |
| T011 | T009 | None |
| T012 | T011 | None |
| T-LOCAL-GATES | T012 | None |
| T-PR | T-LOCAL-GATES | None |
| T-REMOTE-CI | T-PR | None |
| T-MERGE | T-REMOTE-CI and orchestrator authorization | None |

Parallel group A holds three independent checks. Parallel group B holds three test modules in different files. Each test module starts after T004. No task edits `routes.py` in parallel with another task.

## Mapping to the Full-Parity Task Map

| Local task | Full-parity source | Note |
| --- | --- | --- |
| T001 | Issue 4636 task T004 | Verifies the prerequisite layout. |
| T004 | Full-parity T004 and issue 4636 T004 | Extends the `models.py` move to the `intake/` package. |
| T005 | Full-parity T007 | Moves the test path to the converter integration folder. Decision D-17. |
| T006 | Full-parity T007 | Adds the catalog, retention, and route tests. |
| T007 | Full-parity T008 | Implements contained catalog, prepopulation, and validated selection. |
| T008 | Full-parity T009 | Moves the parser tests to the converter integration folder. |
| T009 | Full-parity T008 and T010 | Implements the observation review and the sectioned display. |
| T010 | Full-parity T029 | Narrowed to the isolated converter page. |
| T011 | Issue 4636 task T012 | Audits comments, logs, and function size. |
| T012 | Issue 4636 task T013 | Confirms the guards and the shared-file rule. |

## Test Plan Summary

The plan names 40 test functions. Each parametrized function counts once.

| Module | Functions | Requirements covered |
| --- | --- | --- |
| `input/test_input_contract.py` | 10 | FR-003, FR-004, FR-005, FR-006, FR-020, FR-021 |
| `input/test_catalog_and_retention.py` | 8 | FR-001, FR-002, FR-006, FR-007, FR-008, FR-009, FR-020 |
| `input/test_observations.py` | 11 | FR-011, FR-012, FR-013, FR-014, FR-022 |
| `input/test_input_routes.py` | 9 | FR-007, FR-010, FR-015, FR-016, FR-017 |
| `tests/e2e/web_portal/test_portal_smoke.py` (two new functions) | 2 | FR-010, FR-016, FR-019, FR-022 |

The existing functions in `test_routes.py` and in the unit test module keep their names and assertions. Only the import line in the unit test module changes.
