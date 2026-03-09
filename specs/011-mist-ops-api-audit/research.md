# Research: Mist-Ops Platform API Endpoint Audit

**Branch**: `011-mist-ops-api-audit` | **Date**: 2025-07-16

## R-01: SDK Module Path Verification

**Decision**: All 14 entity registry module paths verified against mistapi 0.60.4.  
**Rationale**: Running `importlib.import_module()` on each `mistapi.api.v1.<path>` confirms importability at runtime.  
**Alternatives considered**: Static analysis only — rejected because dynamic import is how `MistEndpointService._resolve_func()` actually loads modules.

### Results

| Entity Type | Module Path | Status |
|---|---|---|
| ap_template | orgs.aptemplates | OK |
| device | sites.devices | OK |
| device_profile | orgs.deviceprofiles | OK |
| gateway_template | orgs.gatewaytemplates | OK |
| nac_rule | orgs.nacrules | OK |
| network | orgs.networks | OK |
| network_template | orgs.networktemplates | OK |
| org_wlan | orgs.wlans | OK |
| rf_template | orgs.rftemplates | OK |
| security_policy | orgs.secpolicies | OK |
| service_policy | orgs.servicepolicies | OK |
| **site_info** | **sites.site** | **MODULE NOT FOUND** |
| site_setting | sites.setting | OK |
| site_wlan | sites.wlans | OK |

### Fix: site_info Module Path

- **Current**: `sites.site` (singular) — does not exist in SDK
- **Correct**: `sites.sites` (plural) — contains `getSiteInfo`, `updateSiteInfo`, `deleteSite`
- **Impact**: Any `read_entity("site_info", ...)` or `write_entity("site_info", ...)` call will crash with `ModuleNotFoundError`

---

## R-02: SDK Method Name Verification

**Decision**: All 28 read/write methods verified via `hasattr()` against their respective modules.  
**Rationale**: Method name typos cause `AttributeError` at runtime; verifying against installed SDK is definitive.  
**Alternatives considered**: Grepping SDK source code — rejected because `hasattr()` on the imported module is authoritative.

### Mismatches Found

| Entity | Field | Current (Wrong) | Correct | Root Cause |
|---|---|---|---|---|
| org_wlan | read_method | `getOrgWlan` | `getOrgWLAN` | Case sensitivity — SDK uses capital LAN |
| org_wlan | write_method | `updateOrgWlan` | `updateOrgWlan` | **CORRECT** — no change needed |

### External Call Mismatches (outside registry)

| File | Line | Current (Wrong) | Correct | Root Cause |
|---|---|---|---|---|
| pre_checks.py | 73 | `getOrgDevice` | `listOrgDevices` | Method does not exist; `getOrgDevice` is not an SDK method |
| post_checks.py | 65 | `getOrgDevice` | `listOrgDevices` | Same as above |

### All Verified Methods

The following 26 methods are confirmed correct on their modules:
- `getOrgAptemplate`, `updateOrgAptemplate`
- `getSiteDevice`, `updateSiteDevice`
- `getOrgDeviceProfile`, `updateOrgDeviceProfile`
- `getOrgGatewayTemplate`, `updateOrgGatewayTemplate`
- `getOrgNacRule`, `updateOrgNacRule`
- `getOrgNetwork`, `updateOrgNetwork`
- `getOrgNetworkTemplate`, `updateOrgNetworkTemplate`
- `getOrgRfTemplate`, `updateOrgRfTemplate`
- `getOrgSecPolicy`, `updateOrgSecPolicy`
- `getOrgServicePolicy`, `updateOrgServicePolicy`
- `getSiteSetting`, `updateSiteSettings`
- `getSiteWlan`, `updateSiteWlan`
- `updateOrgWlan` (write side of org_wlan — correct)

---

## R-03: APIResponse Structure

**Decision**: `ApiResult` must derive `.success` and `.error` from `status_code` and `data`.  
**Rationale**: The mistapi `APIResponse` class has no `.success` or `.error` attributes. Consumer code references these properties on `ApiResult`, which only has `status_code` and `data`.  
**Alternatives considered**: Rewriting all consumers to check `status_code` directly — rejected per spec clarification (expand ApiResult with derived properties).

