# Phase 1 Data Model: getOrgMistScep

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_setting_mist_scep.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing the Mist SCEP settings for one
organization. MistHelper persists this as a single logical entity (one row per org).

### Entity 1: `MistScepSetting`

One row per organization (singleton per `org_id`).

| Field              | Type    | Source                | PK? | FK?           | Notes |
|--------------------|---------|-----------------------|-----|---------------|-------|
| `org_id`           | TEXT    | MistHelper context    | YES | sites.org_id  | UUID supplied by user; injected before write (API does not echo it). |
| `cert_providers`   | TEXT    | API `cert_providers`  | --  | --            | Array of strings joined with `,` for CSV/SQLite. Source enum values: `intune`, `jamf`, `byod`. Empty string when the array is absent or empty. |
| `cert_providers_count` | INTEGER | len(API `cert_providers`) | -- | --       | Convenience count of configured providers. Always populated (0 when array absent). |
| `enabled`          | INTEGER | API `enabled`         | --  | --            | Boolean stored as 0/1. Read-only on the upstream side. |
| `suspended`        | INTEGER | API `suspended`       | --  | --            | Boolean stored as 0/1. Default `false` upstream. |
| `intune_scep_url`  | TEXT    | API `intune_scep_url` | --  | --            | Intune SCEP enrollment URL. Read-only upstream. |
| `jamf_scep_url`    | TEXT    | API `jamf_scep_url`   | --  | --            | Jamf SCEP enrollment URL. Read-only upstream. |
| `jamf_webhook_url` | TEXT    | API `jamf_webhook_url`| --  | --            | Jamf webhook URL. Read-only upstream. |
| `jamf_access_token`| TEXT    | API `jamf_access_token`| -- | --            | SENSITIVE -- Bearer token Jamf uses against the Mist webhook. Persisted to backend but never logged above DEBUG; DEBUG only logs presence (not value). |
| `polled_at_utc`    | TEXT    | MistHelper clock      | --  | --            | ISO 8601 UTC timestamp of the poll, for audit. |

The `cert_providers` source array is collapsed to a CSV-friendly string column rather
than split into a child table; the array is always a small subset of three enum values
(`intune`, `jamf`, `byod`) and the cardinality does not warrant a join. A separate
boolean / integer column per provider could be added later if a downstream consumer asks
for filterable per-provider columns; the `cert_providers` string is forward-compatible
either way.

## State Transitions

N/A -- this is a read-only endpoint. The underlying *settings document* on the Mist side
can be mutated by an admin via PUT or DELETE on the same path (`PUT_orgs_org_id_setting_mist_scep.md`
and `DELETE_orgs_org_id_setting_mist_scep.md`), and the `enabled` / `suspended` flags can
change asynchronously when SCEP is suspended for billing or policy reasons. MistHelper
does not drive or model those transitions; it merely captures the current snapshot. Each
poll overwrites the prior snapshot for the same `org_id` via SQLite `INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Singleton table: one row per org's Mist SCEP setting.
CREATE TABLE IF NOT EXISTS org_setting_mist_scep (
    org_id                  TEXT     NOT NULL,
    cert_providers          TEXT,
    cert_providers_count    INTEGER,
    enabled                 INTEGER,
    suspended               INTEGER,
    intune_scep_url         TEXT,
    jamf_scep_url           TEXT,
    jamf_webhook_url        TEXT,
    jamf_access_token       TEXT,
    polled_at_utc           TEXT,
    PRIMARY KEY (org_id)
);

CREATE INDEX IF NOT EXISTS idx_org_setting_mist_scep_enabled
    ON org_setting_mist_scep (enabled);

CREATE INDEX IF NOT EXISTS idx_org_setting_mist_scep_suspended
    ON org_setting_mist_scep (suspended);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in
`MistHelper.py` (single insert in the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Mist SCEP setting is a per-org singleton -- natural PK on org_id.
    'getOrgMistScep': {                                                             # operationId from OpenAPI
        'type': 'natural_pk',                                                       # one row per org
        'primary_key': ['org_id'],                                                  # injected from MistHelper context
        'indexes': ['enabled', 'suspended'],                                        # fast filter by enable / suspend state
        'table': 'org_setting_mist_scep',                                           # target SQLite table
    },
}
```

The `org_id` is not returned by the API in the response body, so MistHelper injects it
from the calling context before passing the row to `DataExporter.write_with_format_selection()`.
This is the same pattern used by other org-settings exports.

## Sensitive Field Handling Summary

| Field               | Persisted? | Logged INFO+? | Logged DEBUG?            |
|---------------------|------------|---------------|--------------------------|
| `jamf_access_token` | YES (sink) | NO            | Presence only (`has_jamf_token=True|False`), never value |
| `intune_scep_url`   | YES        | NO            | URL host only            |
| `jamf_scep_url`     | YES        | NO            | URL host only            |
| `jamf_webhook_url`  | YES        | NO            | URL host only            |
| `org_id`            | YES        | YES           | YES                      |
| `enabled`           | YES        | YES (summary) | YES                      |
| `suspended`         | YES        | YES (summary) | YES                      |
| `cert_providers`    | YES        | YES (count)   | YES (CSV string)         |

The "presence only" rule for `jamf_access_token` matches Constitution Principle V
(Observability) and Principle III (Safety-First / Secrets-from-`.env`-only) -- secrets
loaded from `.env` are never logged, and secrets returned by upstream APIs follow the
same rule.
