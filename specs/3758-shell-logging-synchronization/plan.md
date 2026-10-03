# Implementation Plan: Shell Logging Synchronization

**Branch**: `jmorrison-juniper-shell-logging-synchronization` | **Date**: 2026-10-03 | **Spec**: `specs/3758-shell-logging-synchronization/spec.md`

## Summary

Wait for the exact `terminal_outcome_completed` JSON event from the outcomes logger before the shell test snapshots `caplog`. Keep the existing assertions and inputs unchanged. Add deterministic tests for immediate delivery, delivery during polling, missing events, wrong events, and wrong loggers.

## Technical Context

**Language/Version**: Python 3.13 or newer  
**Primary Dependencies**: Existing pytest fixtures and `StructuredTransportLogger`; no dependency changes  
**Storage**: N/A  
**Testing**: pytest; targeted Ruff, Black, mypy, Bandit, docstring, and test-quality checks  
**Target Platform**: Local test environment; no container or browser  
**Project Type**: Python test suite  
**Performance Goals**: Keep the existing two-second maximum wait and 0.01-second polling interval.  
**Constraints**: Test-only changes. Do not change runtime behavior, global time, logging configuration, `caplog` records, or other test inputs.  
**Scale/Scope**: Change only the two named test modules and the unique SpecKit directory.

## Design

Add the class-based helper to `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py`. It will inspect live `caplog.records`, select the exact logger name `src.websocket_streams.live.runners.shell.lifecycle.outcomes`, parse each selected JSON message, and accept only the exact event name `terminal_outcome_completed`. Use the existing `time.monotonic()` deadline and `time.sleep(0.01)` polling pattern with a fixed two-second bound.

Call the helper after the existing STOPPED wait and before the existing log snapshot. Do not alter the original inputs, call identities, AST checks, expected event count, field checks, length checks, or secret checks.

Add `tests/unit/websocket_streams/live/runners/test_ws_shell_log_completion_3758.py`. Call the actual helper with a local time facade. Deliver test events synchronously through a real `StructuredTransportLogger` bound to the outcomes logger. Test an event that exists before polling, delivery during the first poll, no event, a wrong event, and the exact event on a different logger. The facade advances monotonic time in 0.01-second steps and emits during its first sleep when the test requires delivery. It must not patch global time, logging, or `caplog`, and it must not inject records into `caplog`.

## Constitution Check

- **Five-Item Rule**: The helper class contains two methods. The feature directory contains its specification, plan, and task list. Existing directory and module counts remain existing structural debt.
- **Test-only scope**: No production files, fixtures, dependencies, policies, stores, baselines, browser behavior, or containers change. No external API or schema contract applies.
- **Logging and safety**: Read actual structured log records. Do not add runtime logging or include secrets in test output.
- **Delivery boundary**: After implementation and validation, create one local commit, then freeze the branch for the parent. Do not push, open a pull request, or deploy. This user-directed boundary stops the normal deployment pipeline.
- **Existing structural debt**: The existing runner module exceeds the hierarchy limit. Do not restructure preserved tests in this repair. The parent owns separate incremental remediation.

Recheck these constraints after implementation. Record any changed-file or gate deviation before handoff.

## Validation

1. Prove red behavior with deterministic controls for missing, wrong-event, and wrong-logger records. Then add the bounded helper and require each control to pass.
2. Run the new test module separately and report its result separately.
3. Run the original 369-test native scope separately. Require it to pass. Keep the recorded pre-change result distinct: 369 unique tests, 368 passed, one failed, zero skipped, zero errors, and 27.57 seconds. That failure had a 20-event snapshot, while the final report contained 21 events.
4. Run Ruff, Black, mypy, Bandit, docstring checks, and test-quality analysis on both changed test files. Use the actual changed-file scope. Retain every failure. The configured Bandit check excludes tests, so also scan both files directly with all rules and no exclusions.
5. Require all new behavior checks to pass. Preserve the existing fixture type error and unchanged assertion complexity separately. The parent permits the local preservation commit with these unchanged failures.
6. Prepare the private draft and receipt in the CLI session artifact directory. Preserve all 23 pull request template items. Record the exact base as `origin/main`, verified at `38d06c48aa01c553ff2fa4d16d819f82dd68dc94`.
7. Create one local commit. Run the committed-scope analyzer after the required input preflight. Freeze the branch without a push or source changes.

## Recorded validation limits

The direct two-module mypy check fails at unchanged `fake_mist_cloud/server.py:200`.
Exact base source produces the same error.
The configured CI type scope passes across 785 source files.
Issue #3760 tracks the fixture error.
The original assertion method has complexity 13 in both base and current source.
The helper and new controls remain below 10.
The direct Bandit scan reports only intentional test assertions under B101.
No suppressions, policy changes, dependency changes, or fixture changes are permitted.
The parent permits preservation, not publication, with these explicit limits.

## Project Structure

```text
specs/3758-shell-logging-synchronization/
├── spec.md
├── plan.md
└── tasks.md

tests/unit/websocket_streams/live/runners/
├── test_ws_shell_runner.py
└── test_ws_shell_log_completion_3758.py
```

**Structure Decision**: Keep the helper beside the affected test and place deterministic coverage in one unique test module in the same directory. Create the required task list. Do not create unused research, data-model, contract, or quickstart artifacts.

**API, data model, and UI contracts**: N/A. This test-only repair exposes no new interface, data, or user interface.
