# Phase 1 Data Model: getOrgSettings

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-30

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_setting.md` (200 OK body,
~50 KB of nested schema).

## Entities

The endpoint returns a single JSON object describing the organization's full
settings document. MistHelper splits this into three logical entities: one
parent row plus two side tables for the two nested rule arrays. Every other
nested object is JSON-serialized into a single TEXT column on the parent row
(preserving fidelity without exploding the schema into 30+ tables).

### Entity 1: `OrgSettings` (parent)

Exactly one row per organization.

| Field                              | Type    | Source                | PK? | FK?           | Notes |
|------------------------------------|---------|-----------------------|-----|---------------|-------|
| `org_id`                           | TEXT    | API `org_id` (falls back to caller context) | YES | sites.org_id | UUID. |
| `id`                               | TEXT    | API `id`              | --  | --            | Settings-object internal id (distinct from `org_id`). |
| `msp_id`                           | TEXT    | API `msp_id`          | --  | --            | Managed Service Provider UUID (may be null). |
| `for_site`                         | INTEGER | API `for_site`        | --  | --            | Boolean flag stored as 0/1. |
| `allow_mist`                       | INTEGER | API `allow_mist`      | --  | --            | Boolean flag stored as 0/1. |
| `ap_updown_threshold`              | INTEGER | API `ap_updown_threshold` | -- | --          | Nullable; 0..240. |
| `device_updown_threshold`          | INTEGER | API `device_updown_threshold` | -- | --      | Nullable. |
| `gateway_updown_threshold`         | INTEGER | API `gateway_updown_threshold` | -- | --     | Nullable. |
| `gateway_tunnel_updown_threshold`  | INTEGER | API `gateway_tunnel_updown_threshold` | -- | -- | Nullable. |
| `switch_updown_threshold`          | INTEGER | API `switch_updown_threshold` | -- | --      | Nullable. |
| `blacklist_url`                    | TEXT    | API `blacklist_url`   | --  | --            | URL. |
| `disable_pcap`                     | INTEGER | API `disable_pcap`    | --  | --            | Boolean 0/1. |
| `disable_remote_shell`             | INTEGER | API `disable_remote_shell` | -- | --         | Boolean 0/1. |
| `ui_no_tracking`                   | INTEGER | API `ui_no_tracking`  | --  | --            | Boolean 0/1. |
| `pcap_bucket_verified`             | INTEGER | API `pcap_bucket_verified` | -- | --         | Boolean 0/1. |
| `created_time`                     | REAL    | API `created_time`    | --  | --            | Epoch seconds. |
| `modified_time`                    | REAL    | API `modified_time`   | --  | --            | Epoch seconds. |
| `api_policy_json`                  | TEXT    | API `api_policy`      | --  | --            | JSON blob of the `api_policy` object. |
| `auto_device_naming_json`          | TEXT    | API `auto_device_naming` minus `rules` | -- | -- | JSON blob (rules extracted to side table). |
| `auto_deviceprofile_assignment_json` | TEXT | API `auto_deviceprofile_assignment` minus `rules` | -- | -- | JSON blob (rules extracted to side table). |
| `auto_site_assignment_json`        | TEXT    | API `auto_site_assignment` | -- | --          | JSON blob. |
| `cacerts_json`                     | TEXT    | API `cacerts`         | --  | --            | JSON blob. |
| `celona_json`                      | TEXT    | API `celona`          | --  | --            | JSON blob. |
| `cloudshark_json`                  | TEXT    | API `cloudshark`      | --  | --            | JSON blob. |
| `cradlepoint_json`                 | TEXT    | API `cradlepoint`     | --  | --            | JSON blob. |
| `device_cert_json`                 | TEXT    | API `device_cert`     | --  | --            | JSON blob. |
| `gateway_mgmt_json`                | TEXT    | API `gateway_mgmt`    | --  | --            | JSON blob. |
| `installer_json`                   | TEXT    | API `installer`       | --  | --            | JSON blob. |
| `jcloud_json`                      | TEXT    | API `jcloud`          | --  | --            | JSON blob. |
| `jcloud_ra_json`                   | TEXT    | API `jcloud_ra`       | --  | --            | JSON blob. |
| `juniper_json`                     | TEXT    | API `juniper`         | --  | --            | JSON blob. |
| `juniper_srx_json`                 | TEXT    | API `juniper_srx`     | --  | --            | JSON blob. |
| `junos_shell_access_json`          | TEXT    | API `junos_shell_access` | -- | --           | JSON blob. |
| `marvis_json`                      | TEXT    | API `marvis`          | --  | --            | JSON blob. |
| `mgmt_json`                        | TEXT    | API `mgmt`            | --  | --            | JSON blob. |
| `mist_nac_json`                    | TEXT    | API `mist_nac`        | --  | --            | JSON blob. Contains sensitive credentials. |
| `mxedge_mgmt_json`                 | TEXT    | API `mxedge_mgmt`     | --  | --            | JSON blob. |
| `optic_port_config_json`           | TEXT    | API `optic_port_config` | -- | --            | JSON blob. |
| `password_policy_json`             | TEXT    | API `password_policy` | --  | --            | JSON blob. |
| `pcap_json`                        | TEXT    | API `pcap`            | --  | --            | JSON blob. |
| `security_json`                    | TEXT    | API `security`        | --  | --            | JSON blob. |
| `simple_alert_json`                | TEXT    | API `simple_alert`    | --  | --            | JSON blob. |
| `ssr_json`                         | TEXT    | API `ssr`             | --  | --            | JSON blob. |
| `switch_json`                      | TEXT    | API `switch`          | --  | --            | JSON blob. |
| `switch_mgmt_json`                 | TEXT    | API `switch_mgmt`     | --  | --            | JSON blob. |
| `synthetic_test_json`              | TEXT    | API `synthetic_test`  | --  | --            | JSON blob. |
| `tags_json`                        | TEXT    | API `tags`            | --  | --            | JSON blob. |
| `ui_idle_timeout_json`             | TEXT    | API `ui_idle_timeout` | --  | --            | JSON blob. |
| `vpn_options_json`                 | TEXT    | API `vpn_options`     | --  | --            | JSON blob. |
| `wan_pma_json`                     | TEXT    | API `wan_pma`         | --  | --            | JSON blob. |
| `wired_pma_json`                   | TEXT    | API `wired_pma`       | --  | --            | JSON blob. |
| `wireless_pma_json`                | TEXT    | API `wireless_pma`    | --  | --            | JSON blob. |
| `polled_at_utc`                    | TEXT    | MistHelper clock      | --  | --            | ISO8601 UTC timestamp of the poll, for audit. |

### Entity 2: `OrgSettingsAutoDeviceNamingRule` (side table)

Zero-or-more rows per organization -- one per element of the source array
`auto_device_naming.rules[]` (schema title
`org_setting_auto_device_naming_rule`).

| Field           | Type    | Source                       | PK? | FK?                    | Notes |
|-----------------|---------|------------------------------|-----|------------------------|-------|
| `org_id`        | TEXT    | MistHelper context           | YES | org_settings.org_id    | UUID. |
| `rule_index`    | INTEGER | Array position (0-based)     | YES | --                     | Preserves order. |
| `expression`    | TEXT    | rule `expression`            | --  | --                     | e.g. `split(.)[1]`. |
| `match_device`  | TEXT    | rule `match_device`          | --  | --                     | Enum: `ap`, `gateway`, `switch`. |
| `prefix`        | TEXT    | rule `prefix`                | --  | --                     | Optional. |
| `src`           | TEXT    | rule `src`                   | --  | --                     | Enum: `lldp_port_desc`, `mac`. |
| `suffix`        | TEXT    | rule `suffix`                | --  | --                     | Optional. |
| `polled_at_utc` | TEXT    | MistHelper clock             | --  | --                     | ISO8601. |

### Entity 3: `OrgSettingsAutoDeviceprofileAssignmentRule` (side table)

Zero-or-more rows per organization -- one per element of the source array
`auto_deviceprofile_assignment.rules[]` (schema title
`org_setting_auto_deviceprofile_assignment_rule`).

| Field                | Type    | Source                       | PK? | FK?                    | Notes |
|----------------------|---------|------------------------------|-----|------------------------|-------|
| `org_id`             | TEXT    | MistHelper context           | YES | org_settings.org_id    | UUID. |
| `rule_index`         | INTEGER | Array position (0-based)     | YES | --                     | Preserves order. |
| `deviceprofile_id`   | TEXT    | rule `deviceprofile_id`      | --  | --                     | Target device profile UUID. |
| `src`                | TEXT    | rule `src`                   | --  | --                     | Source attribute. |
| `expression`         | TEXT    | rule `expression`            | --  | --                     | Matching expression. |
| `match_type`         | TEXT    | rule `match_type`            | --  | --                     | Match mode. |
| `raw_json`           | TEXT    | full rule dict serialized    | --  | --                     | Fallback: preserves any fields not columnized above (schema evolution). |
| `polled_at_utc`      | TEXT    | MistHelper clock             | --  | --                     | ISO8601. |

## State Transitions

N/A -- this is a read-only endpoint. Org settings on the Mist side change
only when an administrator edits them (reflected in `modified_time`).
MistHelper captures the current state on each poll and upserts via SQLite
`INSERT OR REPLACE`. The side-table rules are wiped and re-inserted per poll
by relying on the composite PK -- any rule that disappears from the source
array between polls remains in the DB until an explicit cleanup pass (out of
scope for this spec; documented as a future enhancement).

## SQLite DDL

```sql
-- Parent settings table: one row per organization.
CREATE TABLE IF NOT EXISTS org_settings (
    org_id                                TEXT     NOT NULL,
    id                                    TEXT,
    msp_id                                TEXT,
    for_site                              INTEGER,
    allow_mist                            INTEGER,
    ap_updown_threshold                   INTEGER,
    device_updown_threshold               INTEGER,
    gateway_updown_threshold              INTEGER,
    gateway_tunnel_updown_threshold       INTEGER,
    switch_updown_threshold               INTEGER,
    blacklist_url                         TEXT,
    disable_pcap                          INTEGER,
    disable_remote_shell                  INTEGER,
    ui_no_tracking                        INTEGER,
    pcap_bucket_verified                  INTEGER,
    created_time                          REAL,
    modified_time                         REAL,
    api_policy_json                       TEXT,
    auto_device_naming_json               TEXT,
    auto_deviceprofile_assignment_json    TEXT,
    auto_site_assignment_json             TEXT,
    cacerts_json                          TEXT,
    celona_json                           TEXT,
    cloudshark_json                       TEXT,
    cradlepoint_json                      TEXT,
    device_cert_json                      TEXT,
    gateway_mgmt_json                     TEXT,
    installer_json                        TEXT,
    jcloud_json                           TEXT,
    jcloud_ra_json                        TEXT,
    juniper_json                          TEXT,
    juniper_srx_json                      TEXT,
    junos_shell_access_json               TEXT,
    marvis_json                           TEXT,
    mgmt_json                             TEXT,
    mist_nac_json                         TEXT,
    mxedge_mgmt_json                      TEXT,
    optic_port_config_json                TEXT,
    password_policy_json                  TEXT,
    pcap_json                             TEXT,
    security_json                         TEXT,
    simple_alert_json                     TEXT,
    ssr_json                              TEXT,
    switch_json                           TEXT,
    switch_mgmt_json                      TEXT,
    synthetic_test_json                   TEXT,
    tags_json                             TEXT,
    ui_idle_timeout_json                  TEXT,
    vpn_options_json                      TEXT,
    wan_pma_json                          TEXT,
    wired_pma_json                        TEXT,
    wireless_pma_json                     TEXT,
    polled_at_utc                         TEXT,
    PRIMARY KEY (org_id)
);

