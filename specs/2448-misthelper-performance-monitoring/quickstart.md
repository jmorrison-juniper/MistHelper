# Performance monitoring quickstart

## 1. Confirm the inventory

The inventory is historical evidence from source revision
`7c4e57f3db93afda4c93ef0aec1e73c35fb7774e`.
Do not regenerate it or compare it with `HEAD`.
Validate its paths against the recorded source revision:

```powershell
git ls-tree -r --name-only 7c4e57f3db93afda4c93ef0aec1e73c35fb7774e
```

The inventory keeps the exact rows and counts from that scan.
The guard checks every inventory path against that Git tree.
It does not compare inventory paths with current source files.
If the checkout has shallow history, fetch the recorded revision before the guard runs:

```powershell
git fetch --no-tags --depth=1 origin 7c4e57f3db93afda4c93ef0aec1e73c35fb7774e
```

The `root-and-contracts` CI shard fetches this revision before its tests.

## 2. Select a hook

Open `artifacts/hook-catalog.csv`.
Select one `production hook` row for runtime instrumentation.
Select one `aggregate boundary only` row for profiler correlation.

Do not add a local timer to an aggregate-only file.
Keep this catalog active and update each affected path after a source move.
Resolve every hook row against the current source tree.
Do not add a path map for moved files.

## 3. Build a safe workload

Create sanitized small, medium, and large fixtures.
Create typical and worst-case variants.
Define cold and warm state controls.
Verify the expected output outside the timed boundary.

## 4. Capture an uninstrumented baseline

Use `perf_counter_ns` and `process_time_ns` in the benchmark harness.
Keep timing separate from profiling and memory tracing.

If `pyperf` is available, use this pattern:

```powershell
python -m pyperf command -o baseline.json -- python WORKLOAD.py
python -m pyperf check baseline.json
python -m pyperf stats baseline.json
```

If `pyperf` is unavailable, use repeated in-process measurements.
Record the reduced process isolation.

## 5. Collect attribution

```powershell
python -m cProfile -o profile.pstats WORKLOAD.py
python -X importtime WORKLOAD.py
```

Use `cProfile` for call attribution.
Use `-X importtime` only for startup analysis.
Do not use either output as the acceptance timing.

## 6. Collect memory

Run `tracemalloc` in a separate diagnostic process.
Record traced current and peak bytes.
Collect RSS with a separate supported process monitor.

Do not compare traced bytes with RSS.

## 7. Validate events

Validate each event against:

```text
contracts/performance-event.schema.json
```

Confirm that each event has an allowlisted dimension set.
Confirm that no event holds private data.

## 8. Compare a candidate

Run the same workload, fixture, interpreter, and environment.
Save the candidate result under a different name.

```powershell
python -m pyperf command -o candidate.json -- python WORKLOAD.py
python -m pyperf compare_to --table baseline.json candidate.json
```

Report the median, MAD or IQR, sample count, memory, and I/O counts.
Reject a result that does not exceed measurement uncertainty.

## 9. Apply the decision rule

Require at least a five percent gain in an important end-to-end path.
Alternatively, require at least a ten percent gain in an isolated hotspot.
Reject a change that breaks behavior, privacy, safety, or resource limits.
