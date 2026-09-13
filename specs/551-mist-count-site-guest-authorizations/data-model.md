# Phase 1 Data Model: countSiteGuestAuthorizations

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/sites/{site_id}/guests/count`

## Source response schema (200)

Per `documentation/api/sites/GET_sites_site_id_guests_count.md` the API returns a single
JSON object:

```jsonc
{
  "distinct": "wlan_id",                          // echoed distinct attribute
  "start":    1719600000,                         // window start epoch seconds
  "end":      1719686400,                         // window end epoch seconds
  "limit":    100,                                // bucket cap
  "total":    873,                                // total authorized guests in window
  "results": [
    { "count": 412, "wlan_id": "1c7d...-aaaa" },  // bucket: 412 guests on this WLAN
    { "count": 287, "wlan_id": "9f02...-bbbb" },  // bucket: 287 guests on this WLAN
    { "count": 174, "wlan_id": "<unknown>" }      // bucket: 174 guests with no WLAN id
  ]
}
```

`results[]` items follow the `count_result` schema: `count` is required and the second
key is the value of `distinct` (its name varies per call). All extra properties are
typed `string` by the OpenAPI schema.

## Entities

### Entity 1: `GuestCountBucket` (one row per `results[]` element)

| Field            | Type      | Required | Notes                                             |
|------------------|-----------|----------|---------------------------------------------------|
| `site_id`        | string    | Yes      | Foreign key to `Sites.id`; supplied at call time. |
| `distinct`       | string    | Yes      | Echoed from the API response (e.g. `wlan_id`).    |
| `bucket_value`   | string    | Yes      | Value of the distinct attribute for this bucket.  |
| `count`          | integer   | Yes      | Number of authorized guests in this bucket.       |
| `window_start`   | integer   | Yes      | Epoch seconds; from response `start`.             |
| `window_end`     | integer   | Yes      | Epoch seconds; from response `end`.               |
| `bucket_limit`   | integer   | Yes      | Response `limit` (default 100).                   |
| `is_summary`     | integer   | Yes      | `0` for buckets, `1` for the synthetic summary.   |
| `total`          | integer   | No       | Only populated when `is_summary = 1`.             |

**Primary key**: synthetic auto-increment `misthelper_internal_id` (per project
convention for aggregate endpoints).

**Foreign keys**: `site_id -> Sites.id` (logical FK; not enforced by SQLite for the
existing schema, but indexed).

**Unique constraint**: `(site_id, distinct, bucket_value, window_start, window_end)` to
prevent duplicate rows when the same query is re-run within the same window.

### Entity 2 (synthetic): summary row

The flatten step also emits **one** synthetic row per API call with `is_summary = 1`,
`bucket_value = "__summary__"`, and `total` populated. This makes the SQLite table
self-describing without a second table -- a NOC engineer can `SELECT * FROM
countSiteGuestAuthorizations WHERE is_summary = 1` to recover the window totals.

## State transitions

N/A -- read-only endpoint. Rows are upserted on re-run; no in-place mutation, no soft
delete, no lifecycle.

## SQLite DDL (created automatically by DataExporter on first run)

```sql
CREATE TABLE IF NOT EXISTS countSiteGuestAuthorizations (
    misthelper_internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id        TEXT    NOT NULL,
    distinct       TEXT    NOT NULL,
    bucket_value   TEXT    NOT NULL,
    count          INTEGER NOT NULL,
    window_start   INTEGER NOT NULL,
    window_end     INTEGER NOT NULL,
    bucket_limit   INTEGER NOT NULL,
    is_summary     INTEGER NOT NULL DEFAULT 0,
    total          INTEGER,
    inserted_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (site_id, distinct, bucket_value, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_csga_site
    ON countSiteGuestAuthorizations (site_id);

CREATE INDEX IF NOT EXISTS idx_csga_distinct
    ON countSiteGuestAuthorizations (distinct);

CREATE INDEX IF NOT EXISTS idx_csga_window
    ON countSiteGuestAuthorizations (window_start, window_end);
```

> Note: `distinct` is a SQLite reserved word in some contexts but is permitted as a
> column identifier when not used in a SELECT projection alias. The existing
> `countOrgGuestAuthorizations` table uses the same column name without issue.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry

Add the following entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in `MistHelper.py`
(alphabetical placement adjacent to `countOrgGuestAuthorizations` at line ~4400):

```python
"countSiteGuestAuthorizations": {                       # operationId verbatim
    "type": "auto_increment_with_unique",               # aggregate, no API UUID
    "primary_key": ["misthelper_internal_id"],          # synthetic surrogate key
    "indexes": ["site_id", "distinct",                  # common WHERE filters
                "window_start", "window_end"],
    "unique_constraints": [                             # de-dup on re-run
        ["site_id", "distinct", "bucket_value",
         "window_start", "window_end"],
    ],
    "description": "Site-level guest authorization count aggregates",
},
```

## Field-by-field source mapping (API response -> SQLite row)

| SQLite column     | Source                                                            |
|-------------------|-------------------------------------------------------------------|
| `site_id`         | `site_id` arg passed to `count_site_guest_authorizations()`       |
| `distinct`        | Response top-level `distinct`                                     |
| `bucket_value`    | For a bucket: `results[i][<distinct>]` (default `<unknown>` if absent). For summary row: literal `"__summary__"`. |
| `count`           | For a bucket: `results[i]["count"]`. For summary row: `0`.        |
| `window_start`    | Response top-level `start`                                        |
| `window_end`      | Response top-level `end`                                          |
| `bucket_limit`    | Response top-level `limit`                                        |
| `is_summary`      | `0` for buckets, `1` for the synthetic summary row                |
| `total`           | For summary row: response top-level `total`. For buckets: `NULL`. |
