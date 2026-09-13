# Plan: Flatten nested fields performance

## Objective

Reduce warm flatten latency for large export batches in a single Python process.

## Measured boundary

The benchmark calls `DataProcessingUtils.flatten_nested_fields(dataset)` on a prebuilt dataset.
It consumes every returned row by counting its keys.
It excludes dataset construction from timing.

## Baseline plan

Run the existing unit tests first.
Run a custom harness that uses `time.perf_counter_ns()` and `time.process_time_ns()`.
Run `tracemalloc` in a separate memory pass.
Run a `pyperf` harness because the repository has an existing pyperf benchmark.

## Candidate plan

Avoid temporary dictionaries and pair lists during recursive flattening.
Check the first character of parse candidates before `json.loads()`.
Cache hot static method lookups inside the per-row loop.

## Correctness plan

Add unit tests for equivalent JSON and Python literal values.
Add unit tests for key order and empty container behavior.
Add unit tests for malformed strings.
Run the existing data processing unit test file.

## Risk plan

Do not change public signatures.
Do not change parser order.
Do not change scalar list formatting.
Do not change empty dictionary and empty list handling.
