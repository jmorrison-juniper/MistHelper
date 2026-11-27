# Data Model: Count export write results

This change adds no table, file format, or natural key. The model names the states of one `_persist` call, so the regression tests can assert each state.

## CountOperation

- **Source**: `src/operations/exporting/export/count_exporter.py`, tables `_ORG_OPS` (line 51), `_SITE_OPS` (line 91), and `_MSP_OPS` (line 126).
- **Natural key**: `operation`, the Mist operation name. All 72 names are distinct, so the key is unique.
- **Fields**: `operation` (the name) and `module` (the dotted SDK module).
- **Counts**: 37 organization rows, 32 site rows, and 3 MSP rows. The menu reference states the same counts on lines 271 to 273 of `documentation/menu_reference.md`.
- **Change**: None.

## WriterResult

- **Source**: The return value of `DataExporter.write_with_format_selection` (`src/operations/exporting/export/data_exporter.py`, line 153, declared Boolean at line 159).
- **Values**: True or false. The count exporter also treats `None` as false.
- **Change**: The exporter stores the value in `written` and tests its truth.

## CountPersistOutcome

Each `_persist` call ends in exactly one state.

| State | Entry condition | Log lines | Operator notice | Writer called |
| - | - | - | - | - |
| NO_ROWS | The response holds no rows. | One info line. | `! No <operation> data found` | No |
| WRITTEN | Rows exist, and the writer result is true. | One info line before the writer call, one debug line after it, and the success notice. | `! <count> <operation> records exported to <filename>` | Yes |
| WRITE_FAILED | Rows exist, and the writer result is false or `None`. | One info line before the writer call, and one error line. | `! Write failed for <operation>. Do not treat <filename> as a complete export.` | Yes |
| WRITE_RAISED | The writer raises an exception. | `_run` logs the error. | `! Error running <operation>: <message>` | Yes |

Transitions:

- SELECTED moves to NO_ROWS when `rawdata` is empty.
- SELECTED moves to WRITTEN when the writer result is true.
- SELECTED moves to WRITE_FAILED when the writer result is false or `None`.
- SELECTED moves to WRITE_RAISED when the writer raises. `_run` catches the exception.

Each state returns control to the menu. No state repeats the writer call.

## Attempt identity

One attempt is identified by the menu number, the operation name, the label, and the filename. The filename is `<operation>_<label>.csv`, with each space in the label replaced by an underscore. The filename rule stays in `_run`, and this change does not alter it.
