# Phase 1 Data Model: getMspOrg

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/msps/GET_msps_msp_id_orgs_org_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object representing one organization managed
by a Managed Service Provider (MSP). MistHelper persists this as a single row
in one logical entity -- there are no nested record arrays to split out.

### Entity 1: `MspOrg`

Exactly one row per (MSP-managed) org.

| Field              | Type     | Source              | PK? | FK?              | Notes |
|--------------------|----------|---------------------|-----|------------------|-------|
| `id`               | TEXT     | API `id`            | YES | --               | Org UUID. Server-issued; globally unique by Mist contract. |
| `msp_id`           | TEXT     | API `msp_id`        | --  | (logical) msps.id | Owning MSP UUID. Indexed for "list orgs for MSP" queries. |
| `name`             | TEXT     | API `name`          | --  | --               | Org display name. Required by API contract. Indexed for name search. |
| `msp_name`         | TEXT     | API `msp_name`      | --  | --               | Owning MSP display name. Read-only echo for convenience. |
| `msp_logo_url`     | TEXT     | API `msp_logo_url`  | --  | --               | MSP logo URL; nullable -- only present when MSP uploaded a logo. |
| `alarmtemplate_id` | TEXT     | API `alarmtemplate_id` | -- | (logical) alarmtemplates.id | Linked alarm template UUID; nullable. Indexed. |
| `allow_mist`       | INTEGER  | API `allow_mist`    | --  | --               | Boolean stored as 0/1. Default 1 (true) per API. |
| `orggroup_ids`     | TEXT     | API `orggroup_ids`  | --  | --               | UUID array flattened to `;`-joined TEXT per MistHelper convention. |
| `session_expiry`   | INTEGER  | API `session_expiry`| --  | --               | Web UI session expiry in minutes (10..20160, default 1440). |
| `created_time`     | REAL     | API `created_time`  | --  | --               | Epoch seconds when the org was created. Read-only. |
| `modified_time`    | REAL     | API `modified_time` | --  | --               | Epoch seconds when the org was last modified. Read-only. |
| `polled_at_utc`    | TEXT     | MistHelper clock    | --  | --               | ISO8601 UTC timestamp of this poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. MistHelper captures a snapshot per poll.
Each subsequent poll overwrites the prior row for the same `id` via SQLite
`INSERT OR REPLACE`. The underlying org on the Mist side may transition through
configuration changes driven by the MSP admin (alarm-template attach/detach,
session-expiry tuning, orggroup membership changes, MSP-managed
allow_mist toggling), but those transitions are observed -- not driven -- by
MistHelper.

## SQLite DDL

```sql
-- One row per MSP-managed org. Natural PK on the org UUID.
CREATE TABLE IF NOT EXISTS msp_org (
    id                  TEXT     NOT NULL,
    msp_id              TEXT,
    name                TEXT,
    msp_name            TEXT,
    msp_logo_url        TEXT,
    alarmtemplate_id    TEXT,
    allow_mist          INTEGER,
    orggroup_ids        TEXT,
    session_expiry      INTEGER,
    created_time        REAL,
    modified_time       REAL,
    polled_at_utc       TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_msp_org_msp_id
    ON msp_org (msp_id);

CREATE INDEX IF NOT EXISTS idx_msp_org_name
    ON msp_org (name);

CREATE INDEX IF NOT EXISTS idx_msp_org_alarmtemplate_id
    ON msp_org (alarmtemplate_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly inside the new menu
method.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Single MSP-managed org details, keyed on the org UUID returned by the API.
    'getMspOrg': {                                                                  # operationId from OpenAPI
        'type': 'natural_pk',                                                       # PK is a server-issued stable UUID
        'primary_key': ['id'],                                                      # globally unique by Mist contract
        'indexes': ['msp_id', 'name', 'alarmtemplate_id'],                          # support common analyst queries
        'table': 'msp_org',                                                         # target SQLite table for this op
    },
}
```

No MistHelper-internal sub-table is required because the response has no nested
record arrays. The `orggroup_ids` UUID list is flattened in-place to a `;`-
joined TEXT column on the same row, following the existing MistHelper
convention for short scalar-UUID arrays.