### APIResponse Instance Attributes (from SDK source)

| Attribute | Type | Description |
|---|---|---|
| `status_code` | `int \| None` | HTTP status code |
| `data` | `dict \| list` | Parsed JSON response body |
| `raw_data` | `str` | Raw response text |
| `url` | `str` | Request URL |
| `next` | `str \| None` | Next page URL (pagination) |
| `headers` | `CaseInsensitiveDict \| None` | Response headers |
| `proxy_error` | `bool` | Whether a proxy error occurred |

### Consumer Code Using Missing Properties

| File | Line | Access | Context |
|---|---|---|---|
| executor.py | 91 | `result.success` | Config push success check |
| executor.py | 99-103 | `result.error` | Error logging |
| rollback.py | 106 | `result.success` | Rollback read check |
| rollback.py | 124,127 | `.success`, `.error` | Rollback write check |
| pre_checks.py | 76 | `api_result.success` | Pre-check validation |

### Proposed ApiResult Expansion

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

---

## R-04: Pagination Mechanism

**Decision**: Implement page-following loop using `APIResponse.next` attribute.  
**Rationale**: The SDK sets `response.next` via `_check_next()` — either from `data["next"]` key or from `X-Page-Total` / `X-Page-Limit` / `X-Page-Page` headers. All list methods accept `limit` and `page` parameters.  
**Alternatives considered**: Using `limit`/`page` parameters manually — rejected because `response.next` is the SDK's built-in mechanism.

### List Methods With Pagination Support

| Method | Module | Has limit/page params |
|---|---|---|
| `listOrgSites` | orgs.sites | Yes |
| `getOrgInventory` | orgs.inventory | Yes |
| `listOrgAuditLogs` | orgs.logs | Yes |
| `listOrgDevices` | orgs.devices | No (returns all) |

### Pagination Pattern

```python
def _paginate(self, func, session, **kwargs) -> list:
    all_data = []
    response = func(session, **kwargs)
    all_data.extend(response.data if isinstance(response.data, list) else [response.data])
    while response.next:
        response = func(session, **kwargs, page=next_page)
        all_data.extend(response.data if isinstance(response.data, list) else [response.data])
    return all_data
```

**Note**: Exact pagination loop implementation depends on whether `response.next` is a URL or a page number. Research shows it can be either — the implementation must handle the SDK's `next` attribute directly.

---

## R-05: Firmware Upgrade SDK Methods

**Decision**: Add firmware upgrade methods to the entity registry and wire into `FirmwareOrchestrator`.  
**Rationale**: The orchestrator currently builds payloads (`build_upgrade_payload`) but never calls the SDK to trigger the actual upgrade. Three SDK methods are available.  
**Alternatives considered**: Direct SDK calls without registry — rejected per spec clarification (all calls through registry).

### Available Firmware Methods

| Method | Module | Signature |
|---|---|---|
| `upgradeDevice` | sites.devices | `(session, site_id, device_id, body)` |
| `upgradeSiteDevices` | sites.devices | `(session, site_id, body)` |
| `upgradeOrgDevices` | orgs.devices | `(session, org_id, body)` |

### Registry Integration

These are write-only operations (no read counterpart). The registry pattern `MistEndpoint` assumes read + write pairs. Options:
1. Add new entity types with `read_method=None` (requires endpoint service changes)
2. Add a parallel `FIRMWARE_ENDPOINT_MAP` for write-only operations
3. Use `list_entities()` pattern for ad-hoc calls

**Decision**: Option 1 — extend `MistEndpoint` to support optional `read_method`, keeping all SDK calls in a single registry.

---

## R-06: Internal Method Name Mismatches

**Decision**: Fix internal cross-service calls alongside SDK calls.  
**Rationale**: Internal method mismatches cause the same category of `AttributeError` as SDK mismatches.  
**Alternatives considered**: Separate audit pass — rejected because the fix is trivial and in scope per FR-006.

### Findings

