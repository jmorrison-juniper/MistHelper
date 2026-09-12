# Implementation Plan Addendum: Adaptive Rate Limiting for AP Profile Migration

**Branch**: `1029-ap-profile-migration` (no new branch)
**Date**: 2026-07-27
**Parent Plan**: [plan.md](./plan.md)
**Addendum Spec**: [spec-addendum-rate-limiting.md](./spec-addendum-rate-limiting.md)
**Status**: Ready for `/speckit.tasks`

## Summary

Wire the migration operation (menu 207) and the revert operation
(menu 208) into the existing PID-based API rate limiter at
`src/utils/rate_limiting.py` so bulk runs of 10,000 APs stay under
Mist's 5000-request-per-clock-hour ceiling. Preserve every parent-
spec guarantee: stop-on-failure semantics for non-429 errors, per-AP
retry bounds, backup-before-first-PUT, dry-run silence. Feed 429
responses back to the PID limiter as an error signal by invalidating
the shared `_api_usage_cache`, which triggers a live refresh from
Mist on the next iteration and grows the returned delay.

The addendum adds **no new module**, **no new third-party
dependency**, **no new limiter API**, and **no new menu entry**. It
modifies only `src/device/ap_profile_migration_manager.py` and the
matching unit-test module.

## Technical Context

**Language / Version**: Python 3.13+ (unchanged from parent).

**Primary Dependencies**: `mistapi >= 0.63.1` (installed surface
`0.63.3`) and existing `src/utils/rate_limiting.py`. No new
third-party dependency (FR-A10, SC-A08).

**Storage**: No new file schema. The backup JSON file schema from
parent FR-013 is unchanged. Pacing statistics land in the operator
summary text and in the existing JSONL audit line (see
`data-model-rate-limiting.md` for the added `pacing` sub-dict).

**Testing**: `pytest` with `pytest-mock` and `caplog`. All pacing
tests co-locate under the existing
`tests/unit/device/test_ap_profile_migration_manager.py`. Every
pacing test patches `time.sleep` at
`src.device.ap_profile_migration_manager.time.sleep` per Q4 of
`research-rate-limiting.md`; a 10,000-AP synthetic run completes in
under two wall-clock seconds.

**Target Platform**: unchanged cross-platform Python CLI.

**Project Type**: unchanged single-project CLI.

**Performance Goals**: Serial 10,000-AP migration completes without
a 429-triggered halt (SC-A01, SC-A02). Steady-state pacing hovers
near `3600 / 5000 = 0.72 s` per PUT; fallback path uses
`_LIMITER_FALLBACK_DELAY = 0.75 s` (Q1). No perceived freeze because
progress prints (parent SC-004) fire on the same cadence.

**Constraints**:

- FR-A03: MUST NOT add a new `RateLimitingUtils` method. 429 feedback
  goes through cache invalidation (`_api_usage_cache["initialized"] = False`),
  which the limiter's existing `_needs_refresh` predicate already
  honors. See Q2 of `research-rate-limiting.md`.
- FR-A04: 429 MUST NOT trigger the parent's stop-on-failure halt.
  Only non-429 4xx/5xx and transport errors do.
- FR-A05: A per-AP retry storm on 429 alone still counts as that AP
  failing after retries exhaust; the limiter feedback fires on every
  429 regardless.
- FR-A06: Limiter fault MUST NOT halt the migration. Fall back to a
  fixed conservative `time.sleep(0.75)` and continue.
- FR-A07: Pacing MUST call `time.sleep(...)` by module-level
  reference so `unittest.mock.patch("src.device.ap_profile_migration_manager.time.sleep", ...)`
  intercepts it. This matches the existing pattern documented at
  line 742 of the manager.
- FR-A08: Dry-run mode issues no PUT and MUST NOT consult the
  limiter.
- FR-A09: Summary and JSONL audit line MUST expose the four pacing
  fields (`puts_issued`, `http_429_seen`, `non_429_failures`,
  `delay_seconds_mean`, `delay_seconds_max`).
- FR-A11: All new operator-visible strings MUST pass ASD-STE100.
- FR-A12: Docstring coverage on the modified manager module MUST
  stay at or above 90 percent per `DOCS.md`.

