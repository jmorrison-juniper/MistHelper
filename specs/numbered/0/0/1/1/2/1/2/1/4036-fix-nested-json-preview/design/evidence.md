# Evidence: Issue #4036 Nested JSON Preview

**Recorded**: 2026-11-06

**Feature**: [Nested JSON Result Preview](../spec.md)

## Confirmed Input Evidence

The user supplied the following confirmed findings from the preceding investigation.
This specification task did not repeat the reproduction or inspect the original screenshot.

- Issue [#4036](https://github.com/jmorrison-juniper/MistHelper/issues/4036) shows menu 243 paths `mib_generator/allowlist.json` and `mib_generator/oid_assignments.json`.
- Download returns HTTP 200. The Results panel reports `Could not read the results: File not found`.
- [PR #4081](https://github.com/jmorrison-juniper/MistHelper/pull/4081) merged on 2026-10-09.
- That pull request excluded read-only MIB input paths from operation output evidence.
- It did not correct the remaining nested JSON preview symptom.

## Supplied Synthetic Reproduction

The preceding investigation used a temporary nested JSON fixture and the Flask test client.
It made no live Mist calls.

| Request | Recorded result |
| --- | --- |
| `GET /api/data/preview/mib_generator%2Fallowlist.json?page=1&per_page=25` | HTTP 404 with `{"error":"File not found"}` |
| `GET /api/data/download/mib_generator%2Fallowlist.json` | HTTP 200 with valid JSON |

Flask selected `data.preview_table`.
The route `/api/data/preview/<path:filepath>/<table_name>` takes precedence over the generic file-preview route.
The selected handler interpreted the nested file's final segment as a SQLite table name.
This explains why the same valid file downloaded successfully but failed preview.

This finding constrains the defect scope.
It does not prescribe a route redesign or permit removal of table previews or path checks.

## Specification-Task Checks

- Local `HEAD` and `origin/main` both resolved to `fb7a7d10d40c89a44ccfdaf0304ec57b2fd3b02d`.
- This task did not fetch a newer remote main revision.
- The open pull request query requested up to 100 records and found no listed owner for either supplied candidate code file.
- The candidate files were `web_portal/routes/data.py` and `tests/unit/web_portal/test_preview_row_order.py`.
- The query also found no open pull request with a listed file path containing `4036`.
- Issue #4036 remained open. This task added its `in-progress` label before the branch hook ran.
- The mandatory branch hook returned `BRANCH_NAME=3998-fix-nested-json-preview` and `FEATURE_NUM=3998`.
- The managed numeric allocator returned the separate issue route for `4036-fix-nested-json-preview`.

The ownership result is a snapshot, not a continuing reservation.
Later implementation must inspect current main and all intended file owners again.

## Scope and Selector

This task adds three files within one managed feature directory.
It changes no application code, tests, production data, or shared feature pointer.

The existing `.specify/feature.json` selects issue #4258.
Preserve that selector because it belongs to a different feature.
Use the following command-scoped directory value for downstream Spec Kit commands:

```text
SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/1/2/1/2/1/4036-fix-nested-json-preview
```

Supporting artifacts use `design/`.
The checklist uses `design/checklists/requirements.md`.
No new directory level may exceed five children.

## Later Implementation Boundary

Use temporary synthetic JSON and SQLite fixtures with local portal requests.
Verify both named JSON paths, deeper nesting, malformed content, missing files, pagination, downloads, table previews, and path-security regressions.
Preserve the output-list behavior from #4081.

If the defect no longer reproduces, record the exact revision and results.
If another pull request owns a required file, report that owner and stop overlapping work.
Do not open a placeholder pull request.
Only a validated focused fix may use `Closes #4036`.
The original implementation task did not authorize a merge.

## Acceptance Reassessment

The user requested repairs for path disclosure and stale contents, followed by acceptance reassessment.
JSON read failures now return a fixed client message and log exception details on the server.
Parser failures retain their reason, line, and column.
The Results panel clears previous rows, headings, and page controls before each preview request.

| Criteria | Evidence |
| --- | --- |
| US1 scenarios 1 and 2, SC-002 and SC-005 | Parameterized Playwright tests display both named nested JSON files through the Results panel. |
| US1 scenarios 3 through 5, SC-001 and SC-006 | Route tests cover root and nested paths, exact page rows and counts, and unchanged download bytes. |
| FR-003 and JSON shape edge cases | Nested route tests preserve arrays, empty objects, and empty arrays. Streaming tests preserve column order and filtering. |
| US2 scenarios 1 and 3, FR-004 and FR-007 | Malformed JSON retains its parser error. Injected permission, operating-system, and unexpected failures expose no internal path. |
| US2 scenario 2, FR-005 | Playwright lists a temporary file, removes it, selects it, and checks empty pending rows followed by the missing-file error. |
| US3 scenarios 1 through 4, SC-004 | SQLite tests verify tables, pagination, search, and missing tables. Path tests deny traversal, absolute paths, and outside links. |
| FR-008 and FR-009 | Source-byte assertions prove read-only previews. Output-discovery tests preserve the merged #4081 input exclusions. |

The feature-specific merge hold is removed because the acceptance criteria have corresponding verified evidence.
The existing empty-array response reports two total rows and displays one content row.
A direct comparison with the committed JSON reader confirms that this response remains unchanged.
This repair preserves that existing behavior and does not change JSON representation rules.
This reassessment does not authorize this agent to merge or enable auto-merge.
A separately approved merge still requires current main, the serial merge slot, and every required check on the latest commit.

## Coverage Shard Failure

Run `42339040613` tested head `8126f033350b61452ea518737dd94cccbc400a79`.
The root-and-contracts shard passed 2,255 tests but failed the blind broad exception handler guard.
The guard reported `web_portal/services/data_browser.py: 1 -> 2`.
The coverage gate failed because the shard failed, not because a measured coverage percentage was too low.

The JSON read handler logged the active exception without binding it.
The repair binds the exception and passes it explicitly as `exc_info` to the server logger.
The client response remains fixed and does not disclose internal paths.
Regression assertions verify that the server log retains the exception type and private path.
The complete blind-handler guard and focused preview tests pass locally.
No baseline or guard threshold changed.
