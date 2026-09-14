# Implementation Plan: Empty pre-check targets

## Approach

1. Reproduce the defect with a failing worker task test.
2. Make `PreCheckService.run_all()` return an explicit failed result for an empty target list.
3. Make the worker task require at least one evaluated result before it can report success.
4. Convert target exceptions and `None` target results to failed check results.
5. Check the inventory response status before the service reads `api_result.data`.
6. Add focused unit tests for the safety edge cases.
7. Run the repository and Mist Ops Platform quality gates.

## Other `all(...)` and `any(...)` review

The repository search found one unsafe safety decision in `mist-ops-platform\src\worker\tasks\check_tasks.py`. The pre-check aggregation and the post-check aggregation both used a bare `all(...)`. This change repairs both sites.

Other reviewed candidates already guard the empty case, validate shape, or drive a non-safety display decision. No other repair belongs in issue #2657.
