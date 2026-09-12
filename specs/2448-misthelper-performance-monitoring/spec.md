# MistHelper performance monitoring specification

## Purpose

This specification defines opt-in performance monitoring for the Python code in MistHelper.
It does not change application code.

The design uses a small set of stable runtime hooks.
It uses profiler correlation for the remaining files, functions, methods, and classes.
It does not add a permanent timer to each function.

## Inventory baseline

The AST scan includes every path returned by these commands:

```powershell
git ls-files '*.py'
git ls-files --others --exclude-standard '*.py'
```

The final inventory contains 1,411 Python files and 31,903 symbols.
The symbols include 27,651 functions, 149 asynchronous functions, and 4,103 classes.
The inventory identifies 18,107 nested symbols and no parse errors.

The scan excludes 9,618 ignored Python files under `.venv`.
Git identifies this directory as a virtual environment.
These files are package-managed external dependencies and are not repository source.

Read `artifacts/scan-summary.json` for the exact root and disposition counts.
Read `artifacts/python-inventory.csv` for one row per eligible file.
The `symbols_json` field lists every top-level and nested AST symbol.

## Dispositions

Each eligible file has one disposition.

| Disposition | Meaning | File count |
| --- | --- | ---: |
| `production hook` | Add one or more low-overhead hooks at a stable runtime boundary. | 59 |
| `aggregate boundary only` | Use a parent span and an opt-in profiler. Do not add a local timer. | 407 |
| `benchmark/profile only` | Use the file only to drive or support controlled measurements. | 850 |
| `no hook` | The file has no useful runtime boundary, or it is a migration or specification file. | 95 |

The hook catalog contains 89 production-hook records and 407 aggregate records.
Each record names an exact file and an exact symbol or class.

## Functional requirements

### FR-001: Monotonic timing

Use `time.perf_counter_ns()` for elapsed wall time.
Use `time.process_time_ns()` for process CPU time.
Do not derive network time from wall time minus CPU time.

### FR-002: Layered instrumentation

Add durable hooks only at the production boundaries in `artifacts/hook-catalog.csv`.
Use an opt-in `cProfile` session to attribute nested Python calls.
Use separate uninstrumented runs for acceptance measurements.

### FR-003: Memory measurements

Use `tracemalloc` only in a bounded diagnostic run.
Report traced current bytes and traced peak bytes.
Measure process RSS separately with a supported process monitor.
Do not describe traced Python memory as RSS.

### FR-004: Startup measurements

Measure fresh process startup through useful readiness.
Use `python -X importtime` for import attribution in a separate run.
Measure a deferred first use as a separate boundary.

### FR-005: Database measurements

Use SQLAlchemy engine events for query count and query duration.
Measure transaction count and pool wait separately.
Use equivalent backend hooks for ArangoDB, Redis, and SQLite.
Do not store SQL text, bind values, or result data.

### FR-006: HTTP and Mist transport measurements

Measure each request, retry, and page at the transport boundary.
Count request bytes, response bytes, returned items, retries, pages, and status classes.
Do not use a raw URL, tenant identifier, or object identifier as a metric label.

### FR-007: File and serialization measurements

Measure file operations and bytes at open-read-close or open-write-close boundaries.
Measure encoding, decoding, validation, flattening, and rendering separately from file I/O.
Do not serialize a payload again only to calculate its size.

### FR-008: Cache measurements

Count hits, misses, populations, invalidations, and evictions.
Define the key, ownership, lifetime, invalidation rule, and size bound before implementation.
Do not record cache keys.

### FR-009: Garbage collection diagnostics

Use GC callbacks only in a bounded diagnostic session.
Remove each callback in a `finally` block.
Do not change the process-wide GC policy in normal operation.

### FR-010: Python and native attribution

Use a supported sampler, such as Scalene or py-spy, for a Python and native split.
Verify the tool version, platform support, permissions, and sampling limits.
Do not enable hidden native parallel execution.

