# Data Model: Mixed WAN History Summaries

The repair changes no stored data. The summaries compute in memory from stored hourly records. Repository paths use forward slashes. Remote checks refer to the numbered rows in `design/research.md`.

## Entities

### HourlyMeasurement

- Source: `src/interfaces/wan_performance/domain/measurement.py`. The frozen dataclass starts at line 64 (remote check 84).
- Fields: `identity`, `hour_start_utc`, `collected_at_utc`, `metrics`, `provenance`, and `is_up_observation`.
- Natural key: the identity natural key, followed by the ISO text of `hour_start_utc`. The property returns that tuple at line 105. The property starts at line 103 (remote check 60).
- Metrics map: metric name to `MetricMeasurement`.

### MetricMeasurement

- Source: `src/interfaces/wan_performance/domain/measurement.py`. The `value` field is the one that accepts `None` (remote check 59).
- Fields: `value`, `unit`, `sample_count`, `coverage_fraction`, `missing_reason`, and `raw_values`.
- The `value` field accepts `None` (remote check 59). A `None` value marks an unmeasured metric. `missing_reason` gives the cause.

### CalendarPeriod

- Source: `src/interfaces/wan_performance/domain/calendar.py`.
- Field `kind` names the period. The summary builder uses six kinds: `daily`, `weekly`, `monthly`, `rolling_3h`, `rolling_12h`, and `rolling_24h` (remote checks 56 and 57).
- Property `expected_hours` returns the number of hours in the period (remote check 58). A daily period has 24 expected hours.

### LinkEventSummary

- Source: `src/interfaces/wan_performance/domain/summary.py`. The dataclass has the optional totals (remote check 85 covers line 47).
- Fields: `complete_hours` (int), `known_hours` (int), `expected_hours` (int), `up_minutes` (float or None), `down_minutes` (float or None), `flap_count` (float or None), and `observed_up_percent` (float or None).
- Natural key: none. The object is computed on request and is not stored.

### PeriodSummary

- Source: `src/interfaces/wan_performance/domain/summary.py`. Field `link_event_summary` is declared at line 73 (remote check 86).
- The field holds one `LinkEventSummary` or `None`. The object is not stored.

## Hour Evidence States

The `flap_count` metric decides the state of each hour. The states do not persist as a separate field.

| State | Metric condition | Adds to complete hours | Adds to totals | Effect on the summary |
| - | - | - | - | - |
| Snapshot hour | No `flap_count` key | No | No | Adds nothing. A period with no `flap_count` key has no link-event summary. |
| Incomplete event hour | `flap_count` key with `value` of `None` | No | No | Counts toward no total. Each total stays unknown when no complete hour exists. |
| Complete hour | `flap_count` key with a measured value | Yes | Flap count | Adds to the flap total (remote check 104). |
| Known hour | Complete hour with measured `up_minutes` and `down_minutes` | Yes, and to known hours | Up and down minutes | Adds minutes. The observed percent stays unknown unless both minute totals are known (remote check 103). |

## State Transitions

| From | Trigger | To | Evidence |
| - | - | - | - |
| No stored hour | Ordinary refresh builds snapshot records | Snapshot hour | `live_service.py` line 43 (remote check 71). Snapshot records name `flap_count` only in the insight set (remote check 72). |
| No stored hour, or snapshot hour | Selected-port refresh stores an insight hour | Complete hour or incomplete event hour | `live_service.py` lines 63 to 77 (remote check 100). The insight parser requires `flap_count` for a port (remote checks 72 and 101). |
| Any state | Later write with the same natural key | Replacement state | Natural-key upsert replaces the row for the same port and UTC hour (`documentation/wan-performance.md` line 444, remote check 78). |

The selected-port refresh always writes a `flap_count` key for a port identity. The key carries a value when the event search returns one. Otherwise, the key carries `None` (remote checks 72 and 101).

## Keys and Identity

- Each summary groups records by one identity. The builder filters records by the selected identity before summaries build (remote check 88).
- Each link-event build selects its hours with `CalendarPeriod.contains` (remote check 102).
