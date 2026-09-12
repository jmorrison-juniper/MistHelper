# Phase 1 Data Model: getOrgWLAN

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-07-01

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_wlans_wlan_id.md` (200 OK body). The full
schema is ~2000 lines; this document captures the columns MistHelper persists in
the flattened tabular form used by the SQLite / CSV / ArangoDB backends.

## Entities

The endpoint returns a single JSON object representing one WLAN configuration
document. MistHelper flattens this into one logical entity for tabular storage.
Deeply nested arrays are re-serialized as JSON strings so the CSV row remains
rectangular; consumers who need to query into them can use SQLite `json_each()`
or the equivalent ArangoDB traversal.

### Entity 1: WlanDetail

One row per WLAN (natural key = WLAN UUID).

Identity and audit columns:

- `id` (TEXT, PK) -- WLAN UUID, stable across polls.
- `org_id` (TEXT) -- FK orgs.id, echoed by the API.
- `site_id` (TEXT) -- FK sites.id, may be null for org-scope-only templates.
- `msp_id` (TEXT) -- managing MSP UUID or null.
- `for_site` (INTEGER) -- 1 if site-scoped, else 0.
- `created_time` (REAL) -- epoch seconds.
- `modified_time` (REAL) -- epoch seconds; audit column.
- `polled_at_utc` (TEXT) -- ISO8601 UTC timestamp of the poll, for audit.

SSID and visibility columns:

- `ssid` (TEXT) -- SSID broadcast name.
- `enabled` (INTEGER) -- 1/0.
- `hide_ssid` (INTEGER) -- 1/0.
- `interface` (TEXT) -- bridge / tunnel interface identifier.
- `apply_to` (TEXT) -- scope enum.

Radio columns:

- `band` (TEXT) -- legacy single band selector.
- `bands_json` (TEXT) -- serialized list of enabled bands.
- `band_steer` (INTEGER), `dtim` (INTEGER), `roam_mode` (TEXT),
  `rateset_json` (TEXT), `disable_ht_vht_rates` (INTEGER),
  `disable_uapsd` (INTEGER), `disable_wmm` (INTEGER),
  `disable_message_authenticator_check` (INTEGER).

Authentication columns (all shared secrets and PSK values redacted before storage):

- `auth_type` (TEXT) -- flattened from nested `auth.type`.
- `auth_psk_present` (INTEGER) -- 1 if `auth.psk` present, else 0.
- `auth_eap_reauth` (INTEGER) -- 1/0.
- `auth_json` (TEXT) -- serialized full `auth` object with `psk` REDACTED.
- `auth_servers_json`, `acct_servers_json`, `coa_servers_json` (TEXT) --
  serialized RADIUS / accounting / CoA server lists with all `secret` fields
  REDACTED.
- `auth_server_selection` (TEXT), `auth_servers_nas_id` (TEXT),
  `auth_servers_nas_ip` (TEXT), `auth_servers_retries` (INTEGER),
  `auth_servers_timeout` (INTEGER).
- `acct_immediate_update` (INTEGER), `acct_interim_interval` (INTEGER).
- `dynamic_psk` (INTEGER), `dynamic_vlan` (TEXT).
- `mist_nac_enabled` (INTEGER) -- flattened from nested `mist_nac.enabled`.
- `radsec_enabled` (INTEGER) -- flattened from nested `radsec.enabled`.
- `enable_local_keycaching` (INTEGER).

Access-control columns:

- `allow_mdns`, `allow_ssdp`, `arp_filter`, `block_blacklist_clients`,
  `sle_excluded`, `no_static_dns`, `no_static_ip`, `limit_bcast`,
  `limit_probe_response`, `legacy_overds`, `enable_wireless_bridging`,
  `enable_wireless_bridging_dhcp_tracking` (all INTEGER 1/0).
- `bonjour_json` (TEXT) -- serialized nested Bonjour config.
- `isolation` (TEXT), `max_num_clients` (INTEGER), `max_idletime` (INTEGER).
- `client_limit_up`, `client_limit_down` (INTEGER kbps),
  `client_limit_up_enabled`, `client_limit_down_enabled` (INTEGER 1/0).
- `app_limit_json`, `app_qos_json`, `qos_json` (TEXT).

Captive portal columns (portal secrets redacted):

- `portal_type` (TEXT) -- flattened from `portal.type`.
- `portal_json` (TEXT) -- serialized portal config with `portal_api_secret`
  REDACTED.
- `portal_allowed_hostnames_json`, `portal_allowed_subnets_json`,
  `portal_denied_hostnames_json` (TEXT).
- `portal_image` (TEXT), `portal_sso_url` (TEXT), `portal_template_url` (TEXT).
- `cisco_cwa_enabled`, `airwatch_enabled` (INTEGER, flattened).

Overlay and tunneling columns:

- `mxtunnel_id` (TEXT), `mxtunnel_ids_json` (TEXT), `mxtunnel_name` (TEXT).
- `disable_when_gateway_unreachable`, `disable_when_mxtunnel_down`,
  `reconnect_clients_when_roaming_mxcluster` (INTEGER 1/0).

Scheduling and placement columns:

- `schedule_json` (TEXT), `dns_server_rewrite_json` (TEXT),
  `hostname_ie_json` (TEXT).
- `ap_ids_json` (TEXT) -- serialized list of AP UUIDs to which the WLAN applies.

Any additional top-level fields that appear in future Mist API versions are
preserved via the existing `flatten_dict()` behavior: unknown keys become extra
columns appended after the canonical schema above and are exported to CSV / SQLite
without loss. The canonical column set above is what `ENDPOINT_PRIMARY_KEY_STRATEGIES`
declares; new columns beyond it are stored in the SQLite table as `TEXT` (SQLite's
dynamic typing tolerates the addition without an explicit schema migration).

## State Transitions

N/A -- this is a read-only endpoint. The underlying WLAN configuration transitions
on the Mist side through operator PUT / PATCH calls, but MistHelper does not drive
or model those transitions; it merely captures snapshots. Each poll overwrites the
prior snapshot for the same `id` via SQLite `INSERT OR REPLACE`, matching the
upsert acceptance scenario in `spec.md`.

## SQLite DDL

```sql
-- One row per WLAN. Primary key is the WLAN's stable UUID.
CREATE TABLE IF NOT EXISTS org_wlan_detail (
    id                                          TEXT     NOT NULL,
    org_id                                      TEXT,
    site_id                                     TEXT,
    msp_id                                      TEXT,
    for_site                                    INTEGER,
    created_time                                REAL,
    modified_time                               REAL,
    ssid                                        TEXT,
    enabled                                     INTEGER,
    hide_ssid                                   INTEGER,
    interface                                   TEXT,
    apply_to                                    TEXT,
    band                                        TEXT,
    bands_json                                  TEXT,
    band_steer                                  INTEGER,
    dtim                                        INTEGER,
    roam_mode                                   TEXT,
    rateset_json                                TEXT,
    disable_ht_vht_rates                        INTEGER,
    auth_type                                   TEXT,
    auth_psk_present                            INTEGER,
    auth_eap_reauth                             INTEGER,
    auth_json                                   TEXT,
    auth_servers_json                           TEXT,
    acct_servers_json                           TEXT,
    coa_servers_json                            TEXT,
    auth_server_selection                       TEXT,
    auth_servers_nas_id                         TEXT,
    auth_servers_nas_ip                         TEXT,
    auth_servers_retries                        INTEGER,
    auth_servers_timeout                        INTEGER,
    acct_immediate_update                       INTEGER,
    acct_interim_interval                       INTEGER,
    dynamic_psk                                 INTEGER,
    dynamic_vlan                                TEXT,
    mist_nac_enabled                            INTEGER,
    radsec_enabled                              INTEGER,
    enable_local_keycaching                     INTEGER,
    allow_mdns                                  INTEGER,
    allow_ssdp                                  INTEGER,
    arp_filter                                  INTEGER,
    bonjour_json                                TEXT,
    block_blacklist_clients                     INTEGER,
    isolation                                   TEXT,
    max_num_clients                             INTEGER,
    max_idletime                                INTEGER,
    client_limit_up                             INTEGER,
    client_limit_down                           INTEGER,
    client_limit_up_enabled                     INTEGER,
    client_limit_down_enabled                   INTEGER,
    app_limit_json                              TEXT,
    app_qos_json                                TEXT,
    qos_json                                    TEXT,
    portal_type                                 TEXT,
    portal_json                                 TEXT,
    portal_allowed_hostnames_json               TEXT,
    portal_allowed_subnets_json                 TEXT,
    portal_denied_hostnames_json                TEXT,
    portal_image                                TEXT,
    portal_sso_url                              TEXT,
    portal_template_url                         TEXT,
    cisco_cwa_enabled                           INTEGER,
    airwatch_enabled                            INTEGER,
    mxtunnel_id                                 TEXT,
    mxtunnel_ids_json                           TEXT,
    mxtunnel_name                               TEXT,
    disable_when_gateway_unreachable            INTEGER,
    disable_when_mxtunnel_down                  INTEGER,
    reconnect_clients_when_roaming_mxcluster    INTEGER,
    schedule_json                               TEXT,
    sle_excluded                                INTEGER,
    no_static_dns                               INTEGER,
    no_static_ip                                INTEGER,
    dns_server_rewrite_json                     TEXT,
    hostname_ie_json                            TEXT,
    limit_bcast                                 INTEGER,
    limit_probe_response                        INTEGER,
    legacy_overds                               INTEGER,
    enable_wireless_bridging                    INTEGER,
    enable_wireless_bridging_dhcp_tracking      INTEGER,
    ap_ids_json                                 TEXT,
    disable_uapsd                               INTEGER,
    disable_wmm                                 INTEGER,
    disable_message_authenticator_check         INTEGER,
    polled_at_utc                               TEXT,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_org_wlan_detail_org_id
    ON org_wlan_detail (org_id);

CREATE INDEX IF NOT EXISTS idx_org_wlan_detail_site_id
    ON org_wlan_detail (site_id);

CREATE INDEX IF NOT EXISTS idx_org_wlan_detail_ssid
    ON org_wlan_detail (ssid);

CREATE INDEX IF NOT EXISTS idx_org_wlan_detail_enabled
    ON org_wlan_detail (enabled);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the
equivalent DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`,
ArangoDB via collection upsert, Redis via key namespacing). MistHelper does not
run the DDL directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
in `MistHelper.py` (single insert in the dict literal, no structural change):

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per WLAN, keyed by the WLAN's stable UUID (natural PK).
    'getOrgWLAN': {                                                                # operationId from OpenAPI spec
        'type': 'natural_pk',                                                      # WLAN id is stable across polls
        'primary_key': ['id'],                                                     # single-column UUID PK
        'indexes': ['org_id', 'site_id', 'ssid', 'enabled'],                       # high-cardinality query columns
        'table': 'org_wlan_detail',                                                # target SQLite table
    },
}
```

The choice of `natural_pk` follows the codebase's Database Strategy: entities with
stable API-provided UUIDs use `natural_pk` with `primary_key: ['id']`. `INSERT OR
REPLACE` on `id` guarantees upsert-clean re-runs, satisfying acceptance scenario 3
in `spec.md`.