| File | Line | Current Call | Correct Method | Target Class |
|---|---|---|---|---|
| drift.py | 85 | `self._diff.compute(...)` | `self._diff.compute_diff(...)` | `DiffService` |

---

## R-07: Direct SDK Calls Bypassing Registry

**Decision**: Refactor all bypass calls to use the entity registry.  
**Rationale**: Per spec clarification, all SDK calls must go through registered entity types — no exceptions.  
**Alternatives considered**: Allowing exceptions for auth/self — rejected per user decision.

### Bypass Calls Found

| File | Line | SDK Call | Required Action |
|---|---|---|---|
| auth.py | 63 | `mistapi.api.v1.self.self.getSelf(session)` | Add `self_identity` entity type to registry |
| pre_checks.py | 73 | `list_entities("orgs.devices", "getOrgDevice", ...)` | Fix method name + add entity type |
| post_checks.py | 65 | `list_entities("orgs.devices", "getOrgDevice", ...)` | Fix method name + add entity type |
| inventory.py | 63 | `list_entities("orgs.sites", "listOrgSites", ...)` | Add `org_site_list` entity type |
| inventory.py | 76 | `list_entities("orgs.inventory", "getOrgInventory", ...)` | Add `org_inventory` entity type |
| status.py | 50 | `list_entities("sites.stats", "getSiteDeviceStats", ...)` | Add `device_stats` entity type |
| events.py | 47 | `list_entities("orgs.logs", "listOrgAuditLogs", ...)` | Add `audit_log` entity type |

### New Entity Types Required

| Entity Type | Module | Method | id_params | Notes |
|---|---|---|---|---|
| self_identity | self.self | getSelf | (none) | Read-only, no write method |
| org_site_list | orgs.sites | listOrgSites | (org_id,) | List operation, pagination |
| org_inventory | orgs.inventory | getOrgInventory | (org_id,) | List operation, pagination |
| org_device_list | orgs.devices | listOrgDevices | (org_id,) | List operation |
| device_stats | sites.stats | getSiteDeviceStats | (site_id, device_id) | Read-only |
| audit_log | orgs.logs | listOrgAuditLogs | (org_id,) | List operation, pagination |
| firmware_upgrade_device | sites.devices | upgradeDevice | (site_id, device_id) | Write-only |
| firmware_upgrade_site | sites.devices | upgradeSiteDevices | (site_id,) | Write-only |
| firmware_upgrade_org | orgs.devices | upgradeOrgDevices | (org_id,) | Write-only |

---

## R-08: Call Signature Mismatches

**Decision**: Fix all call sites to pass arguments matching actual method/service signatures.  
**Rationale**: Passing wrong keyword arguments causes `TypeError` at runtime.  
**Alternatives considered**: None — this is a direct bug fix.

### Findings

| File | Call | Current Args | Correct Args |
|---|---|---|---|
| executor.py | `write_entity()` | `api_module=, write_method=, ids=, body=` | `entity_type=, ids=, body=` |
| rollback.py | `read_entity()` | `api_module=, read_method=, ids=` | `entity_type=, ids=` |
| rollback.py | `write_entity()` | `api_module=, write_method=, ids=, body=` | `entity_type=, ids=, body=` |

---

## R-09: API Documentation Cross-Reference

**Decision**: Cross-referenced all SDK findings against `documentation/api/` enriched endpoint docs (1013 operations across 206 tags).  
**Rationale**: SDK introspection verifies method existence and signatures, but API docs validate endpoint semantics — parameters, response schemas, pagination defaults, and operationId mappings.  
**Source**: `documentation/api/INDEX.md` + individual endpoint files in `orgs/`, `sites/`, `utilities/`

### Confirmations from API Docs

