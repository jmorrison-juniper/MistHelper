# Phase 1 Data Model: countSiteDeviceEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Endpoint**: `GET /api/v1/sites/{site_id}/devices/events/count`
**Source schema**: `documentation/api/sites/GET_sites_site_id_devices_events_count.md`

## Entities

The endpoint returns a single envelope object (here named `CountEnvelope`)
that wraps an array of bucket rows (`CountResult`). MistHelper flattens
this into one logical row per `CountResult`, copying envelope-level fields
onto every row so each persisted row is self-describing.

### Entity 1: `CountEnvelope` (transient -- never persisted on its own)

| Field      | Type            | Notes                                                        |
|------------|-----------------|--------------------------------------------------------------|
| `distinct` | string          | Distinct field chosen by the request (`model`, `type`, ...). |
| `start`    | integer (epoch) | Resolved window start. Server-computed if `duration` used.   |
| `end`      | integer (epoch) | Resolved window end.                                         |
| `limit`    | integer         | Maximum buckets returned (default 100).                      |
| `total`    | integer         | Total events across all buckets (sum of `results[].count`).  |
| `results`  | array           | Bucket rows (see `CountResult`).                             |

All five scalar envelope fields are marked `required` in the OpenAPI
schema, so the flattened row can rely on them being present.

### Entity 2: `CountResult` (one per bucket -- persisted row)

| Field    | Type    | Required | Notes                                                          |
|----------|---------|----------|----------------------------------------------------------------|
| `count`  | integer | yes      | Number of events in this bucket.                               |
| (open)   | string  | no       | Open `additionalProperties: string` carrying the distinct value (for example `model: "AP43"` or `type: "AP_RESTARTED"`). |

The open property name equals the `CountEnvelope.distinct` value. The
flattener writes it into two stable columns (`distinct_field`,
`distinct_value`) so the SQLite schema is fixed regardless of which
distinct field the user picked. The original key is also preserved as a
JSON blob in `raw_properties` for forensic auditing.

### Flattened MistHelper Row (`site_device_events_count`)

| Column                 | Type     | Source                                  |
|------------------------|----------|-----------------------------------------|
| `misthelper_internal_id` | INTEGER | Auto-increment surrogate key.           |
| `site_id`              | TEXT     | Path parameter from the request.        |
| `distinct_field`       | TEXT     | `CountEnvelope.distinct`.               |
| `distinct_value`       | TEXT     | The open additional property value.     |
| `count`                | INTEGER  | `CountResult.count`.                    |
| `window_start`         | INTEGER  | `CountEnvelope.start`.                  |
| `window_end`           | INTEGER  | `CountEnvelope.end`.                    |
| `window_limit`         | INTEGER  | `CountEnvelope.limit`.                  |
| `window_total`         | INTEGER  | `CountEnvelope.total`.                  |
| `filter_model`         | TEXT     | Echo of the `model` query param.        |
| `filter_type`          | TEXT     | Echo of the `type` query param.         |
| `filter_type_code`     | TEXT     | Echo of the `type_code` query param.    |
| `raw_properties`       | TEXT     | JSON dump of the original bucket object.|
| `retrieved_at`         | INTEGER  | Local epoch when MistHelper ran.        |

## State Transitions

N/A -- read-only endpoint. The flattened row is immutable once written.
Re-runs upsert based on the unique constraint defined below.

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS site_device_events_count (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id                TEXT    NOT NULL,
    distinct_field         TEXT    NOT NULL,
    distinct_value         TEXT,
    count                  INTEGER NOT NULL,
    window_start           INTEGER NOT NULL,
    window_end             INTEGER NOT NULL,
    window_limit           INTEGER NOT NULL,
    window_total           INTEGER NOT NULL,
    filter_model           TEXT,
    filter_type            TEXT,
    filter_type_code       TEXT,
    raw_properties         TEXT,
    retrieved_at           INTEGER NOT NULL,
    UNIQUE (
        site_id,
        distinct_field,
        distinct_value,
        window_start,
        window_end,
        filter_model,
        filter_type,
        filter_type_code
    )
);

CREATE INDEX IF NOT EXISTS idx_sdec_site
    ON site_device_events_count (site_id);
CREATE INDEX IF NOT EXISTS idx_sdec_field
    ON site_device_events_count (distinct_field, distinct_value);
CREATE INDEX IF NOT EXISTS idx_sdec_window
    ON site_device_events_count (window_start, window_end);
```

`INSERT OR REPLACE` against this unique constraint produces a clean
upsert when the same logical bucket is re-fetched with the same time
window and filters.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (the dictionary lives near line ~1672 per
`agents.md`):

```python
'countSiteDeviceEvents': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique_constraint': [
        'site_id',
        'distinct_field',
        'distinct_value',
        'window_start',
        'window_end',
        'filter_model',
        'filter_type',
        'filter_type_code',
    ],
    'indexes': [
        'site_id',
        'distinct_field',
        'window_start',
        'window_end',
    ],
    'table_name': 'site_device_events_count',
    'description': (
        'Aggregate count of site device-events history grouped by a '
        'caller-chosen distinct field. Auto-increment surrogate key; '
        'logical identity is (site_id + distinct_field + distinct_value '
        '+ time window + filter tuple).'
    ),
}
```

## Foreign-Key Relationships (logical, not enforced)

| Column         | References                          | Cardinality |
|----------------|-------------------------------------|-------------|
| `site_id`      | `sites.id` (from `listOrgSites`)    | many-to-one |
| `distinct_value` when `distinct_field='model'`     | `inventory.model` (from `listOrgInventory`) | many-to-one |
| `distinct_value` when `distinct_field='device_id'` | `devices.id` (from `listSiteDevices`)       | many-to-one |
| `distinct_value` when `distinct_field='type'`      | Mist constant `device_events` (`mist_get_constants`) | many-to-one |

SQLite does not enforce these (other tables may not exist in every run);
they are documented for ArangoDB graph-edge construction (per the
polyglot backend in spec 188).
