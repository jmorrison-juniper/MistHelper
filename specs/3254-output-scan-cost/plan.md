# Implementation Plan: Reduce Operations Portal Output Scan Cost

## Root Cause

`web_portal/services/output_scan.py` called `_read_state()` after each operation. `_read_state()` listed each unpruned folder. It also statted each reportable file.

The probe measured the remaining cost in file stats. The main cost came from the data root, `CombinedInventory_ByWeek`, and `versions`.

`DataExporter` opens CSV files with mode `w`. An overwrite changes the file modification time. It does not change the parent folder modification time. A folder-only scan would miss that case.

Some writers bypass `builtins.open` and `Path.open`. Examples include SQLite, `os.open`, `os.replace`, C extensions, and child processes. A fast path can miss an in-place rewrite from those writers.

## Design

Add a write tracker to `OutputFileScanner`.

- Start tracking in `snapshot()` after the probe-file mark is recorded.
- Patch `builtins.open` and `Path.open` while at least one scanner is active.
- Record each writable path under the scanner root.
- In `changed_files()`, stop tracking and stat recorded files first.
- Use a directory-mark fallback for new untracked files.
- Use a pruned full-walk fallback only when the fast paths find no output.
- Keep `per-host-logs` unpruned.

## Cost Rule

A run with a tracked write avoids the full walk. It stats only the tracked candidates and new files in changed folders.

A run with no fast-path result pays the old pruned full-walk cost. This preserves untracked in-place rewrites.

## Risks

- A global open hook must be installed and removed safely.
- Concurrent runs can still report a superset. That matches the existing scanner contract.
- A native writer that bypasses Python file open can pay the full-walk fallback.
