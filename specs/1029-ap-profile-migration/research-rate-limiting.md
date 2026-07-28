# Phase 0 Research: Adaptive Rate Limiting for AP Profile Migration

**Feature Branch**: `1029-ap-profile-migration`
**Addendum**: `spec-addendum-rate-limiting.md`
**Date**: 2026-07-27
**Status**: Complete (all five open questions resolved)

## Scope

Phase 0 answers the five concrete implementation questions raised by
the addendum before Phase 1 design begins. Each entry follows the
Decision / Rationale / Alternatives format required by
`.specify/memory/constitution.md`.

## Open Questions Resolved

### Q1. Exact fallback pacing delay (FR-A06)

**Decision**: `_LIMITER_FALLBACK_DELAY = 0.75` seconds, declared as a
module-level constant in `src/device/ap_profile_migration_manager.py`.

**Rationale**:

- Mist enforces 5000 requests per clock hour per API token. The
  theoretical serial minimum interval is `3600 / 5000 = 0.72 s`.
- `0.75 s` sits `4 percent` above the theoretical minimum. That
  margin absorbs (a) any secondary API calls that share the same
  token during a run and (b) small clock drift between the tool
  and the Mist server that resets the hour window.
- The value stays in the same order of magnitude as
  `_RETRY_BACKOFF_SECONDS = (0.5, 1.0)` already present in the
  manager, so operators do not see a new "large" sleep constant.
- The limiter itself already uses `_FALLBACK_DELAY = 0.5` as its
  internal safety net when its own inputs are missing. Choosing
  `0.75 s` for the manager's outer fallback keeps the two
  fallbacks distinguishable and layered (limiter fault -> caller's
  slightly larger safety net).
- At `0.75 s` per PUT, a 10,000-AP run takes at least
  `7500 s = 125 min`. That matches the operator's real-world
  expectation for a "large migration" and is well inside the
  session lifetime.

**Alternatives considered**:

- `0.5 s`: matches the limiter's own fallback, but reuses the same
  scalar and hides the layering. Also under the theoretical
  minimum -> can still push through the ceiling under fallback.
  Rejected.
- `1.0 s`: matches the existing second-retry backoff, safe by a
  wide margin, but a 10,000-AP run stretches to 166 minutes. Adds
  33 percent wall-clock cost with no corresponding safety win.
  Rejected.
- Compute at runtime from `apisession` usage: over-engineered for
  a fallback path that only runs on limiter fault. The whole point
  of the fallback is to avoid touching the limiter's own state.
  Rejected.

### Q2. Exact `RateLimitingUtils` call shape and 429 feedback surface

**Decision**:

- Pre-PUT pacing: the loop calls
  `mh.RateLimitingUtils.get_rate_limited_delay(smoothed, mh.apisession, mh._api_usage_cache)`
  and unpacks `(smoothed, delay) = ...`, then calls
  `time.sleep(delay)`. This exactly matches the call shape in
  `src/api/api_data_fetcher.py._apply_rate_limiting` (lines
  `88-97` region).
- 429 feedback: after a PUT observes a 429 response, the loop
  sets `mh._api_usage_cache["initialized"] = False`. That flips
  the limiter's `_needs_refresh` predicate to `True` on the next
  call, which forces a live `_refresh_api_usage(mh.apisession)`
  round-trip. The refreshed `used` and `limit` values drive the
  limiter's PID error term upward and grow the returned delay.
- No new limiter method, no new limiter signature, no new module.

**Rationale**:

- FR-A03 forbids adding a new limiter API surface. The existing
  `get_rate_limited_delay` entry is the only public method on
  `RateLimitingUtils` today, and its inputs (`smoothed`, session,
  cache) are already the same three that `api_data_fetcher.py`
  passes. Reusing the exact call site verbatim keeps the change
  minimal and matches the existing pattern the codebase already
  ships.
- The limiter has no explicit "signal error" method. The
  documented feedback path is cache invalidation: setting
  `api_usage_cache["initialized"] = False` (or
  `last_updated = 0.0`) forces a refresh, and the refresh brings
  fresh `used` and `limit` from Mist's `getSelfApiUsage`. That is
  the honest "PID error term went up" input to the limiter's
  smoothing.
- 429 detection reuses `getattr(getattr(err, "response", None), "status_code", None) == 429`,
  the same pattern in `api_data_fetcher.py._is_rate_limit_error`.
  No new detection helper is added.

**Alternatives considered**:

