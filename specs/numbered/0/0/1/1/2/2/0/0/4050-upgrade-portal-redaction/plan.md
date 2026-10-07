# Implementation Plan: Upgrade Portal Log Redaction

**Branch**: `fix-4050-upgrade-portal-redaction` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

## Summary

Add a focused test that emits exception text through the real upgrade portal package logger.
Record the red failure before product changes. Install the existing `SensitiveFilter` on the
portal handler. Keep propagation disabled to preserve one output path and the portal context format.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Python logging, `pytest`, and the existing logging utilities

**Storage**: No storage change

**Testing**: Focused pytest, Bandit, Ruff, Black, and the test-quality ratchet

**Target Platform**: Windows 11, macOS, and Linux

**Constraints**: Use only the authorized six files. Do not edit root logging or contested upgrade files.

## Constitution Check

- **Five-Item Rule**: PASS. The change adds no package child.
- **Class-Based Architecture**: PASS. The change reuses an existing filter class.
- **Safety-First**: PASS. The test uses an obvious synthetic marker.
- **Observability and Logging**: PASS. The repair protects the handler boundary and preserves normal output.
- **Inline Comments**: REQUIRED. Each changed executable line receives a cause or purpose comment.
- **Process-folder intake**: PASS. The specification uses the verified fixed-width route for issue #4050.

## Measured Evidence

- `factory.py:259` sets `package_logger.propagate = False`.
- The package handler installs only `RunContextFilter`.
- `LogSanitizer` is a root logger filter, not a handler filter.
- No production handler installs `SensitiveFilter`.
- Existing logging tests reported `86 passed in 11.63s`.
- A direct package-handler probe emitted synthetic credential-shaped content unchanged.

## Design Decisions

### Keep propagation disabled

The root formatter lacks `run_id` and `site_id`. Propagation can duplicate output. A root logger
filter also does not process descendant records during propagation.

### Install redaction on the portal handler

Every standard-library portal record passes through the package handler. A handler filter protects
the actual output boundary without changing each caller.

### Test the installation path

The test calls `configure_logging`, redirects the installed handler to an in-memory stream, and
emits through the package logger. It does not call the filter directly.

## Implementation Plan

1. Add one focused runtime test to `test_logging_contract.py`.
2. Emit credential-shaped exception text and one ordinary context-bearing message.
3. Run the test before product changes and record the failing output.
4. Commit the specification and false-coverage repair.
5. Import `SensitiveFilter` in `factory.py`.
6. Add the filter to the portal handler after `RunContextFilter`.
7. Add the issue-specific security release note.
8. Run targeted tests and all required gates.
9. Commit the product repair separately.
10. Rebase, push once, and create a ready security pull request.
