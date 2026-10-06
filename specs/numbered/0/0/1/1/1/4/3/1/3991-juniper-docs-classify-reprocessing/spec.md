# Feature Specification: Juniper Docs Classification Reprocessing Package

**Feature Branch**: `3991-juniper-docs-classify-reprocessing`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Issue #3991: Refactor the Juniper Docs classification package so reprocessing has its own package. Move `manual_sorter.py` and `reclassifier.py` with no wrappers, update imports, tests, and the structure guard, add a focused structure guard, add a changelog entry, and use only the authorized three routed spec files."

## User Scenarios & Testing

### User Story 1 - Keep classification structure within the project limit (Priority: P1)

As a maintainer, I need reprocessing code in its own package so the classification package remains easy to navigate and follows the five-child structure rule.

**Why this priority**: The current package exceeds the project structure limit. This blocks compliant maintenance and makes the package harder to understand.

**Independent Test**: Inspect the classification package and run the focused structure guard. The guard passes when the package has no more than five direct structural children and the reprocessing package holds both reprocessing modules.

**Acceptance Scenarios**:

1. **Given** the current classification package, **When** the refactor is complete, **Then** `manual_sorter.py` and `reclassifier.py` are located under one `reprocessing` package.
2. **Given** the refactored package, **When** the focused structure guard runs, **Then** it reports the expected package shape and passes.
3. **Given** the old module locations, **When** the implementation is reviewed, **Then** no compatibility wrapper remains at either old location.

### User Story 2 - Preserve classification behavior through canonical imports (Priority: P1)

As a developer, I need runtime code and tests to import the moved modules from their canonical paths so existing behavior continues without duplicate entry points.

**Why this priority**: Incorrect imports would break the classification workflow and its tests even if the directory structure is compliant.

**Independent Test**: Run the focused Juniper Docs tests and inspect imports. The tests pass when all callers use the reprocessing package and the moved public classes retain their existing behavior.

**Acceptance Scenarios**:

1. **Given** callers that use `manual_sorter.py` or `reclassifier.py`, **When** imports are updated, **Then** each caller uses the matching path under `classify.reprocessing`.
2. **Given** the moved modules, **When** their focused tests run, **Then** the tests exercise the canonical modules and pass.
3. **Given** the moved public classes and module-level symbols, **When** symbol checks run, **Then** the symbols remain available at the canonical paths without aliases or wrappers.

### User Story 3 - Record the bounded refactor for maintainers (Priority: P2)

As a maintainer, I need the change record and routed specification scope to show exactly what the refactor includes and excludes.

**Why this priority**: A clear record prevents later work from reintroducing duplicate modules, changing shared registries, or expanding the authorized scope.

**Independent Test**: Review the change manifest and release-note fragment. The review passes when the record names the package move, import and test updates, focused guard, and exclusions.

**Acceptance Scenarios**:

1. **Given** the approved implementation boundary, **When** the release note is reviewed, **Then** it describes the reprocessing package move and its compatibility intent.
2. **Given** the routed specification set, **When** the feature files are reviewed, **Then** only the three authorized routed spec files are used for this feature.
3. **Given** the repository-wide shared files and historical specs, **When** the change is reviewed, **Then** no shared registry, generated reference, historical spec, `AGENTS.md`, or `CLAUDE.md` is changed.

### Edge Cases

- If an import still points to an old module path, the focused import or test check must fail rather than provide a fallback.
- If either moved file is copied instead of moved, the structure guard or symbol check must fail because duplicate module entry points are not allowed.
- If the reprocessing package has more than five direct structural children, the focused structure guard must fail.
- If a caller imports a symbol that the move does not preserve, the focused tests must identify the missing canonical symbol.
- If an unauthorized file is changed, the feature review must reject the change.

## Requirements

### Functional Requirements

- **FR-001**: The implementation MUST add one `reprocessing` package below `src/mist/intelligence/juniper_docs/classify`.
- **FR-002**: The implementation MUST move `manual_sorter.py` and `reclassifier.py` into the `reprocessing` package.
- **FR-003**: The implementation MUST remove the old module locations and MUST NOT add wrapper modules, aliases, or fallback imports.
- **FR-004**: The implementation MUST update every affected runtime import and test import to the canonical `classify.reprocessing` paths.
- **FR-005**: The implementation MUST preserve the public module-level symbols and behavior of the moved modules at their canonical paths.
- **FR-006**: The implementation MUST update the existing structure guard or its covered path contract to recognize the new package shape.
- **FR-007**: The implementation MUST add a focused structure guard that fails when the classification package exceeds five direct structural children or when either moved module is absent from the reprocessing package.
- **FR-008**: The focused structure guard MUST include direct failure tests for an over-limit package shape and for an invalid moved-module layout.
- **FR-009**: The implementation MUST add one release-note fragment for issue #3991.
- **FR-010**: The implementation MUST use only the authorized three routed specification files for this feature and MUST NOT create additional spec records.
- **FR-011**: The implementation MUST NOT edit historical specifications, shared registries, generated references, `AGENTS.md`, or `CLAUDE.md`.
- **FR-012**: The implementation MUST keep the change limited to the reprocessing package move, affected imports and tests, structure guards, the release note, and the authorized routed specification files.

### Mist Cloud Transport Requirements

This feature does not add or change a Mist Cloud transport.

## Key Entities

- **Classification package**: The package that groups Juniper Docs classification modules and must remain within the project hierarchy limit.
- **Reprocessing package**: The package that owns manual sorting and corpus reclassification modules.
- **Canonical module path**: The single supported import path for each moved module after the refactor.
- **Structure guard**: A focused test that proves the package shape and fails for invalid layouts.
- **Routed specification file**: A feature specification stored under the fixed numbered route for issue #3991.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The classification package has no more than five direct structural children after the change.
- **SC-002**: Both moved modules have one canonical location under `classify.reprocessing`, and no old-location wrapper remains.
- **SC-003**: All focused Juniper Docs classification tests pass with imports resolved only through canonical paths.
- **SC-004**: The focused structure guard passes for the valid layout and fails for each required invalid-layout fixture.
- **SC-005**: The final feature diff contains only the authorized implementation files, one release-note fragment, and the three routed specification files.
- **SC-006**: No historical spec, shared registry, generated reference, `AGENTS.md`, or `CLAUDE.md` file changes.

## Assumptions

- The existing public classes and module-level symbols in `manual_sorter.py` and `reclassifier.py` remain the supported behavior contract.
- Existing tests provide the primary behavior checks for the moved modules. The new focused guard provides the structure checks.
- The release-note fragment uses the repository issue naming rule and names issue #3991.
- The three routed specification files are the only specification records authorized for this feature. This request writes only the issue #3991 `spec.md` file.
- No Mist Cloud API, data schema, menu registry, generated reference, or operator workflow changes are required.
