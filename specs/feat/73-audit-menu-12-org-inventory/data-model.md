# Data Model: Audit Menu 12 - Organization Inventory Export

**Date**: 2026-04-08

## Entity: OrgInventory Device Record

Represents a single device in the Mist organization inventory. Returned by
`mistapi.api.v1.orgs.inventory.getOrgInventory`.

| Field | Type | Required | PK | Indexed | Description |
| - | - | - | - | - | - |
| id | str (UUID) | Yes | Yes | - | Device UUID from Mist API |
| mac | str | Yes | No | Yes | Device MAC address |
| serial | str | Yes | No | Yes | Device serial number |
| model | str | Yes | No | Yes | Device model (AP43, EX4400, SRX320) |
| type | str | Yes | No | Yes | Device type: ap, switch, gateway |
| site_id | str (UUID) | No | No | Yes | Assigned site UUID (null if unassigned) |
| org_id | str (UUID) | Yes | No | Yes | Organization UUID |
| name | str | No | No | No | Device hostname |
| sku | str | No | No | No | Product SKU |
| hw_rev | str | No | No | No | Hardware revision |
| created_time | int | No | No | No | Creation epoch timestamp |
| modified_time | int | No | No | No | Last modification epoch timestamp |
| magic | str | No | No | No | Claim code |

## Primary Key Strategy

```python
"getOrgInventory": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
    "unique_constraints": [],
    "description": "Organization device inventory with stable UUID identifiers",
}
```

## Upsert Semantics

- **Insert mode**: `INSERT OR REPLACE` keyed on `id`
- **Behavior on duplicate**: Entire row replaced (last-write-wins)
- **Idempotency guarantee**: Running the export N times with identical data produces
  exactly the same number of rows as running it once

## State Transitions

None. Device inventory records are stateless snapshots — each export overwrites
the previous state for a given device `id`.

## Relationships

- `org_id` → Organization (1:N — one org has many devices)
- `site_id` → Site (1:N — one site has many devices; nullable for unassigned)
- No foreign key enforcement in SQLite (flat export model)
