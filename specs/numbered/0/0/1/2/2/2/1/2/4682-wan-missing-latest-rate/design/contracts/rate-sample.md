# Contract: Rate Sample

**Scope**: The dictionary that the rate sample builder returns for each metric and each requested hour. On the pull request 4208 head, the builder is `GatewayInsights._sample` (R-53). On main, the same contract applies to `GatewayInsightSampleBuilder.build` until the merge replaces it (R-01).

**Source**: The `results` array and the `rt` array of the Mist gateway insight response (R-47, R-49, R-59).

## Fields

| Field | Type | Rule |
| - | - | - |
| `metric` | string | The source metric name, `rx_bps` or `tx_bps`. Unchanged. |
| `unit` | string | Always `bit/s`. Unchanged. |
| `hour_start_utc` | string | The UTC start of the requested hour in ISO 8601 form. Unchanged. |
| `value` | number or null | The value at the latest expected interval start. Null when that interval has no valid value. |
| `raw_values` | tuple of numbers | The valid values in source order. Earlier values stay here when `value` is null. |
| `sample_count` | integer | Equals the length of `raw_values`. Unchanged. |
| `coverage_fraction` | number from 0 to 1 | Equals `len(raw_values)` divided by `maximum_samples` on the pull request head (R-54). Unchanged. |
| `missing_reason` | string or null | Null when `value` is a number. Otherwise one of the two texts in the table below. |
| `points` | list | One entry for each source interval with a `timestamp` and a `value`. Unchanged. |

## Missing Reason Texts

| Condition | Text |
| - | - |
| No valid value exists in the requested hour | The API snapshot has no value. |
| An earlier valid value exists, and the latest expected interval has no valid value | The latest interval has no value. |

## Invariants

- **I-1**: `value` is None if and only if `missing_reason` is a non-empty string.
- **I-2**: When `value` is a number, the number equals the valid value at the latest expected interval start.
- **I-3**: `value` never comes from a position in `raw_values`.
- **I-4**: `sample_count` equals `len(raw_values)`.
- **I-5**: `value` is a finite number that is zero or greater.

## Examples

| Source case | `value` | `missing_reason` | `raw_values` | `sample_count` |
| - | - | - | - | - |
| Six intervals, all valid, latest is 12 | 12.0 | None | Six values | 6 |
| Six intervals, latest is null, fifth is 10 | None | The latest interval has no value. | Five values, ending with 10 | 5 |
| Five intervals, sixth interval absent, fifth is 10 | None | The latest interval has no value. | Five values, ending with 10 | 5 |
| Six intervals, all null | None | The API snapshot has no value. | Empty | 0 |
| Six intervals, latest is measured zero | 0.0 | None | Six values, last one zero | 6 |

## Errors (Unchanged)

| Condition | Exception |
| - | - |
| HTTP status other than 200 | `ConnectionError` |
| `results` is not a list, lengths differ, or the count exceeds `maximum_samples` | `ValueError` (R-59 reads `results`, and R-83 checks the lengths) |
| A timestamp is outside the expected interval starts | `ValueError` (R-78) |
| A value is negative, not finite, or boolean | `ValueError` (R-82) |
