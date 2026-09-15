# Tasks: Narrow broad exception handlers

## Group 3: Keep it, but repair it

- [x] Add traceback logging for the tuning data directory fallback.
- [x] Narrow menu signature inspection failures to `TypeError` and `ValueError`.
- [x] Add traceback logging for the context fast-mode reader.
- [x] Add traceback logging for the CLI fast-mode reader.
- [x] Narrow fast-mode publication failures to `AttributeError` and `TypeError`.

## Group 2: Keep it, and justify it

- [x] Keep the package upgrade check broad and fail-open. Raise the log level.
- [x] Keep one-option systematic test failures broad. Log a traceback.
- [x] Keep the TUI event loop failure handler broad. Add `SystemExit` pass-through.
- [x] Keep interactive menu operation failures broad. Add `SystemExit` pass-through.
- [x] Keep the top-level application failure handler broad. Add `SystemExit` pass-through.

## Group 1: Narrow it

- [x] Narrow installed package metadata lookup failures.
- [x] Narrow PyPI latest version lookup failures.
- [x] Narrow requirements file parse failures.
- [x] Narrow fallback `.env` loader failures.
- [x] Narrow dependency install item failures.
- [x] Narrow import worker result failures.
- [x] Narrow optional `mistapi` wiring failures.
- [x] Narrow organization picker failures.
- [x] Narrow token probe failures.
- [x] Narrow `APISession` signature inspection failures.
- [x] Narrow traceback logging secondary failures.
- [x] Narrow `APISession` constructor attempt failures.
- [x] Narrow filtered-token constructor failures.
- [x] Narrow legacy session fallback failures.
- [x] Narrow telemetry emitter initialization failures.
- [x] Narrow global exception hook formatting failures.
- [x] Narrow global exception hook install failures.
- [x] Narrow top-level traceback formatting failures.
- [x] Keep the remaining startup safety net broad because logging may not be ready.

## Validation

- [x] Add hermetic issue tests for narrowed handlers.
- [x] Add the release-note fragment.
- [x] Run the local quality gates.
- [ ] Open the pull request.
- [ ] Merge the pull request.
