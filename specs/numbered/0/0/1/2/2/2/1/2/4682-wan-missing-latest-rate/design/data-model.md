# Data Model: Report a missing latest WAN rate

The change adds no table, no stored field, and no key. The entities below describe the in-memory model that the change touches. Each source names a row in `design/research.md`.

## Entities

| Entity | Natural key | Source | Change |
| - | - | - | - |
| Circuit | Gateway identity and port name | The port target passed to `collect_for_port` (R-62) | None |
| Metric | Metric name, `rx_bps` or `tx_bps` | The metrics parameter of `getSiteInsightMetricsForGateway` (R-50) | None |
| Interval scope | Port or gateway scope | The expression that selects `10m` for a port and `1h` for a gateway (R-57) | None |
| Interval | Interval name and interval start (UTC) | The `rt` and `results` arrays, aligned by position (R-47, R-59) | The latest interval is found by its expected start (D-4, R-56, R-78) |
| Rate sample | Requested hour, metric, and interval name | The builder output on main (R-01) and on the pull request head (R-53) | `value` and `missing_reason` change. The contract in `design/contracts/rate-sample.md` lists the rules. |

## Natural Key Rules

- A rate sample is unique for one requested hour, one metric, and one interval name.
- An interval is unique by its start instant. Text comparison is not enough, because the offset can differ.
- The latest expected interval start is `start` plus `interval_seconds` times `maximum_samples` minus one.

## State Transitions for a Rate Sample

- **Requested** to **Failed**: The HTTP status is not 200. The existing `ConnectionError` stops the request. No rate sample is created.
- **Requested** to **Rejected**: The window, alignment, interval name, or value checks fail. The existing `ValueError` stops the request. No rate sample is created.
- **Requested** to **Valid**: The latest expected interval holds a number. `value` is that number. `missing_reason` is None.
- **Requested** to **Unavailable with earlier values**: The latest interval is absent or null. At least one earlier valid value exists. `value` is None. `missing_reason` is "The latest interval has no value.".
- **Requested** to **Unavailable without values**: No valid value exists. `value` is None. `missing_reason` is "The API snapshot has no value.".

## Persistence Note

The change does not add a field to any stored record. Each stored rate sample keeps the same field names. Unverified item U-6 in `design/research.md` records the store code that was not read.
