# Quickstart: Audit Menu 12 - Organization Inventory Export

**Date**: 2026-04-08

## Prerequisites

- Python 3.13+
- pytest installed (`pip install pytest`)
- Working directory: the `misthelper-spec024` worktree

## Run Tests

```bash
# Unit tests only (fast, no DB)
pytest tests/unit/test_menu_12_inventory.py -v

# Integration tests only (creates temp SQLite DB)
pytest tests/integration/test_menu_12_sqlite_upsert.py -v

# All Menu 12 tests
pytest tests/unit/test_menu_12_inventory.py tests/integration/test_menu_12_sqlite_upsert.py -v

# Full test suite (verify no regressions)
pytest tests/ -v --timeout=30
```

## File Layout

```text
tests/unit/test_menu_12_inventory.py           # 5 unit tests
tests/integration/test_menu_12_sqlite_upsert.py  # 5 integration tests
```

## What the Tests Validate

1. **Unit**: `OrgInventoryExporter.inventory()` passes correct params to `APIDataFetcher`
2. **Unit**: Progress emitter lifecycle (start/complete) with correct menu ID
3. **Integration**: SQLite upsert idempotency (no duplicates on repeated writes)
4. **Integration**: SQLite field update on changed records
5. **Integration**: Index creation for query performance
6. **Integration**: CSV column schema matches expected fields
7. **Integration**: CSV data roundtrip fidelity

## No Production Code Changes

This feature adds tests only. MistHelper.py is not modified.
No deployment pipeline execution is needed.
