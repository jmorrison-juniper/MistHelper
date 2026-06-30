# Phase 1 Data Model: getMspDetails

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from `documentation/api/msps/GET_msps_msp_id.md` (200 OK
body).

## Entities

The endpoint returns a single flat JSON object describing one Managed Service Provider
account. MistHelper persists it as one row in a single table -- no sub-arrays require
splitting.

### Entity 1: `MspDetails`

One row per MSP. Re-running the menu item against the same `msp_id` upserts the same
row.

| Field           | Type        | Source                | PK? | FK? | Notes |
|-----------------|-------------|-----------------------|-----|-----|-------|
| `id`            | TEXT (UUID) | API `id`              | YES | --  | MSP UUID assigned by Mist. Stable across calls. Natural primary key. |
| `name`          | TEXT        | API `name`            | --  | --  | Human-readable MSP display name. Mutable. |
| `tier`          | TEXT        | API `tier`            | --  | --  | Enum: `advanced`, `base`. Drives which optional fields are populated. |
| `allow_mist`    | INTEGER     | API `allow_mist`      | --  | --  | Boolean stored as 0/1 for SQLite compatibility. |
| `logo_url`      | TEXT        | API `logo_url`        | --  | --  | Advanced (uMSP) tier only; nullable. |
| `url`           | TEXT        | API `url`             | --  | --  | Advanced (uMSP) tier only; nullable. |
| `created_time`  | REAL        | API `created_time`    | --  | --  | Epoch seconds. Read-only on Mist side. |
| `modified_time` | REAL        | API `modified_time`   | --  | --  | Epoch seconds. Read-only on Mist side. |
| `polled_at_utc` | TEXT        | MistHelper clock      | --  | --  | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The MSP record on the Mist side mutates whenever
an admin edits it (name change, tier upgrade, logo upload, etc.), but MistHelper does
not drive or model those transitions; it merely captures snapshots. Each poll
overwrites the prior snapshot for the same `id` via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per MSP. Re-runs upsert by id.
CREATE TABLE IF NOT EXISTS msp_details (
    id              TEXT     NOT NULL,
    name            TEXT,
    tier            TEXT,
    allow_mist      INTEGER,
    logo_url        TEXT,
    url             TEXT,
    created_time    REAL,
    modified_time   REAL,
    polled_at_utc   TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_msp_details_tier
    ON msp_details (tier);

CREATE INDEX IF NOT EXISTS idx_msp_details_name
    ON msp_details (name);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL
directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (single insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per MSP, keyed by the API-supplied UUID.
    'getMspDetails': {                                                              # operationId from OpenAPI
        'type': 'natural_pk',                                                       # PK is the stable API UUID
        'primary_key': ['id'],                                                      # MSP UUID assigned by Mist
        'indexes': ['tier', 'name'],                                                # fast filter by tier / display name
        'table': 'msp_details',                                                     # target SQLite table
    },
}
```

No MistHelper-internal sub-table key is needed -- the response has no nested arrays
requiring a second table (contrast with endpoints that flatten an embedded `details[]`
array).