CREATE INDEX IF NOT EXISTS idx_org_settings_modified_time
    ON org_settings (modified_time);

-- Side table: auto_device_naming.rules[].
CREATE TABLE IF NOT EXISTS org_settings_auto_device_naming_rules (
    org_id          TEXT     NOT NULL,
    rule_index      INTEGER  NOT NULL,
    expression      TEXT,
    match_device    TEXT,
    prefix          TEXT,
    src             TEXT,
    suffix          TEXT,
    polled_at_utc   TEXT,
    PRIMARY KEY (org_id, rule_index),
    FOREIGN KEY (org_id) REFERENCES org_settings(org_id)
);

CREATE INDEX IF NOT EXISTS idx_org_settings_adn_rules_match_device
    ON org_settings_auto_device_naming_rules (match_device);

-- Side table: auto_deviceprofile_assignment.rules[].
CREATE TABLE IF NOT EXISTS org_settings_auto_deviceprofile_assignment_rules (
    org_id            TEXT     NOT NULL,
    rule_index        INTEGER  NOT NULL,
    deviceprofile_id  TEXT,
    src               TEXT,
    expression        TEXT,
    match_type        TEXT,
    raw_json          TEXT,
    polled_at_utc     TEXT,
    PRIMARY KEY (org_id, rule_index),
    FOREIGN KEY (org_id) REFERENCES org_settings(org_id)
);

