# Phase 1 Data Model: getOrgMxEdgeCluster

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) |
**Research**: [research.md](./research.md)

This document enumerates the entities returned by
`GET /api/v1/orgs/{org_id}/mxclusters/{mxcluster_id}`, the SQLite DDL used
to persist them via `DataExporter`, and the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry that governs upserts.

---

## Entity: MxCluster (top-level)

The endpoint returns exactly one `MxCluster` object. There are no parent
entities to dereference and no child collections that warrant separate
tables; nested configuration objects and arrays are JSON-encoded into a
single column each so the row stays flat for CSV consumers while remaining
queryable from SQLite via `json_extract()`.

### Fields

| Field | Type | Source | Notes |
|---|---|---|---|
| `id` | TEXT (UUID) | response.id | **Primary key**. Stable per Mist org; readOnly. |
| `org_id` | TEXT (UUID) | response.org_id | Foreign key to `org`. readOnly. |
| `site_id` | TEXT (UUID, nullable) | response.site_id | Foreign key to `site` (when cluster is site-scoped). readOnly. |
| `for_site` | INTEGER (0/1) | response.for_site | Boolean flag, readOnly. |
| `name` | TEXT | response.name | Human-readable cluster name. |
| `created_time` | REAL | response.created_time | Epoch seconds, readOnly. |
| `modified_time` | REAL | response.modified_time | Epoch seconds, readOnly. |
| `tunterm_monitoring_disabled` | INTEGER (0/1) | response.tunterm_monitoring_disabled | Boolean flag. |
| `mist_das_json` | TEXT (JSON) | response.mist_das | Cloud-assisted dynamic authorization config (CoA servers + enabled flag). |
| `mist_nac_json` | TEXT (JSON) | response.mist_nac | NAC config (acct/auth ports, client_ips map, enabled, secret -- **redacted** in logs). |
| `mxedge_mgmt_json` | TEXT (JSON) | response.mxedge_mgmt | Management config (oob_ip_type, fips_enabled, mist_password, root_password -- **redacted** in logs). |
| `proxy_json` | TEXT (JSON) | response.proxy | Proxy disabled flag + url. |
| `radsec_json` | TEXT (JSON) | response.radsec | RadSec config (auth_servers, acct_servers, proxy_hosts, etc.). Server secrets **redacted** in logs. |
| `radsec_tls_json` | TEXT (JSON) | response.radsec_tls | TLS keypair reference. |
| `tunterm_ap_subnets_json` | TEXT (JSON) | response.tunterm_ap_subnets | Array of CIDR strings. |
| `tunterm_dhcpd_config_json` | TEXT (JSON) | response.tunterm_dhcpd_config | DHCP server/relay map keyed by VLAN id. |
| `tunterm_extra_routes_json` | TEXT (JSON) | response.tunterm_extra_routes | Routes map keyed by CIDR. |
| `tunterm_hosts_json` | TEXT (JSON) | response.tunterm_hosts | Array of hostnames/IPs. |
| `tunterm_hosts_order_json` | TEXT (JSON) | response.tunterm_hosts_order | Array of integer indexes into tunterm_hosts. |
| `tunterm_hosts_selection` | TEXT | response.tunterm_hosts_selection | Enum: `shuffle`, `shuffle-by-site`, `ordered`. |
| `tunterm_monitoring_json` | TEXT (JSON) | response.tunterm_monitoring | Array-of-arrays of monitoring probes. |
| `misthelper_fetched_at` | REAL | local | Epoch seconds, set by MistHelper at write time. Useful for cache-age reasoning. |

### Primary Key

`id` (UUID), single column. Upserts via `INSERT OR REPLACE`.

### Foreign Keys (logical, not enforced by SQLite)

- `org_id` -> `org_inventory.id` (when an org row exists from a prior
  org-list export).
- `site_id` -> `sites.id` (when site-scoped and a site row exists).

### State Transitions

**N/A -- read-only endpoint.** Each invocation overwrites the existing row
by primary key. The MxCluster state machine lives on the Mist Cloud side
(via PUT/PATCH/DELETE on the same path); MistHelper only observes it.

---

## SQLite DDL

```sql
CREATE TABLE IF NOT EXISTS org_mx_edge_cluster (
    id                              TEXT    PRIMARY KEY,
    org_id                          TEXT    NOT NULL,
    site_id                         TEXT,
    for_site                        INTEGER DEFAULT 0,
    name                            TEXT,
    created_time                    REAL,
    modified_time                   REAL,
    tunterm_monitoring_disabled     INTEGER DEFAULT 0,
    mist_das_json                   TEXT,
    mist_nac_json                   TEXT,
    mxedge_mgmt_json                TEXT,
    proxy_json                      TEXT,
    radsec_json                     TEXT,
    radsec_tls_json                 TEXT,
    tunterm_ap_subnets_json         TEXT,
    tunterm_dhcpd_config_json       TEXT,
    tunterm_extra_routes_json       TEXT,
    tunterm_hosts_json              TEXT,
    tunterm_hosts_order_json        TEXT,
    tunterm_hosts_selection         TEXT,
    tunterm_monitoring_json         TEXT,
    misthelper_fetched_at           REAL
);

CREATE INDEX IF NOT EXISTS idx_org_mx_edge_cluster_org_id
    ON org_mx_edge_cluster (org_id);

CREATE INDEX IF NOT EXISTS idx_org_mx_edge_cluster_site_id
    ON org_mx_edge_cluster (site_id);

CREATE INDEX IF NOT EXISTS idx_org_mx_edge_cluster_name
    ON org_mx_edge_cluster (name);
```

The DDL is emitted by `DataExporter` on first write -- MistHelper does
not require a separate migration step. The `_json` columns hold the
nested objects verbatim so future read paths can use SQLite's JSON1
extension (`json_extract(radsec_json, '$.auth_servers[0].host')` etc.)
without an alteration.

---

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the dictionary near the existing
`listOrgMxEdgeClusters` entry (currently at approximately line 3971 of
`MistHelper.py`, inside the `# -- Edge Infrastructure ---` block):

```python
"getOrgMxEdgeCluster": {                                    # Single-cluster fetch by id.
    "type": "natural_pk",                                   # Stable UUID supplied by Mist Cloud.
    "primary_key": ["id"],                                  # MxCluster.id is unique within org.
    "indexes": ["org_id", "site_id", "name"],               # Common lookup paths.
    "unique_constraints": [],                               # No additional uniqueness needed.
    "description": "Single Org MxEdge cluster configuration record",
},
```

Inline comments are mandatory per Constitution VI; the example above
shows the expected comment density.

---

## Cross-Reference

- The list endpoint counterpart (`listOrgMxEdgeClusters`) already exists
  in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with `type: natural_pk` /
  `primary_key: ["id"]`. The two endpoints describe the *same logical
  entity* but with different field depth (list returns trimmed rows,
  single-fetch returns full config). The decision in `research.md` Task
  3 keeps the two endpoints in *distinct tables* so a list-fetch never
  silently overwrites the richer single-fetch row.

- The related `getOrgMxEdge` entry (~line 5203) covers a different entity
  (an MxEdge appliance, not an MxCluster); the two should not be
  conflated.
