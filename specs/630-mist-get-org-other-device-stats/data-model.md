# Phase 1 Data Model: getOrgOtherDeviceStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_stats_otherdevices_device_mac.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing the current stats of one
third-party ("other") device. MistHelper splits this into four logical entities for
clean multi-backend persistence, mirroring the nested-map structure of the response.

### Entity 1: `OtherDeviceStatsSummary`

One row per (org, other-device MAC). Captures top-level device state.

| Field           | Type    | Source                | PK? | FK?          | Notes |
|-----------------|---------|-----------------------|-----|--------------|-------|
| `org_id`        | TEXT    | MistHelper context    | YES | orgs.id      | UUID supplied by user; injected before write. |
| `device_mac`    | TEXT    | MistHelper context    | YES | --           | Path param; normalized to lowercase, 12 hex chars, no separators. |
| `mac`           | TEXT    | API `mac`             | --  | --           | Same MAC as reported by the device itself. Redundant to `device_mac`; kept for audit. |
| `status`        | TEXT    | API `status`          | --  | --           | e.g. `online`, `offline`. |
| `vendor`        | TEXT    | API `vendor`          | --  | --           | e.g. `cradlepoint`. |
| `version`       | TEXT    | API `version`         | --  | --           | Firmware version reported by device. |
| `config_status` | TEXT    | API `config_status`   | --  | --           | e.g. `synced`. |
| `cached_stats`  | INTEGER | API `cached_stats`    | --  | --           | 0/1 boolean -- true when the response came from cache. |
| `lldp_enabled`  | INTEGER | API `lldp_enabled`    | --  | --           | 0/1 boolean. |
| `uptime`        | INTEGER | API `uptime`          | --  | --           | Seconds since device boot. |
| `last_seen`     | REAL    | API `last_seen`       | --  | --           | Epoch seconds, nullable. |
| `last_config`   | INTEGER | API `last_config`     | --  | --           | Epoch seconds. |
| `vendor_target_version` | TEXT | API `vendor_specific.target_version` | -- | -- | Only present when `vendor_specific` is present (e.g. Cradlepoint). |
| `polled_at_utc` | TEXT    | MistHelper clock      | --  | --           | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `OtherDeviceConnectedDevice`

Zero or more rows per (org, other-device MAC). Source: each value of the API
`connected_devices` object (keyed by neighbor MAC).

| Field            | Type | Source                                | PK? | FK?                                       | Notes |
|------------------|------|---------------------------------------|-----|-------------------------------------------|-------|
| `org_id`         | TEXT | MistHelper context                    | YES | org_other_device_stats_summary.org_id     | UUID. |
| `device_mac`     | TEXT | MistHelper context                    | YES | org_other_device_stats_summary.device_mac | Parent device MAC. |
| `connected_mac`  | TEXT | Map key (also API value `mac`)        | YES | --                                        | Neighbor MAC that is directly connected. |
| `connected_name` | TEXT | API `connected_devices.<mac>.name`    | --  | --                                        | Human-readable neighbor name. |
| `connected_type` | TEXT | API `connected_devices.<mac>.type`    | --  | --                                        | e.g. `gateway`, `switch`, `ap`. |
| `port_id`        | TEXT | API `connected_devices.<mac>.port_id` | --  | --                                        | Port on the *other* device that the neighbor is on. |
| `polled_at_utc`  | TEXT | MistHelper clock                      | --  | --                                        | ISO8601 UTC poll timestamp. |

### Entity 3: `OtherDeviceInterface`

Zero or more rows per (org, other-device MAC). Source: each value of the API
`interfaces` object (keyed by interface name).

| Field            | Type    | Source                          | PK? | FK?                                       | Notes |
|------------------|---------|---------------------------------|-----|-------------------------------------------|-------|
| `org_id`         | TEXT    | MistHelper context              | YES | org_other_device_stats_summary.org_id     | UUID. |
| `device_mac`     | TEXT    | MistHelper context              | YES | org_other_device_stats_summary.device_mac | Parent device MAC. |
| `interface_name` | TEXT    | Map key                         | YES | --                                        | e.g. `mdm`, `wan0`. |
| `type`           | TEXT    | API `.type`                     | --  | --                                        | e.g. `mdm`. |
| `mode`           | TEXT    | API `.mode`                     | --  | --                                        | e.g. `wan`. |
| `state`          | TEXT    | API `.state`                    | --  | --                                        | e.g. `READY`. |
| `link`           | INTEGER | API `.link`                     | --  | --                                        | 0/1 boolean. |
| `ip`             | TEXT    | API `.ip`                       | --  | --                                        | IPv4/IPv6 address string. |
| `mtu`            | INTEGER | API `.mtu`                      | --  | --                                        | Interface MTU. |
| `uptime`         | INTEGER | API `.uptime`                   | --  | --                                        | Interface uptime in seconds. |
| `bytes_in`       | INTEGER | API `.bytes_in`                 | --  | --                                        | int64 counter. |
| `bytes_out`      | INTEGER | API `.bytes_out`                | --  | --                                        | int64 counter. |
| `carrier`        | TEXT    | API `.carrier`                  | --  | --                                        | Cellular carrier name (nullable). |
| `imei`           | TEXT    | API `.imei`                     | --  | --                                        | Cellular IMEI (nullable). |
| `imsi`           | TEXT    | API `.imsi`                     | --  | --                                        | Cellular IMSI (nullable). |
| `service_mode`   | TEXT    | API `.service_mode`             | --  | --                                        | e.g. `5G NSA`. |
| `rsrp`           | REAL    | API `.rsrp`                     | --  | --                                        | Cellular signal. |
| `rsrq`           | REAL    | API `.rsrq`                     | --  | --                                        | Cellular signal quality. |
| `rssi`           | INTEGER | API `.rssi`                     | --  | --                                        | Cellular RSSI. |
| `sinr`           | REAL    | API `.sinr`                     | --  | --                                        | Cellular SINR. |
| `polled_at_utc`  | TEXT    | MistHelper clock                | --  | --                                        | ISO8601 UTC poll timestamp. |

