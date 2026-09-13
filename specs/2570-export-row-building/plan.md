# Plan: Export row building performance

## Approach

Measured: Record the baseline before application code changes.

Measured: Use `time.perf_counter_ns()` and `time.process_time_ns()` for timing.

Measured: Use `tracemalloc` outside the timed loop for peak traced memory.

Measured: Import modules from `MISTHELPER_ROOT` and assert that the import path is inside the worktree.

## Candidate

Hypothesis: The capture JSON path can build row dictionaries directly.

Hypothesis: This removes one `ExportRow` object and one `to_dict()` copy for each row.

Measured: The public `build_rows()`, `render_csv()`, and `render_json()` interfaces stay unchanged.

Rejected: The comparison full export direct path was not retained.

## Risk controls

Measured: A parity harness compares old bytes and new bytes for CSV and JSON.

Measured: Unit tests compare `export_capture()` with the public renderers.

Measured: The target tests cover formula disarming and credential field removal.
