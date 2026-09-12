# Plan: Capture log baseline index

## Objective

Reduce repeated libcst tree walks in `tools/capture_log_baseline.py`.
The target function is `_render_call_at_line()`.

## Baseline method

Use the session benchmark harness at `opt2_caplog_bench.py`.
The harness reads the repository root from `MISTHELPER_OPT_ROOT`.
It inserts that root into `sys.path`.
It asserts that `tools.capture_log_baseline` imports from this worktree.

## Candidate

Build one call index after parsing the source module.
Group each `cst.Call` by its start line.
Store calls in libcst visit order.
Use the first call for a line to keep the old selection rule.

## Risks

- A nested call can start on the same line as the logging call.
- A missing fixture must still raise the same lookup error.
- The command output must remain byte-identical.

## Validation

Run the issue 429 parity test.
Add focused tests for the indexed path.
Compare baseline and candidate output files byte for byte.
Run syntax, lint, format, docstring, security, and diff checks.
