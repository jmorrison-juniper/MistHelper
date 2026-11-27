# Contract: CSV resume rules

## File

- **Path**: `data\OrgDeviceEvents_52w.csv`. The name is fixed by `_CSV_FILENAME` (line 17).
- **Encoding**: UTF-8. Rows use `csv.DictWriter` with `newline=""` (line 326 and line 311).
- **Header**: The sorted union of keys from the preload rows (`data_processing_utils.py` line 153). Rows keep only the header fields (lines 385-387).

## Check order for a resumed run

The checks run in this order. Each refusal runs before any page request or write.

| Order | Check | Result | Message text (exact template or reason) |
| - | - | - | - |
| 1 | Checkpoint read | Stop with `RuntimeError` | "Could not read checkpoint file %s. Output and checkpoint are unchanged. Export stopped." (line 150) |
| 2 | Checkpoint empty, CSV present, CSV output | Refuse | Reason: "The checkpoint file is empty." (FR-006) |
| 3 | CSV present | Refuse if missing | Reason: "The CSV file is missing." (line 277) |
| 4 | CSV header equals export fields | Refuse if different | Reason: "The CSV header does not match the export fields." (line 284) |
| 5 | Last CSV byte is a line break | Refuse if not | Reason: "The CSV ends in a partial row." (line 286) |
| 6 | Preload returns rows | Keep both files if none | Info: "No new device events follow the checkpoint. The CSV and checkpoint are unchanged." (FR-008) |

## Refusal template

Each refusal uses the template at lines 267-270:

`Cannot resume into <CSV file>. <reason> Output and checkpoint are unchanged. To start over, remove the checkpoint file. Warning: the next run replaces the CSV.`

- The refusal logs an error with the template, the CSV file, and the reason.
- The refusal raises `RuntimeError` with the same text.

## Append rules

- A resumed run appends rows with mode `a` (line 326).
- A resumed run never writes the header again.
- A fresh run writes the header and rows with mode `w` (line 311).

## Completion rules

- A completed run logs "All org device events (52w) exported to %s." (line 46).
- A completed run removes the checkpoint file (lines 117 and 355).
- A resumed run with no new rows does not log completion. It keeps both files (FR-008).

## Warning

Warning: A fresh run replaces the CSV file. Copy the file before the run when its rows matter.
