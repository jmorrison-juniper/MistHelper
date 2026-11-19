# Feature Specification: Strict entry-point type repairs

**Feature Branch**: `jmorrison-juniper-strict-pyright-repairs`

**Created**: 2026-11-17

**Status**: Specified

**Input**: Resolve issue #4758 methodically from current main. Preserve behavior and record unrelated defects separately.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trust entry-point diagnostics (Priority: P1)

A contributor can examine the entry point without unresolved strict diagnostics.

**Why this priority**: Unknown contracts can conceal incorrect calls.

**Independent Test**: Analyze the entry point with the recorded strict settings and require one analyzed file with zero errors.

**Acceptance Scenarios**:

1. **Given** current main, **When** the contributor records the baseline, **Then** the report identifies every existing diagnostic.
2. **Given** the repaired entry point, **When** the same analysis runs, **Then** the report contains zero errors without disabled rules.

### User Story 2 - Preserve operator behavior (Priority: P1)

An operator retains the existing commands, menu operations, session state, and optional dependency behavior.

**Why this priority**: Type repairs must not change network operations.

**Independent Test**: Run focused mocked regression tests and compare the entry-point symbols.

**Acceptance Scenarios**:

1. **Given** an absent optional package, **When** the module loads, **Then** the existing availability behavior remains unchanged.
2. **Given** dynamic dispatch and context state, **When** a mocked command runs, **Then** it selects the existing callable and state.

### Edge Cases

- Package metadata can be absent or invalid.
- The authenticated session can be absent before startup.
- Dynamic module attributes must reject unknown names.
- External packages can lack type declarations.
- Another feature can reserve a required consumer file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Record the live main revision and strict baseline before source edits.
- **FR-002**: Resolve all entry-point strict diagnostics with accurate contracts.
- **FR-003**: Preserve runtime behavior, live callable implementations, explicit exports, optional dependencies, and dynamic dispatch. Remove private declarations only after caller verification.
- **FR-004**: Do not suppress diagnostics, weaken tests, add dummy references, or erase live declarations.
- **FR-005**: Keep imported consumers consistent and obtain reserved-file handoffs before edits.
- **FR-006**: Use mocked tests without production requests or destructive operations.
- **FR-007**: Record unrelated defects separately and defer their repairs.
- **FR-008**: Commit verified local work without publication or merge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The entry-point diagnostic report contains zero unresolved errors.
- **SC-002**: Every focused behavior regression passes.
- **SC-003**: No live callable implementation disappears. Verify host-helper renames and private-code removals against their callers. Preserve existing explicit exports.
- **SC-004**: Every completed task has recorded evidence.

## Assumptions

- Scope covers the entry point and required supporting contracts, not repository-wide strict adoption.
- Existing ownership and publication holds remain active.
- The app-managed branch replaces the branch-creation hook.
- The active feature path remains command-scoped. The shared selector remains unchanged.
- Review requires public names for verified host helpers and direct typed mode dispatch. It does not permit dummy exports or compatibility aliases.
- The bounded cleanup includes unused private declarations and obsolete test doubles. Tests must exercise real parser, validation, and dependency initialization behavior.
