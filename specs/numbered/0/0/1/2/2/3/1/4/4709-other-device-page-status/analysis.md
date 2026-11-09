# Other-device page-status repair evidence

## Result

Every page now requires a successful integer HTTP status and a valid record list.
The exporter uses the existing SDK `get_next` helper instead of unchecked `get_all`.
It writes only after the final page succeeds.
Failed or missing pages discard the complete aggregate and produce sanitized failure feedback.
Local validation, collection, transforms, and the writer remain outside the request exception boundary.

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
Ten new records reside in this feature directory:
`spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`,
`design/data-model.md`, `design/quickstart.md`, `design/contracts/menu.md`, `design/contracts/cursor.md`,
and `design/checklists/requirements.md`.
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
| FR-006: Reject malformed records and cursors | T008 | Direct repeats, longer cycles, invalid cursors, and malformed records. |
| FR-007: Preserve SDK completion and local boundaries | T009 | Empty-string completion and unexpected local defects propagate without cloud error messages. |

All seven requirements map to the nine completed tasks.
No uncovered requirement, unresolved clarification, or cross-artifact conflict remains.
The class has five methods. Page validation and collection remain separate methods.
The menu method now has 18 lines. The unchanged persistence method retains its existing 27-line debt.
The feature root has five children. The design directory has five children.
Optional commit hooks remain deferred until validation. Disabled companion hooks do not run.

## Cursor extension

The coordinator requested cursor safety after local commit `4ee8f9d5bae65dfe16d784fa391a97dee82d088f`.
That commit and the preserved #1794 commit remain unchanged.

`PickerPageReader.read` and `PolicyResponse.collect` provide the requested-cursor set pattern.
The exporter uses this invariant locally without their domain-specific exception classes.
The first cursor extension treated only `None` as completion.
The correction below also accepts the exact empty string.
Whitespace-only, non-string, and previously requested cursors fail before the next request.
Successful page lists must contain dictionary records.
Every failure discards accumulated rows and retains the sanitized menu fallback.

Before the extension, this exact command produced **13 failed** cases:

```text
.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py::TestPaginationCursorSafety -q
```

The full output remains in the session artifact `issue-4709-cursor-before.txt`.
Finite sentinel responses prevent the failing cycle reproductions from hanging.
The direct repeat made three requests instead of two.
The longer cycle made four requests instead of three.
Both incorrectly reached the writer before the extension.
Malformed cursors either implied completion or caused another request.
Malformed rows reached transformation before the extension.

After the extension, the exact combined pytest command above reports **68 passed**.
This includes 57 exporter cases and 11 managed-record guards.
Exporter coverage is **100 percent**, with 81 statements and zero missing statements.
The existing Dash plugin warning remains.

The exact Ruff, Black, mypy, compilation, Bandit, complexity, pydocstyle, interrogate, symbol, and input-preflight commands above pass again.
Pylint now reports **9.74/10**, with the same two existing notices.
The first Black check requested formatting. Black repaired both owned Python files, and the final check passes.
No new failure suppression or baseline change occurs.
The focused analyzer command above also passes with the cursor-extension tests.
It checks one file, reports zero findings and parse errors, and reports zero new findings.
Its cursor-extension reports use the `issue-4709-cursor-quality` prefix in the session artifact folder.
STE passes for all seven updated Markdown files, with scores from 85 through 98.

## Independent verification corrections

Independent offline verification identified two defects in commit `193789329c0754d0d4d84e467f65f7095ca18b65`.
The documented `next` string has no `minLength`, and installed `mistapi.get_all` treats `""` as terminal.
The coordinator corrected the earlier instruction to reject every blank cursor.
Both `None` and `""` now preserve terminal rows.
Whitespace-only, non-string, and repeated cursors remain invalid.

