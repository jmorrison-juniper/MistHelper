# Tasks: Converter Privacy and Shared Portal Integration

**Input**: `spec.md`, `plan.md`, and the supporting artifacts under `design/`.

**Prerequisites**: Issue #4633 is closed. Its coordinator decision authorizes offline work and names the integration owner. PR #4208 is OPEN and owns `web_portal/app.py` and `web_portal/templates/base.html`.

**Rules for this list**: Each task names exact repository paths and one verification command from the local gates table. A task reaches `verified-present` only after its verification passes on `main`.

## Format

- `[P]`: The task can run in parallel. It uses different files and has no shared dependency.
- `FR-###`: The requirement IDs in `spec.md` that the task satisfies.
- `Depends on`: The tasks or issues that must finish first.
- `Status`: `open` means not started or gated. `absent` means the deliverable is missing from `main` and no gate blocks it.

## Phase A: Handover Check and Offline Cross-Cutting Tests (no shared-file edit)

- [ ] T001 Record the G3 handover state in the handover checklist.
  - Requirements: FR-011
  - Depends on: None
  - Paths: `specs/numbered/0/0/1/2/2/0/4/3/4648-converter-privacy-portal-integration/design/checklists/handover.md`
  - Acceptance: The checklist names PR #4208 and its state. It names both shared paths and the coordinator decision source.
  - Verification: STE row, `ste-linter --config .ste-linter.toml --min-score 80 design/checklists/handover.md`
  - Status: open. The checklist exists in this draft. The handover comment on issue #4648 is absent.

- [ ] T002 [P] Create the composition harness and the baseline snapshot.
  - Requirements: FR-001, FR-002, FR-010
  - Depends on: None
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: A fixture builds `WebPortalApp.create_app` with `apisession=None`, as `tests/e2e/conftest.py` lines 273 to 277 do. The fixture sets `PORTAL_SECRET_KEY` with `monkeypatch`. Teardown calls `shutdown_app`. Each fixture line has an inline comment.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: absent.

- [ ] T003 [P] Add the health, ready, and status-code tests.
  - Requirements: FR-001, FR-002
  - Depends on: T002
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: `test_health_reply_keeps_exact_shape` checks the exact keys `status`, `services`, and `uptime_seconds`. `test_ready_reply_unchanged_with_converter` checks the ready payload. `test_existing_routes_keep_status_codes` covers `/`, `/health`, and `/ready`.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: absent.

- [ ] T004 [P] Add the CSRF and content negotiation tests.
  - Requirements: FR-003, FR-004
  - Depends on: T002
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: `test_converter_post_without_token_returns_400` covers preview, review, and export. `test_json_client_gets_csrf_expired_answer` and `test_html_client_gets_html_csrf_answer` check each answer shape. `test_api_prefix_keeps_json_csrf_answer` uses a test-only route. `test_prefix_without_slash_redirects_before_parse` checks the redirect.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: absent.

- [ ] T005 [P] Add the debug default and safe response tests.
  - Requirements: FR-005, FR-006
  - Depends on: T002
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: `test_debug_off_in_real_factory` checks `app.debug`. `test_container_runner_forces_debug_false` patches the container check and records the `debug` argument. `test_oversize_converter_body_returns_413` checks the limit. `test_error_bodies_hide_traceback_and_source` checks invalid inputs. `test_converter_page_is_html_with_no_store` checks the page headers.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: absent.

- [ ] T006 [P] Add the privacy, log, session, and no-network tests.
  - Requirements: FR-007, FR-008, FR-010
  - Depends on: T002
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: `test_logs_omit_source_name_and_secret` uses a synthetic canary in `caplog`. `test_session_holds_digest_only` reads the session transaction. `test_converter_package_imports_no_network_module` parses four files with `ast`. `test_offline_journey_opens_no_socket` patches `socket.socket.connect` through the real factory.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: absent.

- [ ] T007 [P] Add the route allowlist, upload boundary, registration, and Compose tests.
  - Requirements: FR-016, FR-017, FR-001
  - Depends on: T002
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: `test_route_allowlist_has_no_cloud_write_route` compares the converter rules with the five approved rules. `test_other_upload_routes_keep_flask_limits` uses a test-only route. `test_registration_refused_without_request_class` checks `ValueError`. `test_compose_has_no_converter_service` reads `compose.yml`.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: absent.

