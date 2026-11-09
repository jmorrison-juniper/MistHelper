# Implementation Plan: Traceback log redaction

**Branch**: `jmorrison-juniper-traceback-log-redaction` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4704 and its file ownership claim.

## Summary

Extend `SensitiveFilter` to sanitize rendered exception text before a standard handler emits it.
Keep the existing in-place message contract and credential pattern.
Sanitize cached exception text from earlier handlers.
Retain exception types, frames, chain separators, and safe messages.
If formatting fails, replace the unsafe record with a diagnostic that excludes the error value.

## Technical Context

**Language/Version**: Python 3.13 or newer. The local locked environment uses Python 3.14.7.

**Primary Dependencies**: Standard-library logging and pytest.

**Storage**: In-memory streams in tests only.

**Testing**: Focused unit and portal contract tests, plus applicable file-level gates.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Shared logging utility.

**Performance Goals**: Do not render a traceback when the record has no exception.

**Constraints**: No caller changes, new credentials, live services, containers, or firmware operations.

**Scale/Scope**: One source file, two existing test files, and unique process records.

## Constitution Check

- The owned source and test paths have no open PR overlap.
- The clean starting commit matches current main.
- The specification uses the managed eight-level numeric route.
- The branch remains app-managed. The tracked feature selector remains unchanged.
- New process records use bounded directories, except the required unique changelog fragment.
- Existing module and test classes exceed structural limits. This repair does not restructure unrelated code.
- The separate remediation action is to divide existing logging tests and process records in a future ownership window.
- Do not add a new module-level production name or remove an existing name.
- Keep each new production method within 25 lines and five parameters.
- Do not log inside a logging filter. Recursive logging can re-enter the failed filter.
- Standard traceback text must remain readable after credential replacement.
- Use a Conventional Commit with `Refs #4704` and the required author trailer.
- The user holds publication. Do not execute the deployment, rebase, push, or PR stages.

## Project Structure

### Documentation (this feature)

The managed feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains the checklist, research, data model, and quickstart.
No new external interface needs a contract directory.

### Source Code (repository root)

- `src/foundation/support/utils/logger_utils.py`
- `tests/unit/test_logger_utils.py`
- `tests/unit/upgrade_portal/test_logging_contract.py`
- `changelog.d/issue-4704-traceback-log-redaction.md`

**Structure Decision**: Extend existing files only. Keep the existing portal handler installation.

## Complexity Tracking

The existing logging module and test modules exceed five top-level names.
Keep the production symbol set unchanged and add only the regression tests needed for this defect.
The existing process-folder debt remains outside this repair.
Optional commit hooks are deferred to the final local commit.
