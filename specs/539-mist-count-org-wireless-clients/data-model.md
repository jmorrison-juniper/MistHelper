# Phase 1 Data Model: countOrgWirelessClients

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_clients_count.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing an aggregate count of wireless
clients for an organization over a time window, optionally grouped by a `distinct`
attribute. MistHelper splits this into two logical entities for clean multi-backend
persistence: a one-row envelope and zero-or-more bucket rows.

### Entity 1: `WirelessClientsCountEnvelope`

One row per (org, distinct attribute, time window). Captures the query echo plus the
total bucket count regardless of how many bucket rows landed in `results`.

| Field          | Type    | Source                | PK? | FK?                                              | Notes |
|----------------|---------|-----------------------|-----|--------------------------------------------------|-------|
| `org_id`       | TEXT    | MistHelper context    | YES | sites.org_id                                     | UUID supplied by user; injected before write. |
| `distinct`     | TEXT    | API `distinct`        | YES | --                                               | Echo of the grouping attribute requested (blank string when none). |
| `start`        | INTEGER | API `start`           | YES | --                                               | Inclusive epoch seconds; stable across re-runs of the same window. |
| `end`          | INTEGER | API `end`             | YES | --                                               | Exclusive epoch seconds; stable across re-runs of the same window. |
| `limit`        | INTEGER | API `limit`           | --  | --                                               | Max bucket rows the API was allowed to return. |
| `total`        | INTEGER | API `total`           | --  | --                                               | Total distinct buckets matched (may exceed `limit`). |
| `bucket_count` | INTEGER | len(API `results`)    | --  | --                                               | Convenience count of rows actually returned in this poll. |
| `polled_at_utc`| TEXT    | MistHelper clock      | --  | --                                               | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `WirelessClientsCountResult`

Zero or more rows per envelope, one per `count_result` object in the API `results`
array.

| Field          | Type    | Source                              | PK? | FK?                                                          | Notes |
|----------------|---------|-------------------------------------|-----|--------------------------------------------------------------|-------|
| `org_id`       | TEXT    | MistHelper context                  | YES | wireless_clients_count_envelope.org_id                       | UUID. |
| `distinct`     | TEXT    | Envelope `distinct`                 | YES | wireless_clients_count_envelope.distinct                     | Joins to envelope. |
| `start`        | INTEGER | Envelope `start`                    | YES | wireless_clients_count_envelope.start                        | Joins to envelope. |
| `end`          | INTEGER | Envelope `end`                      | YES | wireless_clients_count_envelope.end                          | Joins to envelope. |
| `bucket`       | TEXT    | API `results[].<distinct>`          | YES | --                                                           | Bucket label (e.g. SSID name when `distinct=ssid`). Empty string when `distinct` is blank. |
| `count`        | INTEGER | API `results[].count`               | --  | --                                                           | Required by schema; number of clients in this bucket. |
| `polled_at_utc`| TEXT    | MistHelper clock                    | --  | --                                                           | ISO8601 UTC timestamp of the poll, for audit. |

Note on `bucket`: the API does not name the bucket-value field uniformly across calls;
instead each `count_result` object has a required `count` plus `additionalProperties`
of type `string`. The actual property key matches the envelope's `distinct` value (e.g.,
when `distinct=ssid` each result looks like `{count: 17, ssid: "Corp-Guest"}`). The
flattener reads the envelope's `distinct` field, pops that key from each result, and
stores it under the fixed column name `bucket`.

## State Transitions

N/A -- this is a read-only endpoint. The underlying client population on the Mist side
changes constantly, but MistHelper does not drive or model those transitions; it merely
captures aggregated snapshots over the caller's chosen window. Each poll for the same
`(org_id, distinct, start, end)` overwrites the prior snapshot via SQLite `INSERT OR
REPLACE`.

## SQLite DDL

```sql
-- Envelope table: one row per (org, distinct attribute, time window).
CREATE TABLE IF NOT EXISTS org_wireless_clients_count_envelope (
    org_id          TEXT     NOT NULL,
    distinct        TEXT     NOT NULL,
    start           INTEGER  NOT NULL,
    end             INTEGER  NOT NULL,
    limit           INTEGER,
    total           INTEGER,
    bucket_count    INTEGER,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_wireless_clients_count_envelope_distinct
    ON org_wireless_clients_count_envelope (distinct);

-- Results table: zero-or-more rows per envelope, one per bucket.
CREATE TABLE IF NOT EXISTS org_wireless_clients_count_results (
    org_id          TEXT     NOT NULL,
    distinct        TEXT     NOT NULL,
    start           INTEGER  NOT NULL,
    end             INTEGER  NOT NULL,
    bucket          TEXT     NOT NULL,
    count           INTEGER,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, distinct, start, end, bucket),
    FOREIGN KEY (org_id, distinct, start, end)
        REFERENCES org_wireless_clients_count_envelope(org_id, distinct, start, end)
);

CREATE INDEX IF NOT EXISTS idx_wireless_clients_count_results_bucket
    ON org_wireless_clients_count_results (bucket);

CREATE INDEX IF NOT EXISTS idx_wireless_clients_count_results_count
    ON org_wireless_clients_count_results (count);
```

Note: `distinct`, `start`, `end`, `limit`, and `count` are reserved or near-reserved
SQL keywords. SQLite tolerates them as column identifiers without quoting in most
contexts, but DataExporter generates DDL with double-quoted identifiers
(`"distinct"`, `"start"`, `"end"`, `"limit"`, `"count"`) to guarantee portability.
The DDL above is shown unquoted for readability; the actual `CREATE TABLE` statement
emitted by DataExporter on first write uses quoted identifiers.

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper itself does not run the DDL
directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (two adjacent inserts in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Envelope row per (org, distinct attribute, time window).
    'countOrgWirelessClients': {                                                    # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['org_id', 'distinct', 'start', 'end'],                      # stable across re-runs of same query
        'indexes': ['distinct'],                                                    # fast filter by grouping attribute
        'table': 'org_wireless_clients_count_envelope',                             # target SQLite table for envelope rows
    },

    # Bucket rows produced from the API `results` array.
    'countOrgWirelessClientsResults': {                                             # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of envelope FK + bucket label
        'primary_key': ['org_id', 'distinct', 'start', 'end', 'bucket'],            # uniquely identifies one bucket snapshot
        'indexes': ['bucket', 'count'],                                             # fast lookup by label or magnitude
        'table': 'org_wireless_clients_count_results',                              # target SQLite table for bucket rows
    },
}
```

The `countOrgWirelessClientsResults` key is a MistHelper-internal identifier (the Mist
API has no operationId for it -- it is the flattened sub-array of the parent response).
This pattern matches how MistHelper already splits other endpoints whose response
contains nested arrays (see `getOrgLicenseAsyncClaimStatusDetails` in spec 500).