CREATE INDEX IF NOT EXISTS idx_org_settings_adpa_rules_devprof
    ON org_settings_auto_deviceprofile_assignment_rules (deviceprofile_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via
`CREATE TABLE IF NOT EXISTS`, ArangoDB via collection upsert, Redis via key
namespacing). MistHelper does not run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following three entries to the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary in `MistHelper.py` (three dict
inserts, no structural change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Parent settings row: exactly one per organization.
    'getOrgSettings': {                                                             # operationId from OpenAPI
        'type': 'natural_pk',                                                       # org_id is a stable natural key
        'primary_key': ['org_id'],                                                  # singleton per organization
        'indexes': ['modified_time'],                                               # fast lookup of recently-changed orgs
        'table': 'org_settings',                                                    # target SQLite table
    },

    # Side table: auto_device_naming.rules[] flattened by ordinal index.
    'getOrgSettingsAutoDeviceNamingRules': {                                        # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # org_id + array position
        'primary_key': ['org_id', 'rule_index'],                                    # preserves rule order across polls
        'indexes': ['match_device'],                                                # common filter: rules per device type
        'table': 'org_settings_auto_device_naming_rules',                           # target SQLite table
    },

    # Side table: auto_deviceprofile_assignment.rules[] flattened by ordinal.
    'getOrgSettingsAutoDeviceprofileAssignmentRules': {                             # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # org_id + array position
        'primary_key': ['org_id', 'rule_index'],                                    # preserves rule order across polls
        'indexes': ['deviceprofile_id'],                                            # common filter: rules per profile
        'table': 'org_settings_auto_deviceprofile_assignment_rules',                # target SQLite table
    },
}
```

The two `...Rules` keys are MistHelper-internal identifiers (the Mist API has
no operationId for either -- they are flattened sub-arrays of the parent
response). This pattern matches how MistHelper already splits other endpoints
whose response contains nested arrays.
