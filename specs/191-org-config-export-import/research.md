# Research: Org Config Export/Import

**Feature**: specs/191-org-config-export-import
**Date**: 2026-05-14

## R1: mistapi Create Endpoint Availability

**Task**: Verify all 6 create endpoints exist in mistapi 0.59+

**Finding**: All 6 endpoints confirmed via runtime inspection:

| Module | Create Function | Signature |
| - | - | - |
| `mistapi.api.v1.orgs.networks` | `createOrgNetwork` | `(apisession, org_id, body=dict)` |
| `mistapi.api.v1.orgs.services` | `createOrgService` | `(apisession, org_id, body=dict)` |
| `mistapi.api.v1.orgs.vpns` | `createOrgVpn` | `(apisession, org_id, body=dict)` |
| `mistapi.api.v1.orgs.gatewaytemplates` | `createOrgGatewayTemplate` | `(apisession, org_id, body=dict)` |
| `mistapi.api.v1.orgs.deviceprofiles` | `createOrgDeviceProfile` | `(apisession, org_id, body=dict)` |
| `mistapi.api.v1.orgs.servicepolicies` | `createOrgServicePolicy` | `(apisession, org_id, body=dict)` |

**Decision**: Use these endpoints directly. No HTTP fallback needed.
**Alternatives considered**: Direct REST calls — rejected because mistapi handles auth, pagination, and rate limiting.

## R2: Menu Number Assignment

**Task**: Find available menu numbers for export and import operations.

**Finding**: Menu 130 and 131 (originally specified) are taken:
- 130 = `DeviceUtilityCommands.show_bgp_summary`
- 131 = `DeviceUtilityCommands.show_arp_table`

Highest used: 175 (`CacheUtils.clear_cache`).

**Decision**: Use 176 (export) and 177 (import).
**Alternatives considered**: Using 200+ range — rejected for sequential consistency with existing numbering.

## R3: IP/Subnet Overlap Detection

**Task**: Find best approach for detecting overlapping IP subnets between import and existing config.

**Finding**: Python stdlib `ipaddress` module is already imported (line 37). It provides:
- `ip_network(addr, strict=False)` — parses CIDR notation, tolerates host bits
- `.overlaps(other)` — returns True if any addresses are shared
- Handles both IPv4 and IPv6

**Decision**: Use `ipaddress.ip_network().overlaps()` for networks and service addresses.
**Alternatives considered**: Manual CIDR math — rejected as error-prone and reinventing the wheel.

## R4: Cross-Reference ID Mapping

**Task**: Identify which fields in each object type contain foreign IDs that need remapping.

**Finding**: Based on Mist API object structures:

| Object Type | Foreign ID Fields | Dependency |
| - | - | - |
| Networks | None | Standalone |
| Services | None | Standalone |
| VPNs | Network IDs in `networks` dict entries | Networks |
| Gateway Templates | Network IDs, VPN IDs in config sections | Networks, VPNs |
| Device Profiles | `gateway_template_id` | Gateway Templates |
| Service Policies | Service IDs in `services[]` list | Services |

**Decision**: Remap top-level reference fields only. Nested config within gateway templates (port configs, routing) is out of scope for v1.
**Alternatives considered**: Deep recursive remapping — rejected due to complexity and risk of corrupting nested structures. Document as known limitation.

## R5: Fields to Strip

**Task**: Determine which source-org fields must be removed before creating in destination org.

**Finding**: Mist API returns these server-managed fields that would cause errors or confusion if sent in a create request:
- `id` — server-assigned UUID
- `org_id` — belongs to source org
- `created_time` — server timestamp
- `modified_time` — server timestamp
- `for_site` — org-level scope marker

**Decision**: Strip all 5 fields. Use a constant set for maintainability.
**Alternatives considered**: Allowlist approach (keep only known fields) — rejected because API schema evolves and an allowlist would break on new fields.

## R6: Existing PK Strategies

**Task**: Verify PK strategies exist for all 6 list endpoints.

**Finding**: All 6 already defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES`:
- `listOrgNetworks` — natural_pk, key: `["id"]`
- `listOrgServices` — natural_pk, key: `["id"]`
- `listOrgVpns` — natural_pk, key: `["id"]`
- `listOrgGatewayTemplates` — natural_pk, key: `["id"]`
- `listOrgDeviceProfiles` — natural_pk, key: `["id"]`
- `listOrgServicePolicies` — natural_pk, key: `["id"]`

**Decision**: No new PK strategies needed. Export/import uses JSON files, not the database backend.