**Scale / Scope**: Two loops touched (the migrate loop
`_run_reassignment_loop` and the revert loop at line ~360), three
new private helpers on the class (`_apply_pacing`,
`_signal_rate_limit_hit`, `_is_429`), one new module constant
(`_LIMITER_FALLBACK_DELAY = 0.75`). Estimated diff: ~80-120 LOC in
`ap_profile_migration_manager.py` plus 5-7 new unit tests.

## Locked-In Design Decisions

The five open questions from the addendum spec are resolved in
`research-rate-limiting.md`. The plan pins the resulting choices
here so `/speckit.tasks` and implementation cannot re-open them:

| # | Decision | Value / Location |
|---|----------|------------------|
| 1 | Fallback pacing delay (FR-A06) | `_LIMITER_FALLBACK_DELAY = 0.75` seconds, module scope of `ap_profile_migration_manager.py`. |
| 2 | Pre-PUT call shape | `smoothed, delay = mh.RateLimitingUtils.get_rate_limited_delay(smoothed, mh.apisession, mh._api_usage_cache); time.sleep(delay)`. Verbatim match to `api_data_fetcher.py._apply_rate_limiting`. |
| 2 | 429 feedback surface | Set `mh._api_usage_cache["initialized"] = False`. Forces `_needs_refresh` -> `True` on the next call, which triggers `_refresh_api_usage` and drives the PID error term up. No new limiter method. |
| 3 | Shared limiter across menus | No shared instance. Each loop owns a per-invocation `smoothed: float \| None = None` local. Shared state is the module global `mh._api_usage_cache` only. Acquire via `importlib.import_module("MistHelper")`. |
| 4 | Hermetic-test patch site | `src.device.ap_profile_migration_manager.time.sleep`. Optional pure-unit stub of `RateLimitingUtils.get_rate_limited_delay` returning `(None, 0.0)`. One integration test leaves the real limiter engaged with a pre-seeded `_api_usage_cache`. |
| 5 | Manager seams | `_reassign_one_ap` and `_revert_one_ap` gain **no** kwarg. Outer loops call `_apply_pacing(smoothed)` once per iteration and `_signal_rate_limit_hit()` on any observed 429. Per-AP retry backoff `time.sleep(_RETRY_BACKOFF_SECONDS[attempt])` is **unchanged**. |

## Constitution Check

Evaluated against `.specify/memory/constitution.md` v1.4.0 (seven
Core Principles). This is a re-check of the parent plan's gate
after the addendum's design collapses in.

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | Three new helpers (`_apply_pacing`, `_signal_rate_limit_hit`, `_is_429`) each do exactly one thing. Each modified loop still orchestrates <=5 items per iteration (pacing call, PUT, success accounting, failure accounting, telemetry). |
| II. Class-Based Architecture | PASS | All new helpers are static methods on the existing `APProfileMigrationManager`. No new class, no new module. |
| III. Safety-First (Destructive Operations) | PASS | 429 is explicitly **not** a hard failure (FR-A04). Non-429 hard failures preserve parent FR-017 verbatim. Dry-run stays PUT-free and limiter-free (FR-A08). No new confirmation prompt required; parent's `MIGRATE`/`REVERT` keywords cover the operation identity. |
| IV. Full Deployment Pipeline | PASS | Feature ships through existing CI (ruff, black, mypy, pytest, interrogate, pydoclint, ASD-STE100 lint, destructive-registry guardrail). No new gate. `SC-A06` re-asserts the suite-wide green. |
| V. Observability (Action Logging non-negotiable) | PASS | Every observed 429 logs a warning that names the AP ID and the fresh delay. Every limiter fault logs a warning that names the fallback delay. Summary carries the four FR-A09 pacing fields. JSONL audit gains a `pacing` sub-dict. Parent's per-PUT `info` line is unchanged. |
| VI. Inline Comments For Non-Obvious Blocks | PASS | Three non-obvious spots need annotations: (a) the cache-invalidation trick as the "429 error signal" surface, (b) the deliberate choice to keep per-AP retry backoff outside the pacing path (FR-A05 semantics), (c) the fallback-delay branch on limiter fault. Each carries a short `#` comment. |
| VII. Documentation Coverage (>=90 percent) | PASS | Three new static methods carry Google-style docstrings with "Why" sections per `DOCS.md`. Modified loop docstrings extend to name the pacing behavior. `interrogate` gate holds; `pydoclint --style=google` passes. |

