# Phase 1 -- Data Model: countOrgDeviceLastConfigs

Entity model and SQLite schema for the response of
`GET /api/v1/orgs/{org_id}/devices/last_config/count`.

Source schema: `documentation/api/orgs/GET_orgs_org_id_devices_last_config_count.md`.

---

## Entities

### Entity 1: `CountEnvelope`

The outer object returned by the API. One envelope per (org_id, distinct,
time window) invocation.

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `org_id` | string (UUID) | Yes | client (path param) | Not in API response; added by handler. |
| `distinct` | string | Yes | API response | The field that was grouped on (e.g. `model`, `version`). |
| `start` | integer (epoch s) | Yes | API response | Window start as returned by the API. |
| `end` | integer (epoch s) | Yes | API response | Window end as returned by the API. |
| `limit` | integer | Yes | API response | Page size used. |
| `total` | integer | Yes | API response | Total number of distinct groups. |
| `results` | array of `CountResult` | Yes | API response | The per-group rows (see Entity 2). |
| `captured_at` | integer (epoch s) | Yes | client | UTC time the call was made; added by handler. |

**Primary key (for the envelope as a row)**: `misthelper_internal_id`
(auto-increment), with `UNIQUE(org_id, distinct, start, end)`.

**Foreign keys**: `org_id` -> `orgs.id` (logical reference; not enforced as
SQLite FK because `orgs` may not be locally cached).

---

### Entity 2: `CountResult`

A single grouped row inside `results[]`. Schema title in the OpenAPI doc is
`count_result`. The shape is `{count, <distinct_field_name>: <string>}` --
the second key is dynamic and matches the `distinct` query parameter.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `count` | integer | Yes | Number of config-history entries in this group. |
| `group_field` | string | Yes | Normalized to the static column `group_field`; equals the envelope's `distinct`. |
| `group_value` | string | Yes | The actual value (e.g. `AP43`, `0.14.29456`). Comes from `additionalProperties` in the schema. |

**Primary key (for a result row)**: `misthelper_internal_id` auto-increment;
unique tuple `UNIQUE(org_id, distinct, start, end, group_field,
group_value)`.

**Foreign keys**: `org_id` -> envelope; no enforced SQLite FK because the
envelope and result rows share a table for query simplicity.

---

## State Transitions

**N/A -- read-only endpoint.** No state machine. Each invocation produces an
immutable snapshot. Re-running with the same `(org_id, distinct, start,
end)` triggers `INSERT OR REPLACE` and overwrites the previous snapshot
rows.

---

## SQLite DDL

```sql
-- Table: count_org_device_last_configs
-- One row per group in results[]; envelope-level fields denormalized for
-- query simplicity. PK is auto-increment; uniqueness enforced on the
-- (org_id, distinct, start, end, group_field, group_value) tuple.

CREATE TABLE IF NOT EXISTS count_org_device_last_configs (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id        TEXT    NOT NULL,
    distinct_on   TEXT    NOT NULL,  -- 'distinct' is a SQL keyword
    start_epoch   INTEGER NOT NULL,
    end_epoch     INTEGER NOT NULL,
    limit_value   INTEGER NOT NULL,
    total         INTEGER NOT NULL,
    group_field   TEXT    NOT NULL,
    group_value   TEXT    NOT NULL,
    count         INTEGER NOT NULL,
    captured_at   INTEGER NOT NULL,
    UNIQUE (org_id, distinct_on, start_epoch, end_epoch, group_field, group_value)
);

CREATE INDEX IF NOT EXISTS idx_count_olc_org      ON count_org_device_last_configs(org_id);
CREATE INDEX IF NOT EXISTS idx_count_olc_distinct ON count_org_device_last_configs(distinct_on);
CREATE INDEX IF NOT EXISTS idx_count_olc_window   ON count_org_device_last_configs(start_epoch, end_epoch);
```

Notes:

- `distinct_on` chosen because `distinct` is a SQLite reserved word in many
  contexts; column name avoids quoting.
- `limit` renamed to `limit_value` for the same reason.
- All `INTEGER` epoch columns are seconds (matches API contentEncoding
  `int32`).

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

To be added to the dict near line ~1672 of `MistHelper.py`:

```python
'countOrgDeviceLastConfigs': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique_constraint': [
        'org_id',
        'distinct_on',
        'start_epoch',
        'end_epoch',
        'group_field',
        'group_value',
    ],
    'indexes': ['org_id', 'distinct_on'],
    'table_name': 'count_org_device_last_configs',
    'sdk_module': 'mistapi.api.v1.orgs.devices.last_config.count',
    'sdk_function': 'countOrgDeviceLastConfigs',
    'http_method': 'GET',
    'path': '/api/v1/orgs/{org_id}/devices/last_config/count',
    'tag': 'Orgs Devices',
    'menu_number': 195,
    'menu_category': 'Safe Org Exports',
    'is_destructive': False,
}
```

---

## Row Materialization (handler pseudocode)

```python
response = countOrgDeviceLastConfigs(  # SDK call -- see contracts/
    mist_session, org_id,
    distinct=distinct, type=type_filter, duration=duration,
    limit=MIST_PAGE_LIMIT,
)
payload = response.data  # dict with envelope fields + results[]
captured_at = int(time.time())  # UTC epoch when snapshot was taken
rows = [
    {
        'org_id':       org_id,
        'distinct_on':  payload['distinct'],
        'start_epoch':  payload['start'],
        'end_epoch':    payload['end'],
        'limit_value':  payload['limit'],
        'total':        payload['total'],
        'group_field':  payload['distinct'],
        'group_value':  result.get(payload['distinct'], ''),
        'count':        result['count'],
        'captured_at':  captured_at,
    }
    for result in payload.get('results', [])
]
DataExporter.write_with_format_selection(
    rows,
    filename_stem=f"countOrgDeviceLastConfigs_{org_id}",
    api_function_name='countOrgDeviceLastConfigs',
)
```
