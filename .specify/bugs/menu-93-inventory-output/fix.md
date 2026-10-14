# Bug Fix: Show Menu 93 Inventory Output

- **Slug**: menu-93-inventory-output
- **Fixed**: 2026-10-13T23:58:31Z
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The portal now requires bounded, explicit empty-result wording. An unrelated database warning stays separate, and Menu 93 keeps its inventory file in completed output.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `web_portal/services/operation.py` | modified | Require bounded wording and an explicit empty-result outcome. |
| `tests/unit/web_portal/test_portal_terminal_state_4025.py` | modified | Reject a warning with later data-row wording and accept an empty inventory result. |
| `tests/unit/test_operation_output_file_discovery.py` | modified | Keep the inventory cache hidden when a real no-data message appears. |
| `tests/unit/web_portal/test_portal_run_isolation.py` | modified | Check the completed response and event for Menu 93. |
| `tests/e2e/web_portal/test_issue_4037_menu_93_output.py` | added | Check the completed Menu 93 result through the no-browser Flask client. |
| `.specify/feature.json` | modified | Point to the managed feature record. |
| `specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/spec.md` | added | Record user needs and acceptance scenarios. |
| `specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/checklists/requirements.md` | added | Record specification quality checks. |
| `changelog.d/issue-4037-menu-93-inventory-output.md` | added | Record the user-visible fix. |
| `.specify/bugs/menu-93-inventory-output/assessment.md` | added | Record the issue assessment. |
| `.specify/bugs/menu-93-inventory-output/fix.md` | added | Record this fix. |

## Tests Added or Updated

- `tests/unit/web_portal/test_portal_terminal_state_4025.py::test_a_database_host_warning_does_not_classify_as_an_empty_result` — checks both the reported warning and the current exporter warning.
- `tests/unit/marvis/actions/test_portal_contract.py::TestPortalRuns::test_a_category_without_open_actions_completes_with_a_reason` — confirms an empty open-action filter keeps its reason.
- `tests/unit/marvis/actions/test_portal_contract.py::TestPortalRuns::test_a_category_without_closed_actions_completes_with_a_reason` — confirms an empty closed-action filter keeps its reason.
- `tests/e2e/web_portal/test_juniper_menus_browser.py::TestTheJuniperMenusAreReadableInTheBrowser::test_menu_301_reports_that_the_access_check_passed` — confirms Menu 301 keeps its no-file reason.
- `tests/unit/web_portal/test_portal_terminal_state_4025.py::test_a_database_host_warning_does_not_classify_as_an_empty_result` — directly checks the Marvis and Menu 301 phrases from issue #4216, as well as unrelated database warnings and known empty results.
- `tests/unit/test_operation_output_file_discovery.py::TestRunRecordMerge::test_finalize_drops_inventory_cache_when_the_run_reports_no_data` — keeps a prompt cache out of a true empty result.
- `tests/unit/web_portal/test_portal_run_isolation.py::test_menu_93_database_warning_keeps_inventory_in_status_and_sse` — checks the file in the completed response and completion event.
- `tests/e2e/web_portal/test_issue_4037_menu_93_output.py::test_menu_93_database_warning_keeps_inventory_in_completed_result` — checks the completed status through the no-browser Flask client.

## Local Verification

- `.venv/bin/python -B -m pytest -q tests/e2e/web_portal/test_issue_4037_menu_93_output.py` — 1 passed.
- `.venv/bin/python -B -m pytest -q tests/e2e/web_portal/test_issue_4037_menu_93_output.py tests/unit/test_operation_output_file_discovery.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/unit/web_portal/test_portal_run_isolation.py tests/unit/web_portal/test_portal_silent_completion.py tests/guardrails/test_process_folder_structure.py` — 55 passed.
- `.venv/bin/python -B -m pytest -q tests/unit/marvis/actions/test_portal_contract.py::TestPortalRuns::test_a_category_without_open_actions_completes_with_a_reason tests/unit/marvis/actions/test_portal_contract.py::TestPortalRuns::test_a_category_without_closed_actions_completes_with_a_reason tests/e2e/web_portal/test_juniper_menus_browser.py::TestTheJuniperMenusAreReadableInTheBrowser::test_menu_301_reports_that_the_access_check_passed` — 3 passed.
- `.venv/bin/python -B -m pytest -q tests/e2e/web_portal/test_issue_4037_menu_93_output.py tests/e2e/web_portal/test_juniper_menus_browser.py tests/unit/test_operation_output_file_discovery.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/unit/web_portal/test_portal_run_isolation.py tests/unit/web_portal/test_portal_silent_completion.py tests/unit/marvis/actions/test_portal_contract.py tests/guardrails/test_process_folder_structure.py` — 101 passed.
- `.venv/bin/ruff check web_portal/services/operation.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/e2e/web_portal/test_issue_4037_menu_93_output.py` — passed.
- `.venv/bin/black --check web_portal/services/operation.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/e2e/web_portal/test_issue_4037_menu_93_output.py` — 3 files unchanged.
- `.venv/bin/black --check web_portal/services/operation.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/unit/marvis/actions/test_portal_contract.py` — 3 files unchanged.
- `.venv/bin/python -B -m py_compile web_portal/services/operation.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/unit/marvis/actions/test_portal_contract.py` — passed.
- `.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` — 1 passed. The guard read and checked all four inputs.
- `.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` — 4 changed test files checked, 0 new findings.
- `.venv/bin/python -B -m pytest -q tests/guardrails/test_process_folder_structure.py` — 5 passed.
- `.venv/bin/ruff check .` — All checks passed.
- `.venv/bin/black --check .` — 2,382 files would remain unchanged.
- `.venv/bin/python -B -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` — Success. Mypy checked 833 source files.
- `.venv/bin/python -B -m py_compile web_portal/services/operation.py` — Passed with no output.
- `.venv/bin/bandit -c pyproject.toml -r web_portal/services/operation.py -q` — Passed with no output.
- `.venv/bin/symbol-diff --base origin/main web_portal/services/operation.py` — No module-level name changed.
- `.venv/bin/ruff check web_portal/services/operation.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/unit/marvis/actions/test_portal_contract.py` — passed.
- `.venv/bin/bandit -c pyproject.toml -r web_portal/services/operation.py -q` — passed.
- `.venv/bin/symbol-diff --base origin/main web_portal/services/operation.py` — no module-level name changed.
- `git diff --check` — passed.
- `.venv/bin/ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/spec.md specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/checklists/requirements.md changelog.d/issue-4037-menu-93-inventory-output.md .specify/bugs/menu-93-inventory-output/assessment.md` — Passed. Scores were 97, 95, 99, and 97.
- `git diff --check` — Passed with no output.

## Deviations from Assessment

The issue comment confirms the warning begins with "no database host answers." The complete warning is unavailable. The regression uses a synthetic continuation about later data rows. The classifier accepts a result noun after at most two subject words. It preserves the data-export, Juniper RMA, Marvis, and Menu 301 no-output reasons. Issue #4216 reported the Marvis and Menu 301 regressions. Direct classifier tests cover those messages.

## Follow-ups

- Wait for the required checks on the pull request that fixes #4037 and #4216.
- Do not merge until all required checks pass.
- Use mocked data only. No production credentials, live Mist requests, Snowflake, or containers were used.
