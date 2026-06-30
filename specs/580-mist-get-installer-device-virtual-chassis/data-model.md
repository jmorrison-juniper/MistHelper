# Phase 1 Data Model: getInstallerDeviceVirtualChassis

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

## Entities

The endpoint returns a single composite JSON object representing one Virtual Chassis
(VC). The object decomposes into two persistence entities:

### Entity 1: VirtualChassisSummary (parent)

One row per VC chassis. Sourced from the top-level response object minus the `members`
array.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | TEXT (UUID) | response `.id` | **PRIMARY KEY**. Mist-assigned chassis UUID. readOnly. |
| `org_id` | TEXT (UUID) | response `.org_id` | Foreign key to org. readOnly. |
| `site_id` | TEXT (UUID) | response `.site_id` | Foreign key to site. readOnly. |
| `vc_mac` | TEXT (12-hex) | response `.vc_mac` | Canonical VC MAC. readOnly. |
| `mac` | TEXT | response `.mac` | Reported MAC field on the chassis object. |
| `model` | TEXT | response `.model` | Chassis model (e.g. EX4300-48P). readOnly. |
| `serial` | TEXT | response `.serial` | Chassis serial. readOnly. |
| `type` | TEXT | response `.type` | Device type. |
| `config_type` | TEXT | response `.config_type` | readOnly. |
| `status` | TEXT | response `.status` | Chassis status. readOnly. |
| `num_routing_engines` | INTEGER | response `.num_routing_engines` | RE count. |
| `locating` | INTEGER (0/1) | response `.locating` | Boolean cast to 0/1 for SQLite. readOnly. |
| `fetched_at` | INTEGER | wall-clock unix ts | Injected by DataExporter for refresh tracking. |

### Entity 2: VirtualChassisMember (child)

One row per element of the response `.members` array. Each member is one switch in the
stack.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `vc_id` | TEXT (UUID) | parent `.id` | **PRIMARY KEY part 1**. Foreign key -> `installer_device_vc_summary.id`. |
| `fpc_idx` | INTEGER | member `.fpc_idx` | **PRIMARY KEY part 2**. Slot index in the VC. readOnly. |
| `mac` | TEXT | member `.mac` | Member MAC (e.g. fc3342123456). |
| `serial` | TEXT | member `.serial` | Member serial. readOnly. |
| `model` | TEXT | member `.model` | Member model. readOnly. |
| `status` | TEXT | member `.status` | Member status. readOnly. |
| `type` | TEXT | member `.type` | readOnly. |
| `vc_role` | TEXT | member `.vc_role` | enum: master, backup, linecard. readOnly. |
| `vc_state` | TEXT | member `.vc_state` | readOnly. |
| `vc_mode` | TEXT | member `.vc_mode` | readOnly. |
| `version` | TEXT | member `.version` | Running Junos version. readOnly. |
| `backup_version` | TEXT | member `.backup_version` | readOnly. |
| `pending_version` | TEXT | member `.pending_version` | readOnly. |
| `recovery_version` | TEXT | member `.recovery_version` | readOnly. |
| `bios_version` | TEXT | member `.bios_version` | readOnly. |
| `uboot_version` | TEXT | member `.uboot_version` | readOnly. |
| `fpga_version` | TEXT | member `.fpga_version` | readOnly. |
| `re_fpga_version` | TEXT | member `.re_fpga_version` | readOnly. |
| `tmc_fpga_version` | TEXT | member `.tmc_fpga_version` | readOnly. |
| `cpld_version` | TEXT | member `.cpld_version` | readOnly. |
| `optics_cpld_version` | TEXT | member `.optics_cpld_version` | readOnly. |
| `power_cpld_version` | TEXT | member `.power_cpld_version` | readOnly. |
| `poe_version` | TEXT | member `.poe_version` | readOnly. |
| `boot_partition` | TEXT | member `.boot_partition` | |
| `last_seen` | REAL | member `.last_seen` | Unix ts (float). readOnly. |
| `uptime` | INTEGER | member `.uptime` | seconds. readOnly. |
| `locating` | INTEGER (0/1) | member `.locating` | Boolean cast. |
| `cpu_idle` | REAL | member `.cpu_stat.idle` | Flattened from cpu_stat. readOnly. |
| `cpu_system` | REAL | member `.cpu_stat.system` | readOnly. |
| `cpu_user` | REAL | member `.cpu_stat.user` | readOnly. |
| `cpu_interrupt` | REAL | member `.cpu_stat.interrupt` | readOnly. |
| `cpu_usage` | REAL | member `.cpu_stat.usage` | readOnly. |
| `cpu_load_avg_json` | TEXT (JSON) | member `.cpu_stat.load_avg` | 1/5/15 min averages. |
| `memory_usage` | REAL | member `.memory_stat.usage` | Master-RE memory usage. |
| `poe_max_power` | REAL | member `.poe.max_power` | Flattened from poe object. |
| `poe_power_draw` | REAL | member `.poe.power_draw` | |
| `poe_status` | TEXT | member `.poe.status` | |
| `fans_json` | TEXT (JSON) | member `.fans` | Serialized array of fan dicts (preserves variable cardinality). |
| `psus_json` | TEXT (JSON) | member `.psus` | Serialized array of PSU dicts. |
| `temperatures_json` | TEXT (JSON) | member `.temperatures` | Serialized array of sensor dicts. |
| `vc_links_json` | TEXT (JSON) | member `.vc_links` | Serialized array of VC link dicts. |
| `pics_json` | TEXT (JSON) | member `.pics` | Serialized array of PIC dicts (port groups nested). |
| `errors_json` | TEXT (JSON) | member `.errors` | Serialized array of error dicts. |
| `fetched_at` | INTEGER | wall-clock unix ts | Injected by DataExporter. |

