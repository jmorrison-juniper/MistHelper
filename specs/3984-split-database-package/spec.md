# Feature Specification: Split Database Package

**Feature Branch**: `jmorrison-juniper-refactor-3984-split-database-package`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #3984 requests a behavior-preserving structural refactor of six database modules.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve Database Behavior (Priority: P1)

As a MistHelper operator, I need each database operation to keep its current result after the package split.

**Why this priority**: A persistence change can damage stored data or interrupt an export.

**Independent Test**: Run the focused database tests before and after the move and compare each result.

**Acceptance Scenarios**:

1. **Given** an existing ArangoDB or Redis write, **When** the refactored code runs, **Then** it produces the same stored data and status.
2. **Given** an existing retention or routing decision, **When** the refactored code runs, **Then** it selects the same action and target.
3. **Given** an existing schema or host resolution input, **When** the refactored code runs, **Then** it returns the same value or error.

---

### User Story 2 - Use Canonical Module Paths (Priority: P2)

As a maintainer, I need each consumer to import the moved symbols from one canonical path.

**Why this priority**: One path prevents hidden compatibility code and future import drift.

**Independent Test**: Search production code and tests for each previous module path and confirm that no reference remains.

**Acceptance Scenarios**:

1. **Given** a direct consumer of a moved module, **When** imports are inspected, **Then** the consumer uses the new canonical path.
2. **Given** a test patch target or dynamic module reference, **When** it is inspected, **Then** it uses the new canonical path.
3. **Given** any package initializer, **When** it is inspected, **Then** it does not re-export a moved symbol.

---

### User Story 3 - Meet the Package Limit (Priority: P3)

As a maintainer, I need the database package to comply with the five-child structure limit.

**Why this priority**: A compliant hierarchy keeps the persistence code easy to navigate and review.

**Independent Test**: Run the source structure guard and count the direct children in each affected package.

**Acceptance Scenarios**:

1. **Given** the refactored database package, **When** direct children are counted, **Then** each affected package has five or fewer.
2. **Given** the database package root, **When** its children are listed, **Then** it contains only its initializer and three named subpackages.
3. **Given** each new subpackage, **When** its children are listed, **Then** it contains one initializer and two moved modules.

### Edge Cases

- Import-time behavior remains safe when an optional database service is unavailable.
- Test patch targets resolve to the canonical module after each move.
- Module-level constants, classes, functions, and exceptions keep their existing names and values.
- Logging keeps the current messages, levels, redaction, and database routing behavior.
- The refactor does not change index declarations, retention rules, host selection, or router decisions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The refactor MUST move exactly six production modules from `src/foundation/persistence/db/`.
- **FR-002**: `arango_writer.py` and `redis_writer.py` MUST move to `src/foundation/persistence/db/backends/`.
- **FR-003**: `router.py` and `retention.py` MUST move to `src/foundation/persistence/db/coordination/`.
- **FR-004**: `database_schema_utils.py` and `host_resolver.py` MUST move to `src/foundation/persistence/db/support/`.
- **FR-005**: Each new subpackage MUST contain an `__init__.py` file.
- **FR-006**: Package initializers MUST NOT re-export moved modules or moved module-level symbols.
- **FR-007**: Every production and test consumer MUST use the canonical new module path.
- **FR-008**: The old six module paths MUST cease to exist.
- **FR-009**: The refactor MUST NOT add compatibility shims, aliases, adapters, or fallback imports.
- **FR-010**: Each moved module MUST preserve all existing public module-level symbols.
- **FR-011**: Database behavior, schemas, indexes, stored values, routing, retention, and host resolution MUST remain unchanged.
- **FR-012**: Direct consumers MAY change only the imports or patch targets required by the module moves.
- **FR-013**: Focused database tests MAY change only to use canonical paths or to prove preserved behavior.
- **FR-014**: The change MUST NOT modify menu files, `MistHelper.py`, `operation_registry.py`, or `endpoint_primary_key_strategies.py`.
- **FR-015**: The change MUST NOT modify unrelated production modules or unrelated tests.
- **FR-016**: The change MAY add no more than one issue-specific changelog fragment.
- **FR-017**: Each affected package MUST have five or fewer direct children.
- **FR-018**: Focused database tests and the source structure guard MUST pass.
- **FR-019**: Ruff, Black, mypy, symbol preservation, security, and complexity gates MUST pass for the affected files.
- **FR-020**: The pull request MUST reference parent issue #3824 without closing it.

### Key Entities

- **Backend modules**: The ArangoDB and Redis writers that persist database records.
- **Coordination modules**: The router and retention logic that select database actions.
- **Support modules**: The schema and host resolution logic used by the database modules.
- **Canonical import**: The single supported path for a moved module or symbol.
- **Behavior baseline**: The existing outputs, errors, schemas, side effects, and public symbols before the move.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The database package root has four direct children after the refactor.
- **SC-002**: Each new subpackage has three direct children, including its initializer.
- **SC-003**: All six modules exist only at their specified canonical paths.
- **SC-004**: A repository search finds zero references to the six previous module paths.
- **SC-005**: The public module-level symbol inventory is identical before and after each move.
- **SC-006**: All focused database tests and each requested gate complete with zero failures.
- **SC-007**: Database schema and persistence behavior comparisons show zero unintended differences.
- **SC-008**: Parent issue #3824 remains open after this issue is complete.

## Assumptions

- The current branch already belongs to issue #3984 and requires no branch change.
- The listed module grouping is the approved canonical layout.
- Import and patch-target updates are structural changes, not behavior changes.
- Existing focused tests define the minimum behavior baseline.
- No Mist cloud transport or menu behavior is part of this refactor.
