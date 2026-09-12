# Phase 1 Data Model: getOrgAsset

**Feature**: 599-mist-get-org-asset | **Date**: 2026-06-29

## Entity: Asset

The 200 response from `GET /api/v1/orgs/{org_id}/assets/{asset_id}` is a single `Asset`
JSON object (not a list). It is normalized to a one-row dataset before persistence.

### Fields

| Field           | Type    | Required | Description                                                  | Notes                                               |
|-----------------|---------|----------|--------------------------------------------------------------|-----------------------------------------------------|
| `id`            | string  | No\*     | UUID assigned by Mist when the asset is created              | `contentEncoding: uuid`, `readOnly`. Natural PK.    |
| `org_id`        | string  | No       | Owning organization UUID                                     | `contentEncoding: uuid`, `readOnly`. Foreign key.   |
| `site_id`       | string  | No       | Site the asset is bound to, when `for_site` is true          | `contentEncoding: uuid`, `readOnly`. Foreign key.   |
| `map_id`        | string  | No       | Floor map UUID the asset is placed on                        | `contentEncoding: uuid`. Foreign key.               |
| `tag_id`        | string  | No       | UUID of the BLE tag attached to the asset                    | `contentEncoding: uuid`. Foreign key.               |
| `name`          | string  | **Yes**  | Operator-visible label of the asset / device                 | Required by upstream schema.                        |
| `mac`           | string  | **Yes**  | BLE MAC address of the tag broadcasting the asset            | Required by upstream schema. Indexed for lookups.   |
| `for_site`      | boolean | No       | True when the asset is scoped to a single site               | `readOnly`.                                         |
| `created_time`  | number  | No       | Epoch seconds when the asset was first created               | `readOnly`. Used for audit only.                    |
| `modified_time` | number  | No       | Epoch seconds when the asset was last modified               | `readOnly`. Drives change-detection at higher level.|

\* `id` is marked `readOnly` and is always present on responses from a successful GET
against a known UUID; the OpenAPI schema technically lists only `mac` and `name` as
required for asset *create*. MistHelper treats `id` as the primary key on the persisted
row and rejects (with a `WARNING` log) any response payload missing `id`.

### Primary Key

- **Primary Key**: `id` (single column, natural UUID).
- **Strategy**: `natural_pk` per the `agents.md` Database Strategy section.

### Foreign Keys (logical, enforced only in ArangoDB graph backend)

| Local Column | References               | Notes                                           |
|--------------|--------------------------|-------------------------------------------------|
| `org_id`     | `list_org_sites.org_id`  | The owning organization.                        |
| `site_id`    | `list_org_sites.id`      | The bound site when `for_site` is true.         |
| `map_id`     | `list_site_maps.id`      | Floor map placement (per-site maps table).      |
| `tag_id`     | `(future asset-tag table)` | No current MistHelper table exists for tags.   |

CSV and SQLite backends store these as plain string columns; ArangoDB edges are created
by the same `DataExporter` codepath that already builds them for `listOrgAssets`.

### State Transitions

N/A -- this endpoint is a read-only GET. There are no state changes, no commands, and no
lifecycle hooks invoked by this menu item. State changes for an asset are observed only
indirectly: re-running the menu item returns the latest snapshot, and the
`modified_time` field reflects the upstream last-modified epoch.

## SQLite DDL

The table is created automatically by `DataExporter` on first run from the registered
primary key strategy. The equivalent explicit DDL is shown below for documentation
and migration auditing:

```sql
-- Created automatically by DataExporter.write_with_format_selection() when the
-- get_org_asset table does not yet exist. INSERT OR REPLACE semantics are used for
-- upserts on subsequent runs against the same asset_id.
CREATE TABLE IF NOT EXISTS get_org_asset (
    id            TEXT PRIMARY KEY,    -- Mist asset UUID, natural PK
    org_id        TEXT,                -- Owning organization UUID
    site_id       TEXT,                -- Bound site UUID (nullable when org-scoped)
    map_id        TEXT,                -- Floor map UUID (nullable)
    tag_id        TEXT,                -- BLE tag UUID (nullable)
    name          TEXT NOT NULL,       -- Operator-visible label
    mac           TEXT NOT NULL,       -- BLE MAC address
    for_site      INTEGER,             -- 0 / 1 boolean
    created_time  REAL,                -- Epoch seconds, upstream readOnly
    modified_time REAL                 -- Epoch seconds, upstream readOnly
);

CREATE INDEX IF NOT EXISTS idx_get_org_asset_org_id  ON get_org_asset(org_id);
CREATE INDEX IF NOT EXISTS idx_get_org_asset_name    ON get_org_asset(name);
CREATE INDEX IF NOT EXISTS idx_get_org_asset_mac     ON get_org_asset(mac);
CREATE INDEX IF NOT EXISTS idx_get_org_asset_site_id ON get_org_asset(site_id);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Insert the following entry inside the existing
`# -- Assets & Inventory --` block in `MistHelper.py` (immediately after the existing
`listOrgAssets` entry at line ~3998):

```python
"getOrgAsset": {                                       # Single-asset GET (menu 195)
    "type": "natural_pk",                              # Mist returns a stable UUID
    "primary_key": ["id"],                             # Asset UUID is the natural PK
    "indexes": ["org_id", "name", "mac", "site_id"],   # Same indexes as listOrgAssets
    "unique_constraints": [],                          # No secondary uniqueness rules
    "description": "Single organization BLE asset detail (singleton GET)",
},
```

Every line carries an inline comment per Principle VI (Inline Comments,
NON-NEGOTIABLE).
