# Phase 1 Data Model: getOrgMarvisClientInvite

**Feature**: 613-mist-get-org-marvis-client-invite
**Date**: 2026-06-30
**Source schema**:
`documentation/api/orgs/GET_orgs_org_id_marvisinvites_marvisinvite_id.md`

## Entity: MarvisClientInvite

Represents a single Marvis Client Invite owned by a Mist organization. Marvis
client invites carry the provisioning URL embedded in the MDM install command
that bootstraps the Marvis mobile SDK on a managed device.

### Fields

| Field          | Type    | Required | Source     | Notes                                                                                  |
|----------------|---------|----------|------------|----------------------------------------------------------------------------------------|
| `id`           | string  | Yes      | API body   | Mist UUID. `readOnly`. Primary key.                                                    |
| `name`         | string  | Yes      | API body   | Human-readable label (e.g. `"Handhelds"`). Secondary index.                            |
| `disabled`     | boolean | No       | API body   | Defaults to `false`. Indicates whether the invite is currently usable.                 |
| `provision_url`| string  | No       | API body   | `readOnly`. Provisioning URL passed as `--provision_url` to the MDM install command.   |
| `org_id`       | string  | Yes      | Path param | Parent organization UUID. Stored alongside the row so SQLite joins back to org tables. |

### Primary Key

- **Type**: `natural_pk`
- **Column(s)**: `id`
- **Rationale**: The API guarantees `id` is a stable, globally unique UUID
  (`readOnly` in the schema). `INSERT OR REPLACE` on `id` gives correct
  upsert behavior on repeated runs of the menu item.

### Foreign Keys

- `org_id` references the conceptual `orgs.id` parent (no formal FK
  constraint -- MistHelper SQLite tables are intentionally loosely related
  to allow partial scope extracts).

### State Transitions

N/A -- read-only endpoint. The row reflects the most recent GET response;
no client-side state machine is maintained.

## SQLite DDL

`DataExporter` creates this table automatically on first run using the
registered primary-key strategy. The effective DDL is:

```sql
CREATE TABLE IF NOT EXISTS org_marvis_client_invite (
    id            TEXT PRIMARY KEY,                  -- Mist invite UUID
    name          TEXT,                              -- Human-readable label
    disabled      INTEGER,                           -- 0 = enabled, 1 = disabled (SQLite bool)
    provision_url TEXT,                              -- MDM provisioning URL
    org_id        TEXT NOT NULL,                     -- Parent org UUID
    last_seen_at  TEXT                               -- ISO-8601 timestamp injected by DataExporter
);

CREATE INDEX IF NOT EXISTS idx_org_marvis_client_invite_name
    ON org_marvis_client_invite (name);

CREATE INDEX IF NOT EXISTS idx_org_marvis_client_invite_org_id
    ON org_marvis_client_invite (org_id);
```

Notes:
- `last_seen_at` is the standard MistHelper "row last refreshed" column
  injected by `DataExporter` and is not part of the API payload.
- The `disabled` boolean is stored as an integer in SQLite per the project's
  established convention (sqlite3 has no native boolean type).

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (near the existing org-admin entries):

```python
"getOrgMarvisClientInvite": {                          # OperationId from mistapi SDK
    "type": "natural_pk",                              # Stable UUID returned by API
    "primary_key": ["id"],                             # Invite UUID is globally unique
    "indexes": ["name", "org_id"],                     # Common lookup columns
},
```

Every line above is annotated per Constitution Principle VI (Inline
Comments, NON-NEGOTIABLE).

## CSV Column Order

`DataExporter` writes the following columns in this exact order to
`data/org_marvis_client_invite.csv`:

1. `id`
2. `name`
3. `disabled`
4. `provision_url`
5. `org_id`
6. `last_seen_at`

The single API response object is wrapped in a one-element list before being
handed to `DataExporter.write_with_format_selection()` so all three backend
writers (CSV / SQLite / ArangoDB+Redis) consume an identical iterable shape.
