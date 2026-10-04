# Feature Specification: Source Domain Packages

**Feature Branch**: `chore/3574-src-domain-packages`

**Created**: 2026-10-03

**Status**: Implemented

**Input**: Issue #3574 requests domain grouping for the direct children of `src`.

## User Scenarios and Testing

### User Story 1 - Find source code by domain (Priority: P1)

A contributor finds a source module through a small set of domain packages.

**Why this priority**: The current source root has 39 package directories. This count violates the structural rule.

**Independent Test**: Inspect the direct children of `src`. The result contains five children or fewer, excluding `__init__.py`.

**Acceptance Scenarios**:

1. **Given** the refactored source tree, **When** a contributor lists `src`, **Then** the contributor sees five domain packages or fewer.
2. **Given** a domain package, **When** a contributor lists each nested package, **Then** each package contains five direct children or fewer.

---

### User Story 2 - Run existing behavior after the move (Priority: P1)

An operator runs MistHelper and receives the same behavior as before the source move.

**Why this priority**: A structural refactor must not change an API call, an output, or a safety control.

**Independent Test**: Run focused behavior tests for each moved domain and compare the results with `origin/main`.

**Acceptance Scenarios**:

1. **Given** an existing menu operation, **When** the operation imports its implementation, **Then** the import resolves from the new domain path.
2. **Given** an existing test, **When** the test runs after the move, **Then** the result matches the result before the move.

---

### User Story 3 - Preserve the public symbol surface (Priority: P1)

A test or tool imports each documented public symbol from its new canonical module.

**Why this priority**: The refactor must not remove a public class, function, or constant.

**Independent Test**: Compare module-level symbols before and after the move. The comparison reports no lost symbol.

**Acceptance Scenarios**:

1. **Given** a moved module, **When** the symbol comparison reads both revisions, **Then** it reports no lost module-level name.
2. **Given** the completed migration, **When** a structural test scans Python imports, **Then** it finds no import from an old source path.

### Edge Cases

- A dynamic import string must move with the static imports.
- A documentation example must use the new canonical path.
- A package initializer must keep each explicit public export.
- A relative import must still resolve after the added package levels.
- A non-Python asset inside a moved package must keep its package-relative location.

## Requirements

### Functional Requirements

- **FR-001**: The change MUST reduce the direct children of `src` to five or fewer, excluding `__init__.py`.
- **FR-002**: Each new package level MUST contain five direct children or fewer.
- **FR-003**: The change MUST move all current source packages into named domain packages.
- **FR-004**: The change MUST update every repository import to the new canonical path.
- **FR-005**: The change MUST preserve every public module-level symbol.
- **FR-006**: The change MUST NOT add a compatibility wrapper, import alias, forwarding module, or fallback path.
- **FR-007**: The change MUST add a structural test for the direct-child limit.
- **FR-008**: The change MUST add a structural test that rejects old source import paths.
- **FR-009**: The change MUST add import tests for representative public symbols in each domain.
- **FR-010**: The change MUST run focused behavior tests for each moved domain.
- **FR-011**: The change MUST update the contributor map and the source architecture diagrams.
- **FR-012**: The change MUST add one release-note fragment for issue #3574.
- **FR-013**: The change MUST run the compile, lint, format, type, symbol, and focused test gates.
- **FR-014**: The change MUST preserve package data and static assets at their package-relative paths.
- **FR-015**: The change MUST not change a Mist API method, a database schema, or a user workflow.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `src` contains no more than five direct children, excluding `__init__.py`.
- **SC-002**: Each new domain package contains no more than five direct children.
- **SC-003**: A repository scan reports zero imports from each old source path.
- **SC-004**: The symbol comparison reports zero lost module-level names.
- **SC-005**: All focused structural, import, and behavior tests pass.
- **SC-006**: Ruff, Black, mypy, and Python compilation pass for the changed tree.

## Assumptions

- The canonical import paths can change because all repository call sites move in one change.
- Public symbols must remain available from their new canonical modules.
- No external package contract promises the old internal `src.<package>` paths.
- Existing open pull requests can require a rebase after this structural change.
