# Other-device event audit evidence

## Result and file ownership

The broad handler now covers only the SDK endpoint and pagination calls.
It retains the existing fallback because malformed remote pages have no shared SDK exception type.
Local transformation and writer errors now reach the caller.
Exporter error messages use fixed text without exception details or tracebacks.

Only these product and test files change:

- `src/operations/exporting/export/site_other_device_events_exporter.py`
- `tests/unit/export/test_site_other_device_events_exporter.py`
- `changelog.d/issue-1794-other-device-events-boundaries.md`

The remaining files are feature-local records in this directory:
`spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`,
`design/data-model.md`, `design/quickstart.md`, `design/contracts/menu.md`, and `design/checklists/requirements.md`.

The initial commit is `3964d21d03f9f5717cb8eafb7272ecff21f5362a`.
No push, rebase, merge, issue closure, Git configuration change, or credential change occurs.

## Before and after reproduction

The original five tests passed after dependency restoration.
The expanded test file produced **9 failures and 14 passes** before the product repair.
Six failures exposed private exception text from endpoint or pagination errors.
Three failures showed that transformation and writer errors did not reach the caller.

The repaired exporter passed **23 tests**.
The final combined run passed **34 tests**, including 11 managed-record guards.
Exporter statement coverage is **100 percent**, with 42 statements and no missing statements.

Tests block socket construction, connection creation, address resolution, and hostname resolution.
They mock the writer and replace shared dependencies.
Real SDK contract tests use `APIRequest` with a mocked HTTP session.
They do not construct the credential-loading `APISession`.
They exercise the real endpoint, pagination, response handling, and transformation path.

The malformed second-page reproduction returns a successful first search page with `next="/next"`.
The second HTTP response contains `{"unexpected": "synthetic-private-response"}`.
The installed `get_all` raises `KeyError` because it indexes `response.data["results"]`.
The narrowed handler retains the error message and returns without writing partial rows.

## Separate HTTP response-status finding

Run this exact offline reproduction:

```text
.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py::TestInstalledSdkContract::test_error_status_becomes_empty_separate_finding -q
```

The test supplies a real `requests.Response` with status **403**, then **503** through parameterization.
Each response contains `{"error": "synthetic failure"}`.
The mocked HTTP session returns the response. No DNS or socket access is possible.
The expected operator behavior is a request-failure message, not an empty-data message.

Both statuses instead produce this exporter message:

```text
! No other-device event data found for this site
```

Neither status produces `Error fetching` or calls the writer.
The SDK retains the error status and body, but `get_all` ignores `status_code`.
It returns an empty list for the error dictionary because that dictionary has no `results`.

The affected installed mistapi 0.64.1 path is:

```text
searchSiteOtherDeviceEvents
  -> APISession.mist_get (inherited from APIRequest)
  -> APIRequest._request_with_retry
  -> APIResponse
  -> mistapi.get_all
  -> SiteOtherDeviceEventsExporter._persist_events
```

Subsequent pages additionally use `get_next` and `mist_get`.
This finding remains unchanged. The coordinator will check for an existing issue before any separate repair.

## Exact local checks

All commands run from this worktree.

