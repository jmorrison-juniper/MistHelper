# Implementation Plan: Bootstrap entry point

**Branch**: `refactor/1701-bootstrap-entrypoint` | **Date**: 2026-09-14 | **Spec**: `specs/1701-bootstrap-entrypoint/spec.md`

## Summary

Move startup work from `MistHelper.py` import into `ApplicationBootstrap`. The CLI bootstrap parses arguments once, stores the namespace, and passes it to dependency, session, and runtime setup. The WSGI bootstrap uses default web arguments and never reads the process command line.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard-library `argparse`, `logging`, `os`, `pathlib`, and the existing MistHelper modules.

**Storage**: No schema change. Runtime logs and telemetry stay under `data/` after explicit bootstrap.

**Testing**: pytest, ruff, black, mypy, bandit, symbol diff, and entry point smoke checks.

**Target Platform**: Windows host, Linux container, and Gunicorn WSGI host.

**Project Type**: CLI and web entry point refactor.

**Performance Goals**: A plain module import must avoid dependency checks and network work.

**Constraints**: Keep the public module symbol table stable. Do not add wrappers. Do not scan `sys.argv` outside the bootstrap parse.

**Scale/Scope**: One root module, one entrypoint module, one WSGI module, two small support modules, tests, and one release-note fragment.

## Constitution Check

- Class-based design: Pass. `ApplicationBootstrap` owns startup behavior.
- No wrapper functions: Pass. No new function delegates to a class method.
- 5-Item Rule: Pass. Bootstrap methods keep small focused blocks.
- Inline comments: Pass. New executable lines explain why they exist.
- Action logging: Pass. Bootstrap logs before and after meaningful startup steps.
- STE prose: Pass. Documents, comments, and messages use short active sentences.
- Security: Pass. Import no longer runs subprocess, file, or network startup work.

## Project Structure

```text
MistHelper.py
wsgi.py
src/refactors/main_entrypoint.py
src/refactors/mist_site_exclude_prefix.py
src/utils/rate_limiting.py
src/utils/tqdm_wrapper.py
tests/unit/refactors/test_reject_unsupported_flag_variants.py
changelog.d/issue-1701-bootstrap-entrypoint.md
specs/1701-bootstrap-entrypoint/
```

**Structure Decision**: Keep the bootstrap class in `src/refactors/main_entrypoint.py`, because that file already owns the entrypoint seam.

## Technical Approach

1. Remove module-scope startup execution from `MistHelper.py`.
2. Keep passive default values for configuration globals during import.
3. Let `ApplicationBootstrap` configure streams, logging, data directory checks, `.env`, dependencies, and import manager state.
4. Let the CLI path parse once before any side effect.
5. Let the WSGI path use default web arguments without a command-line parse.
6. Replace the old unsupported flag guard with the standard argparse error path.
7. Add regression tests for passive import and parse count.

## Complexity Tracking

No constitution violation exists.
