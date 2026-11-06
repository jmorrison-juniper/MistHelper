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
Do not merge.
