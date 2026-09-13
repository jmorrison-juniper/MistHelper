# Phase 1 Data Model: GetOrgLicenseAsyncClaimStatus

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-28

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_claim_status.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing the most recent asynchronous device
claim job for an organization. MistHelper splits this into two logical entities for clean
multi-backend persistence.

### Entity 1: `ClaimStatusSummary`

One row per (org, scheduled claim job).

| Field            | Type     | Source              | PK? | FK?           | Notes |
|------------------|----------|---------------------|-----|---------------|-------|
| `org_id`         | TEXT     | MistHelper context  | YES | sites.org_id  | UUID supplied by user; injected before write. |
| `scheduled_at`   | INTEGER  | API `scheduled_at`  | YES | --            | Epoch seconds when the async job was scheduled. Stable identifier across polls. |
| `status`         | TEXT     | API `status`        | --  | --            | Enum: `prepared`, `ongoing`, `done`. |
| `total`          | INTEGER  | API `total`         | --  | --            | Total devices in claim. |
| `processed`      | INTEGER  | API `processed`     | --  | --            | Devices processed so far. |
| `succeed`        | INTEGER  | API `succeed`       | --  | --            | Devices successfully claimed. |
| `failed`         | INTEGER  | API `failed`        | --  | --            | Devices that failed. |
| `completed_count`| INTEGER  | len(API `completed`)| --  | --            | Convenience count of the `completed` MAC array. |
| `incompleted_count` | INTEGER | len(API `incompleted`) | -- | --       | Convenience count of the `incompleted` MAC array. |
| `timestamp`      | REAL     | API `timestamp`     | --  | --            | Epoch seconds when the response was generated. |
| `polled_at_utc`  | TEXT     | MistHelper clock    | --  | --            | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `ClaimStatusDetail`

Zero or more rows per (org, scheduled claim job). Only populated when the caller passes
`detail=True`. Source: each element of the API `details` array.

| Field           | Type    | Source            | PK? | FK?                                          | Notes |
|-----------------|---------|-------------------|-----|----------------------------------------------|-------|
| `org_id`        | TEXT    | MistHelper context | YES | claim_status_summary.org_id                | UUID. |
| `scheduled_at`  | INTEGER | API `scheduled_at`| YES | claim_status_summary.scheduled_at          | Joins to summary. |
| `mac`           | TEXT    | API details[].mac | YES | --                                          | Device MAC address. |
| `device_status` | TEXT    | API details[].status | -- | --                                         | Per-device status string. |
| `device_timestamp` | REAL | API details[].timestamp | -- | --                                       | Epoch seconds when this device's status was recorded. |
| `polled_at_utc` | TEXT    | MistHelper clock  | --  | --                                          | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying *job* on the Mist side transitions
through `prepared -> ongoing -> done`, but MistHelper does not drive or model those
transitions; it merely captures snapshots. Each poll overwrites the prior snapshot for
the same (org, scheduled_at) tuple via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (org, async claim job).
CREATE TABLE IF NOT EXISTS org_claim_status_summary (
    org_id              TEXT     NOT NULL,
    scheduled_at        INTEGER  NOT NULL,
    status              TEXT,
    total               INTEGER,
    processed           INTEGER,
    succeed             INTEGER,
    failed              INTEGER,
    completed_count     INTEGER,
    incompleted_count   INTEGER,
    timestamp           REAL,
    polled_at_utc       TEXT,
    PRIMARY KEY (org_id, scheduled_at)
);

CREATE INDEX IF NOT EXISTS idx_claim_status_summary_status
    ON org_claim_status_summary (status);

-- Detail table: zero-or-more rows per (org, async claim job, device MAC).
CREATE TABLE IF NOT EXISTS org_claim_status_details (
    org_id              TEXT     NOT NULL,
    scheduled_at        INTEGER  NOT NULL,
    mac                 TEXT     NOT NULL,
    device_status       TEXT,
    device_timestamp    REAL,
    polled_at_utc       TEXT,
    PRIMARY KEY (org_id, scheduled_at, mac),
    FOREIGN KEY (org_id, scheduled_at)
        REFERENCES org_claim_status_summary(org_id, scheduled_at)
);

CREATE INDEX IF NOT EXISTS idx_claim_status_details_mac
    ON org_claim_status_details (mac);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per async-claim job, keyed by (org, scheduled_at).
    'getOrgLicenseAsyncClaimStatus': {                                              # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['org_id', 'scheduled_at'],                                  # stable across polls of same job
        'indexes': ['status'],                                                      # fast filter by prepared/ongoing/done
        'table': 'org_claim_status_summary',                                        # target SQLite table for summary rows
    },

    # Per-device detail rows produced when detail=true.
    'getOrgLicenseAsyncClaimStatusDetails': {                                       # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of summary FK + device MAC
        'primary_key': ['org_id', 'scheduled_at', 'mac'],                           # uniquely identifies a device snapshot
        'indexes': ['mac'],                                                         # fast lookup by device MAC
        'table': 'org_claim_status_details',                                        # target SQLite table for detail rows
    },
}
```

The `getOrgLicenseAsyncClaimStatusDetails` key is a MistHelper-internal identifier (the
Mist API has no operationId for it -- it is a flattened sub-array of the parent
response). This pattern matches how MistHelper already splits other endpoints whose
response contains nested arrays.
