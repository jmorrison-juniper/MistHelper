# Specification: Lock audit read cost

## Goal
Reduce the memory use of the lock audit history read.

## User need
An operator opens the history page. The page asks for the newest lock audit rows. The audit file can hold many old rows.

## Current behavior
The reader reads the whole JSONL file. It builds all inferred rows. It shapes all rows. It then returns the newest page.

## Required behavior
The reader returns the same rows in the same order. Each row keeps the same fields and types. A damaged line still costs that line only. A missing file still returns an empty list.

## Scope
Change `src/upgrade_portal/compare/lock_audit.py`. Keep the writer format in `src/upgrade_portal/runtime/lock.py` unchanged.

## Constraints
Use one sequential process. Do not add threads, processes, async work, workers, or sharding. Use local disposable JSONL fixtures only.

## Acceptance
Retain the change only if measurement shows a clear memory reduction, or enough time reduction, with equal behavior.
