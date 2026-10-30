# Upgrade portal journey performance report

**Feature**: #3200 | **Date**: 2026-10-30

This report measures the local simulated cloud and read-only portal routes. The
journey stopped before the write confirmation. It used no Mist cloud, production
store, or live upgrade. Each page was loaded five times. Each API route was read
20 times.

The p95 value is the 95th percentile.

## Slowest pages

| Rank | Page | p95 (ms) |
| - | - | -: |
| 1 | History | 53.268 |
| 2 | Capture | 51.173 |
| 3 | Options | 40.769 |
| 4 | Run | 40.711 |
| 5 | Confirm | 40.339 |

## Slowest API calls

| Rank | API call | p95 (ms) |
| - | - | -: |
| 1 | Sites | 5.480 |
| 2 | Inventory | 5.105 |
| 3 | Run versions | 3.176 |
| 4 | Run status | 2.963 |
| 5 | Capture status | 2.550 |

## Polling cost

| API call | Cost per minute (ms) |
| - | -: |
| Capture status | 42.040 |
| Run status | 3.954 |

Each sampled page and API call returned status 200. The browser reported zero
faults and no long tasks. The measurements describe this local run only. They
are not production latency measurements.

## Validation

Command:

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1
```

Result: 37 passed, 3 xfailed. The report uses the measurements from this run.