### Entity 4: `OtherDeviceVendorInterface`

Zero or more rows per (org, other-device MAC). Source: each value of the API
`vendor_specific.interfaces` object (keyed by vendor port name, e.g.
`mdm-4d0e073b`). Only populated when `vendor_specific` is present in the response
(e.g. `vendor=cradlepoint`).

| Field            | Type    | Source                                     | PK? | FK?                                       | Notes |
|------------------|---------|--------------------------------------------|-----|-------------------------------------------|-------|
| `org_id`         | TEXT    | MistHelper context                         | YES | org_other_device_stats_summary.org_id     | UUID. |
| `device_mac`     | TEXT    | MistHelper context                         | YES | org_other_device_stats_summary.device_mac | Parent device MAC. |
| `port_name`      | TEXT    | Map key                                    | YES | --                                        | e.g. `mdm-4d0e073b`. |
| `display_name`   | TEXT    | API `.display_name`                        | --  | --                                        | Human-readable port label. |
| `port_parent`    | TEXT    | API `.port_parent`                         | --  | --                                        | Parent interface (e.g. `mdm`). |
| `type`           | TEXT    | API `.type`                                | --  | --                                        | e.g. `mdm`. |
| `mode`           | TEXT    | API `.mode`                                | --  | --                                        | e.g. `wan`. |
| `state`          | TEXT    | API `.state`                               | --  | --                                        | e.g. `READY`. |
| `link`           | INTEGER | API `.link`                                | --  | --                                        | 0/1 boolean. |
| `ip`             | TEXT    | API `.ip`                                  | --  | --                                        | IPv4/IPv6 address string. |
| `mtu`            | INTEGER | API `.mtu`                                 | --  | --                                        | MTU. |
| `uptime`         | INTEGER | API `.uptime`                              | --  | --                                        | Seconds. |
| `bytes_in`       | INTEGER | API `.bytes_in`                            | --  | --                                        | int64. |
| `bytes_out`      | INTEGER | API `.bytes_out`                           | --  | --                                        | int64. |
| `carrier`        | TEXT    | API `.carrier`                             | --  | --                                        | Cellular carrier. |
| `imei`           | TEXT    | API `.imei`                                | --  | --                                        | Cellular IMEI. |
| `imsi`           | TEXT    | API `.imsi`                                | --  | --                                        | Cellular IMSI. |
| `service_mode`   | TEXT    | API `.service_mode`                        | --  | --                                        | e.g. `5G NSA`. |
| `rsrp`           | REAL    | API `.rsrp`                                | --  | --                                        | Signal. |
| `rsrq`           | REAL    | API `.rsrq`                                | --  | --                                        | Signal quality. |
| `rssi`           | INTEGER | API `.rssi`                                | --  | --                                        | RSSI. |
| `sinr`           | REAL    | API `.sinr`                                | --  | --                                        | SINR. |
| `polled_at_utc`  | TEXT    | MistHelper clock                           | --  | --                                        | ISO8601 UTC poll timestamp. |

## State Transitions

N/A -- this is a read-only endpoint. The underlying device transitions through
`online`/`offline` and its interfaces move through cellular states like `READY`, but
MistHelper does not drive those transitions; it captures snapshots. Each poll
overwrites the prior snapshot for the same primary key tuple via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Summary table: one row per (org, other-device MAC).
CREATE TABLE IF NOT EXISTS org_other_device_stats_summary (
    org_id                 TEXT     NOT NULL,
    device_mac             TEXT     NOT NULL,
    mac                    TEXT,
    status                 TEXT,
    vendor                 TEXT,
    version                TEXT,
    config_status          TEXT,
    cached_stats           INTEGER,
    lldp_enabled           INTEGER,
    uptime                 INTEGER,
    last_seen              REAL,
    last_config            INTEGER,
    vendor_target_version  TEXT,
    polled_at_utc          TEXT,
    PRIMARY KEY (org_id, device_mac)
);

