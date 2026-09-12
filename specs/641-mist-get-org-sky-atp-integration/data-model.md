# Phase 1 Data Model: GetOrgSkyAtpIntegration

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_setting_skyatp_setup.md` (200 OK
body).

## Entities

The endpoint returns a single JSON object describing the Juniper Sky ATP
integration configuration for an organization. MistHelper splits this
into two logical entities for clean multi-backend persistence: a summary
row per org, and zero-or-more rows for the third-party threat feeds
enabled on that org.

### Entity 1: `SkyAtpIntegration`

One row per organization.

| Field                    | Type    | Source                            | PK? | FK?          | Notes |
|--------------------------|---------|-----------------------------------|-----|--------------|-------|
| `org_id`                 | TEXT    | MistHelper context                | YES | sites.org_id | UUID supplied by user; injected before write. |
| `secintel_allowlist_url` | TEXT    | API `secintel_allowlist_url`      | --  | --           | Signed S3 URL for the org allowlist. Read-only per schema. Sensitive -- masked at INFO log level. |
| `secintel_blocklist_url` | TEXT    | API `secintel_blocklist_url`      | --  | --           | Signed S3 URL for the org blocklist. Read-only per schema. Sensitive -- masked at INFO log level. |
| `third_party_feed_count` | INTEGER | len(API `secintel.third_party_threat_feeds`) | -- | -- | Convenience count; matches the feed rows in Entity 2. |
| `polled_at_utc`          | TEXT    | MistHelper clock                  | --  | --           | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `SkyAtpThreatFeed`

Zero-or-more rows per organization -- one per element of the
`secintel.third_party_threat_feeds` array in the API response.

| Field           | Type    | Source                                        | PK? | FK?                             | Notes |
|-----------------|---------|-----------------------------------------------|-----|---------------------------------|-------|
| `org_id`        | TEXT    | MistHelper context                            | YES | org_sky_atp_integration.org_id  | UUID. |
| `feed_name`     | TEXT    | API `secintel.third_party_threat_feeds[*]`    | YES | --                              | Identifier string. Known values: `block_list`, `threatfox_ip`, `feodo_tracker`, `dshield`, `tor`, `threatfox_url`, `urlhaus`, `open_phish`, `threatfox_domains`. |
| `feed_category` | TEXT    | Derived by MistHelper from `feed_name`        | --  | --                              | One of `ip`, `url`, `domain`, or `unknown` -- classification per the doc's grouping. |
| `polled_at_utc` | TEXT    | MistHelper clock                              | --  | --                              | ISO8601 UTC timestamp of the poll, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. Sky ATP integration configuration
is edited on the Mist side via `PUT
/api/v1/orgs/{org_id}/setting/skyatp/setup` (out of scope per spec.md).
MistHelper only captures snapshots via GET. Each poll overwrites the
prior snapshot for the same `org_id` (summary) and `(org_id, feed_name)`
(feeds) tuples via SQLite `INSERT OR REPLACE` upserts.

## SQLite DDL

```sql
-- Summary table: one row per org.
CREATE TABLE IF NOT EXISTS org_sky_atp_integration (
    org_id                    TEXT NOT NULL,
    secintel_allowlist_url    TEXT,
    secintel_blocklist_url    TEXT,
    third_party_feed_count    INTEGER,
    polled_at_utc             TEXT,
    PRIMARY KEY (org_id)
);

-- Feeds table: zero-or-more rows per (org, feed_name).
CREATE TABLE IF NOT EXISTS org_sky_atp_threat_feeds (
    org_id          TEXT NOT NULL,
    feed_name       TEXT NOT NULL,
    feed_category   TEXT,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, feed_name),
    FOREIGN KEY (org_id) REFERENCES org_sky_atp_integration(org_id)
);

CREATE INDEX IF NOT EXISTS idx_sky_atp_threat_feeds_feed_name
    ON org_sky_atp_threat_feeds (feed_name);

CREATE INDEX IF NOT EXISTS idx_sky_atp_threat_feeds_feed_category
    ON org_sky_atp_threat_feeds (feed_category);
```

`DataExporter.write_with_format_selection()` emits the equivalent DDL on
first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (two dict
inserts inside the existing literal, no structural change to the
dictionary itself).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Sky ATP integration summary: one row per org, keyed by org_id.
    'getOrgSkyAtpIntegration': {                                                    # operationId from OpenAPI spec
        'type': 'natural_pk',                                                       # org_id is a stable API-provided UUID
        'primary_key': ['org_id'],                                                  # one row per org, upsert on repeat polls
        'indexes': [],                                                              # no secondary indexes needed on singleton table
        'table': 'org_sky_atp_integration',                                         # target SQLite table for summary rows
    },

    # Per-feed rows produced from the secintel.third_party_threat_feeds array.
    'getOrgSkyAtpIntegrationThreatFeeds': {                                         # MistHelper-internal sub-table identifier
        'type': 'composite_pk',                                                     # composite of org FK + feed name
        'primary_key': ['org_id', 'feed_name'],                                     # uniquely identifies a feed enrollment
        'indexes': ['feed_name', 'feed_category'],                                  # fast lookup by feed and by category
        'table': 'org_sky_atp_threat_feeds',                                        # target SQLite table for feed rows
    },
}
```

The `getOrgSkyAtpIntegrationThreatFeeds` key is a MistHelper-internal
identifier (the Mist API has no operationId for it -- it is a flattened
sub-array of the parent response). This matches how MistHelper already
splits other endpoints whose response contains nested arrays (see spec
500's `getOrgLicenseAsyncClaimStatusDetails` for the same pattern).
