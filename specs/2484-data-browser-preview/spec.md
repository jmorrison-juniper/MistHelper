# Specification: Data browser preview memory use

## Goal
Reduce peak Python traced memory in file preview requests.

## Scope
The change covers CSV, JSON, JSON Lines, and log preview paths in `web_portal/services/data_browser.py`.
SQLite preview behavior is out of scope.

## Behavior
The service must keep the same response dictionary for the same input.
It must keep `total_rows`, `total_pages`, `page`, and `per_page` stable.
It must keep case-insensitive search across all row cells.
It must keep JSON fallback from standard JSON to JSON Lines.
It must keep the path guard and the allowed file extensions unchanged.

## Performance objective
Measured: Reduce peak traced Python memory for large single-page previews.
Measured: Use synthetic CSV, JSON Lines, and log files that match exported portal data shape.
Measured: Retain the change only if peak traced memory falls by a meaningful amount.

## Non-goals
Do not add multiprocessing, threading, asyncio, worker changes, or task sharding.
Do not change public APIs or error text.
Do not change SQLite query behavior.
