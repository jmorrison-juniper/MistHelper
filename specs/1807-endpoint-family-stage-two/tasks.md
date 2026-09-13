# Tasks: Endpoint family stage two

## Phase 1: Discovery

- [x] Read issue #1807.
- [x] Scan the installed `mistapi` package for endpoint functions.
- [x] Classify endpoint signatures by required identifier tuple.
- [x] Identify unresolved and active endpoints.

## Phase 2: Implementation

- [x] Add `EndpointFamilyExporter` with six operation tables.
- [x] Add menu entries 263 through 268.
- [x] Register the six menus as `interactive_safe`.
- [x] Add primary-key strategies for shipped table entries.

## Phase 3: Tests

- [x] Add table integrity tests.
- [x] Add prompt error-path tests.
- [x] Add SDK call-shape tests for each table entry.
- [x] Add primary-key strategy coverage tests.

## Phase 4: Documentation

- [x] Update README, the changelog, and menu documents.
- [x] Regenerate the generated menu references.

## Phase 5: Validation

- [x] Compile changed Python files.
- [x] Run ruff, black, mypy, and targeted pytest.
- [x] Run the STE linter on changed prose.
