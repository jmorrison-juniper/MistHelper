# Feature Specification: Source Back-Reference Removal

**Feature Branch**: `refactor/1703-src-backref-final`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #1703 asks for the final source package cleanup that unblocks issue #2670.

## User Scenarios & Testing

### User Story 1 - Source imports stay inside `src` (Priority: P1)

A maintainer can import source packages without a source package importing the root `MistHelper` module.

**Why this priority**: Issue #2670 cannot remove the root alias until this condition is true.

**Independent Test**: Run the grep checks under `src` and import `MistHelper` and `wsgi`.

**Acceptance Scenarios**:

1. **Given** the repository source tree, **When** the guard scans `src`, **Then** it rejects executable `import MistHelper` and `importlib.import_module("MistHelper")` calls.
2. **Given** the installed environment, **When** Python imports `MistHelper`, **Then** the import succeeds.
3. **Given** the installed environment, **When** Python imports `wsgi`, **Then** the import succeeds.

### User Story 2 - Runtime state remains available (Priority: P2)

A source module can read the active API session, organization, output format, and settings without a root module back-reference.

**Why this priority**: Many remaining back-references read shared state rather than helper code.

**Independent Test**: Run the existing guardrail tests and source import tests.

**Acceptance Scenarios**:

1. **Given** a source module needs shared state, **When** it resolves that state, **Then** it reads the source-owned context or settings seam.
2. **Given** a source module needs a helper class, **When** it resolves that class, **Then** it resolves the canonical `src` module.

### User Story 3 - The guard measures its input (Priority: P3)

A future pull request receives a clear failure when it adds a source back-reference.

**Why this priority**: The guard must prove it scanned files, and it must fail on zero files.

**Independent Test**: Run `pytest tests/guardrails -v` and `python -m tools.guard_proof_audit`.

**Acceptance Scenarios**:

1. **Given** a test source file with a deliberate back-reference, **When** the guard scanner checks it, **Then** the scanner reports the violation.
2. **Given** an empty scan root, **When** the guard scanner checks it, **Then** the scanner fails with a zero-file message.

### Edge Cases

- If a source file holds only a comment that mentions the old import, the grep proof must still be empty.
- If a source file uses a lazy import to avoid a cycle, the repair must keep the import lazy without using the root module.
- If a guard cannot find Python files, it must fail instead of passing silently.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST remove 43 executable `import MistHelper` statements from `src`.
- **FR-002**: The system MUST remove 366 executable `importlib.import_module("MistHelper")` calls from `src`.
- **FR-003**: The system MUST remove zero executable `importlib.import_module('MistHelper')` calls from `src`.
- **FR-004**: The system MUST remove all source comments and docstrings that match the final grep proof patterns.
- **FR-005**: The system MUST resolve helper-class needs through canonical `src` modules.
- **FR-006**: The system MUST resolve shared runtime state through a source-owned context or settings seam.
- **FR-007**: The system MUST keep `sys.modules["MistHelper"] = sys.modules["__main__"]` in `MistHelper.py` for issue #2670.
- **FR-008**: The system MUST add an import graph guard under `tests/guardrails/`.
- **FR-009**: The guard MUST report how many files it scanned.
- **FR-010**: The guard MUST fail when it scans zero files.
- **FR-011**: The guard MUST include a negative test for a deliberate source back-reference.

### Back-Reference Groups

- **Helper code**: Calls that need `ConfigUtils`, `DataExporter`, exporters, prompt helpers, or utility classes move to the canonical `src` owner.
- **Shared state**: Calls that need `apisession`, `org_id`, `msp_privileges`, output format, and telemetry move to the source runtime context or settings seam.
- **Lazy cycle break**: Calls that were lazy only to avoid root cycles move to lazy source resolution.
- **Dead import text**: Comments and docstrings that match the final grep proof are rewritten or removed.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `git grep -n "import MistHelper" -- src` returns no rows.
- **SC-002**: `git grep -n "import_module(.MistHelper.)" -- src` returns no rows.
- **SC-003**: `python -c "import MistHelper"` succeeds.
- **SC-004**: `python -c "import wsgi"` succeeds.
- **SC-005**: `python -m tools.guard_proof_audit` does not list the new guard.

## Assumptions

- The current `origin/main` tree is the baseline after pull request #2671.
- Issue #2670 owns removal of the root `sys.modules` alias.
- No open pull request changes `MistHelper.py` at the start of this work.
