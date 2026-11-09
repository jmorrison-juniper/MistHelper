# Other-device page-status repair evidence

## Result

Every page now requires a successful integer HTTP status and a valid record list.
The exporter uses the existing SDK `get_next` helper instead of unchecked `get_all`.
It writes only after the final page succeeds.
Failed or missing pages discard the complete aggregate and produce sanitized failure feedback.
Transforms and the writer remain outside the request exception boundary.

## Preservation before repair

The original #1794 commit remains unchanged:
`63dd076f7c1d96eda6c68a01237e48d6d29cf59b`.

The session artifact folder holds these verified SHA-256 snapshots:

| Artifact | SHA-256 |
|---|---|
| `issue-1794-preserved.patch` | `22386aa46e4f3a145bd4c2057f4f9f6151fe998d72e0eefa8a4974565bed4b7a` |
| `issue-1794-preserved-exporter.py` | `0e51f41c58cf2b7f46230d3ef42d0c262addebb4ef776ec3ac37595b2f0c3ae1` |
| `issue-1794-preserved-tests.py` | `5b85b1a272738b2a12939ddfee98af18dbb3be6b201fec9ff2d2dd11f941c366` |

`issue-1794-preserved-sha256.txt` records the same values.
The patch includes the complete #1794 commit, not only its product diff.
All three hashes were verified again after the repair.

## Precise file set

Only these existing files change:

- `src/operations/exporting/export/site_other_device_events_exporter.py`
- `tests/unit/export/test_site_other_device_events_exporter.py`

The new release note is `changelog.d/issue-4709-other-device-page-status.md`.
Nine new records reside in this feature directory:
`spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`,
`design/data-model.md`, `design/quickstart.md`, `design/contracts/menu.md`, and `design/checklists/requirements.md`.
No #1794 feature record or release note changes.

## Before and after evidence

The initial test extension ran against the preserved #1794 product code:

```text
.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py -q
```

Result: **6 failed, 26 passed**.
The two initial error cases exposed false empty-data messages for 403 and 503.
Four subsequent-page cases covered list and search pages with blank or JSON HTTP 503 bodies.
The list/blank case called the writer with first-page rows before the repair.
The search cases returned to the menu but omitted the useful HTTP status.
The full failure output remains in the session artifact `issue-4709-before.txt`.

The repaired test file contains **44 passing cases**.
The combined run adds 11 managed-record guards, for **55 passed**.
The exporter has **72 statements, zero missing statements, and 100 percent statement coverage**.

The tests use real `requests.Response` objects through the installed SDK request and response path.
List pagination uses real `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` headers.
Search pagination uses the real `next` response field.
Both paths use SDK `get_next` to make the subsequent mocked HTTP request.

No initial or later failed page reaches the writer or reports `records exported`.
HTTP failures report `Other-device event page failed: HTTP 403` or `HTTP 503`.
They also report `! Error fetching other-device event data. Please try again.`
Valid empty lists and `results` lists retain `! No other-device event data found for this site`.
Complete single-page and multiple-page results preserve row order, normalization, filename, and endpoint metadata.

## Exact local checks

