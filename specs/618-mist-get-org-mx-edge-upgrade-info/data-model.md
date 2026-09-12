# Phase 1 Data Model: getOrgMxEdgeUpgradeInfo

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_mxedges_versions.md` (200 OK body).
The response is an array (`uniqueItems: true`) of `mxedge_upgrade_info_items`
objects.

## Entities

The endpoint returns a single, flat JSON array. MistHelper persists it as one
logical entity per row.

### Entity 1: `MxEdgeUpgradeInfoRow`

One row per (org, channel, distro, package, version) tuple. The Mist response
body carries `{default, distro, package, version}`; MistHelper injects `org_id`
and `channel` from the caller's context because the API does not echo them back.

| Field          | Type     | Source                | PK? | FK?           | Notes                                                                                       |
|----------------|----------|-----------------------|-----|---------------|---------------------------------------------------------------------------------------------|
| `org_id`       | TEXT     | MistHelper context    | YES | sites.org_id  | UUID supplied by user; injected before write. Never absent.                                |
| `channel`      | TEXT     | MistHelper prompt     | YES | --            | One of `stable`, `beta`, `alpha`. Defaults to `stable` when the user accepted the default. |
| `distro`       | TEXT     | API `distro`          | YES | --            | E.g. `bullseye`, `buster`. Falls back to sentinel `"_unspecified_"` when API row omits it. |
| `package`      | TEXT     | API `package`         | YES | --            | Required by schema. Debian package name (e.g. `mxagent`, `tunterm`).                       |
| `version`      | TEXT     | API `version`         | YES | --            | Required by schema. Semantic version string (e.g. `2.4.100`).                              |
| `is_default`   | INTEGER  | API `default`         | --  | --            | Stored as `0` / `1` for SQLite portability (response carries native boolean).              |
| `polled_at_utc`| TEXT     | MistHelper clock      | --  | --            | ISO8601 UTC timestamp of the poll, for audit.                                              |
| `distro_filter`| TEXT     | MistHelper prompt     | --  | --            | The literal value the user supplied as the `distro` query parameter (or empty string when omitted). Recorded for audit -- distinct from the response `distro` field. |

The `(org_id, channel, distro, package, version)` tuple is the composite
primary key (see Research Task 2). `distro_filter` is intentionally **not** part
of the PK -- it records *what the user asked for*, while `distro` records *what
the API returned*. The two differ when the user leaves the filter empty and the
API responds with rows from multiple distros.

## State Transitions

N/A -- this is a read-only endpoint. The underlying *firmware catalog* on the
Mist side changes over time as Juniper publishes new releases, but MistHelper
does not drive those transitions; it captures point-in-time snapshots. Each
poll either inserts new `(package, version)` rows or refreshes the
`is_default` flag and `polled_at_utc` of existing rows via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- One row per (org, channel, distro, package, version) tuple.
CREATE TABLE IF NOT EXISTS org_mxedge_upgrade_info (
    org_id          TEXT     NOT NULL,
    channel         TEXT     NOT NULL,
    distro          TEXT     NOT NULL,
    package         TEXT     NOT NULL,
    version         TEXT     NOT NULL,
    is_default      INTEGER,
    polled_at_utc   TEXT,
    distro_filter   TEXT,
    PRIMARY KEY (org_id, channel, distro, package, version)
);

CREATE INDEX IF NOT EXISTS idx_mxedge_upgrade_info_default
    ON org_mxedge_upgrade_info (is_default);

CREATE INDEX IF NOT EXISTS idx_mxedge_upgrade_info_package
    ON org_mxedge_upgrade_info (package);

CREATE INDEX IF NOT EXISTS idx_mxedge_upgrade_info_channel_distro
    ON org_mxedge_upgrade_info (channel, distro);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT
EXISTS`, ArangoDB via collection upsert, Redis via key namespacing). MistHelper
does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no
structural change to surrounding code).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Available Mist Edge firmware packages and versions per channel/distro.
    'getOrgMxEdgeUpgradeInfo': {                                                    # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': [                                                            # five-column natural key
            'org_id',                                                               # injected by MistHelper (API omits it)
            'channel',                                                              # injected from user's channel prompt
            'distro',                                                               # API field; sentinel when missing
            'package',                                                              # API field, required by schema
            'version',                                                              # API field, required by schema
        ],
        'indexes': [                                                                # secondary indexes for common queries
            'is_default',                                                           # filter to "current default per channel/distro"
            'package',                                                              # search by package name across versions
            ('channel', 'distro'),                                                  # narrow to one channel+distro combo
        ],
        'table': 'org_mxedge_upgrade_info',                                         # target SQLite table
    },
}
```

The composite key faithfully models the Mist API's contract: a `(channel,
distro, package, version)` tuple uniquely identifies a published firmware
artifact, and we scope it per `org_id` because MistHelper may track multiple
orgs from a single deployment. The `is_default` boolean changes over time as
Juniper promotes new defaults, so it is intentionally **not** in the PK -- a
re-poll updates the flag on the existing row rather than inserting a duplicate.