**Rationale for JSON columns**: Variable-cardinality nested arrays (fans, PSUs,
temperatures, VC links, PICs with nested port_groups, errors) would explode into an
unbounded set of CSV columns or a third / fourth child table. Serializing them as JSON
text preserves query-ability via SQLite's `json_extract()` and Pandas' `json_normalize`
while keeping the row schema flat and stable across stack sizes.

## State Transitions

**N/A -- read-only endpoint.** This is an HTTP GET that returns a current snapshot of
the VC. MistHelper performs no state-changing operations against this path. Per-row
refresh is modeled as an UPSERT keyed on the natural / composite primary key, so
re-running the menu overwrites prior runtime fields (CPU, memory, last_seen, uptime,
sensor readings) without creating duplicate rows.

## Foreign Keys

- `installer_device_vc_members.vc_id` -> `installer_device_vc_summary.id` (logical
  reference; not enforced by SQLite FK constraint because DataExporter creates tables
  with `PRAGMA foreign_keys = OFF` for performance, but documented here for the
  ArangoDB graph backend which uses this edge).
- `installer_device_vc_summary.org_id` -> external Mist org UUID.
- `installer_device_vc_summary.site_id` -> external Mist site UUID.

## SQLite DDL

```sql
-- VC chassis summary: one row per chassis. Natural PK on the Mist-assigned UUID.
CREATE TABLE IF NOT EXISTS installer_device_vc_summary (
    id                  TEXT PRIMARY KEY,    -- Mist-assigned chassis UUID (readOnly)
    org_id              TEXT NOT NULL,       -- parent org UUID for join / filter
    site_id             TEXT,                -- parent site UUID (nullable on unassigned)
    vc_mac              TEXT,                -- canonical VC MAC (12 hex, no separators)
    mac                 TEXT,                -- chassis-level MAC field from API
    model               TEXT,                -- chassis model string (e.g. EX4300-48P)
    serial              TEXT,                -- chassis serial number
    type                TEXT,                -- device type string
    config_type         TEXT,                -- API-supplied config type
    status              TEXT,                -- chassis status string
    num_routing_engines INTEGER,             -- RE count from API
    locating            INTEGER,             -- 0/1 boolean cast for SQLite
    fetched_at          INTEGER NOT NULL     -- unix ts injected by DataExporter
);

-- VC members: one row per stack member. Composite PK on (vc_id, fpc_idx).
CREATE TABLE IF NOT EXISTS installer_device_vc_members (
    vc_id                TEXT NOT NULL,      -- FK to summary.id (chassis UUID)
    fpc_idx              INTEGER NOT NULL,   -- slot index inside the VC
    mac                  TEXT,               -- member MAC (12 hex)
    serial               TEXT,               -- member serial number
    model                TEXT,               -- member model string
    status               TEXT,               -- member status string
    type                 TEXT,               -- member type string
    vc_role              TEXT,               -- master | backup | linecard
    vc_state             TEXT,               -- member VC state
    vc_mode              TEXT,               -- member VC mode
    version              TEXT,               -- running Junos version
    backup_version       TEXT,               -- backup partition version
    pending_version      TEXT,               -- staged upgrade version
    recovery_version     TEXT,               -- recovery image version
    bios_version         TEXT,               -- BIOS version string
    uboot_version        TEXT,               -- U-Boot version string
    fpga_version         TEXT,               -- main FPGA version
    re_fpga_version      TEXT,               -- RE FPGA version
    tmc_fpga_version     TEXT,               -- TMC FPGA version
    cpld_version         TEXT,               -- CPLD version
    optics_cpld_version  TEXT,               -- optics CPLD version
    power_cpld_version   TEXT,               -- power CPLD version
    poe_version          TEXT,               -- PoE controller version
    boot_partition       TEXT,               -- currently booted partition
    last_seen            REAL,               -- last contact unix ts (float)
    uptime               INTEGER,            -- uptime seconds
    locating             INTEGER,            -- 0/1 boolean cast
    cpu_idle             REAL,               -- cpu_stat.idle percent
    cpu_system           REAL,               -- cpu_stat.system percent
    cpu_user             REAL,               -- cpu_stat.user percent
    cpu_interrupt        REAL,               -- cpu_stat.interrupt percent
    cpu_usage            REAL,               -- cpu_stat.usage overall
    cpu_load_avg_json    TEXT,               -- JSON array of 1/5/15 min load averages
    memory_usage         REAL,               -- memory_stat.usage on master RE
    poe_max_power        REAL,               -- poe.max_power watts
    poe_power_draw       REAL,               -- poe.power_draw watts
    poe_status           TEXT,               -- poe.status string
    fans_json            TEXT,               -- JSON array of fan dicts
    psus_json            TEXT,               -- JSON array of PSU dicts
    temperatures_json    TEXT,               -- JSON array of temperature sensor dicts
    vc_links_json        TEXT,               -- JSON array of VC link dicts
    pics_json            TEXT,               -- JSON array of PIC dicts (port_groups nested)
    errors_json          TEXT,               -- JSON array of error dicts
    fetched_at           INTEGER NOT NULL,   -- unix ts injected by DataExporter
    PRIMARY KEY (vc_id, fpc_idx)             -- composite natural PK for idempotent upsert
);

-- Index for org-wide queries across all chassis members
CREATE INDEX IF NOT EXISTS idx_vc_members_vc_id
    ON installer_device_vc_members (vc_id);
```

