# Shell Log Assertion Structure

## Problem

`test_shell_logs_do_not_hold_address_input_or_output` has cyclomatic
complexity 13. The direct test-module limit is 10. Its assertion checks protect
secret exclusion, event coverage, safe fields, and record bounds.

## Goal

Reduce the test's measured complexity to 10 or less without changing its
assertions, inputs, conditions, event count, or native shell behavior.

## Scope

- Restructure only the reserved assertion region in
  `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`.
- Group related checks in a semantic assertion class in that module.
- Add one uniquely named native contract-control module only if needed.
- Keep all checks on the captured records from the real fake-cloud shell run.

## Requirements

1. Preserve all four secret-exclusion checks and their exact values.
2. Preserve the package-record selection and JSON parsing.
3. Preserve the 21-event count, safe-field allowlist, event-length limit, and
   safe-string length limit.
4. Preserve the completion wait, fixtures, time bounds, and runtime behavior.
5. Prove each grouped check accepts valid native records and rejects invalid
   records through controlled real log delivery.
6. Do not change runtime code, thresholds, exclusions, baselines, shared
   fixtures, other tests, or the frozen #3758 completion-control module.

## Acceptance

- The target test has direct cyclomatic complexity 10 or less.
- Every original assertion condition remains present and measurable.
- Native controls prove both passing and refusal behavior.
- The affected native test scope passes without cloud access.
