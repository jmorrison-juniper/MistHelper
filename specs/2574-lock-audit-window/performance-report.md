# Performance report: Lock audit read cost

## 1. Executive summary
Measured: `read_audit_rows()` used peak traced memory that grew with the whole audit file. The retained change processes the full trail in order, keeps only the newest requested inferred rows, and shapes only the returned page. The 50,000 row fixture peak traced memory fell from 77,410,272 bytes to 599,449 bytes.

## 2. Environment and Python version
Measured: The run used Windows 11 on AMD64. Python was CPython 3.13.3. The worktree was `C:\Users\jmorrison\mh-opt3-lock-audit`. The branch was `perf/2574-lock-audit-window`.

## 3. Benchmark methodology
Measured: The harness wrote local JSONL fixtures with the exact writer fields from `runtime/lock.py`: `action`, `actor_email`, `previous_actor_email`, `occurred_at`, `org_id`, and `site_id`. The harness inserted the repository root from `MISTHELPER_BENCH_ROOT` into `sys.path`. It asserted that the imported `lock_audit` module came from the worktree. It used 5 warmups and 31 samples. It used `time.perf_counter_ns()` and `time.process_time_ns()`. It measured traced memory in a separate run with `tracemalloc` active outside the loop.

## 4. Baseline results
Measured: 1,000 rows took 18.8147 ms wall median and 15.6250 ms CPU median, n=31. Peak traced memory was 1,503,450 bytes. 10,000 rows took 794.8058 ms wall median and 234.3750 ms CPU median, n=31. Peak traced memory was 15,437,429 bytes. 50,000 rows took 6,232.5923 ms wall median and 1,187.5000 ms CPU median, n=31. Peak traced memory was 77,410,272 bytes.

## 5. Ranked hotspot list
Measured: The 10,000 row `cProfile` run spent 0.267 s cumulative time in `audit_row()` across 14,750 calls. It spent 0.254 s in `read_trail_lines()`. It spent 0.157 s in `json.loads()`. It spent 0.109 s in `email_digest()` across 17,250 calls. It spent 0.090 s in `mark_expiries()`. The largest avoidable cost was shaping every inferred row before the limit was applied.

## 6. Recommended optimizations
Measured: Keep expiry inference as a full oldest-first pass. Replace the full materialized answered list with a bounded deque for positive limits. Shape only the rows that can be returned. Hypothesis: A reverse file read could reduce time more, but it can change expiry inference and was not safe for this issue.

## 7. Implemented changes
Measured: `read_audit_rows()` now preserves the old full path for non-integer and non-positive limits. For positive limits it streams all trail records, infers expiry rows in the same order as `mark_expiries()`, counts the same total rows for the debug log, keeps only the newest requested raw rows, and then shapes those rows newest first.

## 8. Before and after measurements
Measured: For 1,000 rows, wall median changed from 18.8147 ms to 16.7006 ms, or -11.24 percent. CPU median was unchanged at 15.6250 ms. For 10,000 rows, wall median changed from 794.8058 ms to 168.6998 ms, or -78.77 percent. CPU median changed from 234.3750 ms to 125.0000 ms, or -46.67 percent. For 50,000 rows, wall median changed from 6,232.5923 ms to 651.3316 ms, or -89.55 percent. CPU median changed from 1,187.5000 ms to 468.7500 ms, or -60.53 percent.

## 9. Memory impact
Measured: Peak traced memory changed from 1,503,450 bytes to 596,686 bytes for 1,000 rows, or -60.31 percent. It changed from 15,437,429 bytes to 599,567 bytes for 10,000 rows, or -96.12 percent. It changed from 77,410,272 bytes to 599,449 bytes for 50,000 rows, or -99.23 percent. The candidate peak stayed near 0.6 MB as the file grew.

## 10. Correctness and regression validation
Measured: `test_the_capped_read_matches_the_full_expiry_inference` proves that the capped read equals a full read plus full expiry inference for the returned page. Added tests also cover one row, a trail shorter than the window, and row field types. Existing tests cover an empty trail and a malformed line. Post-refactor tests passed: 97 passed for the lock audit, history view, store history, and performance hook catalog tests. Post-refactor quality gates also passed.

## 11. Rejected ideas
Rejected: A reverse line reader was not used. It could skip old rows that are needed to infer whether a returned take has a preceding open hold. Rejected: A cache was not used. The measured memory issue did not need retained state, and a cache would add freshness risk.

## 12. Remaining opportunities
Hypothesis: The JSON parse cost is now the main measured cost. A future change could add a safe index or checkpoint format if the project wants history reads to stop scanning the whole file. That design needs a separate specification because it changes persistent data.
