# Phase 1 Data Model: countOrgAlarms

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)
**Endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_alarms_count.md`

## Entity inventory

The endpoint returns one envelope object containing zero or more bucket rows.
The MistHelper data model splits these into two entities to keep table schemas
clean and to allow correct composite-key UPSERT on re-run.

### Entity 1: `org_alarms_count_summary` (envelope)

One row per (org_id, distinct, start, end, duration, limit) invocation.

| Field        | Type              | Source                       | Notes                              |
|--------------|-------------------|------------------------------|------------------------------------|
| `org_id`     | TEXT (UUID)       | path param (user input)      | Primary key component              |
| `distinct`   | TEXT              | response `.distinct`         | Primary key component; empty allowed |
| `start`      | INTEGER (epoch s) | response `.start`            | Primary key component              |
| `end`        | INTEGER (epoch s) | response `.end`              | Primary key component              |
| `duration`   | TEXT              | query param (user input)     | Echoed back for traceability       |
| `limit`      | INTEGER           | response `.limit`            | Bucket cap actually applied        |
| `total`      | INTEGER           | response `.total`            | Sum of all bucket counts           |
| `bucket_count` | INTEGER         | `len(response.results)`      | Convenience -- number of rows in details table |
| `retrieved_at` | TEXT (ISO 8601) | client clock at write time   | Audit column added by DataExporter |

Primary key: `(org_id, distinct, start, end)`
Foreign keys: `org_id` references the org used to authenticate (no FK
constraint enforced -- there is no `org` table in the SQLite backend).

### Entity 2: `org_alarms_count_buckets` (count_result array element)

One row per bucket value in `response.results`. The bucket's distinct-attribute
value is stored as a single dynamic column whose name reflects the grouping
chosen by the user (e.g. `type`, `severity`, `hostname`). To keep the table
schema stable across different `distinct` invocations, the dynamic key/value
pair is normalized into two columns: `bucket_key` (the distinct attribute
name, mirrors `summary.distinct`) and `bucket_value` (the attribute value).

| Field          | Type              | Source                          | Notes                            |
|----------------|-------------------|---------------------------------|----------------------------------|
| `org_id`       | TEXT (UUID)       | path param (user input)         | Primary key + FK to summary      |
| `distinct`     | TEXT              | response `.distinct`            | Primary key + FK to summary      |
| `start`        | INTEGER (epoch s) | response `.start`               | Primary key + FK to summary      |
| `end`          | INTEGER (epoch s) | response `.end`                 | Primary key + FK to summary      |
| `bucket_key`   | TEXT              | duplicates `.distinct` for join | Same value on every row of this run |
| `bucket_value` | TEXT              | first non-`count` key in result | The distinct attribute's actual value |
| `count`        | INTEGER           | result `.count`                 | Required by schema               |
| `retrieved_at` | TEXT (ISO 8601)   | client clock at write time      | Audit column added by DataExporter |

Primary key: `(org_id, distinct, start, end, bucket_value)`
Foreign key: `(org_id, distinct, start, end)` -> `org_alarms_count_summary`
(not enforced as a SQLite `FOREIGN KEY` -- expressed as a documentation-level
contract for the ArangoDB graph edges to consume).

## State transitions

**N/A -- read-only endpoint.** Each menu invocation is a stateless GET. Rows
are upserted (`INSERT OR REPLACE`) by their composite primary key so a re-run
of the same window/grouping does not produce duplicates.

## SQLite DDL

```sql
-- Envelope: one row per (org, distinct, window) invocation.
CREATE TABLE IF NOT EXISTS org_alarms_count_summary (
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL DEFAULT '',
    start         INTEGER NOT NULL,
    end           INTEGER NOT NULL,
    duration      TEXT,
    limit         INTEGER,
    total         INTEGER,
    bucket_count  INTEGER,
    retrieved_at  TEXT,
    PRIMARY KEY (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_org_alarms_count_summary_org
    ON org_alarms_count_summary (org_id);
CREATE INDEX IF NOT EXISTS idx_org_alarms_count_summary_window
    ON org_alarms_count_summary (start, end);

-- Buckets: one row per distinct-attribute value in the envelope's results.
CREATE TABLE IF NOT EXISTS org_alarms_count_buckets (
    org_id        TEXT    NOT NULL,
    distinct      TEXT    NOT NULL DEFAULT '',
    start         INTEGER NOT NULL,
    end           INTEGER NOT NULL,
    bucket_key    TEXT    NOT NULL,
    bucket_value  TEXT    NOT NULL DEFAULT '',
    count         INTEGER NOT NULL,
    retrieved_at  TEXT,
    PRIMARY KEY (org_id, distinct, start, end, bucket_value)
);

CREATE INDEX IF NOT EXISTS idx_org_alarms_count_buckets_org
    ON org_alarms_count_buckets (org_id);
CREATE INDEX IF NOT EXISTS idx_org_alarms_count_buckets_key_value
    ON org_alarms_count_buckets (bucket_key, bucket_value);
```

Notes on DDL:

- SQLite treats `distinct` and `limit` as ordinary identifiers (they are not
  reserved keywords in SQLite); quoting is not required, but the table
  initializer in `DataExporter` already wraps column names in double quotes
  defensively, so no behavior change is needed.
- `IF NOT EXISTS` is used so first-run table creation is idempotent.
- Both tables include `retrieved_at` so the user can correlate envelope rows
  with bucket rows from the same physical API call when multiple windows are
  pulled close together.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry

Append the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (currently anchored around line ~1672). Two logical entries
are required because the endpoint maps to two output tables; the dispatcher
chooses the right strategy based on the `api_function_name` plus the
DataExporter's `table_suffix` argument.

```python
'countOrgAlarms_summary': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'distinct', 'start', 'end'],
    'indexes': ['org_id', 'start', 'end'],
    'table_name': 'org_alarms_count_summary',
},
'countOrgAlarms_buckets': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'distinct', 'start', 'end', 'bucket_value'],
    'indexes': ['org_id', 'bucket_key', 'bucket_value'],
    'table_name': 'org_alarms_count_buckets',
},
```

If the existing dispatcher accepts only a single key per `api_function_name`,
the implementer registers `countOrgAlarms` -> `composite_pk` on
`(org_id, distinct, start, end, bucket_value)` and writes the envelope as a
single bucket-shaped row with `bucket_value=''`. The two-entry form above is
preferred for query clarity but the single-entry fallback is allowed and noted
here so task generation has a clean decision path.

## Validation rules

| Rule                                                                 | Enforced by                                |
|----------------------------------------------------------------------|--------------------------------------------|
| `org_id` matches UUID regex before SDK call                          | New method; logs WARNING and returns early |
| `limit` coerced to int with fallback to 100                          | New method; `try/except ValueError`        |
| `duration` empty -> default `"1d"`                                   | New method; before SDK call                |
| `distinct` empty -> sent as `None` (omits the query param)           | New method; before SDK call                |
| `count` field present on every bucket row                            | Endpoint schema (required by Mist)         |
| Composite PK upsert on re-run produces zero duplicate rows           | SQLite `INSERT OR REPLACE` in DataExporter |