CREATE INDEX IF NOT EXISTS idx_other_device_stats_summary_status
    ON org_other_device_stats_summary (status);
CREATE INDEX IF NOT EXISTS idx_other_device_stats_summary_vendor
    ON org_other_device_stats_summary (vendor);

-- Connected-devices table: zero or more rows per parent device.
CREATE TABLE IF NOT EXISTS org_other_device_connected_devices (
    org_id          TEXT NOT NULL,
    device_mac      TEXT NOT NULL,
    connected_mac   TEXT NOT NULL,
    connected_name  TEXT,
    connected_type  TEXT,
    port_id         TEXT,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, device_mac, connected_mac),
    FOREIGN KEY (org_id, device_mac)
        REFERENCES org_other_device_stats_summary(org_id, device_mac)
);

CREATE INDEX IF NOT EXISTS idx_other_device_connected_type
    ON org_other_device_connected_devices (connected_type);

-- Interfaces table: zero or more rows per parent device.
CREATE TABLE IF NOT EXISTS org_other_device_interfaces (
    org_id          TEXT NOT NULL,
    device_mac      TEXT NOT NULL,
    interface_name  TEXT NOT NULL,
    type            TEXT,
    mode            TEXT,
    state           TEXT,
    link            INTEGER,
    ip              TEXT,
    mtu             INTEGER,
    uptime          INTEGER,
    bytes_in        INTEGER,
    bytes_out       INTEGER,
    carrier         TEXT,
    imei            TEXT,
    imsi            TEXT,
    service_mode    TEXT,
    rsrp            REAL,
    rsrq            REAL,
    rssi            INTEGER,
    sinr            REAL,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, device_mac, interface_name),
    FOREIGN KEY (org_id, device_mac)
        REFERENCES org_other_device_stats_summary(org_id, device_mac)
);

CREATE INDEX IF NOT EXISTS idx_other_device_interfaces_state
    ON org_other_device_interfaces (state);

-- Vendor-specific interfaces table: zero or more rows per parent device.
CREATE TABLE IF NOT EXISTS org_other_device_vendor_interfaces (
    org_id          TEXT NOT NULL,
    device_mac      TEXT NOT NULL,
    port_name       TEXT NOT NULL,
    display_name    TEXT,
    port_parent     TEXT,
    type            TEXT,
    mode            TEXT,
    state           TEXT,
    link            INTEGER,
    ip              TEXT,
    mtu             INTEGER,
    uptime          INTEGER,
    bytes_in        INTEGER,
    bytes_out       INTEGER,
    carrier         TEXT,
    imei            TEXT,
    imsi            TEXT,
    service_mode    TEXT,
    rsrp            REAL,
    rsrq            REAL,
    rssi            INTEGER,
    sinr            REAL,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, device_mac, port_name),
    FOREIGN KEY (org_id, device_mac)
        REFERENCES org_other_device_stats_summary(org_id, device_mac)
);

CREATE INDEX IF NOT EXISTS idx_other_device_vendor_interfaces_state
    ON org_other_device_vendor_interfaces (state);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not run
the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following four entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Summary row per (org, other-device MAC).
    'getOrgOtherDeviceStats': {                                                     # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['org_id', 'device_mac'],                                    # unique per polled device per org
        'indexes': ['status', 'vendor'],                                            # fast filter by state and vendor
        'table': 'org_other_device_stats_summary',                                  # target SQLite table
    },

    # Per-neighbor rows produced from response.connected_devices map.
    'getOrgOtherDeviceStatsConnectedDevices': {                                     # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of parent + neighbor MAC
        'primary_key': ['org_id', 'device_mac', 'connected_mac'],                   # unique per neighbor per parent
        'indexes': ['connected_type'],                                              # fast filter by neighbor type
        'table': 'org_other_device_connected_devices',                              # target SQLite table
    },

    # Per-interface rows produced from response.interfaces map.
    'getOrgOtherDeviceStatsInterfaces': {                                           # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of parent + interface name
        'primary_key': ['org_id', 'device_mac', 'interface_name'],                  # unique per interface per parent
        'indexes': ['state'],                                                       # fast filter by cellular state
        'table': 'org_other_device_interfaces',                                     # target SQLite table
    },

    # Per-vendor-port rows produced from response.vendor_specific.interfaces map.
    'getOrgOtherDeviceStatsVendorInterfaces': {                                     # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of parent + vendor port
        'primary_key': ['org_id', 'device_mac', 'port_name'],                       # unique per vendor port per parent
        'indexes': ['state'],                                                       # fast filter by port state
        'table': 'org_other_device_vendor_interfaces',                              # target SQLite table
    },
}
```

The three `...ConnectedDevices`, `...Interfaces`, and `...VendorInterfaces` keys are
MistHelper-internal identifiers (the Mist API has no operationId for the sub-arrays
-- they are flattened children of the parent response). This pattern matches how
MistHelper already splits other endpoints whose response contains nested maps.
