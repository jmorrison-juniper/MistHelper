# Bug Assessment: Menu 93 inventory output is hidden

- **Slug**: menu-93-inventory-output
- **Created**: 2026-10-13T23:48:07Z
- **Source**: Pasted text for issue #4037
- **Verdict**: likely valid, needs reproduction
- **Severity**: medium

## Report (verbatim or summarized)

Issue #4037 reports that Menu 93 writes a valid `SiteInventory.csv` file, but the portal does not show it. The issue comments describe two mocked Flask and browser runs at commit `e0dc054d`. Both runs returned `output_files=[]` in status JSON and completion SSE. Each finalizer logged that it kept zero of one output file names.

The report attributes this to cache filtering and a database-host warning. The current source confirms the cache filtering path, but it does not confirm that the current database warning triggers the classifier. The emitted warning says “Polyglot database hosts do not answer.” That text does not contain the classifier marker `no `.

## Symptom

The mocked runs write `SiteInventory.csv`, but the portal reports no output file in its status response or completion event. The expected result is for the completed run to list the valid file.

## Reproduction

1. Run the two mocked Flask and browser cases described in issue #4037 at commit `e0dc054d`.
2. Observe that each run writes a mocked `SiteInventory.csv` file.
3. Observe `output_files=[]` in status JSON and completion SSE, with the finalizer logging that it kept zero of one file names.

[NEEDS CLARIFICATION: The issue summary does not provide the exact mock warning text, fixtures, or commands. The current production warning text does not match the `no ` marker.]

## Suspected Code Paths

- `web_portal/services/operation.py:114` — `NO_OUTPUT_REASON_MARKERS` includes the broad substring `no `.
- `web_portal/services/operation.py:144` — `SiteInventory.csv` is classified as a prompt-cache output file.
- `web_portal/services/operation.py:147` — Only menus `1` and `60` are exempt from cache-only filtering. Menu 93 is not listed.
- `web_portal/services/operation.py:1475` — `_no_output_reason()` accepts any log line containing one of the no-output markers.
- `web_portal/services/operation.py:1539` — `_drop_cache_only_empty_result()` removes cache-only names when `_no_output_reason()` finds a match.
- `web_portal/services/operation.py:1591` and `web_portal/services/operation.py:1630` — Completion SSE and status JSON expose the run's filtered `output_files`.
- `src/operations/exporting/export/data_exporter.py:244` — The current standalone warning says database hosts “do not answer.” That exact text does not contain `no `.
- `tests/unit/test_operation_output_file_discovery.py:176` — Existing tests cover removal of a cache-only file for a genuine no-data reason and preservation of the inventory file for Menu 60.

## Root Cause Hypothesis

The reported loss can occur when a standalone log line contains `no `, because the broad marker makes `_no_output_reason()` classify it as a no-output explanation. The cache-only filter then removes `SiteInventory.csv` for Menu 93. Confidence is low that the named current database warning triggers this path: its source text does not match the marker, and the reproduction uses mocked output. The cache-filter behavior itself is present in current source.

## Proposed Remediation

**Preferred**: Narrow the no-output classifier so it recognizes explicit empty-result messages rather than any occurrence of `no `. Keep the cache-only filter in place for genuine no-data runs. Do not treat Menu 93 as a prompt-cache export menu, because the file may still be only a cache refresh for other operations.

Add a regression for the exact standalone warning text and a completed Menu 93 run that writes `SiteInventory.csv`. Confirm that the run preserves the file in status JSON and completion SSE. Keep tests for genuine no-data messages and cache-only removal.

**Files likely to change**:

- `web_portal/services/operation.py`
- `tests/unit/test_operation_output_file_discovery.py`
- `tests/unit/web_portal/test_portal_run_isolation.py`

**Tests to add or update**:

- A standalone database-host warning must not classify a run as an empty result.
- A genuine no-data line must still classify as an empty result and remove a lone prompt-cache file.
- A completed Menu 93 run with a valid `SiteInventory.csv` must retain the file in status JSON and completion SSE.

## Risks & Considerations

- A narrow marker change could stop recognizing a genuine empty-result message. Keep tests for current empty-result wording.
- Do not disable cache-only filtering for Menu 93. That could expose a stale inventory cache as an operation result.
- The targeted pytest command could not run in this environment because Python reported `No module named pytest`.

## Open Questions

- [NEEDS CLARIFICATION: Does the mock use the exact current warning text, or another warning that begins with `No `?]
- [NEEDS CLARIFICATION: Can the two mocked runs be repeated against the current `d176f3e6` source with the exact log messages captured?]
