# Phase 1 Data Model: getOrgEvpnTopology

## Overview

The endpoint returns a single `EvpnTopology` JSON object whose required field is
`switches[]` -- a list of `EvpnTopologySwitch` records that map physical switch
MACs to their fabric role, pod assignment, and EVPN VxLAN identifiers. The
object also embeds three nested configuration blocks: `evpn_options` (overlay /
underlay BGP parameters), `pod_names` (free-form labels keyed by pod number),
and `switch_configs` (per-MAC override map of `switch_network` and
`dhcpd_config`). The model below normalises this into two relational entities
suitable for SQLite upsert and ArangoDB vertex/edge creation.

State transitions: **N/A -- read-only endpoint.** The Mist Cloud is the system
of record; MistHelper only reads and projects the state into the local backends.

## Entity 1: `EvpnTopology` (header)

One row per topology fetched.

| Field             | Type    | Notes                                                                |
|-------------------|---------|----------------------------------------------------------------------|
| `id`              | TEXT    | UUID, primary key (Mist-assigned, stable).                           |
| `org_id`          | TEXT    | UUID, foreign key to `org`.                                          |
| `site_id`         | TEXT    | UUID, foreign key to `sites.id`. Nullable for org-level topologies.  |
| `name`            | TEXT    | Human label.                                                         |
| `created_time`    | REAL    | Epoch seconds (Mist returns `number`).                               |
| `modified_time`   | REAL    | Epoch seconds.                                                       |
| `overwrite`       | INTEGER | 0/1. Maps the JSON `overwrite` boolean.                              |
| `evpn_options_json` | TEXT  | JSON blob of the full `evpn_options` sub-object (overlay/underlay).  |
| `pod_names_json`  | TEXT    | JSON blob of the `pod_names` map (`{"1":"Spine","2":"Leaf"}`).       |
| `switch_configs_json` | TEXT | JSON blob of the `switch_configs` map (per-MAC overrides).          |
| `switch_count`    | INTEGER | Derived: `len(switches)`. Lets operators filter empty topologies.    |

**Primary key**: `id` (natural).
**Foreign keys**: `org_id` -> Mist org (logical), `site_id` -> `sites.id` when
populated.

## Entity 2: `EvpnTopologySwitch` (detail, one row per switch)

One row per element of the response `switches[]` array.

| Field                 | Type    | Notes                                                          |
|-----------------------|---------|----------------------------------------------------------------|
| `evpn_topology_id`    | TEXT    | UUID, foreign key to `org_evpn_topology.id`.                   |
| `mac`                 | TEXT    | Device MAC address (12-char lowercase hex, no separators).     |
| `role`                | TEXT    | One of `core`, `distribution`, `access`, `esilag-access`, etc. |
| `pod`                 | INTEGER | Pod number (`switches[].pod`). Nullable.                       |
| `pods_json`           | TEXT    | JSON array of pod numbers (`switches[].pods`). Nullable.       |
| `evpn_id`             | INTEGER | EVPN VxLAN identifier (`switches[].evpn_id`). Nullable.        |
| `site_id`             | TEXT    | UUID; nullable.                                                |
| `dhcpd_enabled`       | INTEGER | 0/1; derived from `switch_configs[mac].dhcpd_config.enabled`.  |
| `networks_json`       | TEXT    | JSON blob of `switch_configs[mac].networks` (per-VLAN).        |
| `raw_switch_config_json` | TEXT | Full `switch_configs[mac]` blob for forensics.                |

**Primary key**: composite `(evpn_topology_id, mac)`.
**Foreign keys**: `evpn_topology_id` -> `org_evpn_topology.id`.

## SQLite DDL

```sql
-- Header table (one row per fetched EVPN topology).
CREATE TABLE IF NOT EXISTS org_evpn_topology (
    id                    TEXT PRIMARY KEY,
    org_id                TEXT NOT NULL,
    site_id               TEXT,
    name                  TEXT,
    created_time          REAL,
    modified_time         REAL,
    overwrite             INTEGER,
    evpn_options_json     TEXT,
    pod_names_json        TEXT,
    switch_configs_json   TEXT,
    switch_count          INTEGER
);
CREATE INDEX IF NOT EXISTS idx_org_evpn_topology_org_id   ON org_evpn_topology(org_id);
CREATE INDEX IF NOT EXISTS idx_org_evpn_topology_site_id  ON org_evpn_topology(site_id);
CREATE INDEX IF NOT EXISTS idx_org_evpn_topology_name     ON org_evpn_topology(name);

-- Detail table (one row per switch in the topology).
CREATE TABLE IF NOT EXISTS org_evpn_topology_switches (
    evpn_topology_id        TEXT NOT NULL,
    mac                     TEXT NOT NULL,
    role                    TEXT,
    pod                     INTEGER,
    pods_json               TEXT,
    evpn_id                 INTEGER,
    site_id                 TEXT,
    dhcpd_enabled           INTEGER,
    networks_json           TEXT,
    raw_switch_config_json  TEXT,
    PRIMARY KEY (evpn_topology_id, mac),
    FOREIGN KEY (evpn_topology_id) REFERENCES org_evpn_topology(id)
);
CREATE INDEX IF NOT EXISTS idx_org_evpn_topology_switches_mac  ON org_evpn_topology_switches(mac);
CREATE INDEX IF NOT EXISTS idx_org_evpn_topology_switches_role ON org_evpn_topology_switches(role);
CREATE INDEX IF NOT EXISTS idx_org_evpn_topology_switches_pod  ON org_evpn_topology_switches(pod);
```

`INSERT OR REPLACE` (the standard upsert verb already used by `DataExporter`
for `natural_pk` and `composite_pk` strategies) keeps repeated runs idempotent.

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries

Two entries are required -- one per output table. Both are added beside the
existing `listOrgEvpnTopologies` entry in `MistHelper.py` (~line 3944) so
related strategies stay co-located.

```python
"getOrgEvpnTopology": {
    "type": "natural_pk",                                  # Mist-assigned UUID is stable across runs
    "primary_key": ["id"],                                 # Single-column PK on the topology UUID
    "indexes": ["org_id", "site_id", "name"],              # Common operator query axes
    "unique_constraints": [],                              # No additional uniqueness beyond the PK
    "description": "Single Org EVPN topology detail (header row)",
},
"getOrgEvpnTopology_switches": {
    "type": "composite_pk",                                # Per-switch rows scoped to their parent topology
    "primary_key": ["evpn_topology_id", "mac"],            # Each switch appears at most once per topology
    "indexes": ["mac", "role", "pod"],                     # Operators slice by MAC, fabric role, and pod
    "unique_constraints": [],                              # Composite PK already enforces uniqueness
    "description": "Per-switch detail rows for one EVPN topology",
},
```

The synthetic `getOrgEvpnTopology_switches` operationId (suffix `_switches`)
follows the same pattern spec 500 introduced for its rollup -- it is never sent
to the Mist API, it only carries the PK strategy into `DataExporter`.