All commands run from this worktree.

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py tests/guardrails/test_process_folder_structure.py -q --cov=src.operations.exporting.export.site_other_device_events_exporter --cov-report=term-missing` | 55 passed. Exporter coverage: 100 percent. |
| `.venv/bin/python -m ruff check src/operations/exporting/export/site_other_device_events_exporter.py tests/unit/export/test_site_other_device_events_exporter.py` | All checks passed. |
| `.venv/bin/python -m black --check src/operations/exporting/export/site_other_device_events_exporter.py tests/unit/export/test_site_other_device_events_exporter.py` | 2 files unchanged. |
| `.venv/bin/python -m mypy src/operations/exporting/export/site_other_device_events_exporter.py --config-file pyproject.toml` | No issues in 1 source file. |
| `.venv/bin/python -m py_compile src/operations/exporting/export/site_other_device_events_exporter.py tests/unit/export/test_site_other_device_events_exporter.py` | Passed without output. |
| `.venv/bin/bandit -c pyproject.toml src/operations/exporting/export/site_other_device_events_exporter.py -q` | No findings. |
| `.venv/bin/python -m radon cc src/operations/exporting/export/site_other_device_events_exporter.py -j \| .venv/bin/complexity-gate --max 10` | All functions within the threshold. |
| `.venv/bin/pydocstyle src/operations/exporting/export/site_other_device_events_exporter.py` | Passed without output. |
| `.venv/bin/interrogate src/operations/exporting/export/site_other_device_events_exporter.py --fail-under 90 --generate-badge /Users/jmorrison/.copilot/session-state/f2ce7c94-6dfc-4388-9af0-63825b76144a/files/issue-4709-docstrings` | Documentation coverage: 100 percent. Badge remains outside the repository. |
| `.venv/bin/python -m pylint src/operations/exporting/export/site_other_device_events_exporter.py --fail-under=9.5` | 9.70/10. Existing protected-access and public-method-count notices remain. |
| `.venv/bin/symbol-diff --base HEAD src/operations/exporting/export/site_other_device_events_exporter.py` | Before commit: no module-level name changed. |
| `.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | 1 passed. Four inputs read and validated. |
| `git diff --check` | Passed. |

Focused test-quality command:

```text
.venv/bin/test-quality-analyzer --gate --include-mist-api --roots tests/unit/export/test_site_other_device_events_exporter.py --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --report /Users/jmorrison/.copilot/session-state/f2ce7c94-6dfc-4388-9af0-63825b76144a/files/issue-4709-quality-report.json --summary /Users/jmorrison/.copilot/session-state/f2ce7c94-6dfc-4388-9af0-63825b76144a/files/issue-4709-quality-summary.md --log-level WARNING
```

Result: **1 file checked, zero findings, zero parse errors, zero new findings versus baseline**.
No baseline changes occurred.

The initial style check identified three long test comments. Shorter comments repaired them.
The initial Pylint result was 9.39 because exact-type checks violated its type-check rule.
Explicit integer and boolean guards repaired that cause. The final result is 9.70.
Interrogate rejected an unsupported `--no-generate-badge` option.
The corrected command directs the badge into the session artifact folder.

## Specification analysis

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001: Validate every status | T002, T003, T004 | Initial and subsequent HTTP failures, absent status, and invalid statuses. |
| FR-002: Reject incomplete output | T003, T004 | No writer or completion message after any failed page or missing promised page. |
| FR-003: Preserve complete results | T005 | Empty, single-page, and two-page tests for both payload shapes. |
| FR-004: Preserve #1794 boundaries | T005 | Local failures propagate, external failures return, and logs omit private strings. |
| FR-005: Verify offline | T002, T005 | DNS/socket blockers, real SDK responses, mocked HTTP session, and mocked writer. |

All five requirements map to the seven completed tasks.
No uncovered requirement, unresolved clarification, or cross-artifact conflict remains.
The class has five methods. New methods have 7, 23, and 19 physical lines.
The menu method now has 18 lines. The unchanged persistence method retains its existing 27-line debt.
The feature root has five children. The design directory has five children.
Optional commit hooks remain deferred until validation. Disabled companion hooks do not run.

## Intentional changes and limitations

- Every non-2xx, absent, boolean, or non-integer status now fails instead of producing no data.
- Malformed successful bodies now fail instead of proving emptiness.
- Failed later pages discard earlier rows. No partial output schema is introduced.
- SDK transport failures without a response now report failure at either page stage.
- Exporter logs exclude arbitrary exception text, body data, and next-page URLs.
  SDK-internal logging remains outside this repair and is replaced in the tests.
- No live Mist call, SSH operation, firmware operation, or production database access occurs.
- PowerShell remains absent. Executable route tests and selector-writing setup commands do not run.
  The inspected numeric route and managed-tree guards verify the record layout.
- Full-suite tests, dependency audits, and full-tree gates do not run for this bounded change.
- One existing Dash plugin deprecation warning remains.
- No push, pull request, rebase, merge, issue closure, Git configuration change, or credential change occurs.
