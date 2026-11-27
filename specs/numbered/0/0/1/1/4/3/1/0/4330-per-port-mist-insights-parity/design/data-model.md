# Data Model: Per-port Mist Insights parity in the WAN dashboard

This model describes the entities that the port series feature reads and writes. Redis stores the values. The model adds no database table and no file format.

## Entities

| Entity | Source | Natural key | Key attributes |
| - | - | - | - |
| Gateway | Bulk `gateways` dataset (R-82) | Organization and gateway device UUID | `device_id`, `site_id`, `mac` |
| WAN port | Bulk `ports` dataset with usage `wan`, grouped by gateway MAC (R-13) | Organization, gateway device UUID, and `port_id` | `port_id`, `name`, `mac` |
| Port series | SDK gateway insight response for one port (R-37) | Organization, gateway device UUID, `port_id`, and UTC hour | `timestamp`, `timestamp_utc`, `rx_bps`, `tx_bps` (nullable) |
| Port totals | Derived from one port series | Organization, gateway device UUID, `port_id`, and range | `rx_bytes`, `tx_bytes`, `coverage`, `sample_count`, `state`, `collected_at_utc` |
| Request budget | Worker settings and the cap | One refresh | `cap`, `bulk_calls`, `port_calls`, `refreshes_per_hour`, `planned_calls_per_hour`, `skip_reason` |
| Cursor | Worker status record (R-78) | Organization | `index` into the sorted WAN port list |

The port identifier is the Mist port name, for example `ge-0/0/1`, as the query description states (R-38). The port view uses the same identifier for the cache keys (R-09 and R-76).

## Ranges

A single seven-day hourly series yields every range by slicing from the end of the window.

| Range | Hours | Traffic key | Insight key |
| - | - | - | - |
| 1h | 1 | Yes | Yes |
| 6h | 6 | Yes | Yes |
| 24h | 24 | Yes | Yes |
| 3d | 72 | No | Yes |
| 7d | 168 | Yes | Yes |

The traffic route serves 1h, 6h, 24h, and 7d (R-03 and R-83). The insight route also serves 3d (R-04 and R-84). The worker writes nine range keys for each port. Each write uses the existing last-complete-value writer (R-64).

## Window Rules

- The window end equals the latest completed UTC hour. The window start equals the end minus 604800 seconds.
- Each sample time is the window start plus a whole multiple of 3600 seconds.
- A response window that differs from the request window is malformed.
- A sample time outside the window is malformed.
- A sample count above 168 is malformed.

## Derived Values

| Value | Rule |
| - | - |
| `present_samples` | Count of samples where `rx_bps` and `tx_bps` are both finite, non-negative numbers. A sample with one missing value counts for the value that is present. |
| `coverage` | `present_samples` divided by 168. The value is a fraction from 0 to 1. |
| `rx_bytes` | The floor of the sum of present `rx_bps` values times 3600, divided by 8. |
| `tx_bytes` | The floor of the sum of present `tx_bps` values times 3600, divided by 8. |
| `planned_calls_per_hour` | `refreshes_per_hour` times the sum of `bulk_calls` and `port_calls`. |
| `refreshes_per_hour` | 3600 divided by `WAN_DASHBOARD_REFRESH_INTERVAL_SECONDS` (R-19). |

## State Transitions

| From | To | Trigger |
| - | - | - |
| `unavailable` | `live` | A complete, valid series is written in this refresh. |
| `unavailable` | `partial` | A valid series with a `next` value or fewer than 168 samples is written. |
| `live` | `partial` | A later valid series is incomplete. |
| `partial` | `live` | A later valid series is complete. |
| `live` or `partial` | `stale` | A later refresh fails, the lease is lost, or Redis is unavailable. The last complete value remains with its collection time. |
| `stale` | `live` | A later refresh writes a complete, valid series. |
| `stale` | `unavailable` | The last complete value passes the stale time to live (R-65). |
| Any | `unavailable` | A malformed response arrives and no earlier complete value exists. |

The state `live` requires a series written in the current refresh. The state `stale` never carries a live label.

## Cursor Rules

- The cursor starts at zero for a new organization.
- The port list sorts by device UUID, then by `port_id`, before each refresh.
- The cursor advances by the number of port calls. It wraps to zero at the end of the list.
- A changed port list keeps the cursor value. The index wraps if it exceeds the list length.

## Validation Rules

- A missing gateway field skips that gateway. The worker counts the skip.
- A missing `port_id` and `name` skips that port. The worker counts the skip.
- A non-finite or negative rate sample becomes absent for that sample.
- A boolean rate value becomes absent for that sample.
