# Plan: Diagram reference lint performance

## Baseline

Measure the unmodified production command before application code changes.
Use the real repository tree as the workload.
Save raw JSON results in the session artifact directory.

## Candidate

Replace full AST walking with Python symbol table construction.
Read each source file one time.
Use symbol table line numbers to include class definitions and synchronous functions.
Exclude asynchronous function names to preserve current behavior.

## Correctness checks

- Compare the full production command capture before and after the change.
- Add tests for nested statement bodies.
- Add tests for asynchronous function omission.
- Add tests for strings and comments that contain definition words.

## Benchmark checks

- Use `time.perf_counter_ns()` for elapsed time.
- Use `time.process_time_ns()` for CPU time.
- Count `Path.read_text()` calls and bytes.
- Use `tracemalloc` in a separate memory run.
- Assert that the harness imports from this worktree.

## Risk controls

The change uses the Python parser through `symtable.symtable()`.
This keeps syntax error detection before the token list changes behavior.
The line check keeps synchronous function names and class names aligned with the prior AST result.
