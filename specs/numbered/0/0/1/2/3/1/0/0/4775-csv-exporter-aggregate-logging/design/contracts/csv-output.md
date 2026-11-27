# Contract: CSV output of the shared writer

This contract defines the CSV output that must not change. Test T002 reads the file back and checks it.

## Rules that stay unchanged

- **File name**: The caller supplies the file name. A bare name goes under `data/`. A path with a directory is used as given. The rule lives in `_resolve_csv_path` (`src/operations/exporting/export/data_exporter.py`, line 416).
- **Column order**: When the caller supplies a field list, the writer uses that list in its order. Otherwise the writer uses the sorted unique keys of the rows. The rule lives in `_resolve_csv_fields`.
- **Cell escaping**: Each row passes through `DataProcessingUtils.escape_multiline` before the write, as before.
- **Missing key**: A row that lacks a column writes an empty string for that cell. The expression is `row.get(field_name, "")`.
- **Row count**: The file holds one CSV row for each input row, in input order.
- **Header**: The file holds one header row that names the columns, in the column order.
- **Encoding and newline**: The file opens with UTF-8 encoding and `newline=""`, as before.
- **Writer call**: The `writerow` expression in `_emit_rows` stays the same. Only the logging changes.

## Acceptance check

Test T002, `test_csv_keeps_marker_cell_values`, writes three rows that hold synthetic marker values to a file under `tmp_path`. It reads the file back and compares the header and the three rows with the expected values. A failure means that the change altered the CSV bytes, the column order, or the cell values.

## Out of scope

- Spreadsheet formula protection for CSV cells. Issue #4773 owns that work.
- Any change to the CSV file name, the data directory, or the output format selection.
