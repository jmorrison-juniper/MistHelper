# Feature Specification: Audit Report Rendering Packages

**Feature Branch**: `4011-audit-rendering`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Issue #4011: Refactor the audit package so rendering has its own package. Move `renderer.py` under `audit/rendering/` and the five `_renderer_*` helper modules under `audit/rendering/helpers/` with no wrappers, update canonical imports, focused tests, and structure guards, add `changelog.d/issue-4011-audit-rendering.md`, and use only the authorized three routed spec files."

## User Scenarios & Testing

### User Story 1 - Keep the audit structure within the project limit (Priority: P1)

As a maintainer, I need the renderer and its helpers in their own packages, so the audit package remains easy to read and obeys the five-child structure rule.

**Why this priority**: The audit package holds ten structural children. That count breaks the project structure limit and makes the package hard to navigate.

**Independent Test**: Inspect the audit package and run the focused structure guard. The guard passes when each audit level holds five children or fewer and each moved module sits at its canonical path.

**Acceptance Scenarios**:

1. **Given** the current audit package, **When** the refactor is complete, **Then** `renderer.py` sits under one `rendering` package.
2. **Given** the current audit package, **When** the refactor is complete, **Then** the five `_renderer_*` modules sit under one `rendering/helpers` package.
3. **Given** the refactored package, **When** the focused structure guard runs, **Then** it reports the measured package shape and passes.
4. **Given** the old module locations, **When** the implementation is reviewed, **Then** no compatibility wrapper remains at any old location.

### User Story 2 - Preserve audit rendering behavior through canonical imports (Priority: P1)

As a developer, I need runtime code and tests to import the moved modules from their canonical paths, so the audit report output does not change.

**Why this priority**: A wrong import breaks the audit analysis operation and its report output even when the directory structure obeys the limit.

**Independent Test**: Run the focused renderer tests and the audit operation consumer test. The tests pass when each caller uses the canonical path and each moved module keeps its behavior.

**Acceptance Scenarios**:

1. **Given** each caller of the renderer or a helper, **When** the imports are updated, **Then** each caller uses the matching path under `audit.rendering`.
2. **Given** the moved modules, **When** the focused tests and the symbol guard run, **Then** they read the canonical modules and pass.
3. **Given** the moved module-level symbols, **When** the symbol guard runs, **Then** each symbol remains available at its canonical path without an alias or a wrapper.
4. **Given** the HTML, Mermaid, time, format, and delta helpers, **When** the focused tests run, **Then** the escaping and output behavior does not change.

### User Story 3 - Record the bounded refactor for maintainers (Priority: P2)

As a maintainer, I need the change record and the routed specification scope to show what the refactor includes and excludes.

**Why this priority**: A clear record stops later work from adding a duplicate module, changing a shared registry, or widening the authorized scope.

**Independent Test**: Review the release-note fragment and the routed specification set. The review passes when the record names the package move, the import updates, the focused guard, and the exclusions.

**Acceptance Scenarios**:

1. **Given** the approved implementation boundary, **When** `changelog.d/issue-4011-audit-rendering.md` is reviewed, **Then** it describes the rendering package move.
2. **Given** the routed specification set, **When** the feature files are reviewed, **Then** only the three authorized routed spec files exist for this feature.
3. **Given** the shared files and the historical specs, **When** the change is reviewed, **Then** no shared registry, generated reference, historical spec, `AGENTS.md`, or `CLAUDE.md` changes.

### Edge Cases

- If an import still names an old module path, the focused guard must fail instead of giving a fallback.
- If a moved file is copied instead of moved, the structure guard or the symbol guard must fail, because a duplicate entry point is not allowed.
- If the rendering package or the helpers package holds more than five direct structural children, the focused structure guard must fail.
- If a caller imports a symbol that the move does not preserve, the focused tests must name the missing canonical symbol.
- If the guard cannot read the audit package root, it must fail and report that path.

## Requirements

### Functional Requirements

- **FR-001**: The implementation MUST add one `rendering` package below `src/mist/access/audit`.
- **FR-002**: The implementation MUST add one `helpers` package below `src/mist/access/audit/rendering`.
- **FR-003**: The implementation MUST move `renderer.py` into the `rendering` package.
- **FR-004**: The implementation MUST move `_renderer_delta.py`, `_renderer_format.py`, `_renderer_html.py`, `_renderer_mermaid.py`, and `_renderer_time.py` into the `helpers` package.
- **FR-005**: The implementation MUST remove each old module location and MUST NOT add a wrapper module, an alias, or a fallback import.
- **FR-006**: The implementation MUST update each affected runtime import, utility import, and test import to the canonical `audit.rendering` paths.
- **FR-007**: The implementation MUST preserve the module-level symbols and the behavior of each moved module at its canonical path.
- **FR-008**: The implementation MUST add six exact old-to-new module paths to the public symbol-preservation guard.
- **FR-009**: The implementation MUST add a focused structure guard that fails when an audit package level holds more than five direct structural children or when an active file still names a removed renderer path.
- **FR-010**: The focused structure guard MUST include direct failure tests for an over-limit package shape, an unreadable package root, and an active old path.
- **FR-011**: The implementation MUST use `changelog.d/issue-4011-audit-rendering.md` as the only release-note fragment for this feature.
- **FR-012**: The implementation MUST use only the authorized three routed specification files and MUST NOT create another spec record.
- **FR-013**: The implementation MUST NOT edit a historical specification, a shared registry, a generated reference, `AGENTS.md`, or `CLAUDE.md`.
- **FR-014**: The implementation MUST move no source module except the renderer and its five helper modules.

### Mist Cloud Transport Requirements

This feature does not add or change a Mist Cloud transport.

## Key Entities

- **Audit package**: The package that groups audit analysis modules and must stay inside the project hierarchy limit.
- **Rendering package**: The package that owns the audit report renderer.
- **Helpers package**: The package that owns the delta, format, HTML, Mermaid, and time helper modules.
- **Canonical module path**: The one supported import path for each moved module after the refactor.
- **Structure guard**: A focused test that measures the package shape and fails for an invalid layout.
- **Routed specification file**: A feature specification under the fixed numbered route for issue #4011.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The audit package root holds exactly five direct structural children after the change.
- **SC-002**: The rendering package holds exactly two direct structural children, and the helpers package holds exactly five.
- **SC-003**: Each moved module has one canonical location, and no old-location wrapper remains.
- **SC-004**: Each focused audit renderer test and the audit operation consumer test passes through canonical imports.
- **SC-005**: The focused structure guard passes for the live layout and fails for each required invalid fixture.
- **SC-006**: The public symbol-preservation guard reports no lost module-level symbol for the six moved modules.
- **SC-007**: The final feature diff holds only the authorized implementation files, one release-note fragment, and the three routed specification files.

## Assumptions

- The module-level symbols of the six moved modules remain the supported behavior contract.
- The existing renderer tests and the audit operation test give the primary behavior checks. The new focused guard gives the structure checks.
- The release-note fragment is `changelog.d/issue-4011-audit-rendering.md`, and it names issue #4011.
- The three routed specification files are the only specification records authorized for this feature.
- No Mist Cloud API, data schema, menu registry, generated reference, or operator workflow change is required.
