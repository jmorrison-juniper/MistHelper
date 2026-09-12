# Phase 1 Data Model: getOrgWxTunnel

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-07-01

## Source

API response schema lifted from
`documentation/api/orgs/GET_orgs_org_id_wxtunnels_wxtunnel_id.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing one WxLAN tunnel and its embedded
session list. MistHelper splits this into two logical entities for clean multi-backend
persistence: a parent `WxTunnel` row and zero-or-more `WxTunnelSession` rows.

### Entity 1: `WxTunnel`

One row per retrieved WxTunnel. Nested `dmvpn` and `ipsec` sub-objects are flattened
into prefixed columns on this row; the `sessions` array is *not* flattened here (see
Entity 2).

| Field                    | Type    | Source                        | PK? | FK?          | Notes |
|--------------------------|---------|-------------------------------|-----|--------------|-------|
| `id`                     | TEXT    | API `id`                      | YES | --           | WxTunnel UUID. Natural PK. |
| `org_id`                 | TEXT    | API `org_id` (or MistHelper context) | -- | orgs.id | UUID. |
| `site_id`                | TEXT    | API `site_id`                 | --  | sites.id     | UUID. Nullable. |
| `name`                   | TEXT    | API `name`                    | --  | --           | Required by schema. |
| `for_mgmt`               | INTEGER | API `for_mgmt`                | --  | --           | 0/1 bool. Immutable after create. |
| `for_site`               | INTEGER | API `for_site`                | --  | --           | 0/1 bool. Read-only. |
| `is_static`              | INTEGER | API `is_static`               | --  | --           | 0/1 bool. Immutable. |
| `hello_interval`         | INTEGER | API `hello_interval`          | --  | --           | Seconds, 1..300. |
| `hello_retries`          | INTEGER | API `hello_retries`           | --  | --           | 2..30. |
| `hostname`               | TEXT    | API `hostname`                | --  | --           | Optional SCCRQ hostname. |
| `router_id`              | TEXT    | API `router_id`               | --  | --           | Optional SCCRQ router-id. |
| `secret`                 | TEXT    | API `secret`                  | --  | --           | L2TP auth secret. Empty when none. Treated as sensitive; logged as `<redacted>`. |
| `mtu`                    | INTEGER | API `mtu`                     | --  | --           | 0..1500 (0 = PMTU). |
| `peers`                  | TEXT    | API `peers` (JSON-encoded)    | --  | --           | Comma-separated in CSV; JSON in SQLite. |
| `udp_port`               | INTEGER | API `udp_port`                | --  | --           | Only meaningful when `use_udp=1`. |
| `use_udp`                | INTEGER | API `use_udp`                 | --  | --           | 0/1 bool. |
| `dmvpn_enabled`          | INTEGER | API `dmvpn.enabled`           | --  | --           | Flattened from nested `dmvpn`. |
| `dmvpn_holding_time`     | INTEGER | API `dmvpn.holding_time`      | --  | --           | Seconds. |
| `dmvpn_host_routes`      | TEXT    | API `dmvpn.host_routes` (JSON) | -- | --           | Serialized string list. |
| `ipsec_enabled`          | INTEGER | API `ipsec.enabled`           | --  | --           | 0/1 bool. |
| `ipsec_psk`              | TEXT    | API `ipsec.psk`               | --  | --           | **SENSITIVE** -- redacted to `<redacted>` before any log or export. |
| `session_count`          | INTEGER | len(API `sessions`)           | --  | --           | Convenience count. |
| `created_time`           | REAL    | API `created_time`            | --  | --           | Epoch seconds. |
| `modified_time`          | REAL    | API `modified_time`           | --  | --           | Epoch seconds. |
| `fetched_at_utc`         | TEXT    | MistHelper clock              | --  | --           | ISO8601 UTC timestamp of the retrieval, for audit. |

### Entity 2: `WxTunnelSession`

Zero or more rows per parent tunnel. Source: each element of the API `sessions` array.

| Field                       | Type    | Source                       | PK? | FK?                    | Notes |
|-----------------------------|---------|------------------------------|-----|------------------------|-------|
| `wxtunnel_id`               | TEXT    | Parent `id` (injected)       | YES | org_wxtunnels.id       | UUID. |
| `remote_id`                 | TEXT    | API `sessions[].remote_id`   | YES | --                     | Documented unique within tunnel. |
| `ap_as_session_id`          | TEXT    | API `sessions[].ap_as_session_id` | -- | --                | Present when `use_ap_as_session_ids=1`. |
| `comment`                   | TEXT    | API `sessions[].comment`     | --  | --                     | Optional display string. |
| `enable_cookie`             | INTEGER | API `sessions[].enable_cookie` | -- | --                    | 0/1 bool. |
| `ethertype`                 | TEXT    | API `sessions[].ethertype`   | --  | --                     | Enum: `ethernet`, `vlan`. |
| `local_session_id`          | INTEGER | API `sessions[].local_session_id` | -- | --                | 1..2147483647. |
| `pseudo_dot1ad_enabled`     | INTEGER | API `sessions[].pseudo_802.1ad_enabled` | -- | --          | Column renamed for SQL-safety. |
| `remote_session_id`         | INTEGER | API `sessions[].remote_session_id` | -- | --               | 1..2147483647. |
| `use_ap_as_session_ids`     | INTEGER | API `sessions[].use_ap_as_session_ids` | -- | --           | 0/1 bool. |
| `fetched_at_utc`            | TEXT    | MistHelper clock             | --  | --                     | ISO8601 UTC timestamp of the retrieval. |

## State Transitions

N/A -- this is a read-only endpoint. WxTunnels are configuration objects whose lifecycle
(create / modify / delete) is driven by other Mist API endpoints (POST / PUT / DELETE
under the same path). MistHelper does not model or drive those transitions here; it
merely captures the current configuration snapshot. Each retrieval overwrites the prior
snapshot for the same `id` (parent) and `(wxtunnel_id, remote_id)` (session) via SQLite
`INSERT OR REPLACE`.

## SQLite DDL

```sql
-- Parent: one row per WxTunnel keyed by its Mist UUID.
CREATE TABLE IF NOT EXISTS org_wxtunnels (
    id                    TEXT PRIMARY KEY,
    org_id                TEXT NOT NULL,
    site_id               TEXT,
    name                  TEXT NOT NULL,
    for_mgmt              INTEGER,
    for_site              INTEGER,
    is_static             INTEGER,
    hello_interval        INTEGER,
    hello_retries         INTEGER,
    hostname              TEXT,
    router_id             TEXT,
    secret                TEXT,
    mtu                   INTEGER,
    peers                 TEXT,
    udp_port              INTEGER,
    use_udp               INTEGER,
    dmvpn_enabled         INTEGER,
    dmvpn_holding_time    INTEGER,
    dmvpn_host_routes     TEXT,
    ipsec_enabled         INTEGER,
    ipsec_psk             TEXT,
    session_count         INTEGER,
    created_time          REAL,
    modified_time         REAL,
    fetched_at_utc        TEXT
);

