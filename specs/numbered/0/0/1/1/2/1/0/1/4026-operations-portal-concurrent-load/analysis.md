# Verification and specification analysis

## Requirement coverage

| Requirement | Task | Evidence |
| --- | --- | --- |
| FR-001, SC-001 | T003-T005 | Sixteen simultaneous first requests construct exactly one executor. |
| FR-002, SC-002 | T003, T007 | Route response assertions and existing portal workflow tests. |
| FR-003, SC-004 | T003, T005 | A blocked synthetic submission does not hold the initialization lock. |
| FR-004 | T003 | Separate applications retain separate executors. |
| FR-005, SC-003 | T003 | Constructor failure propagates and a later request succeeds. |

Nine requirements and outcomes map to seven tasks. Coverage is 100 percent.
No ambiguity, duplicate requirement, unmapped task, or functional coverage gap remains.
The plan records existing structural debt and its separate remediation.
The explicit user restriction excludes merge and deployment.
Optional commit hooks remain deferred to one feature commit. Disabled companion hooks do not execute.
The app-managed branch replaces the branch-creation hook.

## Regression proof

Before the repair:

```sh
.venv/bin/python -m pytest tests/unit/web_portal/test_operation_executor_concurrency.py::test_simultaneous_first_requests_construct_one_executor -q
```

Result: `1 failed in 0.30s`. The construction assertion reported `16 == 1`.
All 16 requests reached their response assertions before the construction check failed.

After the repair:

```sh
.venv/bin/python -m pytest tests/unit/web_portal/test_operation_executor_concurrency.py tests/unit/web_portal/test_event_bus_deadlock.py tests/unit/web_portal/test_portal_stream_thread_release.py tests/e2e/web_portal/test_portal_smoke.py tests/e2e/web_portal/test_operations_panel_workflow.py -q
```

Result: `42 passed in 10.97s`.
The focused coverage run found no missing line or branch in `_get_executor()`.
This evidence proves the initialization repair, not the absence of every possible container timeout.

## Local gates

| Command | Actual result |
| --- | --- |
| `.venv/bin/python -m ruff check .` | `All checks passed!` |
| `.venv/bin/python -m black --check .` | `2483 files would be left unchanged.` |
| `.venv/bin/python -m py_compile web_portal/routes/operations.py tests/unit/web_portal/test_operation_executor_concurrency.py` | Exit 0, no output. |
| `.venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success: no issues found in 860 source files` |
| `.venv/bin/python -m bandit -c pyproject.toml web_portal/routes/operations.py -q` | Exit 0, no findings. |
| `.venv/bin/python -m pydocstyle web_portal/routes/operations.py tests/unit/web_portal/test_operation_executor_concurrency.py` | Exit 0, no output. |
| `.venv/bin/python -m interrogate web_portal/routes/operations.py --fail-under 90` | `actual: 96.8%` |
| `.venv/bin/python -m pytest tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_move_module_guidance.py -q` | `32 passed, 1 skipped in 0.74s`. The skipped check requires a pull request event. |
| `.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --roots tests/unit/web_portal/test_operation_executor_concurrency.py` | One file checked, zero findings, `gate: 0 new findings vs baseline`. |
| `.venv/bin/symbol-diff --base origin/main web_portal/routes/operations.py` | Exit 1 for intentional additions: `threading` and `_EXECUTOR_INIT_LOCK`. No lost name. |

The STE check read all nine initial Markdown files. Each score was 92 or above.
The repaired helper has 18 lines and cyclomatic complexity 3.

## Existing supplementary failures

The full route complexity check fails for `_build_replay` at 15 and `_fetch_msp_grants` at 13.
The unchanged base reports the same values. Issue #4409 records the separate repair.

Direct mypy checking of `web_portal/routes/operations.py` reports 42 existing errors.
A second run uses `--shadow-file` with the unchanged base source and reports the same 42 errors.
The documented CI type-check selection passes. This repair does not change the typing configuration or suppress errors.

No dependency, container, menu, production data, or Mist transport changed.
Dependency audit, container build, menu generation, and live operation sweeps are not applicable.
All runtime requests used local synthetic clients without a Mist session.
