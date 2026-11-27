# Data Model: OSPF Peer Identity Keys

This model covers the OSPF peer record, the identity components, the identity key, and the three storage outputs. Each schema field cites its line in the local OpenAPI file, which matches `main` by blob SHA (RV-46 to RV-54).

## OSPF Peer Record

The record is one item of the paginated OSPF search result. The 200 response of each OSPF search operation returns the component `OspfPeersStatsSearch` (RV-46 and RV-47). The component is defined at line 64492 (RV-101) and uses the schema defined at line 91223 (RV-102). The item schema lives at lines 91259 to 91310 (RV-49).

| Field | Type | Role in this change | Source |
| - | - | - | - |
| `mac` | string | Required component. Router MAC of the device that advertises the peer. | `documentation/mist-api-openapi31yaml.yaml`, item schema lines 91259 to 91310 (RV-49) |
| `neighbor` | string | Neighbor component. IP address of the OSPF neighbor. | Same file, line 91269 (RV-50) |
| `peer_ip` | string, deprecated | Fallback neighbor component. Used only when `neighbor` is absent or empty. | Same file, lines 91282 and 91283 (RV-51) |
| `port_id` | string | Scope component. Interface on which the neighbor is learned. | Same file, line 91287 (RV-52) |
| `vrf_name` | string | Scope component. Instance name. | Same file, line 91307 (RV-53) |
| `timestamp` | number | Required component. Sampling time in epoch seconds. | Same file, lines 114341 to 114345 (RV-54) |
| `site_id`, `org_id`, `state`, `up`, `priority`, `dead_time`, `neighbor_id` | mixed | Carried into the output. They take no part in the identity. | Same file, item schema lines 91259 to 91310 (RV-49) |

## Identity Components

| Component | Required | Absent value | Empty string | Stored form |
| - | - | - | - | - |
| `mac` | yes | Reject the batch | Reject the batch | The value as received |
| neighbor component | yes | Use `peer_ip`. Reject the batch when `peer_ip` is also absent. | Use `peer_ip`. Reject the batch when `peer_ip` is also empty. | The value as received |
| `timestamp` | yes | Reject the batch | Reject the batch | Decimal text without an exponent |
| `vrf_name` | no | JSON null | JSON null | The value as received, or null |
| `port_id` | no | JSON null | JSON null | The value as received, or null |

A boolean, a negative number, a non-finite number, or text in `timestamp` rejects the batch.

## Identity Key

- **Canonical payload**: A JSON array with five values in this order: `mac`, `vrf_name`, `port_id`, `neighbor`, `timestamp`. The array uses ASCII escaping and no spaces.
- **Format**: The text `ospf_` followed by 64 lowercase hexadecimal characters.
- **Derivation**: SHA-256 digest of the canonical payload.
- **Natural key status**: The key derives from natural components only. The five components remain stored as their own fields.

## SQLite v2 Table

- **Name**: The legacy table name followed by `_v2`. Menus 70 and 225 use `SiteOspfStats_<site>_v2`. Menu 55 uses `OrgOspfStats_v2`.
- **Primary key**: `misthelper_ospf_peer_key`, declared `TEXT NOT NULL` (RV-05 and RV-12).
- **Columns**: One text column for each flattened field in the batch, the key column, and the audit columns that the writer appends.
- **Insert mode**: `INSERT OR REPLACE` (RV-12). A second run with the same key replaces the same row.
- **Legacy table**: Not read and not written by this change (FR-007).

## Redis JSON Document

- **Key**: `searchSiteOspfStats:ospf_<hex>` or `searchOrgOspfStats:ospf_<hex>`. The key builder joins the endpoint name with the value of each strategy primary key field (RV-15 and RV-16).
- **Value**: The full record JSON, including the `misthelper_ospf_peer_key` field.
- **Expiry**: `REDIS_JSON_TTL_SECONDS`, which defaults to 7 days (RV-18).
- **Legacy key**: A key in the earlier format `endpoint:mac:peer_ip:timestamp`, or with the value `unknown`. It expires by the TTL.

## ArangoDB Document

- **Collection**: The API function name, `searchSiteOspfStats` or `searchOrgOspfStats` (RV-22).
- **`_key`**: The identity key (RV-19). The first primary key field now holds the key value.
- **Fields**: The record fields, the `misthelper_ospf_peer_key` field, and the metadata fields that the writer adds.
- **Legacy document**: A document keyed by the MAC or by a generated UUID. It stays in the collection.

## State Transitions

1. **Record received**: The record carries the API fields.
2. **Record validated**: `OspfPeerIdentity` computes the key. Caution: A failure rejects the whole batch, and no output receives a write.
3. **Record attached**: The record carries `misthelper_ospf_peer_key`.
4. **Row or document written**: The SQLite row, the Redis document, and the ArangoDB document each hold one entry for each key.
5. **v2 table state**: The table is absent, then created on the first write. A later write checks the primary key and fails when the key differs.
6. **Legacy state**: Legacy tables, keys, and documents do not change in any transition.
