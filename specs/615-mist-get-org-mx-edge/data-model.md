# Phase 1 Data Model: getOrgMxEdge

**Feature**: 615-mist-get-org-mx-edge | **Date**: 2026-06-30
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Contract**: [contracts/get_org_mx_edge.md](./contracts/get_org_mx_edge.md)

## Entities Returned by the Endpoint

The `GET /api/v1/orgs/{org_id}/mxedges/{mxedge_id}` endpoint returns exactly **one
entity** per call: a single `MxEdge` record. The record contains primitive scalars at
the top level and several nested configuration objects, which the MistHelper
`flatten_dict()` helper unrolls into dot-keyed columns
(e.g. `oob_ip_config.ip`, `tunterm_ip_config.netmask`).

### Primary Entity: `MxEdge` (table `org_mxedge_detail`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | TEXT (UUID) | **PRIMARY KEY**. Stable Mist-issued identifier (`readOnly`). |
| `org_id` | TEXT (UUID) | **FK -> sites/orgs.id** (logical). Owning organization (`readOnly`). |
| `site_id` | TEXT (UUID) NULL | **FK -> sites.id** (logical). Owning site when `for_site=true`. |
| `mxcluster_id` | TEXT (UUID) NULL | **FK -> org_mxedge_clusters.id** (logical). Cluster the edge belongs to. |
| `name` | TEXT | Required by API. Display name (e.g. `Guest`). |
| `model` | TEXT | Required by API. Hardware/virtual model (e.g. `ME-100`). |
| `mac` | TEXT | Edge MAC, formatted `0200009fbe65` (`readOnly`). |
| `for_site` | INTEGER (bool) | 1 if the edge is site-scoped (`readOnly`). |
| `mxagent_registered` | INTEGER (bool) | 1 if the MxAgent has registered (`readOnly`). |
| `tunterm_registered` | INTEGER (bool) | 1 if tunterm has registered (`readOnly`). |
| `created_time` | REAL (epoch s) | Creation timestamp (`readOnly`). |
| `modified_time` | REAL (epoch s) | Last-modified timestamp (`readOnly`). |
| `note` | TEXT NULL | Operator note. |
| `services` | TEXT (JSON) | JSON-encoded array (e.g. `["tunterm"]`). |
| `ntp_servers` | TEXT (JSON) | JSON-encoded array (unique strings). |
| `versions.mxagent` | TEXT NULL | MxAgent version string (`readOnly`). |
| `versions.tunterm` | TEXT NULL | tunterm version string (`readOnly`). |
| `magic` | TEXT NULL | **REDACTED** before storage / logging. |
| `mxedge_mgmt.fips_enabled` | INTEGER (bool) NULL | |
| `mxedge_mgmt.config_auto_revert` | INTEGER (bool) NULL | |
| `mxedge_mgmt.oob_ip_type` | TEXT NULL | enum: `dhcp`, `disabled`, `static`. |
| `mxedge_mgmt.oob_ip_type6` | TEXT NULL | enum: `autoconf`, `dhcp`, `disabled`, `static`. |
| `mxedge_mgmt.mist_password` | TEXT NULL | **REDACTED**. |
| `mxedge_mgmt.root_password` | TEXT NULL | **REDACTED**. |
| `oob_ip_config.type` | TEXT NULL | enum: `dhcp`, `static`. |
| `oob_ip_config.ip` | TEXT NULL | IPv4 when `type=static`. |
| `oob_ip_config.netmask` | TEXT NULL | |
| `oob_ip_config.gateway` | TEXT NULL | |
| `oob_ip_config.dns` | TEXT (JSON) NULL | Array of DNS server strings. |
| `oob_ip_config.type6` | TEXT NULL | enum: `dhcp`, `static`. |
| `oob_ip_config.ip6` | TEXT NULL | |
| `oob_ip_config.netmask6` | TEXT NULL | |
| `oob_ip_config.gateway6` | TEXT NULL | |
| `oob_ip_config.dhcp6` | INTEGER (bool) NULL | |
| `oob_ip_config.autoconf6` | INTEGER (bool) NULL | |
| `proxy.disabled` | INTEGER (bool) NULL | |
| `proxy.url` | TEXT NULL | |
| `tunterm_ip_config.ip` | TEXT NULL | Required when tunterm enabled. |
| `tunterm_ip_config.netmask` | TEXT NULL | Required when tunterm enabled. |
| `tunterm_ip_config.gateway` | TEXT NULL | Required when tunterm enabled. |
| `tunterm_ip_config.ip6` | TEXT NULL | |
| `tunterm_ip_config.netmask6` | TEXT NULL | |
| `tunterm_ip_config.gateway6` | TEXT NULL | |
| `tunterm_port_config.separate_upstream_downstream` | INTEGER (bool) NULL | |
| `tunterm_port_config.upstream_ports` | TEXT (JSON) NULL | |
| `tunterm_port_config.downstream_ports` | TEXT (JSON) NULL | |
| `tunterm_port_config.upstream_port_vlan_id` | TEXT (JSON) NULL | |
| `tunterm_switch_config.enabled` | INTEGER (bool) NULL | |
| `tunterm_dhcpd_config` | TEXT (JSON) NULL | Free-form object keyed by VLAN ID. |
| `tunterm_extra_routes` | TEXT (JSON) NULL | Free-form object keyed by CIDR. |
| `tunterm_igmp_snooping_config` | TEXT (JSON) NULL | Nested object incl. querier + vlans. |
| `tunterm_multicast_config` | TEXT (JSON) NULL | Nested mdns + ssdp object. |
| `tunterm_other_ip_configs` | TEXT (JSON) NULL | Free-form object keyed by VLAN ID. |
| `tunterm_monitoring` | TEXT (JSON) NULL | Array-of-arrays of monitoring items. |

