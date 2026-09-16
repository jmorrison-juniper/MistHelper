# Implementation Plan: Capture portal concurrency evaluation

**Branch**: `chore/1988-capture-concurrency` | **Date**: 2026-09-16 | **Spec**: `specs\1988-capture-concurrency\spec.md`

**Input**: Feature specification from `specs\1988-capture-concurrency\spec.md`

## Summary

Measure the capture portal concurrency headroom without changing production behavior. The benchmark compares the current four-worker model with two candidates. The result supports no production change.

## Technical Context

**Language/Version**: Python 3.13 with `mistapi` 0.64.0.

**Primary Dependencies**: Standard library plus existing `src.utils.performance` recorder and privacy filter.

**Storage**: Raw benchmark rows and scrubbed recorder events under `specs\1988-capture-concurrency\measurements\`.

**Testing**: Pytest for the benchmark contract. Existing upgrade portal unit and contract tests cover portal behavior.

**Target Platform**: Windows local worktree and the existing Linux container target.

**Project Type**: Python CLI and Flask web portal.

**Performance Goals**: A candidate must improve median wall time by at least 5 percent with equal result counts.

**Constraints**: Preserve Mist API rate limits, site locks, deterministic results, operator safety controls, and privacy rules.

**Scale/Scope**: One site at a time, with the existing two-wave capture path and tier-three fan-out.

## Constitution Check

- Five-Item Rule: The change adds one benchmark script, one test file, and one spec folder. It changes no production module.
- Class-Based Architecture: The benchmark logic lives in `CaptureConcurrencyBenchmark`. No production wrapper was added.
- Safety-First: No live Mist API request occurs. The benchmark uses synthetic waits.
- Observability: The benchmark uses `Recorder` and writes scrubbed JSON Lines events.
- Quality Gates: Local lint, format, type, complexity, and targeted tests are required before the pull request.

## Source Findings

### Capture requests and data collection

`src\upgrade_portal\capture\collector.py` states that reads run in two waves. Wave one runs the device, wired, wireless statistics, and wireless search groups through `CapturePool`. Wave two runs tier-three reads only after device statistics exist.

`src\upgrade_portal\runtime\pools.py` sets `CAPTURE_WORKER_TARGET` to 4. The four wave-one groups fill that target. Raising the target to 8 leaves no fifth wave-one group to start.

### Upgrade status polling and settle gate

`src\upgrade_portal\upgrade\phase_gate.py` polls two cloud streams every 20 seconds. `src\upgrade_portal\upgrade\gate.py` publishes 360 calls each hour, which is 7.2 percent of the 5000 call quota.

Issue #2644 and pull request #2729 cap the schedule horizon below the site lock life. This evaluation does not change that work.

### Comparison generation

`src\upgrade_portal\compare\diff.py` uses section digests to skip unchanged device sections. That makes comparison a poor target for more concurrency unless a future profile proves changed captures dominate.

### Database and cache access

ArangoDB and Redis are shared stores. The benchmark models the writes as a contended shared writer. Parallel store writes regressed by 63.6743 ms in the synthetic run.

### Browser response time

The production run driver already runs on a background thread. The browser polls status instead of waiting for the long operation inside the request.

## Measurement Method

The benchmark file is `scripts\benchmarks\bench_capture_concurrency.py`. It uses only synthetic waits and the repository performance recorder. It writes raw rows to `specs\1988-capture-concurrency\measurements\raw-data.jsonl` and recorder events to `raw-data.events.jsonl`.

The workload contains the same section count in each scenario. Each run returns 12 results and 0 errors.

| Scenario | Median wall time | Median CPU time | Result count |
| - | - | - | - |
| Current capture pool, 4 workers | 5381.7857 ms | 31.25 ms | 12 |
| Candidate capture pool, 8 workers | 5243.8340 ms | 31.25 ms | 12 |
| Candidate parallel store writes | 5318.1114 ms | 15.625 ms | 12 |

The eight-worker candidate improved median wall time by 2.56 percent. This is measurement noise, not useful headroom.

## Constraint Findings

1. Rate limiting: More capture workers can increase the burst rate without reducing call count. The existing four-worker cap matches the four wave-one groups and preserves the 7.2 percent hourly gate budget.
2. Site lock: A candidate that lengthens store writes or retries can hold the site lock longer. This evaluation recommends no change that could push a run toward the lock bound.
3. Complexity gates: A production change would need small classes and small methods. No production change avoids new Radon or 5-Item risk.
4. Store contention: Parallel store writes are not a safe target because ArangoDB and Redis are shared. The measured candidate stayed below the 5 percent threshold.

## Files Changed

```text
scripts\benchmarks\bench_capture_concurrency.py
tests\unit\benchmarks\test_capture_concurrency_benchmark.py
specs\1988-capture-concurrency\spec.md
specs\1988-capture-concurrency\plan.md
specs\1988-capture-concurrency\tasks.md
specs\1988-capture-concurrency\measurements\raw-data.jsonl
specs\1988-capture-concurrency\measurements\raw-data.events.jsonl
```

## Complexity Tracking

No constitution violation exists. The change adds measurement and documentation only. It does not change `src\upgrade_portal\` production code.