- [ ] T008 [P] Add the comparison matrix and handover consistency guards.
  - Requirements: FR-009, FR-011, FR-012
  - Depends on: T002
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: `test_comparison_rows_have_dispositions` counts forty rows in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md`. `test_every_row_links_test_or_task` checks each row ID. `test_handover_state_matches_shared_files` reads `design/checklists/handover.md` and the two shared files.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: absent.

## Phase B: Integration (after the G3 handover and the prerequisites)

- [ ] T009 Register the converter in `web_portal/app.py`.
  - Requirements: FR-011, FR-012, FR-001
  - Depends on: T001 with state `recorded`, PR #4208 closed or merged (state `released`), T002 through T008 passing, and issues #4636, #4644, #4646, and #4647 closed
  - Paths: `web_portal/app.py`
  - Acceptance: `create_app` sets `app.request_class = ConverterRequest` before line 53. `_register_blueprints` registers `ConverterRoutes.blueprint()` after line 207. The edit adds an inline comment and an info log before and a debug log after each step. `test_handover_state_matches_shared_files` expects the registration.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: open. PR #4208 owns this file on 2026-11-26.

- [ ] T010 Add the navigation entry in `web_portal/templates/base.html`.
  - Requirements: FR-013
  - Depends on: T009
  - Paths: `web_portal/templates/base.html`
  - Acceptance: One anchor follows the licensing comparison entry at line 79. Its `href` uses `url_for('cisco_converter.page')`. It has `data-testid="nav-cisco-converter"` and the label "Cisco Converter".
  - Verification: Tests row, `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Status: open. PR #4208 owns this file on 2026-11-26.

- [ ] T011 Add the real-portal browser module.
  - Requirements: FR-013, FR-014, FR-020
  - Depends on: T010
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_portal_browser.py`
  - Acceptance: `test_nav_entry_opens_converter_in_real_portal`, `test_upload_preview_review_export_in_real_portal`, `test_invalid_upload_shows_safe_error`, and `test_evidence_path_stays_under_test_artifacts` pass. Each browser test sets `pytest.mark.timeout(120)`. A failure saves a screenshot under `test-artifacts/cisco-portal/`.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_portal_browser.py`
  - Status: open.

