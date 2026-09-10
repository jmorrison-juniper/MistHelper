# Implementation Plan: Dashboard data summary performance

**Branch**: `chore/2439-dashboard-summary-performance`
**Issue**: #2439
**Date**: 2026-09-10

## Summary

The dashboard summary scanned the data directory twice. It also formatted the
size and timestamp for every file before it returned five recent files. The new
path scans once, counts visible files, selects the newest entries with a stable
key, and formats only returned rows.

## Technical Context

- **Language**: Python 3.13.3
- **Runtime**: CPython on Windows 11, AMD64
- **CPU count**: 32 logical cores
- **Concurrency**: Not used. The optimization is sequential only.
- **Entry point**: `web_portal.routes.dashboard._build_data_summary`
- **Benchmark input**: Disposable local directory with 5000 CSV files and hidden
  files.

## Measurement Contract

- **Objective**: Reduce dashboard summary latency, CPU time, and traced Python
  memory.
- **Boundary**: `_build_data_summary(data_dir)` from call entry to returned dict.
- **Baseline revision**: `81dcef84c240ce97f6b2c9cde9b1600da75d5275`
- **Candidate state**: `chore/2439-dashboard-summary-performance` worktree.
- **Acceptance**: At least 5 percent end-to-end time reduction with equal output.

## Design

1. Keep `_build_data_summary()` as the dashboard entry point.
2. Add `_scan_data_summary()` to count files and collect raw metadata once.
3. Use `heapq.nlargest(..., key=...)` to preserve stable tie order.
4. Format file size and timestamp only after selecting the displayed rows.
5. Keep `_count_data_files()` and `_get_recent_files()` as helper contracts.

## Risks

- A bounded heap can reorder equal timestamps. The implementation does not use a
  bounded heap.
- `heapq.nlargest()` without a `key` can compare tuple fields and change ties.
  The implementation always passes a key.
- Negative limits had slice behavior. The implementation preserves it.

## Validation

- Unit tests cover absent directories, visible file count, hidden entries,
  directories, recent-file order, equal timestamp order, display formatting, and
  negative-limit behavior.
- The benchmark compares baseline and candidate outputs.
- Ruff and Black run on the changed files.

