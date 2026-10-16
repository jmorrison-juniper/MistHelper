# Implementation Plan: Single console output

**Branch**: `jmorrison-juniper-menu-readability-doubling` | **Date**: 2026-10-16 | **Spec**: [Specification](spec.md)

## Summary

Exclude records from the direct-output helper at the console handler only. Keep propagation to the existing file handler.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: Standard-library logging. No dependency change.
**Storage**: Existing rotating file log under `data/`.
**Testing**: pytest, including real bootstrap handler routing.
**Target Platform**: Windows, macOS, Linux, and SSH containers.
**Project Type**: CLI.
**Constraints**: Preserve diagnostics and file records at their configured levels.
**Scale/Scope**: Two existing source modules and their existing test modules.

## Constitution Check

- Keep the app-managed branch. Do not create or switch branches through the optional Git hook.
- Add one filter class with one short method to the existing console helper module.
- Attach the filter only to the console handler in the existing bootstrap.
- Preserve `echo()` and all existing callers.
- Add no source directories, dependencies, API calls, credentials, or schema changes.
- Existing bootstrap class size and test-module size exceed current structural limits. This repair does not add bootstrap methods.
- Process folders have existing child-count debt. Add only this change's unique specification and release fragment.
- Incremental remediation: keep new filter behavior in the smaller existing console module rather than adding another bootstrap method.
- Before implementation: passed. After design: passed.

## Project Structure

- `src/foundation/support/utils/console.py`: filter and existing direct-output contract.
- `src/foundation/support/refactors/main_entrypoint.py`: console-handler wiring.
- `tests/unit/utils/test_console.py`: filter unit and edge-case tests.
- `tests/unit/refactors/test_main_entrypoint.py`: bootstrap integration tests.
- `changelog.d/issue-4257-single-console-output.md`: release note.

## Validation

Run focused console and bootstrap tests, source lint, format, types, and security lint.
Verify a menu render with a real console handler and a file handler at INFO.
Preserve the existing running container. Deployment requires a rebuilt image after review.
