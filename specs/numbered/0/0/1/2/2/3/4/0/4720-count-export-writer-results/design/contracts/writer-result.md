# Contract: Writer result

## Scope

This contract covers the call from `CountExporter._persist` to `DataExporter.write_with_format_selection`, and the value that the call returns. The writer belongs to `src/operations/exporting/export/data_exporter.py`, and this change does not edit it.

## Call shape

The count exporter calls the writer with positional arguments for the rows and the filename, and with the keyword `api_function_name`.

```python
written = mh.DataExporter.write_with_format_selection(sanitized_data, filename, api_function_name=operation)
```

The call shape stays as it is today, except for the assignment that stores the result (FR-010).

## Return value

| Writer outcome | Return value | Count exporter reaction |
| - | - | - |
| Primary CSV or SQLite write succeeds | `True` (`csv_ok`, research row 13) | Success notice |
| Format writer raises and the writer catches it | `False` (research row 14) | Failure log and failure notice |
| Any other false value | `False` | Failure log and failure notice |
| Returns `None`, which lies outside the declared Boolean contract | `None` | Failure log and failure notice, because the truth-value test treats `None` as false |
| Exception escapes the writer | Raised exception | `_run` logs the error and prints the raised-error notice |

## Polyglot mirror

The writer also mirrors the rows to the polyglot database. The mirror outcome drives only the warning that `DataExporter` logs when the database write drops rows (research row 15). The mirror outcome never changes the return value. The count exporter therefore judges only the primary result.

## Rules

- The count exporter tests the truth of the stored result, and nothing else.
- The count exporter never compares the result with `True` by identity or equality.
- The count exporter never retries the writer call.
- The count exporter never changes the rows before the writer call. The flatten and escape steps stay as they are.
