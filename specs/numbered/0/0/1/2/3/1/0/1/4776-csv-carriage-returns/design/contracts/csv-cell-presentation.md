# Contract: CSV Cell Presentation

This contract covers the CSV files that `DataExporter.write_to_csv` and the CSV branches of `DeviceEvents52wExporter` write. It does not cover the EX hardware report. That report keeps its own contract (D-6).

## Input

The input is a normalized row. The shared normalizer has already run (`DataProcessingUtils.escape_multiline`). Carriage returns stay raw. Line feeds are already escaped as backslash and `n`. List values are already joined.

## Output Rules

| Input text (raw characters) | CSV cell text |
| - | - |
| apostrophe, carriage return, `plain` | apostrophe, backslash, `r`, `plain` |
| `a`, carriage return, line feed, `b` (after normalization: `a`, carriage return, backslash, `n`, `b`) | `a`, backslash, `r`, backslash, `n`, `b` |
| one carriage return | backslash, `r` |
| one line feed (after normalization: backslash, `n`) | backslash, `n` (unchanged) |
| backslash, `r` already present in the text | backslash, `r` (unchanged, because the presentation changes carriage returns only) |
| list of `x`, carriage return, `y` and `z`, line feed, `w` | `x`, backslash, `r`, `y`, comma, `z`, line feed, `w` (the line feed in a list item stays raw, as before) |
| integer 42 | `42` (unchanged) |
| empty value | empty cell (unchanged) |

## Rules

- The presentation keeps the order of all other characters.
- The presentation returns copies. The caller row is the same before and after the write.
- The presentation adds no apostrophe. The EX hardware report rule for a leading carriage return does not apply here.
- Each CSV write runs the presentation once.
- The SQLite writer and the polyglot writer receive the normalized row. They keep raw carriage returns.

Caution: a text value that holds backslash and `r` looks the same as a presented carriage return. Readers cannot tell the two apart.

## Writers

| Writer | Receives | Applies the presentation |
| - | - | - |
| `DataExporter.write_to_csv` | Raw row from a caller | Yes, through `CsvCellPresenter.prepare_rows` |
| `DeviceEvents52wExporter` CSV branches | Normalized row | Yes, through `CsvCellPresenter.present_carriage_returns` |
| `DeviceEvents52wExporter` SQLite branch | Normalized row | No |
| `DataExporter` SQLite and polyglot paths | Caller row or normalized row | No |
| EX hardware report writer (`csv_file.py`) | Its own report rows | No (FR-010) |

## Example

The example uses invented values.

```text
value
'\rplain
```

The first line is the header. The second line is the cell text for the apostrophe, carriage return, and `plain` value.
