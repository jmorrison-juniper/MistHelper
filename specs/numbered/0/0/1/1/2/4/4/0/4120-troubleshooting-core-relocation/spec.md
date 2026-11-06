# Feature Specification: Cohesive troubleshooting modules

**Feature Branch**: `jmorrison-juniper-troubleshooting-core-relocation`

**Created**: 2026-11-06

**Status**: Specified

**Input**: Implement issue #4120. Find a compliant destination without a sixth execution child.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find code by subject (Priority: P1)

A contributor finds the menu test runner with test support code and Marvis troubleshooting code with Marvis code.

**Why this priority**: The current `core` package combines unrelated subjects.

**Independent Test**: Import each canonical module and compare its declarations with the current base.

**Acceptance Scenarios**:

1. **Given** a contributor needs menu test support, **When** they inspect support packages, **Then** they find the runner.
2. **Given** a contributor needs Marvis troubleshooting, **When** they inspect Marvis packages, **Then** they find both modules.

### User Story 2 - Preserve operator behavior (Priority: P1)

An operator uses the same menus, safeguards, exports, and test sweep after the relocation.

**Why this priority**: A source move must not change operations.

**Independent Test**: Run the existing runner and troubleshooting tests with mocked external responses.

**Acceptance Scenarios**:

1. **Given** an existing caller, **When** it resolves a moved dependency, **Then** it receives the canonical class.
2. **Given** an obsolete import, **When** it runs, **Then** it fails without a compatibility module.

### Edge Cases

- An unbound dependency resolver must resolve the moved source classes without a root CLI import.
- A missing declaration must fail symbol preservation checks.
- Historical inventory paths remain historical evidence, not active import paths.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Move the runner to `src/foundation/support/menu_testing/interactive_test_runner.py`.
- **FR-002**: Move both Marvis modules to `src/mist/intelligence/marvis/troubleshooting/`.
- **FR-003**: Remove the former `core` package without shims.
- **FR-004**: Update active imports, resolver entries, fixtures, tests, hook records, and generated references.
- **FR-005**: Preserve every module-level declaration and all operation behavior.
- **FR-006**: Add no package violation and increase no existing package excess.
- **FR-007**: Preserve the historical inventory under the #4117 contract.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three modules have subject-specific destinations and zero obsolete import modules.
- **SC-002**: All existing declarations remain present.
- **SC-003**: The package guard reports no new violation and no increased excess.
- **SC-004**: All affected operator behavior tests pass without production credentials.

## Assumptions

- Current base is `fb7a7d10d`. Issues #4117 and #4118 are closed.
- The execution package now has five children. The issue's four-child measurement is stale.
- Foundation support has two children. Menu test support is a cohesive third child.
- Marvis has two children. Troubleshooting becomes its third child.
- Operation behavior remains unchanged. Narrow annotations satisfy strict checks outside the former package's relaxed typing configuration.
- Logger names and class `__module__` values change to the canonical destination module names.
- Consumers of serialized class identities or source logger filters must use the destination names.
- Historical records retain their historical paths. Active records use canonical paths.
