# Contract: Writer result for site exports

## Scope

This contract defines the return value of `DataExporter.write_with_format_selection`. The two site exports read that value. Both persistence methods check it before they report success.

## Signature

`src/operations/exporting/export/data_exporter.py` line 152 applies `@staticmethod`. Lines 153-159 define the signature. The method takes `data`, `filename_or_table`, `api_function_name`, `fieldnames`, and `backend_options`. It returns `bool`.

## Return values

| Case | Return value | Source |
| - | - | - |
| Input validation fails (empty data or unsupported format) | `False` | lines 171-172 |
| Primary writer (CSV or SQLite) fails | `False` | `csv_ok` from `_dispatch_format_write` (lines 173-175) |
| Primary writer succeeds | `True` | line 180 (`return csv_ok`) |

## Database mirror

The method sends the rows to the database mirror after the primary write (lines 176-178). The mirror result does not change the return value. When the mirror drops a write, `_warn_when_database_write_dropped` logs a warning (lines 179 and 183-198).

Caution: a mirror drop after a successful file write still returns `True`. The site exports then report success. This limit is out of scope (analysis F-14).

## Exceptions

The method body (lines 153-180) holds no `try` block. An exception from a helper propagates to the caller. The site export persistence methods do not catch it. Their menu handlers catch it (`site_application_list_exporter.py` lines 96-98).

## Caller rule

1. Read the return value into a variable before any success message.
2. Treat `False` as a failed write. Log one error and return.
3. Treat `True` as a successful primary write. Log the success messages.
4. Do not infer success from the absence of an exception.

## Evidence

- `design/research.md` row 4 (blob `f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411`, lines 153-180).
- `design/research.md` row 15 (flatten and escape helpers, which run before the writer).
