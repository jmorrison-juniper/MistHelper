# Contract: Checkpoint file

## File

- **Path**: `data\OrgDeviceEvents_52w.<org_id>.checkpoint`. The name is fixed by `_CHECKPOINT_TEMPLATE` (line 19).
- **Temporary path**: `<checkpoint file>.tmp`, in the same folder.
- **Encoding**: UTF-8 (`_ENCODING`, line 22).

## Content

- The file holds one checkpoint token and no other text.
- The read strips leading and trailing whitespace (line 147).
- The token is a pagination cursor from the Mist response. The exporter does not parse it.

## Read rules

| Condition | Result | Log |
| - | - | - |
| The file does not exist | No token. The run is a fresh run. | None |
| The file exists and the read raises an exception | `RuntimeError`. No page is requested. Both files keep their bytes. | Error with the file name and the cause |
| The file exists and holds only whitespace or zero bytes, and the CSV exists, and the output is CSV | `RuntimeError` (FR-006). Both files keep their bytes. | Error that names the CSV file and the reason |
| The file exists and holds only whitespace or zero bytes, and no CSV exists, or the output is SQLite | No token. The run is a fresh run. | None |
| The file holds a token | The run resumes from the token. | Info with the token (existing line 154) |

## Write rules

1. Write the token to the temporary file in mode `w` with UTF-8 encoding.
2. Replace the checkpoint file with the temporary file by `os.replace`.
3. On any exception during step 1 or 2, log a warning that names the checkpoint file and the cause. Keep the previous checkpoint file.
4. Do not open the live checkpoint file for writing.
5. A write with no token does nothing (line 347-348).

## Removal rules

- The checkpoint file is removed after a completed run (line 117). A resumed run with no new rows keeps the checkpoint file (FR-008).
- A removal failure logs a debug message and does not stop the run (lines 355-361).
- A leftover temporary file is not removed. The next successful write replaces it.

## Compatibility

- Existing checkpoint files hold one token. They read without change.
- The file name and the token format do not change (FR-010).
