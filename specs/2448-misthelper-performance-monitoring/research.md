# MistHelper performance monitoring research

## Scan method

The scan used the Python `ast` module.
It read every tracked and eligible untracked Python file as bytes.
It decoded UTF-8 with byte-order-mark support and reported invalid bytes by replacement.
It parsed each file and visited each `FunctionDef`, `AsyncFunctionDef`, and `ClassDef`.

The inventory records a qualified name, parent, nesting depth, and source range for each symbol.
It also records file bytes, line count, parse state, disposition, and rationale.
The scan found no syntax errors.

The review also examined imports, calls, module roles, and selected implementation bodies.
This content review supports the disposition and hook choices.

## Inclusion and exclusion

The scan includes 1,411 files from the two required Git commands.
It includes application, portal, platform, test, tool, script, migration, and specification Python files.

Git reports 9,618 ignored Python files under `.venv`.
The scan excludes that virtual environment because it contains package-managed external code.
No other ignored Python root exists in the current worktree.

The scan used temporary scripts in this specification directory.
The final package removes those scripts.
The final validation scans the repository again after removal.

## Source findings

MistHelper has two application groups.
The main application uses `MistHelper.py`, `src`, `web_portal`, and the WSGI modules.
The operations platform uses `mist-ops-platform/src`.

The test tree holds 727 Python files across both application groups.
The scripts and tools hold 121 Python files.
These files can drive benchmarks and profiles, but they must not emit production telemetry.

The production roots hold central transport, database, cache, export, portal, and startup boundaries.
The hook catalog selects 59 files for durable hooks.
It assigns 407 other runtime files to profiler correlation.

## Existing measurement facilities

`src/site/address_audit/perf.py` defines `PhaseTimer`.
It uses `time.perf_counter()` and aggregates named phases.
The implementation phase must move new measurements to nanosecond clocks.
It can preserve the existing public behavior.

`src/analytics/telemetry_emitter.py` writes append-only JSON lines.
Its `emit` method performs JSON encoding, file writing, and flushing in one call.
The plan measures encoding and file work as separate stages.

`src/metrics_gateway/collector.py` already measures a complete pass with `time.time()`.
The collector also centralizes three Mist endpoints.
The plan replaces performance duration collection with a monotonic nanosecond clock.
Wall-clock timestamps can continue to use the real-time clock.

`src/metrics_gateway/cache.py` centralizes refresh, stale reads, and cache outcomes.
It is a suitable cache measurement boundary.

`src/db/router.py`, `src/db/arango_writer.py`, and `src/db/redis_writer.py` centralize database writes.
`mist-ops-platform/src/shared/db.py` creates the SQLAlchemy engine and sessions.
These boundaries support query counts and durations without route-level query timers.

## Measurement decisions

### Wall and CPU time

Use `perf_counter_ns` for elapsed time.
Use `process_time_ns` for process CPU time.
Emit integer nanoseconds.
Convert units only in a report or presentation layer.

### Function attribution

Use `cProfile` around a complete representative operation.
Export `pstats` data with file and qualified symbol correlation.
Do not treat profiler time as an acceptance benchmark.

### Python and process memory

Use `tracemalloc` for traced Python current and peak bytes.
Use a process monitor for RSS.
Run these measurements separately.
The event contract gives each measure a distinct name.

### Database work

Use SQLAlchemy events for cursor execution and pool wait.
Use backend wrapper hooks for ArangoDB, Redis, and SQLite.
Count logical operations and physical operations separately.

### Transport work

Measure Mist calls, HTTP requests, WebSocket sessions, and SSH connections at their central wrappers.
Count retries, pages, request bytes, response bytes, and returned items.
Keep status labels coarse.

### File and serializer work

Measure file operations and actual bytes.
Measure JSON, CSV, rendering, flattening, and validation in separate child stages.
Do not count rows as bytes.

### Cache work

Measure hits, misses, populations, invalidations, evictions, and bounded size.
Do not record keys or values.

### Garbage collection

Use GC callbacks only for a bounded diagnostic.
Use a fixed event limit and duration limit.
Remove callbacks during cleanup.

### Native attribution

Use Scalene or py-spy when the environment supports the selected tool.
Record the tool version and permissions.
Verify that a native library does not add hidden parallel execution.

## Optimization checklist coverage

| Category | Evidence source | Required experiment |
| --- | --- | --- |
| 1. Algorithms and repeated work | `cProfile`, call counts, input-size curves | Compare growth for small, medium, and large inputs. |
| 2. I/O and sequential batching | Request, query, page, file, and byte counts | Compare equivalent sequential batches and unchanged failure behavior. |
| 3. Data structures | CPU profile and allocation profile | Include construction cost, duplicates, ordering, and small inputs. |
| 4. Allocations and copying | `tracemalloc`, RSS, serializer bytes | Compare current, peak, retained, and process memory. |
| 5. Serialization and validation | Serializer spans and byte counts | Include malformed inputs, output equality, and conversion cost. |
| 6. Bounded caching | Hit, miss, population, eviction, and size measures | Test cold, warm, invalidation, eviction, and sustained growth. |
| 7. Measured Python loops | `cProfile` and supported sampler | Change a loop only after measured attribution. |
| 8. Object layout and GC | Object counts, RSS, traced bytes, bounded GC events | Test construction, access, release, inheritance, and serialization. |
| 9. Startup and imports | Fresh process timing and `-X importtime` | Compare cold startup, warm startup, and first use. |
| 10. Native acceleration | Supported sampler and end-to-end timing | Include conversion, compilation, startup, and sequential execution. |

## Hypotheses

All performance findings remain hypotheses until a benchmark confirms them.

### Hypothesis: API fan-out can dominate large workloads

Run the H-01 benchmark in `spec.md`.
Reject this hypothesis if request count and wait time remain a small workload share.

### Hypothesis: export conversion can create high allocation pressure

Run the H-02 benchmark in `spec.md`.
Reject this hypothesis if traced peak bytes, RSS, and serializer time remain small.

### Hypothesis: repeated database operations can dominate persistence

Run the H-03 benchmark in `spec.md`.
Reject this hypothesis if query count and database duration scale acceptably.

### Hypothesis: aggregation loops can become CPU hotspots

Run the H-04 benchmark in `spec.md`.
Reject this hypothesis if the profiler and sampler attribute cost elsewhere.

### Hypothesis: import work can delay useful readiness

Run the H-05 benchmark in `spec.md`.
Reject this hypothesis if imports do not consume a material startup share.

### Hypothesis: long-lived state can retain memory

Run the H-06 benchmark in `spec.md`.
Reject this hypothesis if RSS and retained traced memory stabilize within the budget.