## ENDPOINT_PRIMARY_KEY_STRATEGIES Dict Entry

The single operationId expands to **two** registered logical endpoints because
DataExporter writes two tables. The convention used elsewhere in MistHelper is to
suffix the operationId with the flatten role for the child table:

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries above ...

    # Installer-scope VC chassis summary (one row per chassis). Natural PK on Mist UUID.
    "getInstallerDeviceVirtualChassis": {
        "type": "composite_pk",                       # degenerate composite (1 col)
        "primary_key": ["id"],                        # Mist-assigned chassis UUID
        "indexes": ["org_id", "site_id", "vc_mac"],   # common filter columns
        "table_name": "installer_device_vc_summary",  # explicit table override
    },

    # Installer-scope VC member rows (one per stack member). Composite on (vc_id, fpc_idx).
    "getInstallerDeviceVirtualChassis__members": {
        "type": "composite_pk",                       # true composite (2 cols)
        "primary_key": ["vc_id", "fpc_idx"],          # parent UUID + slot index
        "indexes": ["vc_id", "mac", "vc_role"],       # join + identity + role filters
        "table_name": "installer_device_vc_members",  # explicit table override
    },

    # ... existing entries below ...
}
```

The double-underscore suffix `__members` is the documented convention for marking a
child table derived from the same operationId; it keeps the dictionary single-keyed by
endpoint while letting DataExporter route the flattened child rows to the correct
table with the correct PK strategy.
