# Implementation Plan: Reduce Operations Portal Output Scan Cost

## Root Cause

`web_portal/services/output_scan.py` calls `_read_state()` after each operation. `_read_state()` lists each unpruned folder and stats each reportable file. The probe measured the remaining cost in file stats, mainly under the data root, `CombinedInventory_ByWeek`, and `versions`.

`DataExporter` opens CSV files with mode `w`. An overwrite changes the file modification time, but it does not change the parent folder modification time. A folder-only scan would miss that case.

## Design

Add a write tracker to `OutputFileScanner`.

- Start tracking in `snapshot()` after the probe-file mark is recorded.
- Patch `builtins.open` and `Path.open` while at least one scanner is active.
- Record each writable path under the scanner root.
- In `changed_files()`, stop tracking and stat only recorded files first.
- Use a directory-mark fallback for untracked writers. It stats only reportable files in directories whose own modification time changed.
- Keep `per-host-logs` unpruned.

## Risks

- A global open hook must be installed and removed safely.
- Concurrent runs can still report a superset. That matches the existing scanner contract.
- A native writer that bypasses Python file open may need the directory-mark fallback.
