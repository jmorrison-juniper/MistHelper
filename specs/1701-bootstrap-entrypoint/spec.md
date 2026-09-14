# Feature Specification: Bootstrap entry point

**Feature Branch**: `refactor/1701-bootstrap-entrypoint`

**Created**: 2026-09-14

**Status**: Implemented

**Input**: Move import-time side effects into an explicit bootstrap step and parse the command line one time.

## Problem

`MistHelper.py` ran startup work during import. The import created the data directory, configured logging, read `.env`, checked dependencies, and read `sys.argv`. A test, a web server, or a reader could not import the module without runtime work.

The program also read the command line before `argparse`. That design created two parsers. A bad flag spelling needed a special guard.

## User Scenarios and Testing

### User Story 1 - Import is passive (Priority: P1)

A test imports `MistHelper`. The import binds names only. It does not create files, configure logging, start a subprocess, open a network connection, or make a runtime decision from environment variables.

**Why this priority**: Tests and web hosts need a predictable import.

**Independent Test**: Run the import-side-effect regression test in `tests/unit/refactors/test_reject_unsupported_flag_variants.py`.

**Acceptance Scenarios**:

1. **Given** a fresh interpreter, **When** it imports `MistHelper`, **Then** no watched startup side effect runs.
2. **Given** a fresh interpreter, **When** it imports `MistHelper`, **Then** the import does not call `sys.exit()`.

### User Story 2 - CLI parses once (Priority: P1)

The command-line host creates one bootstrap object. The object parses the command line once and stores the `Namespace`. Every later startup decision reads that stored value.

**Why this priority**: One parser removes the raw `sys.argv` scans and the variant guard.

**Independent Test**: Run the parse-count regression test in `tests/unit/refactors/test_reject_unsupported_flag_variants.py`.

**Acceptance Scenarios**:

1. **Given** a parser double, **When** the bootstrap starts, **Then** `parse_args` runs one time.
2. **Given** a bad flag spelling, **When** the bootstrap parses it, **Then** argparse exits with status code 2.

### User Story 3 - Web host starts explicitly (Priority: P2)

The WSGI host imports the bootstrap class and calls the web bootstrap. The web path does not parse the process command line.

**Why this priority**: Gunicorn imports `wsgi.py`, and the web portal must still build its app.

**Independent Test**: Run `python -c "import wsgi"`.

**Acceptance Scenarios**:

1. **Given** a WSGI import, **When** `wsgi.py` starts, **Then** it calls the web bootstrap explicitly.
2. **Given** the web bootstrap, **When** it starts, **Then** it builds a default argument namespace without reading `sys.argv`.

### Edge Cases

- `--help` exits from argparse before the bootstrap performs startup side effects.
- `--skip-deps` skips the early dependency check through the stored parse result.
- `--test` without a token still defers the Mist session for the offline safe test path.
- WSGI still catches a missing credential path and serves the static registry fallback.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST expose an `ApplicationBootstrap` class in `src/refactors/main_entrypoint.py`.
- **FR-002**: The CLI host MUST parse arguments one time through argparse before startup side effects run.
- **FR-003**: The bootstrap object MUST store the parsed `Namespace` for all later startup decisions.
- **FR-004**: `MistHelper.py` MUST NOT read `sys.argv` at module scope.
- **FR-005**: Importing `MistHelper` MUST NOT create directories, configure logging, run subprocesses, or open network connections.
- **FR-006**: `wsgi.py` MUST call an explicit bootstrap path that does not parse command-line arguments.
- **FR-007**: `safe_input()` behavior MUST stay unchanged.
- **FR-008**: The unsupported raw flag guard MUST not run before argparse.
- **FR-009**: The module-level symbol table MUST stay stable against `main`.

## Interfaces and Behavior

- CLI: `python MistHelper.py [flags]` uses `ApplicationBootstrap()`.
- Help: `python MistHelper.py --help` exits before logging, file, dependency, and environment startup work.
- Web: `wsgi.py` uses `ApplicationBootstrap(parse_cli=False).bootstrap_for_web()`.
- Stored arguments: `ApplicationBootstrap.parsed_args` is the only runtime source for startup flag decisions.

## Constraints

- Do not add a wrapper function.
- Do not keep a fallback path that scans raw `sys.argv`.
- Keep all file paths built with `Path` or `os.path.join()`.
- Keep logging calls lazy with `%s` formatting.
- Keep `MistHelper.py` without suppression comments.

## Test Plan

1. Run the symbol check against `main`.
2. Run the import-side-effect regression test.
3. Run the parse-count regression test.
4. Run the entry point smoke checks for `import MistHelper`, `MistHelper.py --help`, and `import wsgi`.
5. Run the full local quality gates.

## Acceptance Criteria

- **AC-001 (#1701)**: `import MistHelper` performs no watched startup side effect.
- **AC-002 (#1701)**: `import MistHelper` does not call `sys.exit()`.
- **AC-003 (#1701)**: `logging.basicConfig` runs only inside the explicit bootstrap path.
- **AC-004 (#1701)**: `python MistHelper.py --help` exits before startup side effects run.
- **AC-005 (#1701)**: `wsgi.py` imports and creates the web app through explicit bootstrap.
- **AC-006 (#1706)**: `MistHelper.py` has zero `sys.argv` reads.
- **AC-007 (#1706)**: The entry point reads `sys.argv` in one place only.
- **AC-008 (#1706)**: The bootstrap parses the command line one time and stores the result.
- **AC-009 (#1706)**: `--test-interactive` fails with the standard argparse status code 2.
- **AC-010 (#1701, #1706)**: The full local quality gates pass.

## Assumptions

- The Python version warning can stay at the top, because issue #1701 allows it.
- The WSGI host can run the same dependency bootstrap as the CLI host.
- The old private names can remain inert to satisfy the symbol stability gate.
