# Phase 1 Data Model: getOrgUiSetting

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-07-01

Source: `documentation/api/orgs/GET_orgs_org_id_uisettings_uisetting_id.md` (200
response schema).

## Entities

The single 200 response object decomposes into two logical entities: the databoard
itself (one row) and each of its tiles (zero or more rows). MistHelper materializes
both as separate SQLite tables joined by `uisetting_id`.

### Entity 1: `org_ui_setting` (databoard summary)

| Field              | Type      | Notes                                            |
|--------------------|-----------|--------------------------------------------------|
| `id`               | TEXT UUID | **Primary key**. Databoard UUID from Mist.       |
| `org_id`           | TEXT UUID | Foreign key -> `org.id` (implicit). Indexed.     |
| `site_id`          | TEXT UUID | Nullable. Foreign key -> `sites.id` when set.    |
| `name`             | TEXT      | Databoard display name.                          |
| `description`      | TEXT      | Free text.                                       |
| `purpose`          | TEXT      | Enum. Currently only `marvisdashboard`.          |
| `for_site`         | INTEGER   | 0/1 boolean. Read-only flag from Mist.           |
| `isCustomDataboard`| INTEGER   | 0/1 boolean. User-created vs. Mist-shipped.      |
| `created_time`     | REAL      | Epoch seconds. Read-only.                        |
| `modified_time`    | REAL      | Epoch seconds. Read-only.                        |

**Primary key**: `id` (natural UUID). No composite required.
**Foreign keys (implicit, cross-table joins only)**: `org_id` -> org table,
`site_id` -> sites table.
**State transitions**: N/A -- read-only endpoint. The row is upserted on every fetch,
overwriting any prior copy with the newest field values.

### Entity 2: `org_ui_setting_tiles` (per-tile detail)

| Field           | Type      | Notes                                              |
|-----------------|-----------|----------------------------------------------------|
| `id`            | TEXT UUID | **Primary key**. Tile UUID from Mist.              |
| `uisetting_id`  | TEXT UUID | Foreign key -> `org_ui_setting.id`. Indexed.       |
| `name`          | TEXT      | Tile display name.                                 |
| `description`   | TEXT      | Free text.                                         |
| `nl_query`      | TEXT      | Natural-language query text used to render tile.   |
| `isAutoTitle`   | INTEGER   | 0/1 boolean.                                       |
| `position_col`  | INTEGER   | Grid column (int32).                               |
| `position_row`  | INTEGER   | Grid row (int32).                                  |
| `position_colSpan` | INTEGER| Column span (int32).                               |
| `position_rowSpan` | INTEGER| Row span (int32).                                  |

**Primary key**: `id` (natural UUID).
**Foreign keys (implicit)**: `uisetting_id` -> `org_ui_setting.id` (same fetch).
**State transitions**: N/A -- read-only endpoint. On each fetch the flattener writes
one row per tile currently returned; stale tiles that the API no longer returns are
NOT auto-deleted (MistHelper's `INSERT OR REPLACE` semantics only cover keys currently
seen -- follow-up cleanup is a separate concern documented for the tasks phase).

## SQLite DDL

`DataExporter` creates these tables on first write. The DDL below is illustrative --
it documents the schema the exporter will produce; MistHelper does not ship raw DDL
files. Column types follow SQLite's dynamic-typing conventions and mirror the choices
made for adjacent tables (booleans as INTEGER, epoch times as REAL).

```sql
CREATE TABLE IF NOT EXISTS org_ui_setting (
    id                 TEXT PRIMARY KEY,
    org_id             TEXT NOT NULL,
    site_id            TEXT,
    name               TEXT,
    description        TEXT,
    purpose            TEXT,
    for_site           INTEGER,
    isCustomDataboard  INTEGER,
    created_time       REAL,
    modified_time      REAL
);
CREATE INDEX IF NOT EXISTS idx_org_ui_setting_org_id
    ON org_ui_setting(org_id);

CREATE TABLE IF NOT EXISTS org_ui_setting_tiles (
    id                 TEXT PRIMARY KEY,
    uisetting_id       TEXT NOT NULL,
    name               TEXT,
    description        TEXT,
    nl_query           TEXT,
    isAutoTitle        INTEGER,
    position_col       INTEGER,
    position_row       INTEGER,
    position_colSpan   INTEGER,
    position_rowSpan   INTEGER
);
CREATE INDEX IF NOT EXISTS idx_org_ui_setting_tiles_uisetting_id
    ON org_ui_setting_tiles(uisetting_id);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Two entries -- one per output table. The dictionary key discriminates on
`(operation_id, table_suffix)` so a single operation can register multiple table
strategies (pattern already used elsewhere in MistHelper).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES.update({
    "getOrgUiSetting": {
        # Databoard summary row -- one row per fetch. Natural UUID PK.
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id"],
        "table": "org_ui_setting",
    },
    "getOrgUiSetting__tiles": {
        # Per-tile detail rows -- N rows per fetch. Natural UUID PK; FK to summary.
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["uisetting_id"],
        "table": "org_ui_setting_tiles",
    },
})
```

The flattener in `export_org_ui_setting()` uses the `__tiles` suffix in the
`api_function_name` argument when writing the tile rows, letting `DataExporter` pick
the right strategy without a second SDK operation ID.

## Notes on Cross-Backend Consistency

- **CSV**: Two files, one per table, both under `data/` with the
  `org_ui_setting_<orgshort>_<uishort>.csv` / `..._tiles.csv` pattern.
- **SQLite**: Two tables, both upserted with `INSERT OR REPLACE` by `id`.
- **ArangoDB + Redis (polyglot)**: Two document collections mirroring the tables. A
  `has_tile` edge is materialized from `org_ui_setting` -> `org_ui_setting_tiles` when
  the graph backend is active. Redis caches the summary row keyed by
  `mist:uisetting:<id>` for read-through use by future menu items.
