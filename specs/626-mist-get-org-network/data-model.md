# Phase 1 Data Model: getOrgNetwork

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_networks_network_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one org-level Network
configuration. MistHelper splits this object into six logical entities so nested
`additionalProperties` maps become first-class SQL rows.

### Entity 1: `OrgNetwork` (parent)

One row per Network object.

| Field                     | Type    | Source                | PK? | FK?           | Notes |
|---------------------------|---------|-----------------------|-----|---------------|-------|
| `id`                      | TEXT    | API `id`              | YES | --            | Network UUID. Server-generated, stable. |
| `org_id`                  | TEXT    | API `org_id` / context| --  | sites.org_id  | Owning org UUID. Injected by MistHelper if the API body omits it. |
| `name`                    | TEXT    | API `name`            | --  | --            | Required by API; human-readable label. |
| `subnet`                  | TEXT    | API `subnet`          | --  | --            | IPv4 CIDR, e.g. `192.168.70.0/24`. |
| `subnet6`                 | TEXT    | API `subnet6`         | --  | --            | IPv6 CIDR. |
| `gateway`                 | TEXT    | API `gateway`         | --  | --            | IPv4 gateway. |
| `gateway6`                | TEXT    | API `gateway6`        | --  | --            | IPv6 gateway. |
| `vlan_id`                 | TEXT    | API `vlan_id`         | --  | --            | Stored as text because the schema allows a numeric literal or a `{{variable}}` reference. |
| `isolation`               | INTEGER | API `isolation`       | --  | --            | 0 / 1 boolean. |
| `disallow_mist_services`  | INTEGER | API `disallow_mist_services` | -- | --      | 0 / 1 boolean, default 0. |
| `routed_for_networks`     | TEXT    | API `routed_for_networks` | -- | --         | JSON-serialized string[] (small list; kept inline for parent readability). |
| `internal_access_enabled` | INTEGER | API `internal_access.enabled` | -- | --      | Flattened scalar from nested object. 0 / 1 or NULL. |
| `internet_access_enabled` | INTEGER | API `internet_access.enabled` | -- | --      | Flattened scalar. |
| `internet_access_restricted` | INTEGER | API `internet_access.restricted` | -- | -- | Flattened scalar; default 0. |
| `internet_access_create_simple_service_policy` | INTEGER | API `internet_access.create_simple_service_policy` | -- | -- | Flattened scalar; default 0. |
| `multicast_enabled`       | INTEGER | API `multicast.enabled`| -- | --            | Flattened scalar; default 0. |
| `multicast_disable_igmp`  | INTEGER | API `multicast.disable_igmp` | -- | --       | Flattened scalar; default 0. |
| `created_time`            | REAL    | API `created_time`    | --  | --            | Epoch seconds, read-only. |
| `modified_time`           | REAL    | API `modified_time`   | --  | --            | Epoch seconds, read-only. |
| `polled_at_utc`           | TEXT    | MistHelper clock      | --  | --            | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `OrgNetworkDestinationNat`

Zero or more rows -- one per key in the `internet_access.destination_nat`
`additionalProperties` map.

| Field           | Type | Source                                         | PK? | FK?                        | Notes |
|-----------------|------|------------------------------------------------|-----|----------------------------|-------|
| `network_id`    | TEXT | Parent `id`                                    | YES | org_network.id             | Joins to parent. |
| `external_key`  | TEXT | Map key (IP / CIDR / port / variable string)   | YES | --                         | Verbatim `additionalProperties` key. |
| `internal_ip`   | TEXT | value `internal_ip`                            | --  | --                         | Destination NAT target IP. |
| `port`          | TEXT | value `port`                                   | --  | --                         | Destination NAT target port. |
| `name`          | TEXT | value `name`                                   | --  | --                         | Human label. |
| `wan_name`      | TEXT | value `wan_name`                               | --  | --                         | SRX-only WAN identifier. |
| `polled_at_utc` | TEXT | MistHelper clock                               | --  | --                         | ISO8601 UTC audit stamp. |

### Entity 3: `OrgNetworkStaticNat`

Zero or more rows -- one per key in the `internet_access.static_nat`
`additionalProperties` map.

