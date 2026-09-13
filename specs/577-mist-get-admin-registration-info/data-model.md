# Phase 1 Data Model: getAdminRegistrationInfo

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

## Entities

The endpoint returns exactly one entity: an `AdminRegistrationInfo` configuration
object describing the reCAPTCHA challenge required to register a new Mist admin.

### Entity: AdminRegistrationInfo

| Field      | Type    | Nullable | Description                                                                 |
|------------|---------|----------|-----------------------------------------------------------------------------|
| `flavor`   | string  | No       | reCAPTCHA provider. Enum: `google`, `hcaptcha`.                             |
| `required` | boolean | No       | Whether reCAPTCHA must be solved before registration is accepted.           |
| `sitekey`  | string  | No       | Public client-side key passed to the reCAPTCHA widget. Tenant-unique.       |

**Primary Key**: `sitekey` (natural_pk -- see research.md Task 2).
**Foreign Keys**: None. This entity is not org-scoped or site-scoped; the Mist Cloud
serves a single reCAPTCHA configuration per region per flavor.
**Indexes**: Secondary index on `flavor` for query-by-provider.

### MistHelper Augmentation Columns

`DataExporter.write_with_format_selection()` adds two standard columns to every row at
write time. They are not part of the API response but are stored to support audit and
multi-backend joins:

| Field             | Type      | Description                                                                |
|-------------------|-----------|----------------------------------------------------------------------------|
| `misthelper_run_ts` | TIMESTAMP | UTC timestamp when this row was written (set on every upsert).             |
| `misthelper_host` | TEXT      | Value of `MIST_HOST` from `.env` at write time (e.g. `api.mist.com`).     |

## State Transitions

**N/A -- read-only endpoint.** The MistHelper menu item only reads the configuration;
it never writes back to Mist. The local SQLite row is overwritten via `INSERT OR
REPLACE` on every successful run, which is the idempotent identity transition. There is
no state machine to model.

## SQLite DDL

```sql
-- Created on first run by DataExporter when the SQLite backend is active.
-- The natural primary key on `sitekey` enables INSERT OR REPLACE upserts
-- so re-running the menu item does not produce duplicate rows.
CREATE TABLE IF NOT EXISTS admin_registration_info (
    sitekey            TEXT      NOT NULL,                         -- Public reCAPTCHA site key (natural PK).
    flavor             TEXT      NOT NULL,                         -- 'google' or 'hcaptcha'.
    required           INTEGER   NOT NULL,                         -- 0 / 1 (SQLite has no native boolean).
    misthelper_run_ts  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Standard DataExporter audit column.
    misthelper_host    TEXT      NOT NULL,                         -- Standard DataExporter source-host column.
    PRIMARY KEY (sitekey)
);

CREATE INDEX IF NOT EXISTS idx_admin_registration_info_flavor
    ON admin_registration_info (flavor);                            -- Query-by-provider support.
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

```python
# Add to the ENDPOINT_PRIMARY_KEY_STRATEGIES dict in MistHelper.py (line ~1672).
# Natural PK on `sitekey` -- the only field unique enough to identify a configuration.
'getAdminRegistrationInfo': {                       # operationId from the OpenAPI spec.
    'type': 'natural_pk',                           # Use INSERT OR REPLACE on the PK.
    'primary_key': ['sitekey'],                     # Single-column natural identifier.
    'indexes': ['flavor'],                          # Secondary index for query-by-provider.
    'table_name': 'admin_registration_info',        # Matches CSV / ArangoDB collection name.
},
```

## Relationships

This entity has no relationships to other MistHelper-modeled entities (orgs, sites,
devices, clients, alarms). It is a standalone tenant-wide configuration row. The
ArangoDB graph backend stores it as a vertex in a `config` collection with no edges.

## Validation Rules

- `flavor` MUST be one of the documented enum values (`google`, `hcaptcha`). Unknown
  values are stored as-is but trigger a `WARNING` log line so a future Mist enum
  expansion is visible in the run log.
- `required` MUST be a boolean. Non-boolean values from a malformed response are
  coerced to `False` with a `WARNING` log line.
- `sitekey` MUST be non-empty. An empty `sitekey` aborts the write with an `ERROR` log
  line because the natural PK would be unusable.