| Finding | API Doc File | Confirmation |
|---|---|---|
| `getOrgWLAN` (capital LAN) | `orgs/GET_orgs_org_id_wlans_wlan_id.md` | operationId is `getOrgWLAN` — confirms R-02 fix |
| `listOrgDevices` (not `getOrgDevice`) | `orgs/GET_orgs_org_id_devices.md` | operationId is `listOrgDevices`, returns `{results: [...]}` wrapper — confirms R-02 fix |
| `getSelf` module path | `self/GET_self.md` | operationId is `getSelf` — confirms R-07 entity type |
| `getSiteSetting` method | `sites/GET_sites_site_id_setting.md` | operationId is `getSiteSetting` — confirms registry entry correct |
| `listOrgSecPolicies` method | `orgs/GET_orgs_org_id_secpolicies.md` | operationId is `listOrgSecPolicies` — confirms R-02 verified list |
| `upgradeSiteDevices` method | `utilities/POST_sites_site_id_devices_upgrade.md` | operationId is `upgradeSiteDevices` — confirms R-05 |

### New Findings from API Docs

| # | Finding | API Doc Source | Impact |
|---|---|---|---|
| 1 | `getOrgInventory` has `limit=100, page=1` defaults | `orgs/GET_orgs_org_id_inventory.md` | Confirms pagination needed for large inventories (R-04) |
| 2 | `listOrgSecPolicies` also has `limit=100, page=1` | `orgs/GET_orgs_org_id_secpolicies.md` | New: security_policy entity may need pagination if >100 policies |
| 3 | `listOrgDevices` is "Not paginated" per docs | `orgs/GET_orgs_org_id_devices.md` | Confirms R-04: no pagination params needed for this endpoint |
| 4 | Firmware `upgradeSiteDevices` returns `{upgrade_id: uuid}` | `utilities/POST_sites_site_id_devices_upgrade.md` | FirmwareOrchestrator should capture and return upgrade_id for tracking |
| 5 | Firmware request body supports `strategy` enum: `big_bang`, `canary`, `rrm`, `serial` | `utilities/POST_sites_site_id_devices_upgrade.md` | Validates `build_upgrade_payload` options; `rrm` is APs-only |
| 6 | Firmware supports `rules` matching (match_name, match_model, match_role) | `utilities/POST_sites_site_id_devices_upgrade.md` | Additional device selection beyond `device_ids` and `models` |
| 7 | `reboot` param is "Switches and Gateways only" (APs auto-reboot) | `utilities/POST_sites_site_id_devices_upgrade.md` | Payload builder should only include `reboot` for non-AP device types |

### Documentation Reference Index

For future implementation, operationId in API docs maps directly to mistapi SDK method names:

| operationId (API Docs) | SDK Method | Doc File |
|---|---|---|
| `getOrgWLAN` | `orgs.wlans.getOrgWLAN()` | `orgs/GET_orgs_org_id_wlans_wlan_id.md` |
| `listOrgDevices` | `orgs.devices.listOrgDevices()` | `orgs/GET_orgs_org_id_devices.md` |
| `getOrgInventory` | `orgs.inventory.getOrgInventory()` | `orgs/GET_orgs_org_id_inventory.md` |
| `getSelf` | `self.self.getSelf()` | `self/GET_self.md` |
| `getSiteSetting` | `sites.setting.getSiteSetting()` | `sites/GET_sites_site_id_setting.md` |
| `upgradeSiteDevices` | `sites.devices.upgradeSiteDevices()` | `utilities/POST_sites_site_id_devices_upgrade.md` |
| `upgradeOrgDevices` | `orgs.devices.upgradeOrgDevices()` | `utilities/POST_orgs_org_id_devices_upgrade.md` |

---

## Summary of All Issues

| # | Category | Count | Severity |
|---|---|---|---|
| 1 | Module path errors | 1 (site_info) | Critical |
| 2 | Method name errors | 3 (getOrgWlan, getOrgDevice x2) | Critical |
| 3 | Missing ApiResult properties | 5 call sites | Critical |
| 4 | Call signature mismatches | 3 call sites | Critical |
| 5 | Missing pagination | 3 list methods | High |
| 6 | Internal method mismatches | 1 (drift.py) | High |
| 7 | Registry bypass calls | 7 call sites | Medium |
| 8 | Missing firmware SDK call | 1 (firmware.py) | Medium |
| 9 | API docs cross-reference | 7 confirmations + 7 new findings | Informational |
| **Total** | | **24 issues + 7 refinements** | |
