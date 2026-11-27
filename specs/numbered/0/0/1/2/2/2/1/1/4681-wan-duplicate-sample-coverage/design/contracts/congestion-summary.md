# Contract: Congestion Summary Inclusion

## Input

The summary reads one `HourlyMeasurement` for each hour. Each congestion metric has `value`, `sample_count`, and `coverage_fraction`. The metric key follows the pattern `congestion_minutes_over_<threshold>_pct`. The key pattern appears in `src/interfaces/wan_performance/domain/summary.py`, line 428 at the PR head (RC-61).

## Inclusion Rule

An hour adds its minutes only when all three conditions hold.

| Condition | Status | Source |
| - | - | - |
| `value` is not missing | Existing rule in the same expression | `summary.py` at the PR head, class start at line 390 (RC-58) |
| `coverage_fraction` equals 1.0 | Existing rule | Summary line 416 at the PR head (RC-14) |
| `sample_count` equals `CongestionDurations.SAMPLES_PER_HOUR`, which is 6 | New rule from task T008 | Class attribute added after the docstring of `CongestionDurations` (RC-58) |

When an hour passes, the summary adds its value to `minutes`. It adds one to `complete_hours`. When an hour fails, it adds nothing.

## Output

The summary returns `CongestionDurationSummary`. The class starts at line 54 of `summary.py` at the PR head (RC-60). Its fields are `threshold_percent`, `complete_hours`, `expected_hours`, and `minutes`.

## Examples

| Hour | `value` | `sample_count` | `coverage_fraction` | Included |
| - | - | - | - | - |
| 14:00 UTC | 20.0 | 6 | 1.0 | Yes. Adds 20.0 minutes and one complete hour. |
| 15:00 UTC | 20.0 | 5 | 1.0 | No. The guard requires six samples, even when coverage reads 1.0. |
| 16:00 UTC | missing | 4 | 0.6666666666666666 | No. The value is missing. |
