# Performance monitoring requirements checklist

## Inventory

- [x] The scan uses both required Git file lists.
- [x] The inventory contains one row per eligible Python file.
- [x] The inventory includes all top-level and nested functions, asynchronous functions, and classes.
- [x] The symbol counts reconcile with the AST scan.
- [x] The scan reports parse errors.
- [x] The scan reports inclusion roots.
- [x] The scan documents ignored exclusions.
- [x] Each file has exactly one disposition.
- [x] Each disposition has a rationale.
- [x] The inventory has no stale file reference.

## Hook design

- [x] Each production hook names an exact file and symbol.
- [x] Each aggregate record names an exact file and symbol or class.
- [x] Each hook names a monitor type and metric names.
- [x] Each hook defines its measured boundary.
- [x] Each hook defines dimensions and a cardinality policy.
- [x] Each hook defines an overhead guard.
- [x] Each hook defines a privacy rule.
- [x] Each hook maps to optimization checklist strategies.
- [x] The design does not add permanent per-function timers.

## Measurement methods

- [x] Wall time uses `perf_counter_ns`.
- [x] Process CPU time uses `process_time_ns`.
- [x] Function attribution uses `cProfile`.
- [x] Python memory uses `tracemalloc`.
- [x] Process RSS uses a separate monitor.
- [x] Startup attribution uses `-X importtime`.
- [x] Database counts and durations use database events or backend wrappers.
- [x] HTTP monitoring counts requests, retries, pages, and bytes.
- [x] File monitoring counts operations and bytes.
- [x] Serializer monitoring isolates conversion boundaries.
- [x] Cache monitoring counts hits, misses, populations, invalidations, and evictions.
- [x] GC callbacks are bounded diagnostics only.
- [x] Native and Python attribution uses a supported sampler.

## Benchmark design

- [x] Workloads define small, medium, and large sizes.
- [x] Workloads define cold and warm states.
- [x] Workloads define typical and worst-case data.
- [x] Benchmarks verify outputs outside the timed boundary.
- [x] Timing, profiling, memory, startup, and sampling runs remain separate.
- [x] The plan keeps application concurrency unchanged.
- [x] The plan preserves raw baseline and candidate artifacts.
- [x] The acceptance rule includes effect size and measurement uncertainty.

## Optimization checklist

- [x] Algorithms and repeated work are covered.
- [x] I/O counts and sequential batching are covered.
- [x] Data structures are covered.
- [x] Allocations and copying are covered.
- [x] Serialization and validation are covered.
- [x] Bounded caching is covered.
- [x] Measured Python loops are covered.
- [x] Object layout and garbage collection are covered.
- [x] Startup and imports are covered.
- [x] Native acceleration is covered.

## Evidence

- [x] Each unmeasured performance finding uses the label `Hypothesis`.
- [x] Each hypothesis defines an exact benchmark.
- [x] The JSON Schema defines the event contract.
- [x] The parent issue references every generated artifact.
- [x] The task list defines dependencies and acceptance criteria.
