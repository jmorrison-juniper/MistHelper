# Data Model: CSV imports

## CsvImportDefinition

One immutable record for each supported import type.

| Field | Type | Meaning |
| - | - | - |
| `key` | `str` | The internal type key, such as `org_psks`. |
| `label` | `str` | The operator-facing name. |
| `file_name` | `str` | The CSV file name under `data/`. |
| `scope` | `str` | `org` or `site`. |
| `operation_id` | `str` | The Mist API operation ID. |
| `required_columns` | `tuple[str, ...]` | Columns that must exist before a request can run. |
| `secret_columns` | `tuple[str, ...]` | Columns that must be masked. |

## CsvImportBatch

One parsed CSV file and its validation state.

| Field | Type | Meaning |
| - | - | - |
| `definition` | `CsvImportDefinition` | The selected import type. |
| `file_path` | `Path` | The resolved path under `data/`. |
| `fieldnames` | `tuple[str, ...]` | CSV header names. |
| `rows` | `tuple[dict[str, str], ...]` | Parsed CSV records. |

## CsvImportResult

One row for `CsvImportLog.csv`.

| Field | Type | Meaning |
| - | - | - |
| `import_type` | `str` | The selected type key. |
| `row_count` | `int` | The number of rows in the input file. |
| `dry_run` | `bool` | Whether the run sent no request. |
| `status` | `str` | `dry_run`, `sent`, `error`, or `cancelled`. |
| `message` | `str` | A sanitized result summary. |
