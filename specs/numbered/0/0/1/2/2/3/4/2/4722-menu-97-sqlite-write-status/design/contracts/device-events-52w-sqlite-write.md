# Contract: 52-Week Exporter SQLite Write

**Interface**: `DeviceEvents52wExporter` writes SQLite batches through `DataExporter.write_with_format_selection`.

**Location**: `src/operations/exporting/export/device_events_52w_exporter.py`, method `_write_sqlite_batch`, and its callers `_write_initial_batch` and `_append_rows`.

## Call Shape

Each SQLite batch uses this call. The table name, endpoint key, and format override stay the same as today.

- Rows: the processed rows of the batch.
- Filename or table: `OrgDeviceEvents_52w`.
- API function name: `searchOrgDeviceEvents`.
- Backend options: `ExportBackendOptions` with `format_override` set to `sqlite` and `require_full_batch` set to True.

## Result Handling

| Writer Result | Exporter Action |
| - | - |
| True | Continue. The checkpoint advances after a later batch. |
| False | Log the error line and raise RuntimeError. The checkpoint stays unchanged. No completion line is logged. |

The error line and the RuntimeError text stay as they are today. The text is `SQLite write failed for table OrgDeviceEvents_52w. The checkpoint was not advanced.`

## Order of Operations

1. Fetch the preload pages.
2. Write the initial batch with the full-batch request. A False result raises before the first checkpoint write.
3. Write the first checkpoint.
4. For each later page, fetch the page, write the batch with the full-batch request, and then write the next checkpoint. A False result raises before the checkpoint write for that page.
5. After the last page, remove the checkpoint and log the completion line.

## Unchanged Paths

- The CSV path does not call `write_with_format_selection` for each batch. It writes the CSV directly. This change does not touch it.
- The empty-result path calls `write_with_format_selection` with no backend options. This change does not touch it.
- The checkpoint read, the checkpoint write warning, and the checkpoint removal keep their behavior.
