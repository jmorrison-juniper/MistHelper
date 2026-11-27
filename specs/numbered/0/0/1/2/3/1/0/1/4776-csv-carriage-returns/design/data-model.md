# Data Model: Preserve CSV Carriage Returns

## Entities

| Entity | Holds | Natural key | Source |
| - | - | - | - |
| Raw row | One dictionary of field names and values that a caller passes to a writer. | None for the CSV file. The endpoint primary key applies to database rows (U-6). | Caller |
| Normalized row | The raw row after `DataProcessingUtils.escape_multiline`. | Same as the raw row. | `src/foundation/models/data/data_processing_utils.py` (RC-01, RC-02) |
| CSV presented row | A copy of the normalized row with each carriage return shown as two characters. | Same as the raw row. | `src/foundation/models/csv_presentation/cell_presenter.py` (T011) |
| CSV cell | One text value in one column of one CSV line. | Row position and column name in the file. | `csv.DictWriter` (RC-07, RC-12, RC-13) |
| Database row | One stored SQLite row that holds normalized values. | Endpoint primary key from the strategy table (U-6). | `src/foundation/support/refactors/sqlite_database_writer.py` (RC-10) |

## Fields

| Field | Type | Constraint | Change |
| - | - | - | - |
| `value` in a text field | string | Carriage return and line feed are allowed. | Carriage return stays raw in a normalized row. In a CSV presented row, carriage return becomes backslash and `r`. |
| `value` in a list field | list | Each item converts to a string. The join uses a comma. | Carriage return in an item stays raw in the joined string. The CSV presentation then shows it as backslash and `r`. |
| `value` in a non-text field | integer, boolean, or empty value | Not changed by any step. | None. |

## State Transitions

| From | Step | To | Rule |
| - | - | - | - |
| Raw row | `escape_multiline` | Normalized row | A line feed becomes backslash and `n`. A carriage return stays raw. A list becomes a joined string. |
| Normalized row | `CsvCellPresenter.prepare_rows` or `present_carriage_returns` | CSV presented row | Each carriage return becomes backslash and `r`. The copy holds the presented text. |
| Normalized row | SQLite writer | Database row | The stored value keeps the raw carriage return. |
| Normalized row | Polyglot writer | Stored document | The stored value keeps the raw carriage return. |
| CSV presented row | `csv.DictWriter` | CSV cell | The cell holds the presented text. |

## Invariants

- The caller's raw row is the same before and after a CSV write (FR-004).
- A carriage return never reaches a CSV cell as a raw character from a text value (FR-002, FR-003).
- A database row never holds the two characters backslash and `r` that the CSV presentation writes (FR-005).
- The natural key of a database row does not depend on the CSV presentation (U-6).
- Applying the CSV presentation twice gives the same text as applying it once, because the second pass finds no raw carriage return.