| Command | Result |
|---|---|
| `python3 -m pytest tests/unit/export/test_site_other_device_events_exporter.py -q` | Initially blocked: `No module named pytest`. |
| `uv sync --locked --extra dev` | Passed. Created the local environment without bootstrap or Git changes. |
| `.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py -q` | Original: 5 passed. New tests before repair: 9 failed, 14 passed. After repair: 23 passed. |
| `.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py tests/guardrails/test_process_folder_structure.py -q --cov=src.operations.exporting.export.site_other_device_events_exporter --cov-report=term-missing` | 34 passed. Exporter coverage: 100 percent. |
| `.venv/bin/python -m ruff check src/operations/exporting/export/site_other_device_events_exporter.py tests/unit/export/test_site_other_device_events_exporter.py` | Passed: `All checks passed!` |
| `.venv/bin/python -m black --check src/operations/exporting/export/site_other_device_events_exporter.py tests/unit/export/test_site_other_device_events_exporter.py` | Passed: 2 files unchanged. |
| `.venv/bin/python -m mypy src/operations/exporting/export/site_other_device_events_exporter.py --config-file pyproject.toml` | Passed: no issues in 1 source file. |
| `.venv/bin/python -m py_compile src/operations/exporting/export/site_other_device_events_exporter.py tests/unit/export/test_site_other_device_events_exporter.py` | Passed with no output. |
| `.venv/bin/bandit -c pyproject.toml src/operations/exporting/export/site_other_device_events_exporter.py -q` | Passed with no findings. |
| `.venv/bin/python -m radon cc src/operations/exporting/export/site_other_device_events_exporter.py -j \| .venv/bin/complexity-gate --max 10` | Passed: all functions within the threshold. |
| `.venv/bin/pydocstyle src/operations/exporting/export/site_other_device_events_exporter.py` | Passed with no output. |
| `.venv/bin/interrogate src/operations/exporting/export/site_other_device_events_exporter.py --fail-under 90` | Passed: 100 percent documentation coverage. Removed its generated badge afterward. |
| `.venv/bin/pylint src/operations/exporting/export/site_other_device_events_exporter.py --fail-under=9.5` | Passed: 9.50/10. Existing protected-access and public-method-count notices remain. |
| `.venv/bin/symbol-diff --base HEAD src/operations/exporting/export/site_other_device_events_exporter.py` | Passed before commit: no module-level name changed. |
| `.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | Passed: 1 test, 4 inputs read and validated. |
| `git diff --check` | Passed. |

Focused analyzer command:

```text
.venv/bin/test-quality-analyzer --gate --include-mist-api --roots tests/unit/export/test_site_other_device_events_exporter.py --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report /Users/jmorrison/.copilot/session-state/f2ce7c94-6dfc-4388-9af0-63825b76144a/files/quality-report.json --summary /Users/jmorrison/.copilot/session-state/f2ce7c94-6dfc-4388-9af0-63825b76144a/files/quality-summary.md --log-level WARNING
```

Result: **1 file checked, 0 findings, 0 parse errors, 0 new findings versus baseline**.
The default Mist API exclusion initially examined no modules and exited 2.
The explicit inclusion then identified the existing empty-result test without a direct assertion.
That test now also asserts the operator message. No baseline changes occurred.

The first style run found import ordering and long comments. Formatting and shorter comments repaired those findings.
The first document command supplied a directory where the tool requires files.
The corrected file-only run checked 9 documents with no skipped files. Scores ranged from 91 to 99.
The final document check also includes this analysis file.

## Specification analysis

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001: Preserve normal behavior | T005 | Selection, empty, writer-contract, and real two-page tests. |
| FR-002: Preserve local defects | T003, T004 | Flatten, multiline escape, and writer failures reach the caller unchanged. |
| FR-003: Protect exception text | T003, T004 | Both external stages test three exception types and multiline private text. |
| FR-004: Preserve external fallback | T001, T005 | Real malformed page and connection/timeout cases. |
| FR-005: Remain offline | T002 | Network-blocking fixture, mocked HTTP session, and mocked writer. |

Five requirements map to seven tasks. Requirement coverage is 100 percent.
No uncovered requirement, terminology conflict, or unresolved clarification remains.
The plan records existing method-length and process-folder debt without expanding this repair.
Optional commit hooks were deferred. Disabled companion hooks did not execute.
The existing app branch replaced branch creation, as required by the session.

## Limitations

- The retained broad handler is intentional. It does not reduce the repository-wide broad-handler count.
- Exception details no longer appear in exporter messages. The request-start message still identifies the selected site.
- Third-party SDK logging can contain exception text. Tests replace that logger to isolate exporter privacy.
- Local exceptions now propagate. This slice does not change any higher-level caller policy.
- No live Mist call, SSH operation, firmware operation, or production database access occurred.
- Full-suite tests, dependency audits, and full-tree gates did not run for this bounded change.
- PowerShell is absent. Executable route tests and selector-writing setup scripts did not run.
  The inspected route algorithm and managed-tree tests validate the record layout.
- Pytest reports one existing Dash plugin deprecation warning.
