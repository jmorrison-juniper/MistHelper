# Quickstart: Mist-Ops Platform API Endpoint Audit

**Branch**: `011-mist-ops-api-audit` | **Date**: 2025-07-16

## Prerequisites

- Python 3.13+
- mistapi 0.60.4 (`pip install mistapi`)
- pytest
- Access to `mist-ops-platform/` source tree

## Implementation Order

Work through these changes in dependency order. Each step is independently testable.

### Step 1: Fix MistEndpoint dataclass (types.py)

Make `read_method` and `write_method` optional. Add `list_method` field.

```python
# Change from:
read_method: str
write_method: str

# Change to:
read_method: str | None
write_method: str | None
list_method: str | None = None
```

**Test**: `MistEndpoint(entity_type="test", api_module="orgs.sites", read_method=None, write_method=None, list_method="listOrgSites", id_params=("org_id",))` constructs without error.

### Step 2: Fix existing registry entries (types.py)

Two fixes in `ENTITY_ENDPOINT_MAP`:

1. `org_wlan`: Change `read_method="getOrgWlan"` to `read_method="getOrgWLAN"`
2. `site_info`: Change `api_module="sites.site"` to `api_module="sites.sites"`

**Test**: Import each module and verify `hasattr(module, method)` for all 14 entries.

### Step 3: Add new entity types (types.py)

Add 9 new entries to `ENTITY_ENDPOINT_MAP` (see data-model.md for full list).

**Test**: `MistEntityRegistry.entity_types()` returns 23 sorted keys. `MistEntityRegistry.get("firmware_site")` returns a valid `MistEndpoint`.

### Step 4: Expand ApiResult (endpoints.py)

Add `.success` and `.error` properties to `ApiResult`.

**Test**:
```python
ok = ApiResult(status_code=200, data={"id": "abc"})
assert ok.success is True
assert ok.error is None

err = ApiResult(status_code=400, data={"detail": "bad request"})
assert err.success is False
assert err.error == "bad request"
```

### Step 5: Add list_all_entities with pagination (endpoints.py)

Add `list_all_entities()` method and `_paginate()` helper to `MistEndpointService`.

**Test**: Mock SDK response with `.next` set on first call, None on second. Verify all data combined.

### Step 6: Fix call signatures (executor.py, rollback.py)

Change `write_entity(api_module=..., write_method=..., ...)` to `write_entity(entity_type=..., ids=..., body=...)`. Same for `read_entity`.

**Test**: Mock `MistEndpointService` and verify correct args passed.

### Step 7: Fix method names (pre_checks.py, post_checks.py)

Change `list_method="getOrgDevice"` to use `list_all_entities("org_device_list", ...)` through the registry.

**Test**: Verify `MistEndpointService.list_all_entities` is called with `entity_type="org_device_list"`.

### Step 8: Fix internal method call (drift.py)

Change `self._diff.compute(...)` to `self._diff.compute_diff(...)`.

**Test**: Mock `DiffService` and verify `compute_diff` is called.

### Step 9: Refactor auth bypass (auth.py)

Replace direct `mistapi.api.v1.self.self.getSelf(session)` with registry-based call through `MistEndpointService`.

**Test**: Verify `list_all_entities("self_identity", {})` is called.

### Step 10: Add firmware SDK call (firmware.py)

Add `execute_upgrade()` method to `FirmwareOrchestrator` that calls `write_entity("firmware_site", ...)` (or `firmware_device`/`firmware_org` as appropriate).

**Test**: Mock `MistEndpointService.write_entity` and verify correct entity type and payload.

### Step 11: Refactor sync services (inventory.py, status.py, events.py)

Replace `list_entities(api_module=..., list_method=..., ids=...)` calls with `list_all_entities(entity_type=..., ids=...)`.

**Test**: Verify each sync service calls the correct entity type through the registry.

## Verification

After all steps:

```bash
cd mist-ops-platform
pytest tests/unit/mist/ -v
```

All 24 issues from research.md should be resolved with zero `AttributeError`, `ModuleNotFoundError`, or `TypeError` at any SDK call site.
