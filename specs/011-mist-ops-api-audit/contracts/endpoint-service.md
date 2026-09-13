# Contract: MistEndpointService

**File**: `src/shared/mist/endpoints.py`
**Consumers**: All sync services, deploy services, checks, auth service

## Public Interface

### read_entity(entity_type, ids) -> ApiResult

Fetch a single entity's configuration from Mist.

**Parameters**:
| Name | Type | Required | Description |
|---|---|---|---|
| entity_type | str | Yes | Registry key (e.g., "device", "site_setting") |
| ids | dict[str, str] | Yes | Scope IDs matching endpoint's `id_params` |

**Returns**: `ApiResult` with the entity's config in `.data`.

**Errors**:
- `ValueError` if `entity_type` not in registry.
- `ValueError` if required ID params missing from `ids`.
- `AttributeError` if endpoint has no `read_method`.

---

### write_entity(entity_type, ids, body) -> ApiResult

Push a configuration payload to a single Mist entity.

**Parameters**:
| Name | Type | Required | Description |
|---|---|---|---|
| entity_type | str | Yes | Registry key |
| ids | dict[str, str] | Yes | Scope IDs matching endpoint's `id_params` |
| body | dict[str, Any] | Yes | Configuration payload |

**Returns**: `ApiResult` with the write response.

**Errors**:
- `ValueError` if `entity_type` not in registry.
- `ValueError` if required ID params missing.
- `AttributeError` if endpoint has no `write_method`.

---

### list_all_entities(entity_type, ids) -> ApiResult

Fetch all pages of a list/search operation.

**Parameters**:
| Name | Type | Required | Description |
|---|---|---|---|
| entity_type | str | Yes | Registry key with `list_method` set |
| ids | dict[str, str] | Yes | Scope IDs (e.g., `{"org_id": "..."}`) |

**Returns**: `ApiResult` with `.data` as a combined list of all pages.

**Errors**:
- `ValueError` if `entity_type` not in registry.
- `AttributeError` if endpoint has no `list_method`.

**Pagination**: Automatically follows `response.next` until all pages exhausted.

---

## ApiResult Contract

```python
@dataclass(frozen=True, slots=True)
class ApiResult:
    status_code: int
    data: dict[str, Any] | list[dict[str, Any]]

    @property
    def success(self) -> bool: ...   # True for 2xx

    @property
    def error(self) -> str | None: ...  # Error detail or None
```

**Invariants**:
- `success` is `True` if and only if `200 <= status_code < 300`.
- `error` is `None` when `success` is `True`.
- `error` extracts `data["detail"]` when available, falls back to `str(data)`.
