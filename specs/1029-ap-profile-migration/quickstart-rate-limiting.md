# Quickstart Addendum: Validating Adaptive Rate Limiting

**Feature Branch**: `1029-ap-profile-migration`
**Parent Quickstart**: `quickstart.md`
**Addendum Scope**: Validation scenarios for SC-A01..SC-A08. Each
scenario is runnable against the existing test suite once the
addendum is implemented.

## Prerequisites

- Working tree on branch `1029-ap-profile-migration`.
- Python 3.13+; project deps installed per `pyproject.toml`.
- Parent feature 1029 already merged into the branch (menus 207
  and 208 present).
- All commands assume repo root as cwd unless noted.

## Setup Commands

```bash
cd src
python -m pytest --collect-only tests/unit/device/test_ap_profile_migration_manager.py
```

Expect the new pacing tests to appear alongside the existing
migration and revert tests.

## Validation Scenarios

Each scenario maps 1:1 to one Success Criterion from the addendum
spec. Run each with `pytest -k` and confirm the assertions.

### SC-A01. 10,000-AP migration, all 200s, hermetic

```bash
cd src
pytest tests/unit/device/test_ap_profile_migration_manager.py \
  -k "test_migrate_10k_paced_all_success" -v
```

Expected:

- Test completes in under 2 seconds wall-clock.
- Mocked `RateLimitingUtils.get_rate_limited_delay` is called 10,000
  times.
- Mocked `time.sleep` (patched at
  `src.device.ap_profile_migration_manager.time.sleep`) is called
  10,000 times.
- The migration reports 10,000 successes, 0 failures.
- Summary output includes the four FR-A09 pacing lines.

### SC-A02. 10,000-AP migration, 429 on every 100th PUT

```bash
cd src
pytest tests/unit/device/test_ap_profile_migration_manager.py \
  -k "test_migrate_10k_paced_429_every_100" -v
```

Expected:

- Test completes with 10,000 successful reassignments.
- 100 429 responses observed; `pacing.http_429_seen == 100` in the
  JSONL audit line and in the summary text.
- `mh._api_usage_cache["initialized"]` is set to `False` at least
  100 times (once per 429).
- Zero stop-on-failure halts. Parent FR-017 is not tripped by 429.

### SC-A03. 10,000-AP revert, 429 on every 100th PUT

```bash
cd src
pytest tests/unit/device/test_ap_profile_migration_manager.py \
  -k "test_revert_10k_paced_429_every_100" -v
```

Expected:

- Revert loop completes with 10,000 reassignments to the recorded
  source profile.
- `pacing.http_429_seen == 100`. Revert audit line contains the
  `pacing` sub-dict.
- No halt; the revert loop already tolerates per-AP errors, and 429
  is handled as a throttle signal.

### SC-A04. HTTP 500 on 42nd PUT still halts

```bash
cd src
pytest tests/unit/device/test_ap_profile_migration_manager.py \
  -k "test_migrate_500_on_42nd_halts_stop_on_failure" -v
```

Expected:

- Migration halts before the 43rd PUT.
- Backup file records exactly 41 successful reassignments.
- Failing AP ID is printed in the stop-on-failure message.
- `pacing.http_429_seen == 0`; `pacing.non_429_failures == 1`;
  `pacing.puts_issued == 42`.
- The 500 is not routed through the cache-invalidation feedback
  path (verified: `mh._api_usage_cache["initialized"]` was not
  toggled to `False`).

### SC-A05. Limiter raises on the 5th call; fallback + continue

```bash
cd src
pytest tests/unit/device/test_ap_profile_migration_manager.py \
  -k "test_migrate_limiter_fault_uses_fallback_and_continues" -v
```

Expected:

- One warning line logged that names the fallback delay.
- The 5th iteration sleeps for exactly `_LIMITER_FALLBACK_DELAY`
  (0.75 s in the code; `time.sleep` mock records `0.75`).
- Migration reaches its planned success count with no halt.

### SC-A06. Suite-wide gates hold

```bash
cd src
pytest -q
ruff check .
interrogate -c ../pyproject.toml src/device/ap_profile_migration_manager.py
```

Expected:

- `pytest` exits 0.
- `ruff check .` reports zero violations.
- `interrogate` reports docstring coverage at or above 90 percent
  for `ap_profile_migration_manager.py`.

### SC-A07. Summary output carries the pacing block

```bash
cd src
pytest tests/unit/device/test_ap_profile_migration_manager.py \
  -k "test_summary_contains_pacing_lines" -v
```

Expected: the four summary lines from `data-model-rate-limiting.md`
section 2 are present in `caplog` (or captured stdout) exactly once
per invocation and in the documented order.

### SC-A08. No new third-party dependency

Manual check (no test):

```bash
git diff main -- pyproject.toml
git diff main -- src/utils/
```

Expected:

- `pyproject.toml` diff is empty (or contains only unrelated
  parent-feature changes; no rate-limit entries).
- No new file under `src/utils/`. `src/utils/rate_limiting.py` is
  the only limiter consulted.

## Cleanup

No persistent artifacts are created by the tests. The parent
feature's `data/` writes are also mocked in the pacing tests.

## Notes

- Every pacing test that exercises the loop must patch
  `src.device.ap_profile_migration_manager.time.sleep` per Q4 of
  `research-rate-limiting.md`. Failure to patch will cause SC-A01
  (10,000-AP hermetic run) to time out at pytest's default limit.
- The one integration-style test (recommended) leaves
  `RateLimitingUtils.get_rate_limited_delay` unpatched but
  pre-populates `mh._api_usage_cache` with a fixed known shape so
  the limiter's PID math runs deterministically without a live
  Mist round-trip. `time.sleep` remains patched.