| Field           | Type | Source                            | PK? | FK?               | Notes |
|-----------------|------|-----------------------------------|-----|-------------------|-------|
| `network_id`    | TEXT | Parent `id`                       | YES | org_network.id    | Joins to parent. |
| `external_key`  | TEXT | Map key (IP / CIDR / variable)    | YES | --                | Verbatim map key. |
| `internal_ip`   | TEXT | value `internal_ip`               | --  | --                | Static NAT target IP. |
| `name`          | TEXT | value `name`                      | --  | --                | Human label. |
| `wan_name`      | TEXT | value `wan_name`                  | --  | --                | SRX-only WAN identifier. |
| `polled_at_utc` | TEXT | MistHelper clock                  | --  | --                | ISO8601 UTC audit stamp. |

### Entity 4: `OrgNetworkMulticastGroups`

Zero or more rows -- one per key in the `multicast.groups` `additionalProperties` map.

| Field           | Type | Source                    | PK? | FK?              | Notes |
|-----------------|------|---------------------------|-----|------------------|-------|
| `network_id`    | TEXT | Parent `id`               | YES | org_network.id   | Joins to parent. |
| `group_cidr`    | TEXT | Map key (CIDR)            | YES | --               | Multicast group CIDR. |
| `rp_ip`         | TEXT | value `rp_ip`             | --  | --               | Rendezvous-point IP. |
| `polled_at_utc` | TEXT | MistHelper clock          | --  | --               | ISO8601 UTC audit stamp. |

### Entity 5: `OrgNetworkTenants`

Zero or more rows -- one per key in the `tenants` `additionalProperties` map. Each
tenant may declare multiple `addresses`; MistHelper stores the address list as a
JSON-serialized text column (tenant lists are short and kept inline for readability
rather than exploding into a fourth level of tables).

| Field           | Type | Source                     | PK? | FK?              | Notes |
|-----------------|------|----------------------------|-----|------------------|-------|
| `network_id`    | TEXT | Parent `id`                | YES | org_network.id   | Joins to parent. |
| `tenant_name`   | TEXT | Map key                    | YES | --               | User / tenant identifier. |
| `addresses`     | TEXT | value `addresses` list     | --  | --               | JSON-serialized string[]. |
| `polled_at_utc` | TEXT | MistHelper clock           | --  | --               | ISO8601 UTC audit stamp. |

### Entity 6: `OrgNetworkVpnAccess`

Zero or more rows -- one per key in the `vpn_access` `additionalProperties` map. Value
is a rich `network_vpn_access_config` object; scalar fields become columns; the
nested `destination_nat`, `static_nat`, `source_nat`, and `other_vrfs` sub-structures
are JSON-serialized inline (they are almost never queried in isolation and exploding
them would push the design past the 5-Item Rule at hierarchy level 4).

| Field                          | Type    | Source                                            | PK? | FK?              | Notes |
|--------------------------------|---------|---------------------------------------------------|-----|------------------|-------|
| `network_id`                   | TEXT    | Parent `id`                                       | YES | org_network.id   | Joins to parent. |
| `vpn_name`                     | TEXT    | Map key                                           | YES | --               | VPN identifier. |
| `routed`                       | INTEGER | value `routed`                                    | --  | --               | 0 / 1 boolean. |
| `allow_ping`                   | INTEGER | value `allow_ping`                                | --  | --               | 0 / 1 boolean. |
| `advertised_subnet`            | TEXT    | value `advertised_subnet`                         | --  | --               | Aggregated CIDR toward HUB. |
| `nat_pool`                     | TEXT    | value `nat_pool`                                  | --  | --               | Subnet advertised to Hub for reachability. |
| `summarized_subnet`            | TEXT    | value `summarized_subnet`                         | --  | --               | Overlay summarization. |
| `summarized_subnet_to_lan_bgp` | TEXT    | value `summarized_subnet_to_lan_bgp`              | --  | --               | LAN BGP summarization. |
| `summarized_subnet_to_lan_ospf`| TEXT    | value `summarized_subnet_to_lan_ospf`             | --  | --               | LAN OSPF summarization. |
| `no_readvertise_to_overlay`    | INTEGER | value `no_readvertise_to_overlay`                 | --  | --               | Overlay re-advertise gate. |
| `no_readvertise_to_lan_bgp`    | INTEGER | value `no_readvertise_to_lan_bgp`                 | --  | --               | LAN BGP re-advertise gate. |
| `no_readvertise_to_lan_ospf`   | INTEGER | value `no_readvertise_to_lan_ospf`                | --  | --               | LAN OSPF re-advertise gate. |
| `source_nat_external_ip`       | TEXT    | value `source_nat.external_ip`                    | --  | --               | Flattened scalar. |
| `other_vrfs`                   | TEXT    | value `other_vrfs` list                           | --  | --               | JSON-serialized string[]. |
| `destination_nat_json`         | TEXT    | value `destination_nat` map                       | --  | --               | JSON-serialized nested map. |
| `static_nat_json`              | TEXT    | value `static_nat` map                            | --  | --               | JSON-serialized nested map. |
| `polled_at_utc`                | TEXT    | MistHelper clock                                  | --  | --               | ISO8601 UTC audit stamp. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying Mist Network object may be edited
via the PUT sibling endpoint, but MistHelper does not model those transitions here. Each
poll overwrites the prior snapshot for the same primary key via SQLite
`INSERT OR REPLACE`, so the local store always reflects the last observed state.

