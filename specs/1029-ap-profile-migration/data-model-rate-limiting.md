# Data Model Addendum: Pacing Telemetry for AP Profile Migration

**Feature Branch**: `1029-ap-profile-migration`
**Parent Data Model**: `data-model.md`
**Addendum Scope**: Extends the summary text and the JSONL audit line
with the pacing statistics required by FR-A09. Does **not** change the
backup JSON schema defined in parent FR-013.

## Scope

The addendum adds four measurable pacing fields to the operator-visible
summary and to the append-only JSONL telemetry line. The backup file
schema (parent `data-model.md` section 1) is untouched. This preserves
parent SC-003 (the backup file remains sufficient input for revert).

## 1. Backup file schema

**Unchanged** from parent `data-model.md` section 1. The pacing
statistics do not belong in the recovery record because they are not
required to replay the migration.

## 2. Operator-visible summary (extends parent section 2.1)

The summary block printed at the end of a migration or revert run
gains four lines (FR-A09):

```text
Total PUTs issued        : <int>
HTTP 429 responses seen  : <int>
Non-429 failures         : <int>
Rate limiter delay (s)   : mean=<float, 3 dp>  max=<float, 3 dp>
```

Field definitions:

| Field | Type | Notes |
|-------|------|-------|
| `Total PUTs issued` | `int` | Count of PUT calls the operation issued, including any retries inside the per-AP retry loop. |
| `HTTP 429 responses seen` | `int` | Count of PUT responses whose `status_code == 429`. A 429 that repeats on retries increments the count each time. |
| `Non-429 failures` | `int` | Count of PUT responses or exceptions that are not `429`. For the migrate path this value is 0 on a fully successful run (any non-429 failure trips the stop-on-failure halt). |
| `Rate limiter delay (s)` | two `float` values | `mean` and `max` of every delay value returned by `RateLimitingUtils.get_rate_limited_delay` during the run. Reported to three decimal places. `0.000` on a cold-start run where the limiter returned zero for every call. |

If the operation halts under parent FR-017, the summary is still
printed and reflects only the PUTs that were actually issued.

## 3. JSONL audit-line schema (extends parent section 2.2)

The revert path already appends a single JSONL line per invocation via
`TelemetryEmitter` (parent FR-025). This addendum extends that line
with a new `pacing` object. It also adds the same `pacing` object to
the migrate path's equivalent audit line (parent FR-018).

```json
{
  "event": "ap_profile_migration.<migrate|revert>.completed",
  "timestamp_utc": "2026-07-27T14:33:12.041Z",
  "org_id": "...",
  "source_profile_id": "...",
  "target_profile_id": "...",
  "ap_count_planned": 10000,
  "ap_count_reassigned": 10000,
  "ap_count_failed": 0,
  "ap_count_skipped": 0,
  "backup_path": "data/ap-profile-migration_...json",
  "pacing": {
    "puts_issued": 10000,
    "http_429_seen": 100,
    "non_429_failures": 0,
    "delay_seconds_mean": 0.734,
    "delay_seconds_max": 1.812
  }
}
```

Field additions:

| Path | Type | Notes |
|------|------|-------|
| `pacing.puts_issued` | `int` | Same value as the summary's `Total PUTs issued`. |
| `pacing.http_429_seen` | `int` | Same value as the summary's `HTTP 429 responses seen`. |
| `pacing.non_429_failures` | `int` | Same value as the summary's `Non-429 failures`. |
| `pacing.delay_seconds_mean` | `float` | Same value as the summary's `mean=`. Serialized as a JSON number with three-decimal precision. |
| `pacing.delay_seconds_max` | `float` | Same value as the summary's `max=`. |

Existing fields from parent section 2.2 are unchanged. Consumers that
did not read the `pacing` key before will continue to work; consumers
that want pacing analytics can pick up the new key without a schema
version bump because JSONL lines are additive.

## 4. In-memory counters (implementation detail; not part of the
external schema)

Each loop maintains a small counter dict:

```python
pacing_stats: dict[str, float | int] = {
    "puts_issued": 0,
    "http_429_seen": 0,
    "non_429_failures": 0,
    "delay_sum": 0.0,
    "delay_max": 0.0,
    "delay_count": 0,
}
```

At summary time the mean is computed as
`delay_sum / delay_count` if `delay_count > 0`, else `0.0`. This
avoids storing the full delay history and stays O(1) memory during a
10,000-AP run.

## 5. Validation rules

- `puts_issued` is monotonic non-decreasing across the run.
- `puts_issued >= ap_count_reassigned + ap_count_failed` because a
  single AP can consume multiple PUTs across the per-AP retry loop.
- `http_429_seen` is counted against PUTs, not against APs. One AP
  that hits 429 twice on retries then succeeds contributes 2 to
  `http_429_seen` and 0 to `non_429_failures` and 1 to
  `ap_count_reassigned`.
- On a limiter-fault fallback (FR-A06), the delay recorded for that
  iteration is the fixed `_LIMITER_FALLBACK_DELAY = 0.75` value.
  The counter accumulates that value into `delay_sum` and updates
  `delay_max` so the summary honestly reflects what was slept.

## 6. References

- Parent `data-model.md` section 1 (backup schema; unchanged),
  section 2.1 (summary), section 2.2 (JSONL audit line).
- Addendum spec `spec-addendum-rate-limiting.md` FR-A09.
- `src/analytics/telemetry_emitter.py` (`TelemetryEmitter`) --
  existing writer; no code change required beyond adding the
  `pacing` sub-dict to the payload the loop already builds.
