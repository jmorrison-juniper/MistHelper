# Phase 1 Data Model: getOrgMxTunnel

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_mxtunnels_mxtunnel_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one Mist tunnel. MistHelper splits
this into two logical entities for clean multi-backend persistence: the parent mxtunnel
record and the nested `ipsec.extra_routes` child rows.

### Entity 1: `MxTunnel`

One row per mxtunnel.

| Field                  | Type    | Source                          | PK? | FK?            | Notes |
|------------------------|---------|---------------------------------|-----|----------------|-------|
| `id`                   | TEXT    | API `id`                        | YES | --             | Mxtunnel UUID. Natural primary key. |
| `org_id`               | TEXT    | API `org_id`                    | --  | (sites.org_id) | UUID of owning org. Indexed. |
| `site_id`              | TEXT    | API `site_id`                   | --  | (sites.id)     | UUID of owning site, only when `for_site=true`. Indexed. |
| `for_site`             | INTEGER | API `for_site`                  | --  | --             | 0/1 boolean -- tunnel is site-scoped. |
| `name`                 | TEXT    | API `name`                      | --  | --             | Human-readable name (nullable). Indexed. |
| `protocol`             | TEXT    | API `protocol`                  | --  | --             | Enum `ip` or `udp`. Indexed. |
| `mtu`                  | INTEGER | API `mtu`                       | --  | --             | 0 = enable PMTU; 552-1500 = start PMTU at lower MTU. |
| `hello_interval`       | INTEGER | API `hello_interval`            | --  | --             | Seconds 1-300; default 60. Nullable. |
| `hello_retries`        | INTEGER | API `hello_retries`             | --  | --             | 2-30; default 7. Nullable. |
| `vlan_ids_json`        | TEXT    | json.dumps(API `vlan_ids`)      | --  | --             | JSON-encoded integer array. |
| `vlan_ids_count`       | INTEGER | len(API `vlan_ids`)             | --  | --             | Convenience count. |
| `mxcluster_ids_json`   | TEXT    | json.dumps(API `mxcluster_ids`) | --  | --             | JSON-encoded UUID array. |
| `mxcluster_ids_count`  | INTEGER | len(API `mxcluster_ids`)        | --  | --             | Convenience count. |
| `anchor_mxtunnel_ids_json` | TEXT | json.dumps(API `anchor_mxtunnel_ids`) | -- | --      | JSON-encoded UUID array. |
| `anchor_mxtunnel_ids_count` | INTEGER | len(API `anchor_mxtunnel_ids`) | -- | --       | Convenience count. |
| `auto_preemption_enabled` | INTEGER | API `auto_preemption.enabled` | -- | --            | 0/1 boolean. |
| `auto_preemption_day_of_week` | TEXT | API `auto_preemption.day_of_week` | -- | --     | Enum `any`/`mon`...`sun`. |
| `auto_preemption_time_of_day` | TEXT | API `auto_preemption.time_of_day` | -- | --     | `any` or `HH:MM` 24h. |
| `ipsec_enabled`        | INTEGER | API `ipsec.enabled`             | --  | --             | 0/1 boolean. |
| `ipsec_use_mxedge`     | INTEGER | API `ipsec.use_mxedge`          | --  | --             | 0/1 boolean. |
| `ipsec_split_tunnel`   | INTEGER | API `ipsec.split_tunnel`        | --  | --             | 0/1 boolean. |
| `ipsec_dns_servers_json` | TEXT  | json.dumps(API `ipsec.dns_servers`) | -- | --         | JSON-encoded string array or null. |
| `ipsec_dns_suffix_json` | TEXT   | json.dumps(API `ipsec.dns_suffix`) | -- | --          | JSON-encoded string array. |
| `created_time`         | REAL    | API `created_time`              | --  | --             | Epoch seconds. Read-only. |
| `modified_time`        | REAL    | API `modified_time`             | --  | --             | Epoch seconds. Read-only. |
| `fetched_at_utc`       | TEXT    | MistHelper clock                | --  | --             | ISO8601 UTC timestamp of the fetch, for audit. |

### Entity 2: `MxTunnelIpsecExtraRoute`

Zero or more rows per mxtunnel. Source: each element of the API
`ipsec.extra_routes` array.

