# Phase 1 Data Model: getOrgSsrUpgrade

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/utilities/GET_orgs_org_id_ssr_upgrade_upgrade_id_cancel.md`
(200 OK body). This is a GET despite the `/cancel` URL suffix (documented
gotcha).

## Entities

The endpoint returns a single JSON object describing one SSR firmware upgrade
job. MistHelper splits this into two logical entities for clean multi-backend
persistence: a `SsrUpgradeSummary` (one row per upgrade) and a set of
`SsrUpgradeTarget` rows (one row per device MAC in each of the four target
buckets).

### Entity 1: `SsrUpgradeSummary`

One row per (org, upgrade).

| Field              | Type    | Source                | PK? | FK?              | Notes |
|--------------------|---------|-----------------------|-----|------------------|-------|
| `id`               | TEXT    | API `id`              | YES | --               | Upgrade UUID from Mist. Marked `readOnly` in the schema. |
| `org_id`           | TEXT    | MistHelper context    | --  | sites.org_id     | Injected by MistHelper before write (not returned in API body). |
| `channel`          | TEXT    | API `channel`         | --  | --               | Non-empty string; SSR release channel (alpha / beta / stable / build-specific). |
| `device_type`      | TEXT    | API `device_type`     | --  | --               | Target device type identifier (SSR family). |
| `status`           | TEXT    | API `status`          | --  | --               | Non-empty string; observed values include `created`, `queued`, `upgrading`, `done`, `failed`, `cancelled`. |
| `versions_json`    | TEXT    | API `versions`        | --  | --               | JSON-encoded map of `{ target: version_string }`. Free-form object per schema; stored as JSON blob to preserve fidelity. |
| `success_count`    | INTEGER | len(API `targets.success`)   | --  | --        | Convenience count of `targets.success` array. |
| `failed_count`     | INTEGER | len(API `targets.failed`)    | --  | --        | Convenience count of `targets.failed` array. |
| `queued_count`     | INTEGER | len(API `targets.queued`)    | --  | --        | Convenience count of `targets.queued` array. |
| `upgrading_count`  | INTEGER | len(API `targets.upgrading`) | --  | --        | Convenience count of `targets.upgrading` array. |
| `polled_at_utc`    | TEXT    | MistHelper clock      | --  | --               | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `SsrUpgradeTarget`

Zero or more rows per (org, upgrade). One row per (bucket, device MAC).
Source: each string in each of the four arrays under API `targets`.

| Field           | Type    | Source                 | PK? | FK?                                        | Notes |
|-----------------|---------|------------------------|-----|--------------------------------------------|-------|
| `org_id`        | TEXT    | MistHelper context     | YES | org_ssr_upgrade_summary.org_id             | UUID. |
| `upgrade_id`    | TEXT    | API `id`               | YES | org_ssr_upgrade_summary.id                 | Joins to summary. |
| `bucket`        | TEXT    | flattener injects      | YES | --                                         | One of `failed`, `queued`, `success`, `upgrading`. |
| `device_mac`    | TEXT    | element of API `targets.<bucket>[]` | YES | --                            | Device MAC address (SSR node identifier). |
| `intended_version` | TEXT | API `versions[device_mac]` when present | -- | --                            | Best-effort join from the `versions` map; may be NULL when the map keys are not MAC-shaped. |
| `polled_at_utc` | TEXT    | MistHelper clock       | --  | --                                         | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying SSR upgrade *job* on the
Mist side transitions through `created -> queued -> upgrading -> (done |
failed | cancelled)`, and individual target devices transition through the
`queued -> upgrading -> (success | failed)` buckets, but MistHelper does not
drive or model those transitions. It only captures snapshots. Each poll
overwrites the prior snapshot for the same primary key via SQLite
`INSERT OR REPLACE`, so a running upgrade produces one summary row and a
consistent set of target rows regardless of how many times an operator polls.

## SQLite DDL

```sql
-- Summary table: one row per (org, SSR upgrade).
CREATE TABLE IF NOT EXISTS org_ssr_upgrade_summary (
    id                  TEXT     NOT NULL,
    org_id              TEXT     NOT NULL,
    channel             TEXT,
    device_type         TEXT,
    status              TEXT,
    versions_json       TEXT,
    success_count       INTEGER,
    failed_count        INTEGER,
    queued_count        INTEGER,
    upgrading_count     INTEGER,
    polled_at_utc       TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_ssr_upgrade_summary_org
    ON org_ssr_upgrade_summary (org_id);
CREATE INDEX IF NOT EXISTS idx_ssr_upgrade_summary_status
    ON org_ssr_upgrade_summary (status);
CREATE INDEX IF NOT EXISTS idx_ssr_upgrade_summary_channel
    ON org_ssr_upgrade_summary (channel);

-- Targets table: zero-or-more rows per (org, upgrade), one per (bucket, MAC).
CREATE TABLE IF NOT EXISTS org_ssr_upgrade_targets (
    org_id              TEXT     NOT NULL,
    upgrade_id          TEXT     NOT NULL,
    bucket              TEXT     NOT NULL,
    device_mac          TEXT     NOT NULL,
    intended_version    TEXT,
    polled_at_utc       TEXT,
    PRIMARY KEY (org_id, upgrade_id, bucket, device_mac),
    FOREIGN KEY (upgrade_id)
        REFERENCES org_ssr_upgrade_summary(id)
);

CREATE INDEX IF NOT EXISTS idx_ssr_upgrade_targets_bucket
    ON org_ssr_upgrade_targets (bucket);
CREATE INDEX IF NOT EXISTS idx_ssr_upgrade_targets_mac
    ON org_ssr_upgrade_targets (device_mac);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly from the new menu
method.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Insert the following two entries into the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (near the
sibling `"listOrgSsrUpgrades"` entry at line 4796 today). Both entries are
single dict inserts -- no structural change to the dictionary.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Per-upgrade status summary, keyed by the API-provided upgrade UUID.
    "getOrgSsrUpgrade": {                                                  # operationId from OpenAPI
        "type": "natural_pk",                                              # API provides stable UUID
        "primary_key": ["id"],                                             # upgrade UUID uniquely identifies the row
        "indexes": ["org_id", "status", "channel"],                        # common filters for operators
        "unique_constraints": [],                                          # PK alone enforces uniqueness
        "description": "Single SSR firmware upgrade status (from GET .../ssr/upgrade/{id}/cancel)",  # audit trail
    },

    # Per-target device rows produced by flattening the targets object.
    "getOrgSsrUpgradeTargets": {                                           # MistHelper-internal sub-table id
        "type": "composite_pk",                                            # composite of org + upgrade + bucket + MAC
        "primary_key": ["org_id", "upgrade_id", "bucket", "device_mac"],   # uniquely identifies a target snapshot
        "indexes": ["bucket", "device_mac"],                               # fast lookup by state or by device
        "unique_constraints": [],                                          # PK alone enforces uniqueness
        "description": "Per-device targets for an SSR firmware upgrade job",  # audit trail
    },
}
```

The `getOrgSsrUpgradeTargets` key is a MistHelper-internal identifier -- no
separate OpenAPI operationId exists for the flattened sub-array. This
pattern matches how MistHelper already splits other endpoints whose response
contains nested arrays (see the reference plan for spec 500 for the same
pattern applied to `GetOrgLicenseAsyncClaimStatus`).
