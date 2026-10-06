# Feature Specification: Database Writers Package

**Feature Branch**: `jmorrison-juniper-database-package-split-3824`

**Created**: 2026-10-06

**Status**: Draft

**Input**: MistHelper issue #3824 moves the ArangoDB and Redis writers into a bounded
`writers` package and adds a scoped structural guard.

**Baseline**: `origin/main` at `2a00e32745472f70764206b060dacc1c4dd13992`

## User Scenarios & Testing

### User Story 1 - Find Database Writers in One Package (Priority: P1)

A maintainer can find the ArangoDB and Redis writer modules in one package that has a clear
database-writer purpose.

**Why this priority**: The current `db` package has six direct modules. The new package restores
the five-item limit without changing database behavior.

**Independent Test**: Inspect the persistence package and confirm that `db` has four direct
modules and the `writers` package.

**Acceptance Scenarios**:

1. **Given** the current `db` package, **When** the change moves both writer modules, **Then**
   `db` has five direct children after package metadata is excluded.
2. **Given** the new `writers` package, **When** a maintainer inspects it, **Then** it contains
   `arango_writer.py`, `redis_writer.py`, and a docstring-only `__init__.py`.
3. **Given** the moved modules, **When** existing database functions run, **Then** their public
   behavior remains unchanged.

---

### User Story 2 - Use Only the New Writer Paths (Priority: P2)

A maintainer can use one canonical import and file path for each database writer in active
repository content.

**Why this priority**: Old active references can hide incomplete moves and can cause import or
mock failures.

**Independent Test**: Search active source, scripts, tests, and documentation. Confirm that each
old writer path is absent and each required reference uses the new package path.

**Acceptance Scenarios**:

1. **Given** active Python imports and mock targets, **When** the move is complete, **Then** each
   reference uses `src.foundation.persistence.db.writers.arango_writer` or
   `src.foundation.persistence.db.writers.redis_writer`.
2. **Given** active documentation and source comments, **When** they name a writer file, **Then**
   they use `src/foundation/persistence/db/writers/`.
3. **Given** historical specifications for other issues, **When** the active-path scan runs,
   **Then** those immutable process records remain unchanged and outside the scan.

---

### User Story 3 - Detect New Persistence Package Violations (Priority: P3)

A maintainer receives a clear test failure when a checked package level under
`src/foundation/persistence` exceeds five direct children.

**Why this priority**: A scoped guard prevents the repaired package level from drifting and does
not expand this issue into unrelated hierarchy debt.

**Independent Test**: Run the guard in its normal state and with a controlled sixth child. Confirm
that the normal state passes and the controlled violation fails.

**Acceptance Scenarios**:

1. **Given** compliant checked package levels, **When** the structural guard runs, **Then** it
   passes and reports the checked directory count.
2. **Given** a checked package level with six direct children, **When** the failure proof runs,
   **Then** it fails with the checked directory count and the violating path.
3. **Given** an unrelated hierarchy violation outside `src/foundation/persistence`, **When** the
   scoped guard runs, **Then** it does not report that violation.

### Edge Cases

- Package metadata such as `__init__.py` and generated cache directories do not count as direct
  structural children.
- Import strings in patch targets and delayed imports must move with normal imports.
- Active path references in comments and documentation must move even when runtime imports pass.
- Historical specifications can contain old paths because they record the state of their own
  issues.
- The guard must fail if it cannot inspect its required package root.

## Requirements

### Functional Requirements

- **FR-001**: The change MUST move
  `src/foundation/persistence/db/arango_writer.py` to
  `src/foundation/persistence/db/writers/arango_writer.py`.
- **FR-002**: The change MUST move
  `src/foundation/persistence/db/redis_writer.py` to
  `src/foundation/persistence/db/writers/redis_writer.py`.
- **FR-003**: The change MUST add
  `src/foundation/persistence/db/writers/__init__.py`.
- **FR-004**: The new `writers/__init__.py` MUST contain only a package docstring.
- **FR-005**: The new `writers/__init__.py` MUST NOT re-export a writer name.
- **FR-006**: The change MUST NOT add an alias, compatibility shim, forwarding module, or fallback
  for either old writer path.
- **FR-007**: The change MUST update every active source import, script import, test import, mock
  target, source path, and active documentation path for the two moved modules.
- **FR-008**: The change MUST leave historical specifications for other issues unchanged because
  they are immutable process records.
- **FR-009**: The active old-path check MUST exclude historical specifications without excluding
  active source, scripts, tests, or active documentation.
- **FR-010**: The `db` package MUST have exactly five direct structural children after the move:
  four modules and the `writers` package.
- **FR-011**: The change MUST add a structural guard that checks applicable package levels under
  `src/foundation/persistence`.
- **FR-012**: The structural guard MUST enforce a maximum of five direct structural children for
  each checked package level.
- **FR-013**: The structural guard MUST report the number of directories that it checked.
- **FR-014**: The structural guard MUST report each violating package path and its measured child
  count.
- **FR-015**: The guard tests MUST prove failure with a controlled package level that has more
  than five direct structural children.
- **FR-016**: The guard MUST fail with a clear cause when its required package root cannot be read.
- **FR-017**: Existing database writer behavior, public classes, constants, error handling, and
  persistence results MUST remain unchanged.
- **FR-018**: The implementation MUST use the current branch and MUST use
  `2a00e32745472f70764206b060dacc1c4dd13992` as the approved `origin/main` baseline.

### Scope Boundaries

The implementation scope includes these items:

- Move the two writer modules into the new `writers` package.
- Add the docstring-only package initializer.
- Update active imports, patch targets, comments, scripts, tests, and documentation paths.
- Add focused tests for the new canonical paths and the persistence package structure.
- Add the scoped structural guard and its failure proof.

### Non-Goals

- Do not change `MistHelper.py`.
- Do not repair or guard an unrelated hierarchy violation.
- Do not change database writer behavior or persistence schemas.
- Do not split, rename, or refactor classes, functions, constants, or methods in either writer.
- Do not add a re-export, alias, shim, forwarding module, fallback import, or deprecation path.
- Do not change historical specifications for other issues.
- Do not broaden the structural guard beyond package levels under
  `src/foundation/persistence`.
- Do not change unrelated imports, documentation, tests, scripts, or source files.
- Do not create or rename a branch.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The `db` package has exactly five direct structural children after package metadata
  is excluded.
- **SC-002**: All active source, script, test, and active documentation references use the new
  writer paths.
- **SC-003**: Zero active references use either old writer module path.
- **SC-004**: All existing tests for ArangoDB and Redis writer behavior pass without behavior
  changes.
- **SC-005**: The structural guard passes for the repository and reports a nonzero checked
  directory count.
- **SC-006**: The controlled failure test proves that a sixth direct child causes the guard to
  fail and identify the violating path.
- **SC-007**: No file under another issue's specification directory changes.
- **SC-008**: `MistHelper.py` and unrelated hierarchy levels have zero changes.

## Assumptions

- The approved move keeps each writer module body unchanged except for imports that the new
  package location requires.
- Active documentation means maintained repository documentation and active source comments. It
  does not include historical specifications for other issues.
- The structural count excludes `__init__.py`, cache directories, and other generated metadata.
- Existing tests remain the authority for database writer behavior.
- The implementation will add only the files and edits that the bounded change requires.
