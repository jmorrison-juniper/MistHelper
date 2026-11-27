# Contract: Progress Complete Event for Statistics Exports

## Scope

This contract covers the `progress_complete` event for two statistics exports:

- `device_stats`, with progress label "13" and operation name "device_stats".
- `vpn_peer_stats`, with progress label "15" and operation name "vpn_peer_stats".

The event shape stays the same. The rule for `items_processed` changes for failed and empty fetches.

## Event Shape (unchanged)

| Field | Type | Value for these exports |
| - | - | - |
| `event_type` | string | `progress_complete` (RC-20) |
| `timestamp` | string | UTC timestamp in ISO 8601 form |
| `menu_option` | string | `"13"` for `device_stats` and `"15"` for `vpn_peer_stats` (RC-01, RC-04) |
| `operation_name` | string | `device_stats` or `vpn_peer_stats` |
| `total_items` | integer | 1 |
| `items_processed` | integer | 1 or 0, by the rule below (RC-21) |
| `was_stopped` | boolean | `false` (RC-22) |
| `duration_seconds` | number | Wall-clock seconds from the start of the run to the completion event |

## Processed Count Rule (changed)

| Condition | `items_processed` | Event emitted |
| - | - | - |
| `APIDataFetcher.execute()` returns True | 1 | Yes |
| `APIDataFetcher.execute()` returns False, for an HTTP failure, an empty response, an unparsed body, or a rate-limit stop | 0 | Yes |
| Fast-mode cache hit, before the progress start | Not applicable | No (FR-007) |
| `APIDataFetcher.execute()` re-raises an error | Not applicable | No. This behavior is unchanged and out of scope (D-8, RC-11). |

## Consumers

- A consumer that reads `items_processed` as the number of exported items reads 0 for a failed or empty fetch. That count is correct.
- A consumer that treats every completion event as success must read `items_processed` before it reports success.
- A local search found no consumer of these labels in the checked folders. The search covered local copies only (research U-6).

## Compatibility

- The field names, types, and labels do not change (FR-005, FR-006).
- The only change is the value of `items_processed` after a failed or empty fetch. The previous value of 1 was incorrect.