### FR-011: Privacy and cardinality

Use allowlisted dimensions and coarse size buckets.
Do not record tokens, credentials, payloads, SQL text, paths, MAC addresses, IP addresses, or tenant identifiers.
Use a run-local identifier for correlation.
Limit an event to 16 dimensions and 32 measurements.

### FR-012: Failure behavior

Monitoring must never change an operation result.
Monitoring must not suppress an application exception.
Disable the hook after repeated sink failures.
Bound buffers, flush work, and shutdown work.

## Workload contract

Every retained optimization must use all applicable cells in this matrix.

| Axis | Small | Medium | Large |
| --- | --- | --- | --- |
| Typical data | 1 site, 10 devices, 100 records | 25 sites, 1,000 devices, 10,000 records | 200 sites, 10,000 devices, 100,000 records |
| Worst-case data | Deep nesting, sparse fields, duplicate keys | Maximum page count, mixed device types, retries | Maximum supported pages, large exports, partial failures |
| Cold state | Fresh process, empty application cache, first connection | Fresh process with normal fixture | Fresh process with full fixture |
| Warm state | Reused client and populated bounded cache | Repeated stable operation | Sustained run with eviction and retention |

Use sanitized fixtures or disposable stores.
Keep application concurrency settings unchanged.
Do not use a live tenant without explicit authorization and a request budget.

## Acceptance criteria

1. The event data validates against `contracts/performance-event.schema.json`.
2. The default state emits no performance events.
3. A production hook adds less than one percent median wall time to its enabled parent workload.
4. A sampled hot hook adds less than five percent median wall time to its isolated benchmark.
5. The event sink uses bounded memory and bounded label values.
6. Tests confirm output, ordering, errors, cleanup, and security behavior.
7. A retained optimization improves an important end-to-end path by at least five percent.
8. Alternatively, it improves an isolated hotspot by at least ten percent.
9. The measured effect exceeds the reported uncertainty.
10. The report includes median, spread, sample count, memory, I/O counts, and raw artifact links.

## Hypotheses and required benchmarks

### Hypothesis H-01: Mist request fan-out dominates large organization work

Benchmark the same read-only operation with 1, 25, and 200 sites.
Record requests, retries, pages, bytes, wall time, and process CPU time.
Run cold and warm states with typical responses and a worst-case retry fixture.

### Hypothesis H-02: Export conversion and file writes dominate large result sets

Benchmark 100, 10,000, and 100,000 sanitized records.
Measure flattening, serialization, and file writing as separate stages.
Record output bytes, operations, wall time, process CPU time, traced peak bytes, and RSS.

### Hypothesis H-03: Database writes perform avoidable repeated work

Benchmark one, 1,000, and 50,000 records on disposable stores.
Record logical writes, physical queries, transactions, rows, retries, and bytes.
Compare cold connections, warm pools, typical records, and duplicate-heavy records.

### Hypothesis H-04: Python aggregation loops dominate metrics and inventory builds

Benchmark 10, 1,000, and 10,000 devices with stable expected output.
Collect an uninstrumented timing run, a `cProfile` run, and a `tracemalloc` run.
Use a supported sampler to separate Python and native cost.

### Hypothesis H-05: Imports delay CLI and portal readiness

Measure fresh process startup for the CLI, both portals, and the metrics gateway.
Collect `-X importtime` output for each entry point.
Measure warm startup and deferred first use separately.

### Hypothesis H-06: Long-lived caches or object graphs retain excess memory

Run 1, 10, and 100 warm operation cycles.
Record cache outcomes, entries, evictions, traced bytes, RSS, and GC collections.
Use fixed fixture identities and verify release after explicit cleanup.

## Out of scope

- This specification does not implement application hooks.
- This specification does not change worker counts or concurrency.
- This specification does not recommend process, thread, or async parallelism.
- This specification does not claim that an unmeasured change is faster.
