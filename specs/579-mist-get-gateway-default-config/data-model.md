# Phase 1 Data Model: getGatewayDefaultConfig

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Research**: [research.md](./research.md)
**Date**: 2026-06-29

## Source

API response schema lifted from
`documentation/api/constants/GET_const_default_gateway_config.md` (200 OK body).

## Entities

The endpoint returns a single JSON object describing the factory-default gateway
configuration Mist hands to a freshly adopted SRX or SSR for a given (model, ha)
combination. MistHelper persists this as a single logical entity with the raw JSON
preserved alongside denormalized convenience counts for SQL queryability.

### Entity 1: `DefaultGatewayConfig`

One row per (gateway hardware model, HA mode) tuple.

| Field                | Type    | Source                                  | PK? | FK? | Notes |
|----------------------|---------|-----------------------------------------|-----|-----|-------|
| `model`              | TEXT    | MistHelper user input                   | YES | --  | Lowercased gateway model token (e.g. `srx320`, `ssr120`). |
| `ha_flag`            | TEXT    | MistHelper user input                   | YES | --  | Literal string `"true"` or `"false"`. Never `NULL` to keep the composite PK total. |
| `dhcpd_lan_ip_start` | TEXT    | API `dhcpd_config.lan.ip_start`         | --  | --  | First DHCP-assignable LAN IP. May be `NULL` for models that ship without a LAN DHCP pool. |
| `dhcpd_lan_ip_end`   | TEXT    | API `dhcpd_config.lan.ip_end`           | --  | --  | Last DHCP-assignable LAN IP. |
| `lan_ip`             | TEXT    | API `ip_configs.lan.ip`                 | --  | --  | LAN interface IP. |
| `lan_ip_type`        | TEXT    | API `ip_configs.lan.type`               | --  | --  | Typically `static`. |
| `lan_subnet`         | TEXT    | API `networks.lan.subnet`               | --  | --  | CIDR (e.g. `192.168.1.0/24`). |
| `lan_vlan_id`        | INTEGER | API `networks.lan.vlan_id`              | --  | --  | LAN VLAN ID. |
| `wan_path_count`     | INTEGER | len(API `path_preferences.wan.paths`)   | --  | --  | Convenience count of WAN paths. |
| `port_config_count`  | INTEGER | len(API `port_config` keys)             | --  | --  | Convenience count of port-config groups. |
| `service_policy_count` | INTEGER | len(API `service_policies`)          | --  | --  | Convenience count of default service policies. |
| `config_json`        | TEXT    | API body (serialized)                   | --  | --  | Full response body as canonical JSON (`json.dumps(body, sort_keys=True)`) for round-trip fidelity. |
| `fetched_at_utc`     | TEXT    | MistHelper clock                        | --  | --  | ISO8601 UTC timestamp of the fetch, for audit. |

## State Transitions

N/A -- this is a read-only constants/reference endpoint. The Mist server may publish a
revised default configuration for a given model over time, but MistHelper does not
model that transition; it merely captures the most recent snapshot. Each fetch
overwrites the prior snapshot for the same `(model, ha_flag)` tuple via SQLite
`INSERT OR REPLACE`. There is no state machine on the MistHelper side.

## SQLite DDL

```sql
-- Reference table: one row per (gateway model, HA mode) default config.
CREATE TABLE IF NOT EXISTS default_gateway_config (
    model                 TEXT NOT NULL,
    ha_flag               TEXT NOT NULL,
    dhcpd_lan_ip_start    TEXT,
    dhcpd_lan_ip_end      TEXT,
    lan_ip                TEXT,
    lan_ip_type           TEXT,
    lan_subnet            TEXT,
    lan_vlan_id           INTEGER,
    wan_path_count        INTEGER,
    port_config_count     INTEGER,
    service_policy_count  INTEGER,
    config_json           TEXT,
    fetched_at_utc        TEXT,
    PRIMARY KEY (model, ha_flag)
);

CREATE INDEX IF NOT EXISTS idx_default_gateway_config_model
    ON default_gateway_config (model);
```

`DataExporter.write_with_format_selection()` is responsible for emitting the equivalent
DDL on first write per backend (SQLite via `CREATE TABLE IF NOT EXISTS`, ArangoDB via
collection upsert, Redis via key namespacing). MistHelper does not run the DDL
directly.

## ENDPOINT_PRIMARY_KEY_STRATEGIES Entry

Add the following single entry to the existing `ENDPOINT_PRIMARY_KEY_STRATEGIES`
dictionary in `MistHelper.py` (single insert in the dict literal, no structural
change).

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    # ... existing entries ...

    # One row per (gateway hardware model, HA mode) default configuration snapshot.
    'getGatewayDefaultConfig': {                                                    # operationId from OpenAPI
        'type': 'composite_pk',                                                     # PK is composite of business fields
        'primary_key': ['model', 'ha_flag'],                                        # natural key from query params
        'indexes': ['model'],                                                       # fast lookup by gateway model
        'table': 'default_gateway_config',                                          # target SQLite table
    },
}
```

The single-entry pattern is appropriate because the response shape is a single config
blob -- there is no nested array that would justify a sibling sub-table entry (unlike,
for example, `getOrgLicenseAsyncClaimStatus` which splits into summary + detail).
