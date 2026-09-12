# Plan

## Objective

Repair issue #2511 in the data browser preview path.
Use only sequential Python code.

## Measurement plan

Use `opt2_browserfix_benchmark.py` in the session artifact directory.
Read the repository root from `MISTHELPER_ROOT`.
Insert that root into `sys.path`.
Assert that the imported `data_browser.py` file is inside the tested root.
Use local fixture files only.
Use 5 warmups and 31 samples.
Use `time.perf_counter_ns()` for wall time.
Use `time.process_time_ns()` for CPU time.
Measure peak traced memory in a separate pass with `tracemalloc`.

## Profile plan

Use `cProfile` on current `main` before an edit.
Confirm duplicate JSON Lines parse work.
Confirm tail deque append work in the common page path.
Profile the repaired candidate after the edit.

## Change plan

Detect JSON Lines with a single parsed prefix.
Reuse the parsed first item when the file is JSON Lines.
Fuse JSON Lines row construction with search.
Keep only the requested page rows and the fallback tail that can affect a high page request.
Stop appending to the fallback tail after the requested page starts.

## Validation plan

Run the data browser unit tests.
Run the web portal unit tests.
Run compile, Ruff, Black, pydocstyle, Bandit, and diff checks on the changed files.
Run the parity harness against states A, B, and C.
