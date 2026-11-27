# Contract: Migration Bundle Schema 1.1

The export writes this JSON file to the `data/` directory. The file name starts with `OrgConfig_Export_` and ends with `.json`. Menu 187 reads the file. This contract defines the file shape for schema 1.1. The name pattern and the encoding stay unchanged. The file uses UTF-8 and two-space indentation.

## Top-level shape

| Key | Type | Constraint |
| --- | --- | --- |
| `metadata` | object | Required. Holds the fields in the metadata table below. |
| `networks` | array | Required. Holds the verified network objects. Empty when the organization holds none. |
| `services` | array | Required. Holds the verified service objects. |
| `vpns` | array | Required. Holds the verified VPN objects. |
| `gateway_templates` | array | Required. Holds the verified gateway template objects. |
| `device_profiles` | array | Required. Holds the verified gateway device profile objects. |
| `service_policies` | array | Required. Holds the verified service policy objects. |

## Metadata

| Key | Type | Constraint |
| --- | --- | --- |
| `source_org_id` | string | Required. The organization identifier. |
| `source_org_name` | string | Required. The verified organization name, or `Unknown` when the lookup is not verified. |
| `export_timestamp` | string | Required. UTC time in ISO 8601 form. |
| `schema_version` | string | Required. Exactly `1.1`. |
| `object_counts` | object | Required. Holds one integer for each of the six keys. |
| `fetch_status` | object | Required. Holds the string `verified` for each of the six keys. |

## Example

The example shows a verified bundle for an organization with one network. Each other list is empty.

```json
{
  "metadata": {
    "source_org_id": "00000000-0000-0000-0000-000000000001",
    "source_org_name": "Example Organization",
    "export_timestamp": "2026-11-26T15:00:00+00:00",
    "schema_version": "1.1",
    "object_counts": {
      "networks": 1,
      "services": 0,
      "vpns": 0,
      "gateway_templates": 0,
      "device_profiles": 0,
      "service_policies": 0
    },
    "fetch_status": {
      "networks": "verified",
      "services": "verified",
      "vpns": "verified",
      "gateway_templates": "verified",
      "device_profiles": "verified",
      "service_policies": "verified"
    }
  },
  "networks": [
    {
      "id": "00000000-0000-0000-0000-000000000002",
      "name": "Example Network",
      "subnet": "10.10.10.0/24"
    }
  ],
  "services": [],
  "vpns": [],
  "gateway_templates": [],
  "device_profiles": [],
  "service_policies": []
}
```

## Acceptance rules for import

The import accepts a file only when every rule holds:

1. The file parses as JSON.
2. `metadata` exists.
3. Each of the six keys exists at the top level.
4. `metadata.schema_version` equals `1.1`.
5. `metadata.fetch_status` is an object.
6. Each of the six keys in `metadata.fetch_status` equals `verified`.

A file that fails rule 4, 5, or 6 is rejected before the preview. A file that fails rule 2 or 3 uses the existing error text.

## Compatibility

- A file with schema `1.0` is rejected. It has no proof that each type was verified. The operator runs menu 58 again.
- The six keys, their order, and their item shape do not change.