- [ ] T012 Run the existing regression suites.
  - Requirements: FR-015, SC-007
  - Depends on: T009, T010, T011
  - Paths: `tests/e2e/web_portal/test_portal_smoke.py`, `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/integration/web_portal`
  - Acceptance: Each suite reports the same pass count as the baseline. The baseline counts appear in `analysis.md` after the first run. The run records any new failure as a defect.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal`
  - Status: open.

- [ ] T013 Update the operator guide and add the changelog fragment.
  - Requirements: FR-019
  - Depends on: T011, T012
  - Paths: `documentation/operator-guide.md`, `changelog.d/pr-<number>.md`
  - Acceptance: The web portal row near line 215 names the converter tab. The fragment has one `### Added` heading and one bullet that names issue #4648. The fragment name follows `changelog.d/README.md`.
  - Verification: STE row, `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
  - Status: open.

- [ ] T014 Complete the comparison matrix after the prerequisites.
  - Requirements: FR-009, FR-010, SC-005
  - Depends on: T008, and issues #4636, #4644, #4646, and #4647 closed
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Acceptance: Each row C01 through C40 links to a passing test or to a named task in the full-parity record. A row that needs a legal or owner decision stays open and names the decision. When issue #4636 or #4643 writes private files, add listing, preview, download, output-scan, and log tests for that folder.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`
  - Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run each applicable local gate.
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020
  - Depends on: T009 through T014
  - Paths: each changed file from T002 to T014
  - Acceptance: Run each applicable gate from the local gates table in `.github/copilot-instructions.md`. Record each exact result in the pull request body. Run the guard tests in `tests/guardrails`. The nested package guard covers FR-018.
  - Applicable gates, one per line:
    - Compile: `python -m py_compile web_portal/app.py`
    - Lint: `python -m ruff check .`
    - Format: `python -m black --check .`
    - Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml`
    - Tests: `python -m pytest tests/integration/web_portal/cisco_config_converter`
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
    - Test quality: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
    - Complexity: `radon cc web_portal -j | complexity-gate --max 10`
    - Security lint: `bandit -c pyproject.toml -r web_portal -q`
    - Dead code: `vulture $VULTURE_PATHS --min-confidence 70`
    - Docstrings: `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90`
    - Symbols: `symbol-diff --base origin/main web_portal/app.py`
    - STE: `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file
  - Not applicable, one reason per line:
    - Safe sweep and menu reference: no menu operation changes.
    - Dependency audit: no dependency changes.
    - Ops portal and ops platform: no file changes in those trees.
  - Verification: Each applicable command exits with the expected result from the table.
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request.
  - Requirements: FR-001 through FR-020
  - Depends on: T-LOCAL-GATES
  - Paths: branch `feat/4648-converter-portal-integration`, `changelog.d/pr-<number>.md`
  - Acceptance: The commit subject is `feat(web-portal): integrate the Cisco config converter tab`. The pull request title uses the same subject. The body contains `Closes #4648` and each gate result. Remote check: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body` shows both.
  - Verification: Tests row, `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks.
  - Requirements: FR-001 through FR-020
  - Depends on: T-PR
  - Paths: the pull request from T-PR
  - Acceptance: Each required check reports success on the latest commit. CodeQL reports success before the `auto-merge` label is added. Remote check: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter`
  - Status: open.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-001 through FR-020
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Paths: the pull request from T-PR
  - Acceptance: Add the `auto-merge` label only after T-REMOTE-CI passes. The merge is a squash merge. The branch and worktree are removed after the merge. Remote check: `gh pr view <number> -R jmorrison-juniper/MistHelper --json autoMergeRequest,state`.
  - Verification: Tests row, `python -m pytest tests/integration/web_portal/cisco_config_converter`
  - Status: open.

## Dependencies and Execution Order

| Task | Depends on | Parallel group |
| - | - | - |
| T001 | None | A |
| T002 | None | A |
| T003 to T008 | T002 | B (different test functions, same file) |
| T009 | T001 (state `recorded`), PR #4208 released, T002 to T008, and issues #4636, #4644, #4646, #4647 closed | None |
| T010 | T009 | None |
| T011 | T010 | None |
| T012 | T009, T010, T011 | None |
| T013 | T011, T012 | None |
| T014 | T008, and issues #4636, #4644, #4646, #4647 closed | None |
| T-LOCAL-GATES | T009 to T014 | None |
| T-PR | T-LOCAL-GATES | None |
| T-REMOTE-CI | T-PR | None |
| T-MERGE | T-REMOTE-CI and orchestrator authorization | None |

Group B tasks share one file. They add different test functions to `test_parity.py`. Run them in one editing session, or in separate branches that rebase cleanly.

## Test Plan Summary

The plan names 28 test functions and 32 test cases. Two functions are parametrized with three cases each.

| Module | Functions | Cases | Task | Requirements covered |
| - | - | - | - | - |
| `test_parity.py` | 24 | 28 | T002 to T008 | FR-001 to FR-012, FR-016, FR-017 |
| `test_portal_browser.py` | 4 | 4 | T011 | FR-013, FR-014, FR-020 |

Test functions in `test_parity.py`, by task:

- T003: `test_health_reply_keeps_exact_shape`, `test_ready_reply_unchanged_with_converter`, `test_existing_routes_keep_status_codes` (three cases).
- T004: `test_converter_post_without_token_returns_400` (three cases), `test_json_client_gets_csrf_expired_answer`, `test_html_client_gets_html_csrf_answer`, `test_api_prefix_keeps_json_csrf_answer`, `test_prefix_without_slash_redirects_before_parse`.
- T005: `test_debug_off_in_real_factory`, `test_container_runner_forces_debug_false`, `test_oversize_converter_body_returns_413`, `test_error_bodies_hide_traceback_and_source`, `test_converter_page_is_html_with_no_store`.
- T006: `test_logs_omit_source_name_and_secret`, `test_session_holds_digest_only`, `test_converter_package_imports_no_network_module`, `test_offline_journey_opens_no_socket`.
- T007: `test_route_allowlist_has_no_cloud_write_route`, `test_other_upload_routes_keep_flask_limits`, `test_registration_refused_without_request_class`, `test_compose_has_no_converter_service`.
- T008: `test_comparison_rows_have_dispositions`, `test_every_row_links_test_or_task`, `test_handover_state_matches_shared_files`.

Test functions in `test_portal_browser.py`, by task: T011 adds `test_nav_entry_opens_converter_in_real_portal`, `test_upload_preview_review_export_in_real_portal`, `test_invalid_upload_shows_safe_error`, and `test_evidence_path_stays_under_test_artifacts`.

Existing tests cover FR-015, FR-018, and FR-019 through the regression run, the nested package guard, and the changelog fragment guard. Storage exposure tests from T014 are not counted until issue #4636 or #4643 writes private files.