CREATE INDEX IF NOT EXISTS idx_org_wxtunnels_org_id
    ON org_wxtunnels (org_id);
CREATE INDEX IF NOT EXISTS idx_org_wxtunnels_site_id
    ON org_wxtunnels (site_id);
CREATE INDEX IF NOT EXISTS idx_org_wxtunnels_name
    ON org_wxtunnels (name);

-- Sessions: zero-or-more rows per WxTunnel, keyed by (wxtunnel_id, remote_id).
CREATE TABLE IF NOT EXISTS org_wxtunnel_sessions (
    wxtunnel_id             TEXT NOT NULL,
    remote_id               TEXT NOT NULL,
    ap_as_session_id        TEXT,
    comment                 TEXT,
    enable_cookie           INTEGER,
    ethertype               TEXT,
    local_session_id        INTEGER,
    pseudo_dot1ad_enabled   INTEGER,
    remote_session_id       INTEGER,
    use_ap_as_session_ids   INTEGER,
    fetched_at_utc          TEXT,
    PRIMARY KEY (wxtunnel_id, remote_id),
    FOREIGN KEY (wxtunnel_id) REFERENCES org_wxtunnels(id)
);

CREATE INDEX IF NOT EXISTS idx_org_wxtunnel_sessions_wxtunnel_id
    ON org_wxtunnel_sessions (wxtunnel_id);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL directly.

## Sensitive Field Handling

`ipsec_psk` (source: API `ipsec.psk`) is a pre-shared key and MUST be handled as
sensitive:

- **In logs**: emit as the literal string `<redacted>`. Never log the actual value at
  any level (INFO, DEBUG, WARNING, or ERROR).
- **In CSV / SQLite output**: the value is written verbatim so that operators with
  filesystem access to `data/` can rebuild tunnel state. The `data/` directory is
  documented as sensitive by the top-level README.
- **In `debug` summary line after the SDK call**: the summary uses the literal
  `psk=<redacted>` regardless of whether IPsec is enabled.

The same handling applies to `secret` (L2TP auth secret) at log level. In persistent
output the `secret` column is written verbatim for the same operational reason as
`ipsec_psk`.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entries

Add the following two entries to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert per key in the dict literal, no structural
change to the dictionary itself).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # Parent WxTunnel row keyed by the Mist-assigned UUID.
    'getOrgWxTunnel': {                                                             # operationId from OpenAPI
        'type': 'natural_pk',                                                       # Mist assigns a stable UUID
        'primary_key': ['id'],                                                      # top-level id field
        'indexes': ['org_id', 'site_id', 'name'],                                   # common query paths
        'table': 'org_wxtunnels',                                                   # SQLite table for parent rows
    },

    # Per-session detail rows produced from the nested sessions[] array.
    'getOrgWxTunnelSessions': {                                                     # MistHelper-internal sub-table id
        'type': 'composite_pk',                                                     # composite of FK + remote_id
        'primary_key': ['wxtunnel_id', 'remote_id'],                                # Mist doc: remote_id is unique within tunnel
        'indexes': ['wxtunnel_id'],                                                 # fast join back to parent tunnel
        'table': 'org_wxtunnel_sessions',                                           # SQLite table for session rows
    },
}
```

The `getOrgWxTunnelSessions` key is a MistHelper-internal identifier (the Mist API has
no operationId for it -- it is a flattened sub-array of the parent response). This
pattern matches how MistHelper already splits other endpoints whose response contains
nested arrays.
