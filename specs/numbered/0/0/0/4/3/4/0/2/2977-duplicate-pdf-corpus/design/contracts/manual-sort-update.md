# Contract: Manual Document Sort Update

**Issue**: #2977

**Module**: `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py`

**Class**: `ManualDocumentSorter` (R16, line 88)

## Constructor

- `ManualDocumentSorter(output_dir: Path, apply_changes: bool = False)`.
- `apply_changes` defaults to false. A dry run is the safe default (`manual_sorter.py` line 99).

## Method: run

- Signature: `run(database: Path) -> SortStats`.
- Reads each document row with `stage = 'classified'`, `category = 'uncategorized'`, and a non-null `local_path`. The read uses a read-only connection.
- Decides a folder for each row from the file name and the root URL. A row without a matching folder counts as unsorted and stays in place.

## Behavior by Mode

| Mode | File move | Database write |
| - | - | - |
| Dry run (`apply_changes` false) | None. The move count increases by the planned moves. | None |
| Apply (`apply_changes` true) | The file moves to `output_dir / folder`. A free name is chosen when the name exists. | `UPDATE documents SET local_path = ?, updated_at = ? WHERE root_url = ?` in one transaction |

- The `updated_at` value is a UTC timestamp in ISO 8601 form (AGENTS.md, Data and input).
- The write sets `local_path` and `updated_at` only. It leaves `stage` and `category` unchanged.

## Failure Behavior

- A missing source file increases `missing` and writes no row.
- A database error after a successful move logs both the source path and the target path at error level. It increases `unrecorded` and continues with the next row. The file stays at the target path.
- A failed move raises no exception to the caller. The move count does not increase.

## SortStats Fields

- `inspected`: rows read.
- `missing`: rows whose source file does not exist.
- `unsorted`: rows that match no folder rule.
- `moved`: moves completed in apply mode, or planned moves in dry-run mode.
- `unrecorded`: moves completed in apply mode whose database write failed. This field is new (T005).

## Tests That Pin the Contract

- `test_apply_moves_file_and_updates_local_path` (T004).
- `test_dry_run_changes_no_file_and_no_row` (T004).
- `test_missing_source_counts_missing_and_keeps_row` (T004).
