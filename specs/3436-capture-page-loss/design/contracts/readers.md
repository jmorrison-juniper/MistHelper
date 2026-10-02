# Reader contracts for issue #3436

## Actual readers and callers

| Surface | Actual reader | Actual result consumer |
| - | - | - |
| Capture inventory | `devices.read_inventory` through `_read_group` | `collector.read_devices`, `device_rows`, and `collect_reasons` |
| Capture device statistics | `devices.read_device_statistics` through `_read_group` | The device index, radio source, and `collect_reasons` |
| Gate fleet statistics | `gate.read_fleet_statistics` | The existing phase and organization gate readers |
| Wireless statistics | `clients.fetch_wireless_stats_rows` through `_collect` | `collector.wireless_records` and `collect_reasons` before final assembly |
| Tier 3 map reads | The four native fetchers through `extras._paged` | `ExtraSection`, port derivation, and the existing collector before final assembly |

## Lost later page

A later refusal, unreadable body, malformed shape, or absent response stops the walk.
The result retains earlier valid pages.
Its reason uses `page_count_mismatch`.
Its status equals that later response's status, or `0` if no response exists.
No subsequent page call occurs.
No error-body key becomes a record.

A malformed individual record must stay inside the read boundary.
It must not create a silent complete result.

## First page and successful reads

The existing first-page guard classifies refusal, absent status, unknown shape, and body-total mismatch.
It does not read header totals.
A complete paged read keeps the same values and order.
A valid empty list or results list remains successful.
The client join keeps its existing address order and field precedence.

The three loud map client reads keep their existing visible failure behavior.
Their endpoint parameters and short search window stay unchanged.

## Final capture

The final document must retain each available wireless and extra section record.
The existing collector mapping supplies these report rows.

| Source | Report row |
| - | - |
| `devices_inventory`, `devices_statistics` | `devices` |
| `wireless_statistics` | `clients_wireless` |
| `switch_ports`, `poe`, `tunnels`, `bgp_peers` | `extras` |
| `alarms` | `alarms` |

The `source` field preserves the precise source name.
The `reason` and `http_status` fields remain exact.
The document reports `partial` when a required read carries a reason.
No store call is necessary to prove this document contract.

## Protected boundaries

No change to endpoint type, `vc`, fields, limit, filter, SDK version, rate limit, or scheduling is authorized.
No change to keys, topology, normalization, schema, or firmware-read decisions is authorized.
No change to writes, settle policy, confirmations, or numeric-input policy is authorized.
Human review is mandatory before merge.
