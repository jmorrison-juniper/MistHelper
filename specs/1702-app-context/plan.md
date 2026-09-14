# Implementation Plan: Application context

**Branch**: `refactor/1702-app-context` | **Date**: 2026-09-14 | **Spec**: `specs/1702-app-context/spec.md`

## Summary

Add `AppContext` beside `ApplicationBootstrap`. Store the live session state on that object. Move token and interactive session writes into the context. Add a single `MistSessionConfigurator` seam that configures the transport one time and validates the session without adding attributes.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard-library `argparse`, `dataclasses`, `logging`, and the existing `requests` adapter already used by MistHelper.

**Storage**: No schema change.

**Testing**: pytest, ruff, black, mypy, bandit, symbol diff, and entry point smoke checks.

**Target Platform**: Windows host, Linux container, and Gunicorn WSGI host.

**Project Type**: CLI and web state refactor.

**Performance Goals**: No slow tests. The new tests use fakes and no network.

**Constraints**: Keep the public module symbol table stable. Do not add session patching after construction. Do not add compatibility shims that copy state.

## Constitution Check

- Class-based design: Pass. `AppContext` and `MistSessionConfigurator` own behavior.
- No wrapper functions: Pass. New behavior lives on classes.
- 5-Item Rule: Pass. New methods stay focused and small.
- Inline comments: Pass. New executable lines explain their purpose.
- Action logging: Pass. New methods log before and after meaningful state changes.
- STE prose: Pass. Documents, comments, and messages use short active sentences.
- Security: Pass. Tests and logs do not expose tokens.

## Project Structure

```text
MistHelper.py
src/refactors/main_entrypoint.py
src/refactors/initialize_mist_session.py
src/refactors/initialize_mist_session_interactive.py
tests/unit/refactors/test_app_context_session_state.py
changelog.d/issue-1702-app-context.md
specs/1702-app-context/
```

**Structure Decision**: Keep `AppContext` in `src/refactors/main_entrypoint.py`, because `ApplicationBootstrap` owns startup.

## Technical Approach

1. Add `AppContext` with session, configuration, argument, and selector state.
2. Store the parsed arguments on the context during bootstrap.
3. Replace session-state reads in `MistHelper.py` with `MainEntrypoint.context` reads.
4. Remove `ConfigUtils` mirror calls from `MistHelper.py`.
5. Change token and interactive session initializers to write context state.
6. Add `MistSessionConfigurator` as the only transport configuration seam.
7. Change validation so it never adds `mist_get` to the session object.
8. Add regression tests for context isolation and edge cases.

## Research

No alternate dependency was needed. The existing requests `HTTPAdapter` still serves the timeout policy. The safer design moves that private transport access into one named seam.

## Complexity Tracking

No new block exceeds complexity 10.
