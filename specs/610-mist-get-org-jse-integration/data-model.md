# Phase 1 Data Model: getOrgJseIntegration

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_setting_jse_setup.md` (200 OK body,
schema title `account_jse_info`).

## Entities

The endpoint returns a single JSON object describing the Juniper Sky
Enterprise (JSE) integration currently bound to an organization.
MistHelper models this as one logical entity with one row per org.

### Entity 1: `OrgJseIntegrationSetup`

One row per (org). Re-running the menu item against the same `org_id`
upserts the existing row -- no historical snapshots are kept (see
research.md Task 2 for rationale).

| Field             | Type    | Source                    | PK? | FK?          | Notes |
|-------------------|---------|---------------------------|-----|--------------|-------|
| `org_id`          | TEXT    | MistHelper context        | YES | sites.org_id | UUID supplied by user; injected before write (Mist does not echo it in the body). |
| `cloud_name`      | TEXT    | API `cloud_name`          | --  | --           | JSE cloud the org is bound to, e.g. `devcentral.juniperclouds.net`. |
| `username`        | TEXT    | API `username`            | --  | --           | JSE account email, e.g. `john@abc.com`. |
| `org_names_joined`| TEXT    | "," join of API `org_names`| --  | --          | Comma-joined list of JSE org names visible to the user. Empty string when the array is absent or empty. |
| `org_names_count` | INTEGER | len(API `org_names`)      | --  | --           | Convenience count of the `org_names` array. `0` when absent. |
| `polled_at_utc`   | TEXT    | MistHelper clock          | --  | --           | ISO8601 UTC timestamp of the poll, for audit. Stamped by MistHelper at write time. |

The `org_names` array is collapsed into two flat columns
(`org_names_joined` and `org_names_count`) so that the table stays
single-row and CSV-friendly. Operators who need the raw array can re-run
the call against the JSON cache in ArangoDB (the polyglot backend stores
the unflattened body); the relational tables prefer flat rows.

## State Transitions

N/A -- this is a read-only endpoint. The JSE integration binding itself
transitions on the Mist side (configured -> unconfigured via the sibling
DELETE; unconfigured -> configured via the sibling POST), but
MistHelper's read-only menu item does not model or drive those
transitions. Each poll overwrites the prior row for the same `org_id` via
SQLite `INSERT OR REPLACE`. A 404 response from Mist is treated as "no
JSE integration is currently configured for this org" and produces zero
output rows (with a `WARNING` log line), not an error.

## SQLite DDL

```sql
-- Single-row-per-org table: current JSE integration setup for the org.
CREATE TABLE IF NOT EXISTS org_jse_integration_setup (
    org_id              TEXT     NOT NULL,
    cloud_name          TEXT,
    username            TEXT,
    org_names_joined    TEXT,
    org_names_count     INTEGER,
    polled_at_utc       TEXT,
    PRIMARY KEY (org_id)
);

CREATE INDEX IF NOT EXISTS idx_org_jse_integration_cloud_name
    ON org_jse_integration_setup (cloud_name);
```

`DataExporter.write_with_format_selection()` is responsible for emitting
the equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via
key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (a single
insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # JSE integration setup is a single-row-per-org snapshot. Re-polls
    # must upsert in place, not append.
    'getOrgJseIntegration': {                                                       # operationId from OpenAPI
        'type': 'natural_pk',                                                       # PK is a single natural business field
        'primary_key': ['org_id'],                                                  # one row per org -- upsert on re-poll
        'indexes': ['cloud_name'],                                                  # fast filter by bound JSE cloud
        'table': 'org_jse_integration_setup',                                       # target SQLite table
    },
}
```

The PK strategy entry mirrors the pattern used for other single-row-per-
org settings exports already in MistHelper. No MistHelper-internal
sub-table key is required because the response has no nested array that
would warrant a second flattened table.
