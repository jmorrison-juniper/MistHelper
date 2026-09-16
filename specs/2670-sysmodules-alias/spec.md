# Feature Specification: Remove the MistHelper sys.modules Alias

**Feature Branch**: `refactor/2670-sysmodules-alias`

**Created**: 2026-09-16

**Status**: Ready for implementation

**Input**: GitHub issue #2670 asks to remove the root module alias after source back-references move.

## User Scenarios and Testing

### User Story 1 - Remove the entry point alias (Priority: P1)

A maintainer imports or runs MistHelper without a runtime alias from `__main__` to `MistHelper`.

**Why this priority**: The alias is a compatibility shim. It can hide a double import of the entry point.

**Independent Test**: Import `MistHelper` and `wsgi`. Search the source tree for removed back-references.

**Acceptance Scenarios**:

1. **Given** the source packages no longer import the root module, **When** the script starts, **Then** it does not assign `sys.modules["MistHelper"]`.
2. **Given** a developer imports `MistHelper`, **When** Python loads the module, **Then** the import succeeds without the alias.
3. **Given** the WSGI loader imports the application, **When** Python loads `wsgi`, **Then** the import succeeds without the alias.

### User Story 2 - Preserve the import graph guard (Priority: P2)

A maintainer gets a test failure if new source code imports the root module.

**Why this priority**: The guard prevents a new hidden dependency after the alias removal.

**Independent Test**: Run `python -m pytest tests/guardrails/test_source_misthelper_backrefs.py -q`.

**Acceptance Scenarios**:

1. **Given** source code contains `import MistHelper`, **When** the scanner reads it, **Then** the scanner reports a finding.
2. **Given** source code contains `importlib.import_module("MistHelper")`, **When** the scanner reads it, **Then** the scanner reports a finding.

### Edge Cases

- If a test patch still injects `sys.modules["MistHelper"]`, it must stay in tests only.
- If a string mention of `MistHelper` appears in a docstring, the guard must not fail.
- If a source module imports the entry point by name, the guard must fail before the alias can hide it.
- If a source module hides the entry point name in a constant, the guard must still fail.

## Requirements

### Functional Requirements

- **FR-001**: `MistHelper.py` MUST not assign `sys.modules["MistHelper"]`.
- **FR-002**: `src` MUST contain no executable `import MistHelper` statement.
- **FR-003**: `src` MUST contain no executable `importlib.import_module("MistHelper")` call.
- **FR-004**: `python -c "import MistHelper"` MUST succeed.
- **FR-005**: `python -c "import wsgi"` MUST succeed.
- **FR-006**: The source back-reference guard MUST reject a direct root import and a lazy root import.
- **FR-007**: The test plan MUST search string patch targets because symbol checks cannot see them.

### Key Entities

- **Root entry point**: `MistHelper.py`, which owns the command line startup path.
- **Source packages**: Code under `src` that must not import the root entry point.
- **Import graph guard**: `tests/guardrails/test_source_misthelper_backrefs.py`, which scans executable imports.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `git grep -n "import MistHelper" -- src` prints no matches.
- **SC-002**: `git grep -n "import_module(.MistHelper.)" -- src` prints no matches.
- **SC-003**: `git grep -n 'sys.modules["MistHelper"]' -- MistHelper.py` prints no matches.
- **SC-004**: `python -c "import MistHelper; print('MistHelper OK')"` prints `MistHelper OK`.
- **SC-005**: `python -c "import wsgi; print('wsgi OK')"` prints `wsgi OK`.
- **SC-006**: `python -m pytest tests/guardrails/test_source_misthelper_backrefs.py -q` passes.

## Double-Import Risk

The removed alias made a later root import resolve to the active `__main__` module. Without that alias, a stale source back-reference could load a second module copy. The second copy would hold separate module state. The search plan therefore includes executable source imports, lazy source imports, string patch targets, and constant-based root imports.

## Test Plan

1. Search `src` for `import MistHelper`.
2. Search `src` for `import_module(.MistHelper.)`.
3. Search the repository for `sys.modules["MistHelper"]`.
4. Import `MistHelper` from Python.
5. Import `wsgi` from Python.
6. Run the guardrail tests.
7. Run the requested lint, type, complexity, symbol, and test gates.
8. Confirm the improved guard rejects a constant-based root import and a `sys.modules` root lookup.

## Assumptions

- Pull request #2730 merged before this work started.
- `sys` remains required in `MistHelper.py` because other startup and dependency code uses it.
- Test-only `sys.modules` patching can remain when it does not create a production alias.
