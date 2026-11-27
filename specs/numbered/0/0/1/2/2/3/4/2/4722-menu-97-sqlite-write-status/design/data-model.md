# Data Model: Menu 97 SQLite Write Status

## Entities

| Entity | Natural Key | Attributes | Source |
| - | - | - | - |
| Checkpoint file | Organization identifier in the file name `OrgDeviceEvents_52w.<org_id>.checkpoint` | One continuation token as UTF-8 text. The file exists only while the export is incomplete. | `device_events_52w_exporter.py` line 19 (name template), lines 133 to 139 (paths), lines 342 to 353 (write), lines 355 to 361 (removal) |
| Continuation token | Value of the checkpoint file | Text passed as `search_after` to the next page request | `device_events_52w_exporter.py` lines 175 and 214 |
| Batch | Rows of one page, or the rows of the preload pages | Processed rows and a result. The result is True when the writer stores the batch. | `device_events_52w_exporter.py` lines 252 to 263 |
| SQLite table `OrgDeviceEvents_52w` | Composite key `id`, `device_id`, `timestamp` | Indexes on `device_id`, `timestamp`, `type`, `org_id`, and `site_id`. Rows are written with `INSERT OR REPLACE`. | `endpoint_primary_key_strategies.py` lines 265 to 271 and writer line 362 |
| Row rejection | One row in a batch | The per-row handler logs the row and counts it as failed. | `sqlite_database_writer.py` lines 396 to 414 |
| Full-batch request | One SQLite write call | The flag `require_full_batch`. It is False when the caller does not set it. | `export_backend_options.py` (new field, T010) |

## Batch Result Rules

| Stored Rows | Full-Batch Request | Writer Result | Stored Rows After Call | Exporter Result |
| - | - | - | - | - |
| All rows | No | True | All rows | Continue |
| All rows | Yes | True | All rows | Continue |
| Some rows | No | True | Stored rows only | Continue, which is the existing defect for this path |
| Some rows | Yes | False | No row of this batch | Raise RuntimeError, keep the checkpoint |
| No row | No or yes | False | No row of this batch | Raise RuntimeError, keep the checkpoint |
| Zero rows in batch | No or yes | True | Nothing written | Continue |

## State Transitions

| From | Event | To | Checkpoint | Completion Log |
| - | - | - | - | - |
| Fresh run | Preload pages stored | Initial batch stored | Written with the next token | Not logged |
| Batch stored | Next page has rows and a token | Streaming | Written with the next token | Not logged |
| Batch stored | Next page is empty or has no token | Complete | Removed | Logged |
| Batch rejected | Writer returns False | Stopped | Unchanged at the last saved token | Not logged |
| Empty first page | No rows | Empty branch returns | Unchanged | Not logged |
| Resume with unreadable checkpoint | Read fails | Stopped before any page request | Unchanged | Not logged |

The empty-result row follows the existing behavior at `device_events_52w_exporter.py` lines 90 to 91 and 120 to 125. The empty branch returns before the checkpoint removal.

## Natural Key Rule

The SQLite table keeps the natural key from `ENDPOINT_PRIMARY_KEY_STRATEGIES`. This record does not change the key. Issue #4723 owns the key defect that replaces distinct events with the same timestamp.
