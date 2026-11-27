# Data Model: WAN Performance portal integration

Each entity lists its natural key. The feature uses no artificial identifier as a key, except the configured store row number that the store assigns.

## Entities

| Entity | Natural key | Key fields | Source |
|---|---|---|---|
| Site | `org_id` and `site_id` (`SiteIdentity`, `identity.py` L44) | organization and site identifiers | R63 |
| Gateway | `org_id`, `site_id`, and `device_id` (`GatewayIdentity`, `identity.py` L66) | device identifier and site | R63 |
| WAN port | site, gateway, and port name (`CircuitIdentity`, `identity.py` L87) | port name, validated by `IdentityValidator.port_name` | R63 |
| VPN peer path | organization, peer MAC, and site scope (`PeerPathIdentity`, `identity.py` L108) | peer MAC validated by `IdentityValidator.peer_mac` | R63 |
| Hourly observation | entity key plus UTC hour | metric name, metric unit, value, and capture time | FR-006 |
| Summary | scope, period type, and period start in UTC | daily, weekly, or monthly value with equal weights | FR-006 |
| Snapshot | organization and scope | current values and capture time | R66 |
| Refresh lease | `misthelper:wan:v1:refresh:{org_id}` | owner token and expiry | R66 |
| Worker lease | `misthelper:wan:v1:worker:{org_id}` | owner token and expiry | R90 |
| Synthetic record | not stored | `data_origin` set to `synthetic` | D-10 |

## Identifier rules

- Identifiers match `^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$` (`IdentityValidator.IDENTIFIER_PATTERN`, `identity.py` L10).
- Identifiers `.` and `..` are rejected.
- Peer MAC values use 12 hexadecimal digits or six colon-separated octets (`PEER_MAC_PATTERN`, `identity.py` L11-13).
- Port names reject control characters and path components (`identity.py` port_name method).

## State transitions

- Refresh lease: `free` to `held` by `SET NX` with a 300-second expiry. `held` to `free` by release or expiry. Renewal extends the expiry before it ends.
- Snapshot: `empty` to `current` after a successful refresh. `current` to `stale` when the capture time is older than 3600 seconds.
- Hourly observation: `missing` to `stored` after one write. A later write for the same key replaces the row (upsert on the natural key).
- Summary: `no history` when no hourly row exists for the scope. `partial` when the period has fewer rows than hours. `complete` when every hour has one row.

## Storage rules

- Writes go through `DataExporter.write_with_format_selection()` (D-7).
- Each new endpoint key needs an entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (`src/foundation/support/refactors/endpoint_primary_key_strategies.py`) before the write code runs.
- The configured SQLite file is `data/mist_data.db`. The Safety section of `.github/copilot-instructions.md` (line 309 onward) names this store.
- A write that fails returns a store-error state. No success message appears on failure.
