# Research: Audit Menu 12 - Organization Inventory Export

**Date**: 2026-04-08
**Spec**: [spec.md](../../024-audit-menu-12-org-inventory/spec.md)

## R1: MistHelper.py Import Side Effects

**Decision**: Rely on the existing `tests/conftest.py` import mechanism which uses
`importlib.util.spec_from_file_location` with `SystemExit` suppression. Unit tests
then use `monkeypatch` to mock globals (`PROGRESS_EMITTER`, `apisession`, etc.).

**Rationale**: The conftest pattern is already proven in `test_exports.py` and
`test_data_processing.py`. It loads MistHelper.py once into `sys.modules` and all
test files import from it. Monkeypatching specific attributes is the standard pytest
approach and avoids fragile import-order dependencies.

**Alternatives Considered**:

- Duplicate classes in test fixtures — rejected: drifts from production code over time.
- Skip conftest and use direct `importlib` in each test file — rejected: redundant
  and violates DRY.

## R2: APIDataFetcher Mocking Strategy

**Decision**: Capture `APIDataFetcher.__init__` arguments by replacing the class with
a mock that records init kwargs and provides a no-op `execute()`. This validates that
`OrgInventoryExporter.inventory()` passes the correct wiring.

**Rationale**: The test goal is to verify parameter passing, not APIDataFetcher
internals. The existing `test_exports.py` demonstrates this pattern by monkeypatching
`ConfigUtils.get_cached_or_prompted_org_id` and stubbing API responses.

**Implementation Pattern**:

```python
captured = {}

class MockAPIDataFetcher:
    def __init__(self, **kwargs):
        captured.update(kwargs)
    def execute(self):
        pass

monkeypatch.setattr(MistHelper, "APIDataFetcher", MockAPIDataFetcher)
MistHelper.OrgInventoryExporter.inventory()
assert captured["filename"] == "OrgInventory.csv"
assert captured["sort_key"] == "model"
assert captured["limit"] == 1000
```

## R3: SQLite Integration Test Strategy

**Decision**: Call `DataExporter.write_with_format_selection()` directly with fixture
data and `api_function_name="getOrgInventory"`. Monkeypatch `DATABASE_PATH` to point
at a temp directory. Read back with raw `sqlite3` to verify row counts and indexes.

**Rationale**: This isolates the SQLite layer from API transport. The PK strategy
resolution (`ENDPOINT_PRIMARY_KEY_STRATEGIES["getOrgInventory"]`) is exercised
end-to-end through `SQLiteDatabaseWriter` without needing to mock API calls.

**Key Assertions**:

1. After writing N records twice, table has exactly N rows (upsert idempotency).
2. After writing a record, then writing same `id` with changed `model`, the table
   reflects the updated value.
3. `PRAGMA index_list(OrgInventory)` returns indexes for `org_id`, `mac`, `serial`, etc.

## R4: PROGRESS_EMITTER Mocking

**Decision**: Use `unittest.mock.MagicMock()` assigned to `MistHelper.PROGRESS_EMITTER`.
Assert `emit_progress_start("12", "inventory", 1)` and
`emit_progress_complete("12", "inventory", 1, 1, False, <any_float>)` are called.

**Rationale**: The emitter pattern is consistent across all menu operations (seen in
inventory, devices, sites, device_stats). A MagicMock records all calls without
side effects.

**Edge Case**: When `PROGRESS_EMITTER is None` (default), the inventory method skips
emitter calls. A separate test verifies no exception is raised in this case.

## R5: Fixture Data Design

**Decision**: Three device records covering AP, switch, and gateway with varying
field completeness. Stored as module-level constants in each test file (not shared
across unit/integration to avoid coupling).

**Rationale**: The `getOrgInventory` API returns relatively flat records. Three
records cover the three device types and the "missing optional fields" edge case.

**Fields sourced from**: Mist API documentation and the existing PK strategy definition
which indexes `org_id`, `site_id`, `mac`, `serial`, `model`, `type`.
