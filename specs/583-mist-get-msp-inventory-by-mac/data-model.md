# Phase 1 Data Model: getMspInventoryByMac

**Feature**: 583-mist-get-msp-inventory-by-mac
**Source response schema**: `documentation/api/msps/GET_msps_msp_id_inventory_device_mac.md`

---

## Entities

### Entity: `MspInventoryDevice`

Represents a single device record returned by
`GET /api/v1/msps/{msp_id}/inventory/{device_mac}`. The endpoint returns one object,
not a list -- so each successful call produces exactly one row of this entity.

| Field      | Type    | Source                                | Required | Notes                                                  |
|------------|---------|---------------------------------------|----------|--------------------------------------------------------|
| `msp_id`   | string  | path parameter (user-supplied)        | YES      | UUID. Synthesized into the row because the response body omits it. Part of composite PK. |
| `mac`      | string  | response body                         | YES      | Device hardware MAC, lowercase colon-separated. Part of composite PK. |
| `org_id`   | string  | response body                         | YES      | UUID. Indexed for cross-table joins to org-scoped tables. |
| `site_id`  | string  | response body                         | YES      | UUID. Indexed for joins to `sites` and per-site stats. |
| `model`    | string  | response body                         | YES      | Hardware model code (e.g. `AP43`, `EX2300-24P`).       |
| `serial`   | string  | response body                         | YES      | Manufacturer serial number; indexed for warranty lookups. |
| `type`     | string  | response body                         | YES      | Device class: `ap` / `switch` / `gateway`.             |
| `for_site` | boolean | response body                         | NO       | Read-only flag indicating whether the device is bound to a site (vs MSP-claimed but unassigned). Defaults to `0` when absent. |

### Primary Key

- **Composite**: `(msp_id, mac)`
- **Rationale**: See `research.md` Task 2. MSP scope is implicit context the response
  does not carry, so we synthesize it from the prompt to keep the row globally unique
  within a multi-MSP database file.

### Foreign Keys

These are logical foreign keys for the polyglot ArangoDB backend (SQLite does not
enforce FKs by default, but DataExporter uses these for graph edges):

- `org_id` -> `orgs.id` (org-level operations table)
- `site_id` -> `sites.id` (menu 1 / `listOrgSites` output)

### State Transitions

**N/A -- read-only endpoint.** No state machine. Each invocation upserts the current
snapshot; previous values are overwritten via `INSERT OR REPLACE`.

---

## SQLite DDL

The table is created automatically on first run by `DataExporter`, but the canonical
schema is:

```sql
CREATE TABLE IF NOT EXISTS msp_inventory_by_mac (
    msp_id   TEXT NOT NULL,        -- MSP scope synthesized from prompt; part of PK
    mac      TEXT NOT NULL,        -- Device MAC, lowercase colon-separated; part of PK
    org_id   TEXT NOT NULL,        -- Org that owns the device; indexed for joins
    site_id  TEXT NOT NULL,        -- Site the device is bound to (or "" if for_site=0)
    model    TEXT NOT NULL,        -- Hardware model (AP43 / EX2300 / SRX320 / etc.)
    serial   TEXT NOT NULL,        -- Manufacturer serial number; indexed for RMA lookups
    type     TEXT NOT NULL,        -- ap | switch | gateway
    for_site INTEGER NOT NULL DEFAULT 0,  -- 0 = MSP-claimed only, 1 = assigned to a site
    PRIMARY KEY (msp_id, mac)
);

CREATE INDEX IF NOT EXISTS idx_msp_inv_by_mac_org_id
    ON msp_inventory_by_mac (org_id);
CREATE INDEX IF NOT EXISTS idx_msp_inv_by_mac_site_id
    ON msp_inventory_by_mac (site_id);
CREATE INDEX IF NOT EXISTS idx_msp_inv_by_mac_model
    ON msp_inventory_by_mac (model);
CREATE INDEX IF NOT EXISTS idx_msp_inv_by_mac_serial
    ON msp_inventory_by_mac (serial);
CREATE INDEX IF NOT EXISTS idx_msp_inv_by_mac_type
    ON msp_inventory_by_mac (type);
```

---

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

Add to the dictionary at approximately line 1672 of `MistHelper.py`:

```python
'getMspInventoryByMac': {                       # MSP single-MAC inventory lookup
    'type': 'composite_pk',                     # Two-field natural composite key
    'primary_key': ['msp_id', 'mac'],           # MSP scope + device MAC = global uniqueness
    'indexes': [                                # Secondary indexes for follow-up queries
        'org_id',                               # Common pivot: which org owns this device?
        'site_id',                              # Common pivot: which site is it bound to?
        'model',                                # Inventory rollup by hardware model
        'serial',                               # RMA / warranty lookup support
        'type',                                 # Filter by ap / switch / gateway
    ],
},
```

---

## Row Construction (Flatten Logic)

Pseudocode for converting the SDK response to a row:

```python
row = {                                                # Build one CSV/SQLite row
    'msp_id':   msp_id,                                # From the prompt, NOT the response
    'mac':      response_data.get('mac', '').lower(),  # Normalize echo to lowercase
    'org_id':   response_data.get('org_id', ''),       # Required by schema
    'site_id':  response_data.get('site_id', ''),      # Required by schema
    'model':    response_data.get('model', ''),        # Required by schema
    'serial':   response_data.get('serial', ''),       # Required by schema
    'type':     response_data.get('type', ''),         # Required by schema
    'for_site': int(bool(response_data.get('for_site', False))),  # Optional boolean -> 0/1
}
```

No nested arrays or sub-objects to flatten -- the response is a flat dict.