| Field          | Type    | Source                       | PK? | FK?                          | Notes |
|----------------|---------|------------------------------|-----|------------------------------|-------|
| `mxtunnel_id`  | TEXT    | parent API `id`              | YES | org_mxtunnels.id             | Mxtunnel UUID; joins to parent. |
| `dest`         | TEXT    | API extra_routes[].dest      | YES | --                           | Destination CIDR string. |
| `next_hop`     | TEXT    | API extra_routes[].next_hop  | YES | --                           | Next-hop IP string. |
| `org_id`       | TEXT    | parent API `org_id`          | --  | (sites.org_id)               | Denormalized for org-wide queries. |
| `fetched_at_utc` | TEXT  | MistHelper clock             | --  | --                           | ISO8601 UTC timestamp of the fetch, for audit. |

## State Transitions

N/A -- this is a read-only endpoint. The mxtunnel object on the Mist side is mutated
via the corresponding PUT/POST/DELETE operations (which are explicitly out of scope per
the spec), but MistHelper does not drive or model those transitions; it captures
snapshots only. Each fetch overwrites the prior snapshot for the same mxtunnel UUID via
SQLite `INSERT OR REPLACE`, and child extra-route rows upsert on
`(mxtunnel_id, dest, next_hop)`.

## SQLite DDL

```sql
-- Summary table: one row per mxtunnel.
CREATE TABLE IF NOT EXISTS org_mxtunnels (
    id                              TEXT     NOT NULL,
    org_id                          TEXT,
    site_id                         TEXT,
    for_site                        INTEGER,
    name                            TEXT,
    protocol                        TEXT,
    mtu                             INTEGER,
    hello_interval                  INTEGER,
    hello_retries                   INTEGER,
    vlan_ids_json                   TEXT,
    vlan_ids_count                  INTEGER,
    mxcluster_ids_json              TEXT,
    mxcluster_ids_count             INTEGER,
    anchor_mxtunnel_ids_json        TEXT,
    anchor_mxtunnel_ids_count       INTEGER,
    auto_preemption_enabled         INTEGER,
    auto_preemption_day_of_week     TEXT,
    auto_preemption_time_of_day     TEXT,
    ipsec_enabled                   INTEGER,
    ipsec_use_mxedge                INTEGER,
    ipsec_split_tunnel              INTEGER,
    ipsec_dns_servers_json          TEXT,
    ipsec_dns_suffix_json           TEXT,
    created_time                    REAL,
    modified_time                   REAL,
    fetched_at_utc                  TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_org_mxtunnels_org_id   ON org_mxtunnels (org_id);
CREATE INDEX IF NOT EXISTS idx_org_mxtunnels_site_id  ON org_mxtunnels (site_id);
CREATE INDEX IF NOT EXISTS idx_org_mxtunnels_name     ON org_mxtunnels (name);
CREATE INDEX IF NOT EXISTS idx_org_mxtunnels_protocol ON org_mxtunnels (protocol);

-- Child table: zero or more rows per mxtunnel.
CREATE TABLE IF NOT EXISTS org_mxtunnel_ipsec_extra_routes (
    mxtunnel_id      TEXT     NOT NULL,
    dest             TEXT     NOT NULL,
    next_hop         TEXT     NOT NULL,
    org_id           TEXT,
    fetched_at_utc   TEXT,
    PRIMARY KEY (mxtunnel_id, dest, next_hop),
    FOREIGN KEY (mxtunnel_id) REFERENCES org_mxtunnels(id)
);

CREATE INDEX IF NOT EXISTS idx_mxtunnel_extra_routes_org_id
    ON org_mxtunnel_ipsec_extra_routes (org_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (two inserts into the dict literal, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Parent mxtunnel record, keyed on the API-supplied UUID.
    'getOrgMxTunnel': {                                                             # operationId from OpenAPI
        'type': 'natural_pk',                                                       # API supplies a stable UUID
        'primary_key': ['id'],                                                      # mxtunnel UUID is globally unique
        'indexes': ['org_id', 'site_id', 'name', 'protocol'],                       # common query filters
        'table': 'org_mxtunnels',                                                   # target SQLite table for the summary row
    },

    # IPSec extra-routes child rows produced from the nested array.
    'getOrgMxTunnelIpsecExtraRoutes': {                                             # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # no per-item ID; key on natural fields
        'primary_key': ['mxtunnel_id', 'dest', 'next_hop'],                         # uniquely identifies one route
        'indexes': ['org_id'],                                                      # org-wide queries across tunnels
        'table': 'org_mxtunnel_ipsec_extra_routes',                                 # target SQLite table for extra routes
    },
}
```

The `getOrgMxTunnelIpsecExtraRoutes` key is a MistHelper-internal identifier (the Mist
API has no operationId for an individual extra route -- it is a flattened sub-array of
the parent response). This pattern matches how MistHelper already splits other
endpoints whose response contains nested arrays.