**Gate result**: PASS (zero variances).

## Project Structure

### Documentation (this addendum, under existing feature folder)

```text
specs/1029-ap-profile-migration/
|-- plan-rate-limiting.md              # This file
|-- research-rate-limiting.md          # Phase 0 output
|-- data-model-rate-limiting.md        # Phase 1 output (schema extension)
|-- quickstart-rate-limiting.md        # Phase 1 output (validation runbook)
|-- spec-addendum-rate-limiting.md     # Input (unchanged)
|-- checklists/
|   `-- rate-limiting.md               # Input (unchanged)
|-- plan.md                            # Parent -- NOT modified
|-- spec.md                            # Parent -- NOT modified
|-- research.md                        # Parent -- NOT modified
|-- data-model.md                      # Parent -- NOT modified
|-- quickstart.md                      # Parent -- NOT modified
`-- tasks.md                           # Parent -- NOT modified
                                       # (addendum tasks land in a
                                       # separate `tasks-rate-limiting.md`
                                       # via `/speckit.tasks`)
```

`contracts/` is not created for the addendum. The addendum exposes
no external interface; the summary and JSONL fields are documented
in `data-model-rate-limiting.md`.

### Source Code (repository root)

```text
src/
|-- device/
|   `-- ap_profile_migration_manager.py   # MODIFIED
|                                         # - +1 module constant
|                                         #   (_LIMITER_FALLBACK_DELAY)
|                                         # - +3 static-method helpers
|                                         #   (_apply_pacing,
|                                         #    _signal_rate_limit_hit,
|                                         #    _is_429)
|                                         # - migrate loop calls
|                                         #   _apply_pacing once per
|                                         #   iteration
|                                         # - revert loop calls
|                                         #   _apply_pacing once per
|                                         #   iteration
|                                         # - both loops call
|                                         #   _signal_rate_limit_hit
|                                         #   on observed 429
|                                         # - summary and telemetry
|                                         #   payload gain the four
|                                         #   FR-A09 fields
|-- utils/
|   `-- rate_limiting.py                  # UNCHANGED -- consumed only
`-- api/
    `-- api_data_fetcher.py               # UNCHANGED -- reference
                                          # pattern only

tests/
`-- unit/
    `-- device/
        `-- test_ap_profile_migration_manager.py  # MODIFIED
                                                  # - +7 pacing tests
                                                  #   covering
                                                  #   SC-A01..SC-A07
```

**Structure Decision**: The addendum touches exactly one production
file and one test file. No new module. No new package. The static-
method decomposition pattern (parent Principle II) absorbs the three
new helpers without a new class.

## Phase Ordering

- **Phase 0 (Research)**: complete. See `research-rate-limiting.md`.
- **Phase 1 (Design & Contracts)**: complete. See
  `data-model-rate-limiting.md` (schema extension) and
  `quickstart-rate-limiting.md` (validation runbook). No
  `contracts/` file (rationale in Project Structure).
- **Phase 2 (Tasks)**: not this command. `/speckit.tasks` will
  generate `tasks-rate-limiting.md` from these artifacts.

## Complexity Tracking

> No violations. This section is empty by design.

The addendum introduces no exception to any constitutional
principle. Cache invalidation as a "429 error signal" is the
existing feedback path in `_needs_refresh`; the addendum consumes
it as-is instead of adding a new limiter surface. No new dependency,
no new module, no new gate, no schema break.

## References

- Addendum spec: `spec-addendum-rate-limiting.md` FR-A01..FR-A12,
  SC-A01..SC-A08.
- Parent plan: `plan.md` (unchanged; addendum inherits every
  constitutional gate).
- Reference caller: `src/api/api_data_fetcher.py._apply_rate_limiting`
  and `_is_rate_limit_error`.
- Limiter: `src/utils/rate_limiting.py` (`RateLimitingUtils`,
  `_needs_refresh`, `_refresh_api_usage`).
- Manager sites of change: `src/device/ap_profile_migration_manager.py`
  (`_RETRY_BACKOFF_SECONDS` line ~51, `_reassign_one_ap` line ~732,
  `_run_reassignment_loop` line ~777, revert loop line ~360,
  `_revert_one_ap` line ~1158).
