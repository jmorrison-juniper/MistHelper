# Contract: MistEntityRegistry

**File**: `src/shared/mist/types.py`
**Consumers**: `MistEndpointService`, tests

## Public Interface

### MistEntityRegistry.get(entity_type) -> MistEndpoint

Return the endpoint record for an entity type.

**Parameters**:
| Name | Type | Required | Description |
|---|---|---|---|
| entity_type | str | Yes | Key in ENTITY_ENDPOINT_MAP |

**Returns**: `MistEndpoint` frozen dataclass.

**Errors**: `ValueError` if entity_type is not registered.

---

### MistEntityRegistry.entity_types() -> list[str]

Return sorted list of all registered entity type names.

---

### MistEntityRegistry.has(entity_type) -> bool

Check whether an entity type is registered.

---

## MistEndpoint Contract

```python
@dataclass(frozen=True, slots=True)
class MistEndpoint:
    entity_type: str
    api_module: str
    read_method: str | None
    write_method: str | None
    id_params: tuple[str, ...]
    list_method: str | None = None
```

**Invariants**:
- At least one of `read_method`, `write_method`, or `list_method` must be non-None.
- `api_module` must resolve via `importlib.import_module(f"mistapi.api.v1.{api_module}")`.
- Each non-None method name must exist as an attribute on the imported module.

## Entity Type Catalog (post-audit)

| Entity Type | read | write | list | Scope |
|---|---|---|---|---|
| ap_template | Y | Y | - | org |
| audit_log | - | - | Y | org |
| device | Y | Y | - | site |
| device_profile | Y | Y | - | org |
| device_stats | Y | - | - | site |
| firmware_device | - | Y | - | site |
| firmware_org | - | Y | - | org |
| firmware_site | - | Y | - | site |
| gateway_template | Y | Y | - | org |
| nac_rule | Y | Y | - | org |
| network | Y | Y | - | org |
| network_template | Y | Y | - | org |
| org_device_list | - | - | Y | org |
| org_inventory | - | - | Y | org |
| org_site_list | - | - | Y | org |
| org_wlan | Y | Y | - | org |
| rf_template | Y | Y | - | org |
| security_policy | Y | Y | - | org |
| self_identity | - | - | Y | global |
| service_policy | Y | Y | - | org |
| site_info | Y | Y | - | site |
| site_setting | Y | Y | - | site |
| site_wlan | Y | Y | - | site |
