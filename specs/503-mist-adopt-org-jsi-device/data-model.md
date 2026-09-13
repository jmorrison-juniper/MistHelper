# Phase 1 Data Model: adoptOrgJsiDevice

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-28

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_jsi_devices_outbound_ssh_cmd.md` (200 OK body).

## Entities

The endpoint returns a single JSON object with one required field. MistHelper persists
it as a single logical entity, augmented with the calling `org_id` (the API does not
echo the org in the body) and a MistHelper-side poll timestamp for audit.

### Entity 1: `JsiOutboundSshCmd`

One row per organization. Re-running the menu item upserts the existing row.

| Field           | Type    | Source              | PK? | FK?          | Notes |
|-----------------|---------|---------------------|-----|--------------|-------|
| `org_id`        | TEXT    | MistHelper context  | YES | sites.org_id | UUID supplied by the user; injected before write because the API does not include it in the body. |
| `cmd`           | TEXT    | API `cmd`           | --  | --           | Outbound SSH command string used to onboard JSI devices to this organization. Treated as sensitive: never logged at INFO or above, never echoed to stdout. |
| `cmd_length`    | INTEGER | len(API `cmd`)      | --  | --           | Convenience length of the command string for quick health checks without exposing the string itself. |
| `polled_at_utc` | TEXT    | MistHelper clock    | --  | --           | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying `cmd` string changes only when
Mist rotates an organization's adoption bootstrap (rare, operator-driven). MistHelper
captures snapshots; each poll overwrites the prior snapshot for the same `org_id` via
SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per organization. Re-poll upserts via INSERT OR REPLACE on org_id.
CREATE TABLE IF NOT EXISTS org_jsi_outbound_ssh_cmd (
    org_id          TEXT     NOT NULL,
    cmd             TEXT,
    cmd_length      INTEGER,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id)
);

CREATE INDEX IF NOT EXISTS idx_jsi_outbound_ssh_cmd_polled_at
    ON org_jsi_outbound_ssh_cmd (polled_at_utc);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per organization keyed by org_id; upsert on re-poll.
    'adoptOrgJsiDevice': {                                                          # operationId from OpenAPI
        'type': 'natural_pk',                                                       # PK is the stable business identifier
        'primary_key': ['org_id'],                                                  # injected by MistHelper before write
        'indexes': ['polled_at_utc'],                                               # fast lookup of recent polls
        'table': 'org_jsi_outbound_ssh_cmd',                                        # target SQLite table
    },
}
```

The operationId key `adoptOrgJsiDevice` matches the OpenAPI document and the
`api_function_name` argument the menu method passes to
`DataExporter.write_with_format_selection()`. No sub-table or split-entity entry is
required because the response body is a single flat object.
