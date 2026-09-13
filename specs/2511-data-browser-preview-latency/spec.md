# Data browser preview latency

## Problem

Issue #2511 tracks a latency regression in the web portal data browser preview.
PR #2494 kept preview memory bounded, but some measured requests became slower.

## Goal

Keep bounded memory for CSV, JSON Lines, and log previews.
Remove the wall time regression for the measured request workloads.
Keep the response dictionary identical for the same input.

## Non-goals

Do not change the path guard.
Do not change the allowed file extension list.
Do not change the page size limits.
Do not add worker processes, threads, or async execution.

## Behavior contract

The preview result keeps the same `columns`, `rows`, `total_rows`, `page`, `per_page`, and `total_pages` values.
The page size stays between the module constants.
The page number clamps to the valid page range.
A page past the last page returns the last valid page rows.
Search stays case insensitive and matches a substring in any cell.
The JSON path keeps the fallback from standard JSON to JSON Lines.
A single JSON item still returns the item itself.
JSON object column order stays first-seen.
Unreadable file error text does not change.
Log preview line numbers do not change.

## Acceptance criteria

1. Each measured workload is equal to or faster than commit `29fcb967`, within measurement noise.
2. Peak traced memory stays near the bounded values from current `main`.
3. The parity harness reports identical output dictionaries for all states.
