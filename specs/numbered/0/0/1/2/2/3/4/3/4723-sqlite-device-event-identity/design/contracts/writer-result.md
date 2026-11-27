# Contract: SQLite Writer Result for Device Events

## Scope

This contract covers `SQLiteDatabaseWriter.write()` when the API function name is `searchOrgDeviceEvents`. Other endpoints keep the existing contract (R10 and R11).

## Return value

| Case | Return | Table state |
| - | - | - |
| Every distinct submitted row is stored after verification | True | Rows added or already present |
| Verification finds a missing row | False | Unchanged. The transaction is discarded. |
| The table uses the legacy key | False | Unchanged |
| A database error occurs | False | Unchanged. The transaction is discarded. |
| The batch holds zero rows | False | Unchanged. Validation rejects an empty batch (R17). |

## Callers

- Menu 97 (`DeviceEvents52wExporter`): raises `RuntimeError` on False (R22). Its existing behavior stays unchanged.
- Menu 21 (`OrgAlarmEventExporter.device_events`): logs an error and prints no completion line on False, when the batch holds one or more rows (FR-016).
- Menu 153 (`APIDataFetcher`): unchanged by this change. A False result leads to a success log line (R32). A follow-up issue owns this gap.

## Log text

Each message uses ASCII. Each message names the table.

| Event | Level | Text pattern |
| - | - | - |
| Identity write starts | info | `Writing %s rows to identity table %s` |
| Identity write result | debug | `Identity write for table %s stored %s rows, merged %s identical rows` |
| Legacy table refused | error | `Table %s uses the legacy device event key. Run the migration command before you write. No row was written.` |
| Verification failed | error | `Verification found %s of %s rows missing in table %s. The batch was discarded.` |
| Menu 21 write failed | error | `The SQLite write failed for OrgDeviceEvents. No completion line is printed.` |

## Error text

The legacy refusal names the migration command, with the table name and the database path:

```text
python -m src.foundation.persistence.device_events.legacy_migration --db <path> --table <name>
```

## Unchanged behavior

- The CSV path does not change.
- The polyglot path does not change.
- The endpoint catalog entry does not change.