The broad `_fetch_events` catch also covered local `_collect_events` and `_page_records` execution.
A local `NameError` therefore became a false SDK failure.
`_fetch_events` now performs only one endpoint or SDK `get_next` call inside its catch.
Dependency resolution, logging, page validation, and collection execute outside that catch.
Known invalid page shapes and cursors log fixed messages and return a failed result explicitly.
No exception class acts as a proxy for malformed remote data.
Unexpected local `NameError` and `ValueError` exceptions propagate with their original identity and no private log text.
The later-page regression also verifies this boundary after a successful follow-up request.

Before the correction, this exact command reported **5 failed, 1 passed**:

```text
.venv/bin/python -m pytest tests/unit/export/test_site_other_device_events_exporter.py::TestLocalCollectionBoundaries -q
```

The output remains in session artifact `issue-4709-boundary-before.txt`.
The exact empty-string case failed, while the `None` case passed.
Four local-defect cases failed because the menu swallowed their exceptions.
The later-page regression was added after that reproduction.

The final combined pytest command above reports **74 passed**, comprising 63 exporter cases and 11 managed-record guards.
Exporter coverage is **100 percent**, with 85 statements and zero missing statements.
The unchanged status, partial-page, external-call, privacy, success, and empty-result scenarios remain covered.
The exact Ruff, Black, mypy, compilation, Bandit, complexity, documentation, symbol, and input-preflight commands above pass.
Pylint reports **9.75/10**, with its existing two notices.
The focused API-inclusive analyzer checks one file and reports zero findings, zero parse errors, and zero new findings.
Its reports use the `issue-4709-boundary-quality` prefix in the session artifact folder.
One long test comment failed Ruff initially. A shorter comment repaired it before the final successful run.
The class still has five methods.
Their lengths are 27, 20, 21, 19, and 24 lines, including unchanged persistence debt.
All prior commits remain unchanged. The publication hold and source ownership remain active.

## Advertised completeness

The schema `response_events_other_devices_search` defines `total` as matching rows across all pages.
The installed SDK sets `next` from the JSON `next` field. Else it uses three integer `X-Page-*` headers.
A parse error leaves `next` as `None`. The installed `get_all` does not compare a total.

The red run added 14 cases. Seven failed and seven passed before the repair.
The seven failures covered a short JSON total with no `next` and with `next=""`.
They also covered a non-integer page header, partial headers, and text, boolean, and negative totals.
After the repair, the targeted command reported 88 passed with 100 percent exporter coverage.
The exporter has 88 statements. The highest complexity is 10.

## Metadata boundary corrections

Independent verification found three defects in commit `6a4aea6`.
A later page without `total` replaced a known total of 3 with 0, so two of three rows were written.
Three empty `X-Page-*` headers counted as absent, so the page was written.
A 5,000-digit `total` string reached `int` and raised the conversion `ValueError`.

The red run added 6 cases. Before the repair, 4 failed and 80 passed.
The failures were the empty headers, one empty header, the 5,000-digit total, and the later absent total.
After the repair, the targeted command reported 95 passed with 100 percent exporter coverage.
The page validator has complexity 9, and no module-level name changed.

## Cursor destination safety

Independent verification found that the SDK appends the `next` cursor to `https://` and the cloud host.
A synthetic cursor that starts with `@` moved the next request and its synthetic credential to a different host.
This result needs control of the upstream response. The finding stays private until review.

The red run added 9 unsafe cursor cases. Before the repair, 9 failed and 85 passed.
One case sent a request to `example.invalid`, and one case sent a request to a different host name.
Seven cases sent a second request with a non-API path, whitespace, or a control character.
After the repair, the targeted command reported 105 passed with 100 percent exporter coverage.
A documented cursor still reaches the cloud host with its path and query.

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
- A JSON numeric string such as `"2"` passes as a count. Other text, booleans, and negative values fail.
- Rows above the JSON `total` pass, because events can arrive during a read.
- Valid `X-Page-Total` values receive no row comparison. The SDK cursor uses them.
- A count with more than 18 digits fails as malformed metadata.
- A cursor that does not start with `/api/v1/` fails, even if a later SDK accepts it.
