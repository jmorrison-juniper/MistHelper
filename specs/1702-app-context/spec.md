# Feature Specification: Application context

**Feature Branch**: `refactor/1702-app-context`

**Created**: 2026-09-14

**Status**: Implemented

**Input**: Replace the module-level session globals with an application context object and remove the run-time session patching.

## Problem

`MistHelper.py` stored the live Mist API session and the selected organization in module-level variables. Several functions changed those variables with `global` statements. Other code copied the same values into `ConfigUtils`. A reader could not know which value was current.

The session initializer also changed the Mist API session object after construction. It added `mist_get` when the SDK exposed `get`. It mounted timeout adapters through a private transport. It also changed the process environment during a filtered-token retry.

## User Scenarios and Testing

### User Story 1 - Context owns the state (Priority: P1)

A maintainer reads the entry point. The maintainer sees one `AppContext` object that owns the session, the selected organization, the MSP grants, the output format, and the parsed arguments.

**Independent Test**: Run `tests/unit/refactors/test_app_context_session_state.py`.

**Acceptance Scenarios**:

1. **Given** an imported `MistHelper`, **When** a test reads the module dictionary, **Then** it finds no live session global.
2. **Given** two `AppContext` instances, **When** one receives a session and MSP grants, **Then** the other remains empty.

### User Story 2 - Session setup has one seam (Priority: P1)

A maintainer reads the token session path. The maintainer sees one `MistSessionConfigurator` seam that configures the session once for the context.

**Independent Test**: Run `tests/unit/refactors/test_app_context_session_state.py`.

**Acceptance Scenarios**:

1. **Given** a new context and a fake session, **When** the configurator runs twice, **Then** it mounts adapters only during the first run.
2. **Given** a session that exposes `get`, **When** validation runs, **Then** no code adds `mist_get` to the session object.

### User Story 3 - Startup still works (Priority: P2)

An operator starts the CLI, the help path, or the WSGI host. The entry points keep the same behavior while they read state from the context.

**Independent Test**: Run the entry point smoke commands.

**Acceptance Scenarios**:

1. **Given** a fresh interpreter, **When** it imports `MistHelper`, **Then** the import succeeds.
2. **Given** the CLI help flag, **When** the command runs, **Then** argparse prints help.
3. **Given** a WSGI import, **When** it runs, **Then** the import succeeds.

## Edge Cases

- A missing token fails local credential validation before a session is built.
- A placeholder token fails local credential validation before a session is built.
- An absent `.env` file returns no organization and does not crash.
- A second bootstrap call in one process reuses the same explicit context.
- `safe_input()` stays in the existing `InputUtils` path.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST expose an `AppContext` class in `src/refactors/main_entrypoint.py`.
- **FR-002**: `AppContext` MUST own the Mist API session, the SDK module, the selected organization, the MSP grants, the selected MSP, the output format, the progress emitter, and the parsed arguments.
- **FR-003**: Two `AppContext` instances MUST NOT share the session or MSP grant list.
- **FR-004**: `MistHelper.py` MUST NOT store live session state in module globals.
- **FR-005**: Session initialization MUST store the built session on `AppContext`.
- **FR-006**: Interactive login MUST apply selector state to `AppContext`.
- **FR-007**: `ConfigUtils.set_apisession` and `ConfigUtils.set_cached_org_id` MUST NOT be called by `MistHelper.py`.
- **FR-008**: A single explicit session configurator MUST own the request timeout mount.
- **FR-009**: Validation MUST NOT add `mist_get` or another attribute to the third-party session object.
- **FR-010**: The module-level symbol table MUST stay stable against `main`.

## Interfaces and Behavior

- `AppContext` is a dataclass in `src/refactors/main_entrypoint.py`.
- `MainEntrypoint.context` holds the process context for CLI and WSGI startup.
- `ApplicationBootstrap` stores the parsed arguments on the context.
- `MistSessionInitializer.initialize()` writes the session to `MainEntrypoint.context`.
- `MistSessionConfigurator.configure_once()` configures and validates the session.

## Constraints

- Do not add a standalone function that only delegates to a class method.
- Do not log tokens or passwords.
- Keep file paths built with `Path` or `os.path.join()`.
- Keep `MistHelper.py` without suppression comments.
- Keep compatibility for issue #1703 call sites that still import `MistHelper`.

## Test Plan

1. Run the symbol check against `main`.
2. Run the entry point smoke checks.
3. Run the new AppContext regression tests.
4. Run the local quality gates.
5. Watch the pull request checks through CodeQL before merge.

## Acceptance Criteria

- **AC-001 (#1702)**: `MistHelper` declares no live module-level session global.
- **AC-002 (#1702)**: Two `AppContext` instances do not share state.
- **AC-003 (#1702)**: `MistHelper.py` has no calls to `ConfigUtils.set_apisession` or `ConfigUtils.set_cached_org_id`.
- **AC-004 (#1702)**: The snapshot helper pair no longer runs in the interactive initializer.
- **AC-005 (#1702)**: The module-level symbol table stays unchanged.
- **AC-006 (#1712)**: `MistSessionConfigurator` configures a session only once per context.
- **AC-007 (#1712)**: The session validation path does not add `mist_get` to a session.
- **AC-008 (#1712)**: The timeout private-transport access lives in one explicit seam.
- **AC-009 (#1712)**: Missing token, placeholder token, and absent `.env` edges are covered.
- **AC-010 (#1702, #1712)**: The entry point smoke checks pass.
- **AC-011 (#1702, #1712)**: The local quality gates pass.

## Assumptions

- Issue #1703 will move modules that still import `MistHelper` for dependency access.
- The current Mist API SDK exposes a supported `mist_get` or `get` method.