- Add a new `RateLimitingUtils.report_rate_limit_error(...)`
  method: violates FR-A03. Rejected.
- Set `last_updated = 0.0` instead of `initialized = False`: also
  triggers `_needs_refresh` via the elapsed-seconds check. Same
  net effect, but `initialized = False` reads more clearly as
  "invalidate this cache". Chose the clearer flag.
- Add a second sleep on top of the limiter's returned delay after
  a 429 (for example a fixed `time.sleep(2.0)`): duplicates back-
  pressure. The limiter's next-call delay already reflects the
  refreshed usage. Rejected.
- Honor the `Retry-After` header: explicitly out of scope for v1
  per addendum Assumptions. Deferred to a follow-up addendum if
  operational data shows PID convergence is too slow.

### Q3. Single shared limiter instance for menus 207 and 208?

**Decision**: **No shared instance**. Each loop that issues PUTs owns
its own per-invocation `smoothed: float | None = None` local. The
underlying shared state is the module global `mh._api_usage_cache`,
which is the same cache already shared with every other API caller
in MistHelper.

**Rationale**:

- `RateLimitingUtils` is a static-method facade with no instance
  state of its own. The "state" that matters is the smoothed
  delay (a caller-owned scalar) and the API-usage cache (a
  module-global dict). There is nothing to construct.
- Menus 207 and 208 do not run at the same time -- both are
  interactive and single-threaded through the menu dispatch.
  There is no correctness benefit to a shared `smoothed` between
  them.
- Sharing `smoothed` across menus would silently carry state from
  a previous migration into a later revert (or vice-versa) run
  in the same process, which is worse for observability, not
  better.
- Acquisition matches the manager's existing pattern:
  `mh = importlib.import_module("MistHelper")` inside the loop
  method, then `mh.RateLimitingUtils.get_rate_limited_delay(...)`.
  This mirrors `api_data_fetcher.py._apply_rate_limiting` exactly.

**Alternatives considered**:

- Class-level `_shared_smoothed` on `APProfileMigrationManager`:
  couples menu 207 and 208 state without a real reason and makes
  hermetic testing harder (state must be reset between tests).
  Rejected.
- New singleton limiter object under `src/utils/`: adds an entire
  module for a scalar. Rejected -- violates FR-A08 in spirit and
  FR-A10 in letter (no new module for rate-limit handling).

### Q4. Hermetic testing seam

**Decision**:

- Patch `src.device.ap_profile_migration_manager.time.sleep` in
  every test that exercises the migration or revert loop. The
  manager already imports `time` at module scope and calls
  `time.sleep(...)` by attribute access (documented at line 742
  of the manager). That existing seam is the only one required.
- For pure-unit tests that assert call count without exercising
  the real PID math, additionally patch
  `src.device.ap_profile_migration_manager.mh.RateLimitingUtils.get_rate_limited_delay`
  to a `Mock` that returns `(None, 0.0)` (or a fixed delay). This
  isolates the test from `_api_usage_cache` shape drift.
- For one integration-style test that verifies the real limiter is
  wired correctly, do NOT patch `get_rate_limited_delay`. Instead,
  pre-populate `mh._api_usage_cache` with a known
  `{"initialized": True, "used": 4000, "limit": 5000, "last_updated": <now>, ...}`
  shape so `_needs_refresh` returns `False` and the limiter runs
  its own math against that fixed input. Still patch
  `time.sleep`.
- The limiter itself never calls `time.sleep(...)` (verified
  against `src/utils/rate_limiting.py`; it only calls
  `time.time()`), so no patch on the limiter module is needed.

**Rationale**:

- Existing tests in
  `tests/unit/device/test_ap_profile_migration_manager.py` already
  patch `time.sleep` at the manager module level. Reusing that
  seam avoids introducing a second convention.
- Mocking the limiter for pure-unit tests keeps those tests
  deterministic and fast without duplicating the limiter's own
  test coverage that already lives under
  `tests/unit/utils/test_rate_limiting.py`.
- One integration-style test guards the wiring itself (call
  shape, cache mutation on 429, argument order) so the two-layer
  strategy still catches integration regressions.

**Alternatives considered**:

- Patch the global `time.sleep` in the built-in module: leaks
  into unrelated tests running in the same session. Rejected.
- Monkey-patch `RateLimitingUtils` at class scope: works but
  requires cleanup fixtures. Patching the module reference to it
  through `mh` is scoped to each test and auto-cleans via
  `pytest-mock`. Chose the module-level patch.