### Relationships

- `org_mxedge_detail.org_id` (logical FK) -> `org_sites.org_id` (existing tables).
- `org_mxedge_detail.site_id` (logical FK, nullable) -> `org_sites.id`.
- `org_mxedge_detail.mxcluster_id` (logical FK) -> `org_mxedge_clusters.id` (table
  managed by `listOrgMxEdgeClusters`).
- `org_mxedge_detail.id` is also referenced by `org_mxedges.id` from the bulk listing
  (same UUID space) -- the two tables are complementary views of the same logical
  entity.

### State Transitions

**N/A -- read-only endpoint.** This GET only observes existing state; it never mutates
the MxEdge. Repeated calls return the current snapshot, which the SQLite upsert path
overwrites in place (no history is preserved by this menu item). State transitions on
the upstream resource (registration, upgrade, config push) are tracked by other
endpoints already cataloged: `listOrgMxEdgeUpgrades`, `searchOrgMxEdges`,
`getOrgMxEdgeUpgradeInfo`.

## SQLite DDL Snippet

The table is created on first run by `DataExporter.write_with_format_selection()`
using the primary-key strategy. Equivalent explicit DDL:

```sql
CREATE TABLE IF NOT EXISTS org_mxedge_detail (
    id                                              TEXT PRIMARY KEY NOT NULL,
    org_id                                          TEXT NOT NULL,
    site_id                                         TEXT,
    mxcluster_id                                    TEXT,
    name                                            TEXT NOT NULL,
    model                                           TEXT NOT NULL,
    mac                                             TEXT,
    for_site                                        INTEGER,
    mxagent_registered                              INTEGER,
    tunterm_registered                              INTEGER,
    created_time                                    REAL,
    modified_time                                   REAL,
    note                                            TEXT,
    services                                        TEXT,
    ntp_servers                                     TEXT,
    "versions.mxagent"                              TEXT,
    "versions.tunterm"                              TEXT,
    "mxedge_mgmt.fips_enabled"                      INTEGER,
    "mxedge_mgmt.config_auto_revert"                INTEGER,
    "mxedge_mgmt.oob_ip_type"                       TEXT,
    "mxedge_mgmt.oob_ip_type6"                      TEXT,
    "oob_ip_config.type"                            TEXT,
    "oob_ip_config.ip"                              TEXT,
    "oob_ip_config.netmask"                         TEXT,
    "oob_ip_config.gateway"                         TEXT,
    "oob_ip_config.dns"                             TEXT,
    "oob_ip_config.type6"                           TEXT,
    "oob_ip_config.ip6"                             TEXT,
    "oob_ip_config.netmask6"                        TEXT,
    "oob_ip_config.gateway6"                        TEXT,
    "oob_ip_config.dhcp6"                           INTEGER,
    "oob_ip_config.autoconf6"                       INTEGER,
    "proxy.disabled"                                INTEGER,
    "proxy.url"                                     TEXT,
    "tunterm_ip_config.ip"                          TEXT,
    "tunterm_ip_config.netmask"                     TEXT,
    "tunterm_ip_config.gateway"                     TEXT,
    "tunterm_ip_config.ip6"                         TEXT,
    "tunterm_ip_config.netmask6"                    TEXT,
    "tunterm_ip_config.gateway6"                    TEXT,
    "tunterm_port_config.separate_upstream_downstream" INTEGER,
    "tunterm_port_config.upstream_ports"            TEXT,
    "tunterm_port_config.downstream_ports"          TEXT,
    "tunterm_port_config.upstream_port_vlan_id"     TEXT,
    "tunterm_switch_config.enabled"                 INTEGER,
    tunterm_dhcpd_config                            TEXT,
    tunterm_extra_routes                            TEXT,
    tunterm_igmp_snooping_config                    TEXT,
    tunterm_multicast_config                        TEXT,
    tunterm_other_ip_configs                        TEXT,
    tunterm_monitoring                              TEXT
);

CREATE INDEX IF NOT EXISTS idx_org_mxedge_detail_org_id       ON org_mxedge_detail(org_id);
CREATE INDEX IF NOT EXISTS idx_org_mxedge_detail_mxcluster_id ON org_mxedge_detail(mxcluster_id);
CREATE INDEX IF NOT EXISTS idx_org_mxedge_detail_site_id      ON org_mxedge_detail(site_id);
CREATE INDEX IF NOT EXISTS idx_org_mxedge_detail_mac          ON org_mxedge_detail(mac);
CREATE INDEX IF NOT EXISTS idx_org_mxedge_detail_name         ON org_mxedge_detail(name);
```

