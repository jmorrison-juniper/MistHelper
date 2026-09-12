# Phase 1 Data Model: getOrgDeviceUpgrade

**Feature**: 605-mist-get-org-device-upgrade
**Date**: 2026-06-30
**Source schema**: `documentation/api/utilities/GET_orgs_org_id_devices_upgrade_upgrade_id.md`

## Entity Catalog

The endpoint returns a single nested JSON object. MistHelper flattens it
into two related entities -- a summary record (the upgrade job itself) and
a per-site detail record (the `upgrades[]` array exploded).

### Entity 1: OrgDeviceUpgrade (summary)

One row per upgrade job per org.

| Field | Type | Source path | Required | Notes |
|-------|------|-------------|----------|-------|
| `org_id` | TEXT (UUID) | path param | yes | Injected by MistHelper, not in API response body |
| `id` | TEXT (UUID) | `$.id` | yes | Upgrade job UUID -- primary identifier |
| `target_version` | TEXT | `$.target_version` | no | Firmware version requested, e.g. `0.14.29411` |
| `strategy` | TEXT | `$.strategy` | no | Enum: `big_bang`, `canary`, `rrm`, `serial` |
| `enable_p2p` | BOOLEAN | `$.enable_p2p` | no | Allow local AP-to-AP firmware copy |
| `force` | BOOLEAN | `$.force` | no | Upgrade even when running version == target |
| `site_count` | INTEGER | derived `len($.upgrades)` | yes | Convenience count; FK link to detail table |
| `fetched_at` | TIMESTAMP | now() at write time | yes | Polling timestamp for delta analysis |

**Primary key**: `(org_id, id)` -- composite_pk
**Foreign keys**: none
**State transitions**: N/A -- read-only endpoint. The same row is upserted
on every poll; the `fetched_at` column captures the most recent observation.

### Entity 2: OrgDeviceUpgradeSiteDetail (per-site)

Zero or more rows per upgrade job; one per affected site.

| Field | Type | Source path | Required | Notes |
|-------|------|-------------|----------|-------|
| `org_id` | TEXT (UUID) | path param | yes | Injected by MistHelper |
| `upgrade_id` | TEXT (UUID) | `$.id` | yes | FK back to summary table |
| `site_id` | TEXT (UUID) | `$.upgrades[*].site_id` | yes | Affected site |
| `site_upgrade_id` | TEXT (UUID) | `$.upgrades[*].upgrade.id` | no | Per-site sub-upgrade UUID |
| `start_time` | INTEGER (epoch s) | `$.upgrades[*].upgrade.start_time` | no | Per-site kickoff timestamp |
| `status` | TEXT | `$.upgrades[*].upgrade.status` | no | Enum: `cancelled`, `completed`, `created`, `downloaded`, `downloading`, `failed`, `upgrading`, `queued` |
| `total_devices` | INTEGER | `$.upgrades[*].upgrade.targets.total` | no | Devices in scope at this site |
| `macs_download_requested` | TEXT | `$.upgrades[*].upgrade.targets.download_requested` | no | Comma-joined MACs |
| `macs_downloading` | TEXT | `$.upgrades[*].upgrade.targets.downloading` | no | Comma-joined MACs |
| `macs_downloaded` | TEXT | `$.upgrades[*].upgrade.targets.downloaded` | no | Comma-joined MACs |
| `macs_scheduled` | TEXT | `$.upgrades[*].upgrade.targets.scheduled` | no | Comma-joined MACs |
| `macs_reboot_in_progress` | TEXT | `$.upgrades[*].upgrade.targets.reboot_in_progress` | no | Comma-joined MACs |
| `macs_rebooted` | TEXT | `$.upgrades[*].upgrade.targets.rebooted` | no | Comma-joined MACs |
| `macs_upgraded` | TEXT | `$.upgrades[*].upgrade.targets.upgraded` | no | Comma-joined MACs |
| `macs_failed` | TEXT | `$.upgrades[*].upgrade.targets.failed` | no | Comma-joined MACs |
| `macs_skipped` | TEXT | `$.upgrades[*].upgrade.targets.skipped` | no | Comma-joined MACs |
| `fetched_at` | TIMESTAMP | now() at write time | yes | Polling timestamp |

