# Phase 1 Data Model: getOrgAssetFilter

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-29

## Entities

The endpoint returns exactly one entity: an **Asset Filter** object. The schema is
derived from
`documentation/api/orgs/GET_orgs_org_id_assetfilters_assetfilter_id.md`.

### Entity: `AssetFilter`

A Mist Asset Filter is a BLE / iBeacon / Eddystone matching rule scoped to an
organization (and optionally inherited by sites). It is configuration data, not
time-series telemetry.

| Field                      | Type                | Required | PK | Notes |
|----------------------------|---------------------|----------|----|-------|
| `id`                       | string (UUID)       | yes (readOnly) | **PK** | Globally unique within Mist. Stable across reads. |
| `org_id`                   | string (UUID)       | yes (readOnly) | FK -> org | Foreign key to the parent organization. Indexed. |
| `site_id`                  | string (UUID)       | no  (readOnly) | FK -> site | Optional foreign key when the filter is scoped to a site. May be NULL. |
| `name`                     | string              | **yes**  |    | Human-readable label (e.g. "Visitor Tags"). Indexed. |
| `disabled`                 | boolean             | no       |    | Defaults to false; true means the filter is inactive. |
| `for_site`                 | boolean (readOnly)  | no       |    | True when the filter is owned by a site rather than the org. |
| `ap_mac`                   | string              | no       |    | Optional BLE-advertising AP MAC filter. |
| `beam`                     | integer (int32)     | no       |    | Optional beam number. |
| `rssi`                     | integer (int32)     | no       |    | Optional RSSI threshold. |
| `mfg_company_id`           | integer (int32)     | no       |    | BLE manufacturing-specific company ID. |
| `service_uuid`             | string (UUID)       | no       |    | BLE service-data UUID used to filter assets. |
| `ibeacon_uuid`             | string (UUID, nullable) | no   |    | iBeacon UUID; may be NULL. |
| `ibeacon_major`            | integer (int32, nullable) | no |    | iBeacon major (1-65535); may be NULL. |
| `eddystone_uid_namespace`  | string              | no       |    | Eddystone UID namespace string. |
| `eddystone_url`            | string              | no       |    | Eddystone URL string. |
| `created_time`             | number (epoch, readOnly) | no  |    | Creation epoch seconds (Mist supplies sub-second precision). |
| `modified_time`            | number (epoch, readOnly) | no  |    | Last-modified epoch seconds. |

#### Field-type rules

- All UUIDs are stored as `TEXT` in SQLite (SQLite has no native UUID type).
- Booleans are stored as `INTEGER` 0/1 to match SQLite's actual storage class while
  remaining compatible with Python `bool`.
- Epoch times stay as `REAL` (number) -- they are Mist-side floats with sub-second
  precision.
- Nullable Mist fields (`ibeacon_uuid`, `ibeacon_major`, `site_id`) are nullable in
  SQLite as well.

#### Required field handling

The schema marks only `name` as required. Every other field may be absent from the API
response; the export code reads with `record.get(<field>)` defaulting to `None` so that
SQLite stores `NULL` for missing values rather than raising `KeyError`.

## State Transitions

**N/A -- read-only endpoint.** This GET retrieves an existing Asset Filter without
mutating any state on the Mist side. From MistHelper's perspective the only
"transition" is the SQLite row state, which moves through:

1. `(not present)` -- first run for a given `(id)` -- the row is INSERTed.
2. `(present)` -- subsequent runs for the same `(id)` -- the row is REPLACEd via
   `INSERT OR REPLACE` using the natural primary key.

There is no destructive transition; rows are never deleted by this menu item.

## SQLite DDL

The `DataExporter` creates the table on first run. The expected DDL emitted by the
exporter (using the registered PK strategy) is:

```sql
CREATE TABLE IF NOT EXISTS org_asset_filter (
    id                      TEXT PRIMARY KEY,
    org_id                  TEXT,
    site_id                 TEXT,
    name                    TEXT NOT NULL,
    disabled                INTEGER,
    for_site                INTEGER,
    ap_mac                  TEXT,
    beam                    INTEGER,
    rssi                    INTEGER,
    mfg_company_id          INTEGER,
    service_uuid            TEXT,
    ibeacon_uuid            TEXT,
    ibeacon_major           INTEGER,
    eddystone_uid_namespace TEXT,
    eddystone_url           TEXT,
    created_time            REAL,
    modified_time           REAL,
    misthelper_imported_at  REAL DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_org_asset_filter_org_id
    ON org_asset_filter (org_id);
CREATE INDEX IF NOT EXISTS idx_org_asset_filter_name
    ON org_asset_filter (name);
```

Upsert semantics: `INSERT OR REPLACE INTO org_asset_filter (...) VALUES (...)` so a
re-run with the same `id` overwrites the row in place without raising a uniqueness
error.

## ENDPOINT_PRIMARY_KEY_STRATEGIES entry

The following entry is added to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py`
(approximate line 1672 -- the exact line is confirmed at implementation time):

```python
'getOrgAssetFilter': {                                       # operationId from OpenAPI
    'type': 'natural_pk',                                    # id is a stable Mist UUID
    'primary_key': ['id'],                                   # globally unique within Mist
    'indexes': ['org_id', 'name'],                           # common lookup paths
    'table': 'org_asset_filter',                             # SQLite table name
    'description': 'Single Mist BLE asset filter retrieved by ID.',
},
```

This entry is the source of truth for both the SQLite DDL above and the upsert behavior
of `DataExporter.write_with_format_selection()` when called with
`api_function_name="getOrgAssetFilter"`.
