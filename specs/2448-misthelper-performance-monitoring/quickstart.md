# Performance monitoring quickstart

## 1. Confirm the inventory

Run these commands from the repository root:

```powershell
git ls-files '*.py'
git ls-files --others --exclude-standard '*.py'
```

Compare the paths with `artifacts/python-inventory.csv`.
The CSV must contain one row for each eligible file.

## 2. Select a hook

Open `artifacts/hook-catalog.csv`.
Select one `production hook` row for runtime instrumentation.
Select one `aggregate boundary only` row for profiler correlation.

Do not add a local timer to an aggregate-only file.

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
