# Data Model: Org Config Export/Import

**Feature**: specs/191-org-config-export-import
**Date**: 2026-05-14

## Entities

### ExportBundle

The top-level JSON file produced by Menu 176.

| Field | Type | Description |
| - | - | - |
| `metadata` | `BundleMetadata` | Export context and provenance |
| `networks` | `list[dict]` | Raw network objects from `listOrgNetworks` |
| `services` | `list[dict]` | Raw service objects from `listOrgServices` |
| `vpns` | `list[dict]` | Raw VPN objects from `listOrgVpns` |
| `gateway_templates` | `list[dict]` | Raw gateway template objects from `listOrgGatewayTemplates` |
| `device_profiles` | `list[dict]` | Raw device profile objects from `listOrgDeviceProfiles` (type=gateway) |
| `service_policies` | `list[dict]` | Raw service policy objects from `listOrgServicePolicies` |

### BundleMetadata

Provenance information embedded in each export bundle.

| Field | Type | Description |
| - | - | - |
| `source_org_id` | `str` | UUID of the source organization |
| `source_org_name` | `str` | Human-readable name of the source org |
| `export_timestamp` | `str` | ISO 8601 UTC timestamp of export |
| `misthelper_version` | `str` | MistHelper version that created the bundle |
| `object_counts` | `dict[str, int]` | Count per config type (e.g., `{"networks": 5, "services": 3, ...}`) |

### ConflictRecord

Represents a detected conflict that prevents an object from being imported.

| Field | Type | Description |
| - | - | - |
| `object_type` | `str` | Config type key (e.g., "networks") |
| `object_name` | `str` | Name of the conflicting object |
| `reason` | `str` | Conflict type: "name_match", "subnet_overlap", "address_overlap" |
| `detail` | `str` | Human-readable explanation of the conflict |
| `existing_id` | `str` | ID of the existing object in the destination org |

### ImportResult

Per-object result recorded during import for the final report.

| Field | Type | Description |
| - | - | - |
| `object_type` | `str` | Config type key |
| `object_name` | `str` | Name of the object |
| `status` | `str` | One of: "imported", "skipped", "failed" |
| `new_id` | `str or None` | Destination org ID (if imported) |
| `reason` | `str or None` | Skip/fail reason (if not imported) |

### IdRemapTable

Runtime mapping built during import to resolve cross-references.

| Field | Type | Description |
| - | - | - |
| Key | `str` | Source org object UUID |
| Value | `str` | Destination org object UUID (new or existing) |

Populated from:
- Successfully created objects: source `id` → API response `id`
- Skipped-by-name objects: source `id` → existing object `id` (matched by name)

## Relationships

```text
ExportBundle
  └── BundleMetadata (1:1)
  └── ConfigObjects per type (1:N)

ImportResult[] ← produced by import process
ConflictRecord[] ← produced by conflict detection
IdRemapTable ← populated during import, consumed by reference remapping
```

## Dependency Graph (Import Order)

```text
Tier 0 (no dependencies):
  ├── networks
  └── services

Tier 1 (depends on tier 0):
  ├── vpns          → references network IDs
  └── gateway_templates → references network IDs, VPN IDs

Tier 2 (depends on tier 0+1):
  ├── device_profiles    → references gateway_template_id
  └── service_policies   → references service IDs
```

## Validation Rules

| Entity | Rule | Error Behavior |
| - | - | - |
| ExportBundle | Must contain `metadata` key with `source_org_id` | Reject file with clear error |
| ExportBundle | Must contain all 6 type keys (empty arrays OK) | Reject file with clear error |
| BundleMetadata | `source_org_id` must be valid UUID format | Reject file |
| BundleMetadata | `misthelper_version` mismatch with current | Warning only, allow proceed |
| ConfigObject | `name` field required for conflict detection | Skip object with warning |
| Network subnet | Must be valid CIDR notation | Skip overlap check, log warning |
| Import file | Must be valid JSON | Reject with parse error details |

## Fields Stripped Before Import

These source-org-specific fields are removed from each object before the create API call:

```python
STRIP_FIELDS = {"id", "org_id", "created_time", "modified_time", "for_site"}
```