**Primary key**: `(org_id, upgrade_id, site_id)` -- composite_pk
**Foreign keys**: `(org_id, upgrade_id)` references `org_device_upgrade(org_id, id)`
**State transitions**: N/A -- read-only endpoint. Status field evolves
upstream over the upgrade lifecycle; each poll upserts the row in place.

## SQLite DDL

The DDL below is what `DataExporter` produces on first run; it is
documented here for reviewer traceability. MistHelper does not embed raw
DDL -- the schema is derived from the entity catalog and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registration.

```sql
-- Summary table: one row per upgrade job per org.
CREATE TABLE IF NOT EXISTS org_device_upgrade (
    org_id          TEXT NOT NULL,
    id              TEXT NOT NULL,
    target_version  TEXT,
    strategy        TEXT,
    enable_p2p      INTEGER,        -- SQLite BOOLEAN -> INTEGER
    force           INTEGER,
    site_count      INTEGER,
    fetched_at      TEXT NOT NULL,  -- ISO 8601
    PRIMARY KEY (org_id, id)
);
CREATE INDEX IF NOT EXISTS idx_org_device_upgrade_org
    ON org_device_upgrade (org_id);
CREATE INDEX IF NOT EXISTS idx_org_device_upgrade_strategy
    ON org_device_upgrade (strategy);

-- Detail table: one row per affected site per upgrade job.
CREATE TABLE IF NOT EXISTS org_device_upgrade_site_details (
    org_id                    TEXT NOT NULL,
    upgrade_id                TEXT NOT NULL,
    site_id                   TEXT NOT NULL,
    site_upgrade_id           TEXT,
    start_time                INTEGER,
    status                    TEXT,
    total_devices             INTEGER,
    macs_download_requested   TEXT,
    macs_downloading          TEXT,
    macs_downloaded           TEXT,
    macs_scheduled            TEXT,
    macs_reboot_in_progress   TEXT,
    macs_rebooted             TEXT,
    macs_upgraded             TEXT,
    macs_failed               TEXT,
    macs_skipped              TEXT,
    fetched_at                TEXT NOT NULL,
    PRIMARY KEY (org_id, upgrade_id, site_id),
    FOREIGN KEY (org_id, upgrade_id)
        REFERENCES org_device_upgrade (org_id, id)
);
CREATE INDEX IF NOT EXISTS idx_org_device_upgrade_site_details_upgrade
    ON org_device_upgrade_site_details (org_id, upgrade_id);
CREATE INDEX IF NOT EXISTS idx_org_device_upgrade_site_details_status
    ON org_device_upgrade_site_details (status);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Registration

Two entries land in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (MistHelper.py near
line 3983, adjacent to the existing `listOrgDeviceUpgrades` entry):

```python
# -- Device Management ---------------------------------------------------
"getOrgDeviceUpgrade": {                              # Single-upgrade summary view
    "type": "composite_pk",                           # Upserts in place across polls
    "primary_key": ["org_id", "id"],                  # org + upgrade UUID is the natural key
    "indexes": ["org_id", "strategy"],                # Common filters used by NOC reports
    "unique_constraints": [],                         # PK alone is unique
    "description": "Single device upgrade job summary (top-level fields).",
},
"getOrgDeviceUpgrade_site_details": {                 # Per-site flatten of upgrades[] array
    "type": "composite_pk",                           # Upserts per (upgrade, site) on each poll
    "primary_key": ["org_id", "upgrade_id", "site_id"],  # Natural composite key from schema
    "indexes": ["org_id", "upgrade_id", "status"],    # Used by progress dashboards
    "unique_constraints": [],                         # PK alone is unique
    "description": "Per-site detail rows flattened from upgrades[] array.",
},
```

The `_site_details` suffix on the second key is a MistHelper convention for
sub-entities flattened from a parent endpoint's response. `DataExporter`
reads the strategy via the suffix-aware lookup helper that already exists
for sibling endpoints with parent/child tables.

## Cross-Reference

- Parent endpoint that surfaces valid `upgrade_id` values for prompting:
  `listOrgDeviceUpgrades` (MistHelper.py line 3983).
- Sibling per-site endpoint for the same upgrade job at site scope:
  `GET /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}` (cataloged
  separately under `documentation/api/utilities/GET_sites_site_id_devices_upgrade_upgrade_id.md`).
- Cancel action against the same upgrade job:
  `POST /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}/cancel`
  (destructive; out of scope for this read-only feature).
