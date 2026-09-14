# Plan: Exclusion drift cache

## Workload
Run `python scripts/check_exclusion_drift.py --format github --output exclusion-drift.json` from the repository root.

## Measurement
Use `time.perf_counter_ns()` for wall time. Use `time.process_time_ns()` for parent process CPU time. Count `Path.rglob()` calls and `subprocess.run()` calls. Start `tracemalloc` only for separate memory runs.

## Change
Cache mypy file lists by manifest digest and scan path. Cache completed tool runs by manifest digest, gate, and scan path. Build mypy batches from a command length budget instead of a fixed file count.

## Risk controls
Keep manifest loading and validation unchanged. Clear caches when the manifest text changes. Compare complete standard output and the JSON artifact exactly.
