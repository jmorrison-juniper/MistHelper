# Data Model: Mist-Ops Platform API Endpoint Audit

**Branch**: `011-mist-ops-api-audit` | **Date**: 2025-07-16

## Entity Changes

### 1. MistEndpoint (modified)

**File**: `src/shared/mist/types.py`
**Change**: Make `read_method` and `write_method` optional to support read-only, write-only, and list-only entity types.

```python
@dataclass(frozen=True, slots=True)
class MistEndpoint:
    entity_type: str
    api_module: str
    read_method: str | None       # None for write-only (firmware)
    write_method: str | None      # None for read-only (self_identity, stats)
    id_params: tuple[str, ...]
    list_method: str | None = None  # For list/search operations
```

**Fields**:
| Field | Type | Required | Description |
|---|---|---|---|
| entity_type | str | Yes | Unique key in the registry |
| api_module | str | Yes | Dotted path under `mistapi.api.v1` |
| read_method | str or None | No | SDK method for single-entity reads |
| write_method | str or None | No | SDK method for single-entity writes |
| id_params | tuple[str, ...] | Yes | Required ID kwargs for SDK calls |
| list_method | str or None | No | SDK method for listing/searching |

**Validation rules**:
- At least one of `read_method`, `write_method`, or `list_method` must be non-None.
- `id_params` must contain only valid Mist API parameter names.

---

### 2. ApiResult (modified)

**File**: `src/shared/mist/endpoints.py`
**Change**: Add derived `.success` and `.error` properties to the existing dataclass.

```python
@dataclass(frozen=True, slots=True)
class ApiResult:
    status_code: int
    data: dict[str, Any] | list[dict[str, Any]]

    @property
    def success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def error(self) -> str | None:
        if self.success:
            return None
        if isinstance(self.data, dict):
            return self.data.get("detail", str(self.data))
        return str(self.data)
```

**Fields**:
| Field/Property | Type | Stored/Derived | Description |
|---|---|---|---|
| status_code | int | Stored | HTTP status code from SDK response |
| data | dict or list | Stored | Parsed response payload |
| success | bool | Derived | True when status_code is 2xx |
| error | str or None | Derived | Error detail on non-2xx, None on success |

**Validation rules**:
- `status_code` must be a valid HTTP status code (100-599).
- `success` is read-only (no setter).

---

### 3. ENTITY_ENDPOINT_MAP (modified)

**File**: `src/shared/mist/types.py`
**Change**: Fix existing entries and add new entity types.

#### Fixes to Existing Entries

| Entity Type | Field | Current | Corrected |
|---|---|---|---|
| org_wlan | read_method | `getOrgWlan` | `getOrgWLAN` |
| site_info | api_module | `sites.site` | `sites.sites` |

#### New Entity Types

| Entity Type | api_module | read_method | write_method | list_method | id_params |
|---|---|---|---|---|---|
| self_identity | self.self | None | None | getSelf | () |
| org_site_list | orgs.sites | None | None | listOrgSites | (org_id,) |
| org_inventory | orgs.inventory | None | None | getOrgInventory | (org_id,) |
| org_device_list | orgs.devices | None | None | listOrgDevices | (org_id,) |
| device_stats | sites.stats | getSiteDeviceStats | None | None | (site_id, device_id) |
| audit_log | orgs.logs | None | None | listOrgAuditLogs | (org_id,) |
| firmware_device | sites.devices | None | upgradeDevice | None | (site_id, device_id) |
| firmware_site | sites.devices | None | upgradeSiteDevices | None | (site_id,) |
| firmware_org | orgs.devices | None | upgradeOrgDevices | None | (org_id,) |

---

### 4. MistEndpointService (modified)

**File**: `src/shared/mist/endpoints.py`
**Change**: Add `list_all_entities()` method with pagination support.

```python
def list_all_entities(
    self,
    entity_type: str,
    ids: dict[str, str],
) -> ApiResult:
    """Fetch all pages of a list operation."""
    endpoint = MistEntityRegistry.get(entity_type)
    func = self._resolve_func(endpoint, endpoint.list_method)
    args = self._build_args(endpoint, ids)
    all_data = self._paginate(func, args)
    return ApiResult(status_code=200, data=all_data)
```

New private helper:

```python
def _paginate(self, func, args) -> list:
    """Follow SDK pagination until all pages retrieved."""
    all_data: list = []
    response = func(self._session, **args)
    all_data.extend(self._extract_list(response))
    while getattr(response, "next", None):
        response = func(self._session, **args)
        all_data.extend(self._extract_list(response))
    return all_data
```

---

### 5. FirmwareOrchestrator (modified)

**File**: `src/worker/deploy/firmware.py`
**Change**: Add `execute_upgrade()` method that calls the SDK via registry.

```python
def execute_upgrade(
    self,
    mist_service: MistEndpointService,
    image_id: UUID,
    target_device_ids: list[UUID],
) -> ApiResult:
    """Execute firmware upgrade via SDK after validation."""
    validation = self.validate_upgrade(image_id, target_device_ids)
    if not validation["valid"]:
        raise ValueError(validation["errors"])
    payload = self.build_upgrade_payload(image_id, target_device_ids)
    return mist_service.write_entity(
        entity_type="firmware_site",
        ids={"site_id": site_id},
        body=payload,
    )
```

---

## Relationships

```text
MistEntityRegistry ──uses──> ENTITY_ENDPOINT_MAP (dict of MistEndpoint)
MistEndpointService ──uses──> MistEntityRegistry (lookups)
MistEndpointService ──returns──> ApiResult (from _wrap)
FirmwareOrchestrator ──uses──> MistEndpointService (for execute_upgrade)
Sync services ──uses──> MistEndpointService.list_all_entities()
Deploy services ──uses──> MistEndpointService.write_entity()
Auth service ──uses──> MistEndpointService.list_all_entities() (self_identity)
Pre/Post checks ──uses──> MistEndpointService.list_all_entities() (org_device_list)
Drift scanner ──uses──> DiffService.compute_diff() (internal fix)
```

## State Transitions

No state machines are introduced. The `ApiResult.success` property is a pure derivation from `status_code` — no state tracking.

The `FirmwareOrchestrator` workflow is sequential:
1. `validate_upgrade()` → returns validation dict
2. `build_upgrade_payload()` → returns payload dict
3. `execute_upgrade()` → calls SDK, returns `ApiResult`

Step 3 must only run after step 1 returns `{"valid": True}`.
