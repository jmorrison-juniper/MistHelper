# Scope Guard and Hard-Gate Policy

## Wave Scope Lock

This wave covers only the 9 target groups defined in `specs/193-main-decomposition-wave-2/spec.md` and `tasks.md`.

### Explicit Out-of-Scope Guard

- `GlobalImportManager` is excluded from this wave.
- No direct feature expansion is allowed outside the 9 target groups.
- Any incidental wiring edits outside the 9 target groups must be minimal and justified in phase gate notes.

## Hard-Gate Remediation Policy

For every phase gate:

1. If any validation check fails, fix in the same phase.
2. If any parity check fails, fix in the same phase.
3. If any import graph check fails, fix in the same phase.
4. If any runtime coupling check fails, fix in the same phase.
5. Re-run failed checks until all are green before signoff.

## Pre-Phase-1 Checklist

- [x] Out-of-scope guard acknowledged.
- [x] Hard-gate remediation policy acknowledged.
- [x] Gate harness tests exist and are runnable.
- [x] Parity baseline location is initialized.
