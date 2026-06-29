# Phase 1 Data Model: countSiteNacClients

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document specifies the entity model returned by
`GET /api/v1/sites/{site_id}/nac_clients/count`, the SQLite schema MistHelper will
create on first run, and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration entry.

---

## Entities returned by the endpoint

The endpoint returns a single JSON object with the following top-level structure (per
`documentation/api/sites/GET_sites_site_id_nac_clients_count.md`):

```json
{
  "distinct": "type",
  "start": 1719600000,
  "end":   1719686400,
  "limit": 100,
  "total": 1234,
  "results": [
    { "count": 800, "type": "wireless" },
    { "count": 434, "type": "wired" }
  ]
}
```

There are two logical entities. MistHelper flattens both into a single tabular shape
by copying the top-level summary metadata onto each `results` row -- one table is
sufficient and matches the way every other `*Count*` endpoint is persisted.

### Entity 1: CountSummary (top-level wrapper)

| Field      | Type    | Notes                                                              |
|------------|---------|--------------------------------------------------------------------|
| distinct   | string  | The grouping field chosen by the caller (e.g. `"type"`, `"vlan"`). |
| start      | int32   | Epoch seconds, inclusive lower bound of the count window.          |
| end        | int32   | Epoch seconds, exclusive upper bound of the count window.          |
| limit      | int32   | Max number of bucket rows returned (default 100).                  |
| total      | int32   | Sum of `count` across all returned buckets (after limit).          |

Not persisted as a separate row -- merged into each CountBucket row below.

### Entity 2: CountBucket (one per `results[*]`)

| Field            | Type    | Notes                                                       |
|------------------|---------|-------------------------------------------------------------|
| count            | int32   | Number of NAC clients in this bucket. REQUIRED by schema.   |
| distinct_value   | string  | The value of the `distinct` field for this bucket (dynamic).|

The `distinct_value` column carries whatever string the API put under the chosen
`distinct` key (e.g. `"wireless"` when `distinct="type"`, `"eap-tls"` when
`distinct="auth_type"`, `"100"` when `distinct="last_vlan_id"`). This collapses
the dynamic `additionalProperties` shape into a fixed column. The original
`distinct` field name itself is stored in the CountSummary-derived column so the
data is self-describing.

### MistHelper-added columns (provenance)

| Field          | Type    | Notes                                                  |
|----------------|---------|--------------------------------------------------------|
| site_id        | text    | The site UUID supplied by the caller; copied onto every row for FK linkage. |
| fetched_at     | text    | ISO-8601 UTC timestamp when the menu item was run; for audit. |

---

## Foreign keys

- `site_id` references `sites.id` (the `id` column in the existing `sites` SQLite
  table populated by the existing `listOrgSites` menu item). Not enforced as a
  `FOREIGN KEY` constraint -- MistHelper stays read-only on schema and lets each
  endpoint's table stand alone; the ArangoDB backend records the equivalent edge
  separately.

---

## State transitions

N/A -- this is a read-only endpoint. Re-running the menu item replaces the existing
row for the composite key `(site_id, distinct, distinct_value, end_epoch)` via the
upsert behavior described in
`coding-standards.instructions.md` ("INSERT OR REPLACE for composite_pk").

---

## SQLite DDL snippet

`DataExporter` creates this table on first run. The DDL below is the canonical shape;
MistHelper does not maintain explicit migrations because every `*Count*` table follows
the same pattern.

```sql
CREATE TABLE IF NOT EXISTS site_nac_clients_count (
    site_id         TEXT    NOT NULL,
    distinct        TEXT    NOT NULL,
    distinct_value  TEXT    NOT NULL,
    end_epoch       INTEGER NOT NULL,
    count           INTEGER NOT NULL,
    start_epoch     INTEGER,
    limit_value     INTEGER,
    total           INTEGER,
    fetched_at      TEXT,
    PRIMARY KEY (site_id, distinct, distinct_value, end_epoch)
);

CREATE INDEX IF NOT EXISTS idx_site_nac_clients_count_site
    ON site_nac_clients_count(site_id);

CREATE INDEX IF NOT EXISTS idx_site_nac_clients_count_distinct
    ON site_nac_clients_count(distinct);

CREATE INDEX IF NOT EXISTS idx_site_nac_clients_count_end
    ON site_nac_clients_count(end_epoch);
```

Notes:
- `end` is renamed to `end_epoch` and `start` to `start_epoch` because both are
  reserved-ish identifiers in SQL; `limit` is renamed to `limit_value` for the same
  reason. The original JSON keys are preserved on the CSV header and ArangoDB
  document fields.
- The composite primary key matches the strategy registered below.

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES dict entry

Add the following entry to `MistHelper.py` near the existing NAC entries (the dict
lives at approximately line 1672 of `MistHelper.py` per the Constitution's database
strategy section):

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES['countSiteNacClients'] = {
    # Composite PK: aggregated time-windowed data, no stable UUID returned.
    'type': 'composite_pk',
    'primary_key': ['site_id', 'distinct', 'distinct_value', 'end_epoch'],
    'indexes': ['site_id', 'distinct', 'end_epoch'],
}
```

Rationale recap (full justification in `research.md` Task 2):
- The endpoint is a histogram aggregation -- not a per-entity listing -- so no
  natural UUID exists.
- The four-column composite uniquely identifies one histogram bucket for one time
  window at one site, enabling `INSERT OR REPLACE` upserts on repeat runs without
  losing historical buckets.
- Indexes match the three most common query shapes:
  ranged-by-time, grouped-by-distinct-field, and per-site lookups.
