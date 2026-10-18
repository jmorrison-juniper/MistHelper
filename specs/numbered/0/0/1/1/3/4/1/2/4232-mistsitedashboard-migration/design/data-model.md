# Data model: Site health dashboard

## Current offline contract

`ServiceMeasurement` is an immutable value with `total` and `degraded` counts.
Each count is an integer or `None`.
Both absent counts mean unavailable data.
One absent count is invalid.
Boolean, fractional, infinite, string, and negative counts are invalid.
Degraded counts must not exceed total counts.

The derived `percentage` is `100 * (total - degraded) / total`.
Zero total returns `None`, not zero or 100.
No display rounding occurs in the model.
Validation raises `ValueError` with a fixed message and logs no caller values.
The model has no network, database, route, environment, or clock dependency.
Tests use synthetic records only.

## Future scoped records

| Entity | Natural identity | Fields and validation |
| --- | --- | --- |
| Site | Organization UUID plus site UUID | Display name, validated organization membership |
| Device snapshot | Organization, site, device UUID, collection UTC | Type, state, model, address, running firmware, uptime |
| Service record | Organization, site, category, exact metric, start UTC, end UTC | Measurement, units, state, collection UTC |
| Affected item | Service key, classifier, item type, source identity | Impact duration, events, failure rate, safe display fields |
| Refresh state | Organization, site or organization scope, period, category | Generation, state, last success UTC, failure code |

Do not strip metric suffixes or invent a natural identity when the source supplies none.
Reject incompatible units before combining samples.
Unknown device state remains a separate count.
An absent running firmware version remains absent with its cause.
Do not substitute configured firmware for the running version.

## State transitions

Future refresh follows `idle -> loading -> ready`, `empty`, `partial`, or `error`.
A failed refresh preserves the last complete snapshot and marks it stale.
An unavailable metric does not become ready merely because another metric succeeded.
A changed selection invalidates the earlier request generation.
Validate membership again before persisting or exporting scoped data.

## Persistence boundary

The current slice writes no records.
Future collected data uses the selected existing output backend and declared primary-key strategies.
Use natural composite keys to prevent duplicate refresh records.
Keep all product outputs under `data/`.
Use existing private storage access, backup, and recovery procedures.

Do not add persistent history by default.
Persist one validated latest snapshot per scope only after approval.
Retention for client identifiers and history remains part of the access decision.
If the durable write fails, report failure and retain the previous complete snapshot.
