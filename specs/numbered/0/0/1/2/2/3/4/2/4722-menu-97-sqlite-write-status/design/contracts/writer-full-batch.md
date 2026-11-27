# Contract: SQLite Writer Full-Batch Write

**Interface**: `SQLiteDatabaseWriter.write(require_full_batch: bool = False) -> bool`

**Location**: `src/foundation/support/refactors/sqlite_database_writer.py`

## Inputs

| Argument | Type | Default | Meaning |
| - | - | - | - |
| `require_full_batch` | bool | False | When True, the writer discards the whole batch if any row is rejected. |

The constructor keeps its three arguments: `data`, `table_name`, and `api_function_name`. The constructor does not change.

## Results

| Case | Flag | Stored Rows | Result | Table Effect |
| - | - | - | - | - |
| Every row stored | False or True | All | True | Batch committed |
| Some rows rejected, some stored | False | Some | True | Stored rows committed. Existing behavior from issue #3350 |
| Some rows rejected, some stored | True | Some | False | Batch discarded. No row of the batch remains. Rows of earlier batches stay |
| Every row rejected | False or True | None | False | Batch discarded. Existing behavior |
| Zero rows in the batch | False or True | None | True | Nothing written |
| SQLite error or other exception | False or True | None | False | Batch discarded. Existing behavior |

## Log Lines

| Condition | Level | Text |
| - | - | - |
| Some rows rejected, flag not set | error | `The writer did not insert %s of %s rows into table %s at %s` (existing text) |
| Some rows rejected, flag set | error | `The writer did not insert %s of %s rows into table %s at %s. The writer discarded the batch.` (new text) |
| Every row rejected | error | `The writer inserted 0 of %s rows into table %s at %s. The writer rolled back the batch.` (existing text) |

The new text uses the term discarded. The existing text keeps its term rolled back. Issue A-15 in `analysis.md` records the difference.

## Call Order

1. `write` passes the flag to `_execute_database_operations`.
2. `_execute_database_operations` passes the flag to `_finish_batch` after `_insert_all_rows` returns the count of stored rows.
3. `_finish_batch` returns False for an empty batch with no stored row, as it does today.
4. When the flag is set and some rows are rejected, `_finish_batch` calls `_reject_partial_batch`.
5. `_reject_partial_batch` logs the error line, calls `_rollback_transaction`, and returns False.
6. Otherwise, `_finish_batch` commits, logs the partial summary when needed, and returns True.

## Failure Safety

- The writer never raises for a rejected row. It returns False.
- The writer closes the connection in every case, as `_execute_database_operations` does today.
- A rollback error is logged and does not change the result. `_rollback_transaction` already handles this case.
