# Data Model: Nested JSON Result Preview

## Result file

An existing result within the configured data directory.

| Field | Meaning | Validation or invariant |
|---|---|---|
| `relative_path` | Complete path relative to the configured data directory | Keep all directory segments. Reject paths that the existing path guard denies. |
| `format` | Supported file format, including JSON | Preserve the existing format support. |
| `contents` | Read-only file data used by the preview or download | Do not modify the source. |

## Preview request

A request for a file preview or an SQLite table preview.

| Field | Meaning | Validation or invariant |
|---|---|---|
| `selection_kind` | File selection or SQLite table selection | Do not infer a table from the final segment of a nested file path. |
| `relative_path` | File path selected for preview | Preserve the complete path and apply the existing path guard. |
| `table_name` | Selected SQLite table, when the request is a table selection | Use only for an explicit SQLite table selection. |
| `page` | Requested result page | Preserve existing defaults, ordering, and pagination behavior. |
| `per_page` | Requested page size | Preserve existing limits and response behavior. |

## Preview result

A read-only response for one selected file or SQLite table.

| Field | Meaning | Validation or invariant |
|---|---|---|
| `rows` and column data | Existing representation of preview contents | Preserve the current schema, row order, and empty-result behavior. |
| `counts` and pagination data | Existing totals and page metadata | Preserve current values and page behavior. |
| `error` | Failure reason for a missing file, malformed JSON, denied path, or missing table | Do not disclose an internal absolute path. Keep file and table failures distinct. |

## Relationships and transitions

- A file selection identifies one result file by its complete relative path.
- An SQLite table selection identifies a table within an SQLite file.
- Preview and download read the same source file without changing it.
- The path guard decides whether either file selection can access the requested path.
- A file can be present at listing time and absent at preview time. In that case, return the existing missing-file result without stale contents.

## Existing HTTP interface contract

| Request | Selection | Required behavior |
|---|---|---|
| `GET /api/data/preview/<path:filepath>` | File preview | Treat the complete `filepath` as the selected file. Preserve current query parameters, JSON response shape, and error status rules. |
| `GET /api/data/preview/<path:filepath>/<table_name>` | SQLite table preview | Use the requested SQLite file and table. Preserve its response shape, pagination, and missing-table result. |
| `GET /api/data/download/<path:filepath>` | File download | Keep the existing safe-path check and unchanged file contents. |

The change must separate the first two selections without changing their public request or response formats. The endpoint must not treat a nested file name as a table name.
