# Bug Assessment: Menu 93 inventory output is hidden

- **Slug**: menu-93-inventory-output
- **Created**: 2026-10-13T23:48:07Z
- **Source**: Pasted text for issue #4037
- **Verdict**: likely valid, needs reproduction
- **Severity**: medium

## Report (verbatim or summarized)

Issue #4037 reports that Menu 93 writes a valid `SiteInventory.csv` file, but the portal does not show it. The issue comments describe two mocked Flask and browser runs at commit `e0dc054d`. Both runs returned `output_files=[]` in status JSON and completion SSE. Each finalizer logged that it kept zero of one output file names.

The report attributes this to cache filtering and a database-host warning. The issue comment confirms that the mock warning starts with “No database host answers.” The complete warning text is unavailable. The current production warning says “Polyglot database hosts do not answer.” That text does not match the current classifier.

## Symptom

The mocked runs write `SiteInventory.csv`, but the portal reports no output file in its status response or completion event. The expected result is for the completed run to list the valid file.

## Reproduction

1. Run the two mocked Flask and browser cases described in issue #4037 at commit `e0dc054d`.
2. Observe that each run writes a mocked `SiteInventory.csv` file.
3. Observe `output_files=[]` in status JSON and completion SSE, with the finalizer logging that it kept zero of one file names.

The issue comment confirms the warning prefix. It does not provide the complete warning text, fixtures, or commands.

## Suspected Code Paths

- `web_portal/services/operation.py:114` — `NO_OUTPUT_REASON_MARKERS` holds established no-output phrases.
- `web_portal/services/operation.py:144` — `SiteInventory.csv` is classified as a prompt-cache output file.
- `web_portal/services/operation.py:147` — Only menus `1` and `60` are exempt from cache-only filtering. Menu 93 is not listed.
- `web_portal/services/operation.py:1475` — `_no_output_reason()` classifies log lines as empty results.
- `web_portal/services/operation.py:1539` — `_drop_cache_only_empty_result()` removes cache-only names when `_no_output_reason()` finds a match.
- `web_portal/services/operation.py:1591` and `web_portal/services/operation.py:1630` — Completion SSE and status JSON expose the run's filtered `output_files`.
- `src/operations/exporting/export/data_exporter.py:244` — The current standalone warning says database hosts “do not answer.” That exact text does not contain `no `.
- `tests/unit/test_operation_output_file_discovery.py:176` — Existing tests cover removal of a cache-only file for a genuine no-data reason and preservation of the inventory file for Menu 60.

## Root Cause Hypothesis

The reported loss can occur when a standalone log line starts with “No database host answers” and later mentions data or rows. The broad classifier can treat those later words as an empty-result phrase. The cache-only filter then removes `SiteInventory.csv` for Menu 93. The classifier-to-filter path has high confidence because a regression reproduces it with a mocked warning. Confidence in the complete original warning remains limited because the issue does not include its full text. The current production warning does not match the prior classifier.

## Proposed Remediation

**Preferred**: Narrow the no-output classifier so it recognizes bounded, explicit empty-result messages rather than unrelated later data or row mentions. Keep the cache-only filter in place for genuine no-data runs. Do not treat Menu 93 as a prompt-cache export menu, because the file may still be only a cache refresh for other operations.

Add a regression for the confirmed warning prefix with synthetic later data-row wording and a completed Menu 93 run that writes `SiteInventory.csv`. Confirm that the run preserves the file in status JSON and completion SSE. Keep tests for genuine no-data messages and cache-only removal.

**Files likely to change**:

- `web_portal/services/operation.py`
- `tests/unit/test_operation_output_file_discovery.py`
- `tests/unit/web_portal/test_portal_run_isolation.py`
- `tests/unit/web_portal/test_portal_terminal_state_4025.py`
- `tests/e2e/web_portal/test_issue_4037_menu_93_output.py`

**Tests to add or update**:

- A standalone database-host warning with later data-row wording must not classify a run as an empty result.
- A genuine no-data line must still classify as an empty result and remove a lone prompt-cache file.
- A completed Menu 93 run with a valid `SiteInventory.csv` must retain the file in status JSON and completion SSE.

## Risks & Considerations

- A narrow marker change could stop recognizing a genuine empty-result message. Keep tests for current empty-result wording.
- Do not disable cache-only filtering for Menu 93. That could expose a stale inventory cache as an operation result.
- The targeted pytest command could not run in this environment because Python reported `No module named pytest`.

## Open Questions

- The complete mocked warning text and original command remain unavailable.
