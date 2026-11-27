# Data Model: WAN Duplicate Sample Coverage

## Entities and Natural Keys

| Entity | Natural key | Fields | Source |
| - | - | - | - |
| Expected interval | Hour start in UTC, interval seconds, and slot index from 0 | Timestamp in UTC ISO 8601 form | `_sample_points` expected set, PR #4208 head line 320 |
| Point | Metric name and timestamp in UTC | `timestamp`, `value` as a float in bit/s or missing | `_sample_points` output, PR #4208 head lines 325 to 328 |
| Insight sample | Device identifier, selected port name, metric name, hour start in UTC, and interval | `metric`, `unit`, `hour_start_utc`, `value`, `raw_values`, `sample_count`, `coverage_fraction`, `missing_reason`, `points` | `_sample`, PR #4208 head lines 270 to 288 |
| Congestion metric | Hour start in UTC and threshold percent | `metric`, `value`, `sample_count`, `coverage_fraction`, `missing_reason` | `_congestion_metric`, PR #4208 head lines 429 to 440 |
| Hourly measurement | Natural key of the measurement, as read by `SummaryValidation.check` | Metrics mapping and hour start in UTC | `summary.py` line 89 |

## Point States

1. Accepted. The timestamp belongs to the expected set and appears once.
2. Identical duplicate. The timestamp appears again with the same normalized value. The fix keeps one point.
3. Conflicting duplicate. The timestamp appears again with a different normalized value. The fix raises `ValueError`.
4. Missing value. The point has a `null` value. The interval stays unknown.

A point outside the expected set is rejected before the duplicate check. The existing membership check handles that case.

## Insight Sample States

| State | Condition | Coverage fraction |
| - | - | - |
| Complete | Six known unique intervals for 10 minutes, or one known interval for 1 hour | 1.0 |
| Incomplete | At least one known unique interval and at least one unknown interval | Greater than 0.0 and less than 1.0 |
| Empty | No known interval | 0.0 |

The fix changes how an insight sample reaches the Complete or Incomplete state. It does not add a state.

## Congestion Metric States

| State | Condition | Value |
| - | - | - |
| Computed | `sample_count` is 6 | Minutes over the threshold, multiplied by 10 |
| Missing | `sample_count` is less than 6 | Missing, with a reason |

## Summary Inclusion Transitions

1. Read the congestion metric for one threshold in one hour.
2. Exclude the hour when the metric is missing or the value is missing.
3. Exclude the hour when `coverage_fraction` is not 1.0. This check exists at PR #4208 head line 416.
4. Exclude the hour when `sample_count` is not 6. The fix adds this check in T008.
5. Include the hour. Add its minutes and count one complete hour.

## Hour Lifecycle

1. The collection requests one completed UTC hour.
2. The collection validates each returned point. A conflicting duplicate ends the collection before publication. On the port path, it also ends before the history write at `live_service.py` line 77.
3. The collection builds one insight sample for each rate. Each sample reports its coverage.
4. The collection computes utilization from aligned unique points.
5. The collection computes congestion only for a sample count of six.
6. The summary counts the hour only when the summary guard passes.
