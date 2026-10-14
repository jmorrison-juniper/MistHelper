# Bug Fix: Show Menu 93 Inventory Output

- **Slug**: menu-93-inventory-output
- **Fixed**: 2026-10-13T23:58:31Z
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The portal now treats a standalone database warning as separate from an empty result. Menu 93 keeps its inventory file in the completed response and completion event.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `web_portal/services/operation.py` | modified | Require an empty-result term instead of any occurrence of "no". |
| `tests/unit/web_portal/test_portal_terminal_state_4025.py` | modified | Keep reported and current database warnings out of empty-result classification. |
| `tests/unit/test_operation_output_file_discovery.py` | modified | Keep the inventory cache hidden when a real no-data message appears. |
| `tests/unit/web_portal/test_portal_run_isolation.py` | modified | Check the completed response and event for Menu 93. |
| `.specify/feature.json` | modified | Point to the managed feature record. |
| `specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/spec.md` | added | Record user needs and acceptance scenarios. |
| `specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/checklists/requirements.md` | added | Record specification quality checks. |
| `changelog.d/issue-4037-menu-93-inventory-output.md` | added | Record the user-visible fix. |
| `.specify/bugs/menu-93-inventory-output/assessment.md` | added | Record the issue assessment. |
| `.specify/bugs/menu-93-inventory-output/fix.md` | added | Record this fix. |

## Tests Added or Updated

- `tests/unit/web_portal/test_portal_terminal_state_4025.py::test_a_database_host_warning_does_not_classify_as_an_empty_result` — checks both the reported warning and the current exporter warning.
- `tests/unit/test_operation_output_file_discovery.py::TestRunRecordMerge::test_finalize_drops_inventory_cache_when_the_run_reports_no_data` — keeps a prompt cache out of a true empty result.
- `tests/unit/web_portal/test_portal_run_isolation.py::test_menu_93_database_warning_keeps_inventory_in_status_and_sse` — checks the file in the completed response and completion event.

## Local Verification

- `.venv/bin/python -B -m pytest -q tests/unit/test_operation_output_file_discovery.py tests/unit/web_portal/test_portal_terminal_state_4025.py tests/unit/web_portal/test_portal_run_isolation.py tests/unit/web_portal/test_portal_silent_completion.py` — 49 passed.
- `.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` — 1 passed. The guard read and checked all four inputs.
- `.venv/bin/python -B -m pytest -q tests/guardrails/test_process_folder_structure.py` — 5 passed.
- `.venv/bin/ruff check .` — All checks passed.
- `.venv/bin/black --check .` — 2,382 files would remain unchanged.
- `.venv/bin/python -B -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` — Success. Mypy checked 833 source files.
- `.venv/bin/python -B -m py_compile web_portal/services/operation.py` — Passed with no output.
- `.venv/bin/bandit -c pyproject.toml -r web_portal/services/operation.py -q` — Passed with no output.
- `.venv/bin/symbol-diff --base origin/main web_portal/services/operation.py` — No module-level name changed.
- `.venv/bin/ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/spec.md specs/numbered/0/0/1/1/3/1/3/2/4167-menu93-inventory-output/checklists/requirements.md changelog.d/issue-4037-menu-93-inventory-output.md .specify/bugs/menu-93-inventory-output/assessment.md` — Passed. Scores were 97, 95, 99, and 97.
- `git diff --check` — Passed with no output.

## Deviations from Assessment

The assessment found that the current exporter warning, "Polyglot database hosts do not answer," does not match the broad `no ` marker. The issue reproduction describes a standalone warning that does match it. The tests cover both warning forms. The fix narrows the classifier and keeps true no-data behavior.

## Follow-ups

- Run the test-quality analyzer after the implementation commit.
- Open a pull request for #4037 and wait for all required checks.
- Use mocked data only. No production credentials, live Mist requests, Snowflake, or containers were used.
