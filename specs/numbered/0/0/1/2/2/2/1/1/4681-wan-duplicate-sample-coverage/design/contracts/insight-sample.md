# Contract: Gateway Insight Sample

## Request

The request calls `getSiteInsightMetricsForGateway` from `mistapi.api.v1.sites.insights`. The SDK signature spans lines 290 to 302 of `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py` (RC-48). The SDK route is `/api/v1/sites/{site_id}/insights/gateway/{device_id}/stats` at line 341 (RC-49). The OpenAPI route starts at line 32714 of `documentation/mist-api-openapi31yaml.yaml` (RC-43).

| Query parameter | Value for this feature | Source |
| - | - | - |
| `metrics` | `rx_bps` or `tx_bps`, one call for each rate | SDK signature, lines 290 to 302 (RC-48) |
| `port_id` | Selected port name | SDK signature, lines 290 to 302 (RC-48) |
| `start` and `end` | Epoch seconds for the completed UTC hour | SDK signature, lines 290 to 302 (RC-48) |
| `interval` | `10m` for a port, `1h` for the gateway | OpenAPI interval example at line 59722 (RC-46) |
| `limit` | 6 for `10m`, 1 for `1h` | Snapshot client line 244 at the PR head (RC-64) |
| `page` | 1 | Snapshot client line 244 at the PR head (RC-64) |

## Response

The OpenAPI response schema `response_device_metrics` starts at line 94086 (RC-75). It declares these fields.

| Field | Type | Meaning | Source |
| - | - | - | - |
| `start` and `end` | integer | Epoch bounds of the query window | Schema block, line 94086 (RC-75) |
| `interval` | integer | Aggregation interval in seconds for each sample | Line 94093 (RC-44) |
| `results` | array of string or integer | Values aligned by position with `rt` | Line 94106 (RC-45) |
| `rt` | array of string | Timestamps aligned by position with `results` | Line 94106 (RC-45) |

The schema lists `start`, `end`, `interval`, and `results` as required. The schema does not require `rt`. The snapshot client requires `rt` (PR head line 265, RC-57). This choice fails closed. It is recorded as finding A-09 in `analysis.md`.

## Validation Rules

1. The HTTP status must be 200. Any other status raises `ConnectionError`.
2. The response window must match the requested `start`, `end`, and `interval`. A mismatch raises `ValueError`.
3. `results` and `rt` must be arrays with equal length. The length must not exceed the maximum sample count.
4. Each `rt` value must parse as a UTC instant inside the expected interval set. A value outside the set raises `ValueError`.
5. A repeated `rt` value with the same normalized value counts once.
6. A repeated `rt` value with a different normalized value raises `ValueError`. No sample publishes.

## Normalized Sample

The example shows an hour with five known intervals out of six. The `value` field holds the last known point, as `_sample` does (RC-53).

```json
{
  "metric": "rx_bps",
  "unit": "bit/s",
  "hour_start_utc": "2026-11-26T14:00:00+00:00",
  "value": 1310000.0,
  "raw_values": [1250000.0, 1100000.0, 980000.0, 1020000.0, 1310000.0],
  "sample_count": 5,
  "coverage_fraction": 0.8333333333333334,
  "missing_reason": null,
  "points": [
    {"timestamp": "2026-11-26T14:00:00+00:00", "value": 1250000.0},
    {"timestamp": "2026-11-26T14:10:00+00:00", "value": 1100000.0},
    {"timestamp": "2026-11-26T14:20:00+00:00", "value": 980000.0},
    {"timestamp": "2026-11-26T14:30:00+00:00", "value": 1020000.0},
    {"timestamp": "2026-11-26T14:40:00+00:00", "value": 1310000.0},
    {"timestamp": "2026-11-26T14:50:00+00:00", "value": null}
  ]
}
```

The `points` list holds one entry for each expected interval, in timestamp order. A null value keeps the interval unknown.

## Error Contract

| Condition | Exception | Publication |
| - | - | - |
| HTTP status is not 200 | `ConnectionError` | None |
| Window or interval mismatch | `ValueError` | None |
| Length mismatch, or more than six timestamps | `ValueError` | None |
| Timestamp outside the expected set | `ValueError` | None |
| Conflicting duplicate | `ValueError` | None |

Log lines carry counts and timestamps only. A log line never carries a token or a secret.