- Real `time.sleep` with a small delay: makes the 10,000-AP tests
  slow. Rejected outright by SC-A01's "no wall-clock sleep"
  requirement.

### Q5. Exact seams inside the manager

**Decision**:

- `_reassign_one_ap` gains **no new keyword argument**. Its
  signature stays exactly as it is today.
- `_run_reassignment_loop` (migrate path) owns the pacing state.
  It declares `smoothed: float | None = None` at the top and,
  once per outer iteration and before calling `_reassign_one_ap`,
  it calls `_apply_pacing(smoothed)` (a new private static
  helper). `_apply_pacing` returns the updated `smoothed` value.
- The revert loop that begins near line 360 owns its own
  `smoothed: float | None = None` and calls `_apply_pacing` once
  per iteration before `_revert_one_ap`.
- On a 429 observed either by `_reassign_one_ap` raising a
  wrapped exception or by the revert helper returning a failure
  tuple, the enclosing loop calls a second new private helper
  `_signal_rate_limit_hit()` which mutates
  `mh._api_usage_cache["initialized"] = False`. The next
  iteration's `_apply_pacing` sees the invalidated cache and
  gets a refreshed (larger) delay.
- Per-AP retry backoff `time.sleep(_RETRY_BACKOFF_SECONDS[attempt])`
  inside `_reassign_one_ap` and `_revert_one_ap` is **unchanged**.
  The addendum does not add pacing inside the per-AP retry loop;
  the addendum paces only the outer iteration. See FR-A05: a
  429 that exhausts a single AP's retry budget still counts as a
  hard failure, and the limiter feedback still fires on each
  429 encountered.
- 429 detection reuses the two-line `getattr(getattr(...))` check
  from `api_data_fetcher.py._is_rate_limit_error`, copied as a
  small private helper `_is_429(err)` in the manager. This keeps
  the manager self-contained (no cross-module import of a private
  helper).

**Rationale**:

- Passing `smoothed` down into `_reassign_one_ap` would spread
  pacing state into the per-AP helper and force every existing
  test that mocks `_reassign_one_ap` to update its signature.
  Keeping the state in the loop keeps the diff small and
  preserves the parent tests unchanged.
- Two tiny helpers (`_apply_pacing`, `_signal_rate_limit_hit`)
  keep each loop iteration inside the Five-Item Rule per method
  and give the test suite a clean pair of patch points.
- Reusing `_is_rate_limit_error`'s exact pattern -- without
  importing it -- avoids coupling the manager module to
  `api_data_fetcher`'s internals. The pattern is two lines and
  the copy is annotated with an inline comment naming the source
  of truth.

**Alternatives considered**:

- Push pacing inside `_reassign_one_ap` (and thus into every
  retry attempt): would double or triple the effective interval
  during a retry storm and violate FR-A05's clear split (429s
  across APs feed the limiter; 429s that exhaust one AP's
  retries count as failure). Rejected.
- One shared helper on the class that both loops call: viable,
  and this is what the design uses (`_apply_pacing`). Loops keep
  ownership of `smoothed` because that scalar is per-invocation.

## Consolidated Constants and Names

| Name | Value / Type | Where |
|------|--------------|-------|
| `_LIMITER_FALLBACK_DELAY` | `0.75` (float, seconds) | `ap_profile_migration_manager.py` module scope |
| `_apply_pacing` | private static method | `APProfileMigrationManager` |
| `_signal_rate_limit_hit` | private static method | `APProfileMigrationManager` |
| `_is_429` | private static helper | `APProfileMigrationManager` |
| `smoothed` | `float \| None` local per loop | `_run_reassignment_loop`, revert loop |

## References

- `src/utils/rate_limiting.py` (`RateLimitingUtils.get_rate_limited_delay`,
  `_needs_refresh`, `_refresh_api_usage`, `_FALLBACK_DELAY`).
- `src/api/api_data_fetcher.py` (`_apply_rate_limiting`,
  `_is_rate_limit_error`) -- reference caller pattern.
- `src/device/ap_profile_migration_manager.py` (`_reassign_one_ap`
  at line ~732, `_run_reassignment_loop` at line ~777, `_revert_one_ap`
  at line ~1158, revert loop at line ~360,
  `_RETRY_BACKOFF_SECONDS` at line ~51).
- Parent spec `spec.md` FR-017 (stop-on-failure semantics preserved
  for non-429 errors).
- Addendum spec `spec-addendum-rate-limiting.md` FR-A01..FR-A12.

## Output

All five open questions closed. Ready for Phase 1 design.
