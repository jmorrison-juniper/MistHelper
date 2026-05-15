# Export Bundle JSON Schema

**Feature**: specs/191-org-config-export-import

## File Naming Convention

```text
data/OrgConfig_Export_{org_name}_{YYYYMMDD_HHMMSS}.json
```

Example: `data/OrgConfig_Export_Acme-Corp_20260514_183045.json`

## Top-Level Structure

```json
{
  "metadata": {
    "source_org_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_org_name": "Acme Corp Staging",
    "export_timestamp": "2026-05-14T18:30:45Z",
    "misthelper_version": "26.05.14.18.30",
    "object_counts": {
      "networks": 5,
      "services": 3,
      "vpns": 2,
      "gateway_templates": 4,
      "device_profiles": 2,
      "service_policies": 6
    }
  },
  "networks": [ ... ],
  "services": [ ... ],
  "vpns": [ ... ],
  "gateway_templates": [ ... ],
  "device_profiles": [ ... ],
  "service_policies": [ ... ]
}
```

## Required Fields

| Field | Type | Required | Description |
| - | - | - | - |
| `metadata` | object | YES | Export provenance |
| `metadata.source_org_id` | string (UUID) | YES | Source org identifier |
| `metadata.source_org_name` | string | YES | Source org display name |
| `metadata.export_timestamp` | string (ISO 8601) | YES | When the export was created |
| `metadata.misthelper_version` | string | YES | MistHelper version |
| `metadata.object_counts` | object | YES | Per-type counts |
| `networks` | array | YES | May be empty `[]` |
| `services` | array | YES | May be empty `[]` |
| `vpns` | array | YES | May be empty `[]` |
| `gateway_templates` | array | YES | May be empty `[]` |
| `device_profiles` | array | YES | May be empty `[]` |
| `service_policies` | array | YES | May be empty `[]` |

## Validation Rules

1. File must be valid JSON
2. `metadata` key must exist with `source_org_id` present
3. All 6 type keys must exist (empty arrays are valid)
4. `source_org_id` must be a valid UUID format
5. Version mismatch between `misthelper_version` and current version triggers a warning (not an error)

## Object Contents

Each array contains the raw API response objects from the corresponding `listOrg*` endpoint. Objects retain all API fields including `id`, `org_id`, `created_time`, `modified_time` — these are stripped at import time, not at export time. This preserves the full snapshot for audit purposes.

## Import Behavior

The import process:
1. Validates file structure against this schema
2. Strips `id`, `org_id`, `created_time`, `modified_time`, `for_site` from each object
3. Processes types in dependency order: networks/services → VPNs/gateway_templates → device_profiles/service_policies
4. Detects conflicts by name match and IP/subnet overlap
5. Remaps cross-reference IDs to destination org IDs
6. Creates non-conflicting objects via `createOrg*` endpoints
