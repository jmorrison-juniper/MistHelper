# Data Model: Resumed 52-week device-event CSV export

## Entities

### Organization

- **Key**: `org_id`, a Mist organization identifier. It names the checkpoint file.
- **Source**: The authenticated session. The menu passes it to `DeviceEvents52wExporter`.
- **Rule**: An empty `org_id` stops the export before any file or page access (`device_events_52w_exporter.py` lines 77-79).

### CSV file

- **Path**: `data\OrgDeviceEvents_52w.csv` (line 17). The path has no organization segment.
- **Key**: None. The CSV holds one row for each device event. It has no natural row key.
- **Header**: The sorted union of keys from the preload rows (`data_processing_utils.py` line 153).
- **Writes**: A fresh run writes a header and rows with mode `w` (line 311). A resumed run appends rows with mode `a` (line 326).
- **Invariant**: A resumed run never truncates the file. A row ends with a line break.

### Checkpoint file

- **Path**: `data\OrgDeviceEvents_52w.<org_id>.checkpoint` (line 19).
- **Key**: The organization identifier in the file name.
- **Content**: One checkpoint token in UTF-8 text. The read strips leading and trailing whitespace (line 147).
- **Lifecycle**: Written after each batch (lines 96 and 340). Removed when the run completes (lines 117 and 355).

### Temporary checkpoint file

- **Path**: `<checkpoint file>.tmp`. The suffix is added to the file name.
- **Lifecycle**: Created during a checkpoint write. Replaces the checkpoint file on success. Can remain after a failed write. The next successful write replaces it.

### Checkpoint token

- **Form**: Text from the checkpoint file. Passed to the API as `search_after`.
- **Source of value**: The `search_after` or `next` key of the response body (`_TOKEN_KEYS`, line 29).
- **Open question**: The live form of `next` is unverified (research U-1).

### Preload

- **Form**: The first three pages of a run (`_DEFAULT_PRELOAD_PAGES`, line 26).
- **Use**: Builds the CSV header. Supplies the rows for the first batch.

## State transitions

| From state | Condition | To state | Effect on files |
| - | - | - | - |
| Start | Output is SQLite, or no checkpoint file exists | Fresh run | The CSV is written with mode `w` after the first batch |
| Start | Checkpoint file exists and the read fails | Stopped | No change. A `RuntimeError` is raised |
| Start | Checkpoint file is empty, output is CSV, and CSV exists | Refused | No change. A `RuntimeError` is raised (FR-006) |
| Start | Checkpoint file is empty, and no CSV exists | Fresh run | The CSV is written with mode `w` |
| Start | Checkpoint token exists, output is CSV, and CSV is missing | Refused | No change (FR-002) |
| Start | Checkpoint token exists, and the CSV header differs | Refused | No change (FR-003) |
| Start | Checkpoint token exists, and the last CSV row is partial | Refused | No change (FR-004) |
| Start | Checkpoint token exists, and the CSV is compatible | Resumed run | The CSV gains rows by append |
| Resumed run | Preload returns no rows | Kept | The CSV and checkpoint keep their bytes. The log names no new rows (FR-008) |
| Streaming | A batch is appended and the next token exists | Streaming | The checkpoint is replaced through the temporary file (FR-007) |
| Streaming | A checkpoint write fails | Streaming | The previous checkpoint stays. A warning is logged |
| Streaming | A page has no rows | Completed | The checkpoint is removed. Completion is logged. An API error can cause this state (finding A-19) |
| Any | An exception in an API call after retries | Failed | The CSV keeps the rows already appended. The checkpoint keeps the last saved token |

## Natural keys and idempotence

- The CSV has no natural key. A replayed batch appends duplicate rows. Decision D-5 accepts this for a failed checkpoint write.
- The SQLite writer uses a composite key defined outside this change. This record does not change the SQLite key.

## Migration

No migration is needed. The CSV and checkpoint formats do not change (FR-010).
