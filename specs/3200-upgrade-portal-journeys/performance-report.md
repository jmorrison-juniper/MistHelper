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
| 1 | Capture | 52.653 |
| 2 | History | 46.888 |
| 3 | Confirm | 39.801 |
| 4 | Run | 39.787 |
| 5 | Options | 39.462 |

## Slowest API calls

| Rank | API call | p95 (ms) |
| - | - | -: |
| 1 | Inventory | 3.512 |
| 2 | Sites | 3.419 |
| 3 | Run versions | 2.494 |
| 4 | Capture status | 2.377 |
| 5 | Run status | 2.108 |

## Polling cost

| API call | Cost per minute (ms) |
| - | -: |
| Capture status | 38.280 |
| Run status | 3.490 |

Each sampled page and API call returned status 200. The browser reported zero
faults and no long tasks. The measurements describe this local run only. They
are not production latency measurements.

## Validation

Command:

```sh
UPGRADE_PORTAL_JOURNEYS=1 .venv/bin/python -m tests.e2e.upgrade_portal.journeys.run_journeys --parallel 1
```

Result: 37 passed, 3 xfailed. The report uses the measurements from this run.