## SQLite DDL

```sql
-- Parent table: one row per Network object.
CREATE TABLE IF NOT EXISTS org_network (
    id                                             TEXT NOT NULL,
    org_id                                         TEXT,
    name                                           TEXT,
    subnet                                         TEXT,
    subnet6                                        TEXT,
    gateway                                        TEXT,
    gateway6                                       TEXT,
    vlan_id                                        TEXT,
    isolation                                      INTEGER,
    disallow_mist_services                         INTEGER,
    routed_for_networks                            TEXT,
    internal_access_enabled                        INTEGER,
    internet_access_enabled                        INTEGER,
    internet_access_restricted                     INTEGER,
    internet_access_create_simple_service_policy   INTEGER,
    multicast_enabled                              INTEGER,
    multicast_disable_igmp                         INTEGER,
    created_time                                   REAL,
    modified_time                                  REAL,
    polled_at_utc                                  TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_org_network_org_id ON org_network (org_id);
CREATE INDEX IF NOT EXISTS idx_org_network_name   ON org_network (name);

-- Child: destination NAT entries under internet_access.destination_nat.
CREATE TABLE IF NOT EXISTS org_network_destination_nat (
    network_id     TEXT NOT NULL,
    external_key   TEXT NOT NULL,
    internal_ip    TEXT,
    port           TEXT,
    name           TEXT,
    wan_name       TEXT,
    polled_at_utc  TEXT,
    PRIMARY KEY (network_id, external_key),
    FOREIGN KEY (network_id) REFERENCES org_network(id)
);

-- Child: static NAT entries under internet_access.static_nat.
CREATE TABLE IF NOT EXISTS org_network_static_nat (
    network_id     TEXT NOT NULL,
    external_key   TEXT NOT NULL,
    internal_ip    TEXT,
    name           TEXT,
    wan_name       TEXT,
    polled_at_utc  TEXT,
    PRIMARY KEY (network_id, external_key),
    FOREIGN KEY (network_id) REFERENCES org_network(id)
);

-- Child: multicast groups under multicast.groups.
CREATE TABLE IF NOT EXISTS org_network_multicast_groups (
    network_id     TEXT NOT NULL,
    group_cidr     TEXT NOT NULL,
    rp_ip          TEXT,
    polled_at_utc  TEXT,
    PRIMARY KEY (network_id, group_cidr),
    FOREIGN KEY (network_id) REFERENCES org_network(id)
);

-- Child: tenant entries under tenants.
CREATE TABLE IF NOT EXISTS org_network_tenants (
    network_id     TEXT NOT NULL,
    tenant_name    TEXT NOT NULL,
    addresses      TEXT,
    polled_at_utc  TEXT,
    PRIMARY KEY (network_id, tenant_name),
    FOREIGN KEY (network_id) REFERENCES org_network(id)
);

-- Child: VPN access entries under vpn_access.
CREATE TABLE IF NOT EXISTS org_network_vpn_access (
    network_id                       TEXT NOT NULL,
    vpn_name                         TEXT NOT NULL,
    routed                           INTEGER,
    allow_ping                       INTEGER,
    advertised_subnet                TEXT,
    nat_pool                         TEXT,
    summarized_subnet                TEXT,
    summarized_subnet_to_lan_bgp     TEXT,
    summarized_subnet_to_lan_ospf    TEXT,
    no_readvertise_to_overlay        INTEGER,
    no_readvertise_to_lan_bgp        INTEGER,
    no_readvertise_to_lan_ospf       INTEGER,
    source_nat_external_ip           TEXT,
    other_vrfs                       TEXT,
    destination_nat_json             TEXT,
    static_nat_json                  TEXT,
    polled_at_utc                    TEXT,
    PRIMARY KEY (network_id, vpn_name),
    FOREIGN KEY (network_id) REFERENCES org_network(id)
);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following six entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert into the dict literal, no structural
change). The parent `getOrgNetwork` entry aligns with the existing `listOrgNetworks`
entry at MistHelper.py:4727 so both writers share the same `org_network` table.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Parent Network object, keyed by Mist-assigned UUID.
    "getOrgNetwork": {                                                              # operationId from OpenAPI
        "type": "natural_pk",                                                       # stable server-assigned UUID
        "primary_key": ["id"],                                                      # single-column natural key
        "indexes": ["org_id", "name"],                                              # match listOrgNetworks index set
        "unique_constraints": [],                                                   # no additional uniqueness required
        "description": "Organization network definition (by ID)",                   # human-readable purpose
        "table": "org_network",                                                     # shared with listOrgNetworks writer
    },

    # Child: internet_access.destination_nat map, one row per external key.
    "getOrgNetworkDestinationNat": {                                                # MistHelper-internal sub-table id
        "type": "composite_pk",                                                     # composite of parent FK + map key
        "primary_key": ["network_id", "external_key"],                              # uniquely identifies a NAT row
        "indexes": ["network_id"],                                                  # accelerate join back to parent
        "unique_constraints": [],                                                   # PK already enforces uniqueness
        "description": "Per-network destination NAT entries",                       # human-readable purpose
        "table": "org_network_destination_nat",                                     # target SQLite table
    },

    # Child: internet_access.static_nat map, one row per external key.
    "getOrgNetworkStaticNat": {                                                     # MistHelper-internal sub-table id
        "type": "composite_pk",                                                     # composite of parent FK + map key
        "primary_key": ["network_id", "external_key"],                              # uniquely identifies a static NAT row
        "indexes": ["network_id"],                                                  # accelerate join back to parent
        "unique_constraints": [],                                                   # PK already enforces uniqueness
        "description": "Per-network static NAT entries",                            # human-readable purpose
        "table": "org_network_static_nat",                                          # target SQLite table
    },

    # Child: multicast.groups map, one row per group CIDR.
    "getOrgNetworkMulticastGroups": {                                               # MistHelper-internal sub-table id
        "type": "composite_pk",                                                     # composite of parent FK + group cidr
        "primary_key": ["network_id", "group_cidr"],                                # uniquely identifies a multicast group
        "indexes": ["network_id"],                                                  # accelerate join back to parent
        "unique_constraints": [],                                                   # PK already enforces uniqueness
        "description": "Per-network multicast group -> RP mappings",                # human-readable purpose
        "table": "org_network_multicast_groups",                                    # target SQLite table
    },

    # Child: tenants map, one row per tenant name.
    "getOrgNetworkTenants": {                                                       # MistHelper-internal sub-table id
        "type": "composite_pk",                                                     # composite of parent FK + tenant name
        "primary_key": ["network_id", "tenant_name"],                               # uniquely identifies a tenant row
        "indexes": ["network_id"],                                                  # accelerate join back to parent
        "unique_constraints": [],                                                   # PK already enforces uniqueness
        "description": "Per-network tenant address lists",                          # human-readable purpose
        "table": "org_network_tenants",                                             # target SQLite table
    },

    # Child: vpn_access map, one row per VPN name.
    "getOrgNetworkVpnAccess": {                                                     # MistHelper-internal sub-table id
        "type": "composite_pk",                                                     # composite of parent FK + vpn name
        "primary_key": ["network_id", "vpn_name"],                                  # uniquely identifies a VPN access row
        "indexes": ["network_id"],                                                  # accelerate join back to parent
        "unique_constraints": [],                                                   # PK already enforces uniqueness
        "description": "Per-network VPN access configurations",                     # human-readable purpose
        "table": "org_network_vpn_access",                                          # target SQLite table
    },
}
```

The five `getOrgNetwork*` child keys are MistHelper-internal identifiers -- the Mist
API has no operationId for the sub-arrays. This pattern matches how MistHelper already
splits other endpoints whose response contains nested `additionalProperties` maps.
