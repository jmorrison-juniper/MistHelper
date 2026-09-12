# Plan: Citation reference lint performance

## Objective

Measured. Reduce default citation lint wall time and filesystem reads on the real repository tree.

## Workload

Measured. Run `python -m tools.check_citations src tests specs documentation tools` from the worktree. Use the warm filesystem state that follows one warmup run.

## Method

Measured. Use `time.perf_counter_ns()` for wall time. Use `time.process_time_ns()` for CPU time. Use `tracemalloc` outside the memory run. Count file opens, read calls, bytes read, and `os.walk` calls with a benchmark harness.

## Candidate

Measured. Build the default file index and source list in one walk. Skip the regex when a line lacks a folder separator or a line separator. Reuse the source file line count when the source file can also be a target.

## Risk controls

Measured. Capture stdout and exit code before and after the change. Compare the captured results exactly. Add unit tests for the single-walk path and the regex skip path.