Upsert semantics: `INSERT OR REPLACE` keyed on `id`, supplied by
`DataExporter.write_with_format_selection()` based on the `natural_pk` strategy
registered below.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (line
~1672, alongside `listOrgMxEdges` at line ~4685):

```python
"getOrgMxEdge": {                                          # operationId from the OpenAPI spec
    "type": "natural_pk",                                  # MxEdge has a stable Mist UUID
    "primary_key": ["id"],                                 # response field "id" is the UUID PK
    "indexes": [                                           # cover the common filter columns
        "org_id",
        "mxcluster_id",
        "site_id",
        "mac",
        "name",
    ],
    "description": "Single MxEdge appliance detail record",
},
```

## Redaction Rules (applied before logging and before flatten)

The following fields are stripped from the in-memory record before logging and before
the `DataExporter` call, replaced with the literal string `"<redacted>"`:

- `magic`
- `mxedge_mgmt.mist_password`
- `mxedge_mgmt.root_password`

This satisfies Constitution Principle V (Observability & Logging) and the spec's
non-functional security requirement (`API token loaded from .env; never logged`,
extended here to all credential-like fields in the response).

## Notes on Polyglot Backends

- **CSV**: `data/OrgMxEdgeDetail.csv` -- one row per call. Columns mirror the flattened
  keys above; complex sub-objects survive as JSON-encoded strings.
- **SQLite**: `data/mist_data.db` table `org_mxedge_detail` per DDL above. Upsert by
  `id`.
- **ArangoDB**: collection `org_mxedge_detail`, primary key `_key = id`. Optional
  graph edges to existing collections `org_sites` and `org_mxedge_clusters` are
  created when the polyglot graph mode is enabled (out of scope for this menu item,
  handled centrally by `DataExporter`).
- **Redis**: cache key `org_mxedge_detail:<id>` with TTL governed by the existing
  shared cache config (default 1 hour for read-only org metadata).
