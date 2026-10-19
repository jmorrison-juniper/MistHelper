# Add opt-in Python performance monitoring

## Summary

Add layered, opt-in performance monitoring for MistHelper.
Use stable production hooks for resource boundaries.
Use profiler correlation for per-file, per-function, and per-class attribution.
Do not add permanent timers to every function.

## Inventory evidence

The AST inventory covers every Python file from the required tracked and
untracked Git lists.
It contains 1,337 files and 31,598 symbols.
The symbols include 27,379 functions, 167 asynchronous functions, and 4,052
classes.
The scan found 17,960 nested symbols and no parse errors.

The scan excludes 9,618 ignored Python files under `.venv`.
These files are package-managed external dependencies.

The file dispositions are:

- 58 `production hook` files.
- 414 `aggregate boundary only` files.
- 762 `benchmark/profile only` files.
- 103 `no hook` files.

## Hook catalog

| Measure | Value |
| --- | --- |
| Planned hooks | 710 |
| Files with a planned hook | 495 |
| Catalog validation errors | 0 |

The hook dispositions are:

- 87 `production hook` rows at resource boundaries.
- 414 `aggregate boundary only` rows for profiler correlation.
- 209 `targeted diagnostic hook` rows for loop, allocation, object layout, and
  native costs.

See `quickstart.md` section 1 for the validation contract for each artifact.
The validation step reports zero unresolved rows.

## Monitor coverage

The catalog uses the monitor vocabulary in `monitor-vocabulary.md`. That file
defines each type, its tool, its clock, its metrics, and its measured boundary.

| Monitor type | Hooks |
| --- | --- |
| `cProfile correlation` | 414 |
| `loop_counter` | 173 |
| `operation_span` | 26 |
| `http_transport` | 25 |
| `allocation_trace` | 17 |
| `compute_span` | 10 |
| `database` | 9 |
| `gc_diagnostic` | 7 |
| `cache` | 7 |
| `startup_import` | 5 |
| `serializer_file` | 5 |
| `file_io` | 4 |
| `serializer` | 4 |
| `database_events` | 1 |
| `native_boundary` | 1 |
| `cache_file` | 1 |
| `bounded_diagnostic` | 1 |

## Optimization strategy coverage

Each of the ten optimization strategies has hook evidence.
`artifacts/strategy-coverage.csv` holds the complete matrix.

| Strategy | Hooks | Files |
| --- | --- | --- |
| 1 algorithms and repeated work | 640 | 470 |
| 2 input and output counts | 147 | 125 |
| 3 data structures | 391 | 364 |
| 4 allocations and copying | 562 | 405 |
| 5 serialization and validation | 198 | 185 |
| 6 bounded caching | 61 | 47 |
| 7 measured Python loops | 610 | 454 |
| 8 object layout and collection | 284 | 271 |
| 9 startup and imports | 10 | 10 |
| 10 native acceleration | 16 | 15 |

## Required implementation

1. Use `time.perf_counter_ns()` for elapsed wall time.
2. Use `time.process_time_ns()` for process CPU time.
3. Use `cProfile` for Python call attribution.
4. Use `tracemalloc` for traced Python memory.
5. Measure process RSS separately.
6. Use `python -X importtime` for import attribution.
7. Use SQLAlchemy or backend events for query count and duration.
8. Count HTTP requests, retries, pages, request bytes, response bytes, and
   returned items.
9. Count file operations and bytes.
10. Measure serializer boundaries separately from file and transport work.
11. Count cache hits, misses, populations, invalidations, and evictions.
12. Use GC callbacks only during bounded diagnostics.
13. Use a supported sampler for Python and native attribution.

## Privacy and overhead

Disable monitoring by default.
Use bounded queues, event sizes, labels, retention, and flush work.
Sample successful high-frequency events and keep failures.

Do not record credentials, headers, cookies, payloads, SQL text, paths, MAC
addresses, IP addresses, or tenant identifiers.
Do not add a local timer to an aggregate-only file.
Do not change application concurrency.

## Benchmark requirements

Use small, medium, and large workloads.
Use cold and warm states.
Use typical and worst-case inputs.
Verify outputs outside the timed boundary.

Run timing, profiling, memory, input and output, startup, and sampler sessions
separately.
Preserve raw baseline and candidate artifacts.
Report the median, spread, sample count, memory effect, and operation counts.

Retain an optimization only when the effect exceeds measurement uncertainty.
Require a five percent end-to-end gain or a ten percent isolated hotspot gain.
Reject changes that alter behavior, safety, privacy, ordering, errors, or
cleanup.

## Artifacts

- [Specification](spec.md)
- [Research](research.md)
- [Implementation plan](plan.md)
- [Tracking tasks](tasks.md)
- [Quickstart](quickstart.md)
- [Data model](data-model.md)
- [Monitor vocabulary](monitor-vocabulary.md)
- [Requirements checklist](checklists/requirements.md)
- [Performance event JSON Schema](contracts/performance-event.schema.json)
- [Complete Python inventory](artifacts/python-inventory.csv)
- [Hook catalog](artifacts/hook-catalog.csv)
- [Strategy coverage matrix](artifacts/strategy-coverage.csv)
- [Hook catalog summary](artifacts/hook-catalog-summary.json)
- [Scan summary](artifacts/scan-summary.json)

## Acceptance

- Every eligible Python file appears exactly once in the inventory.
- Every AST symbol appears in its file record.
- Every production or aggregate hook resolves to an inventory path and symbol.
- Every event validates against the JSON Schema.
- The default state emits no performance event.
- The enabled overhead stays within the specification budgets.
- Each unmeasured finding remains a `Hypothesis` with an exact benchmark.
