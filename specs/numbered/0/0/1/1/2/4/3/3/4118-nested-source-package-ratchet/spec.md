# Feature Specification: Nested Source Package Ratchet

**Feature Branch**: `jmorrison-juniper-assess-4118`

**Created**: 2026-10-07

**Status**: Draft

**Input**: Issue #4118: add a nested source package ratchet guard for issue #3824.

## User Stories

### User Story 1 - Measure nested Python packages

As a maintainer, I need one repeatable measurement for nested source packages.

**Independent Test**: Run the guard on tracked `src/**/*.py` paths and compare its counts with the baseline.

### User Story 2 - Prevent structural regression

As a maintainer, I need CI to reject a new sixth structural child.

**Independent Test**: Add a synthetic sixth child and verify that the guard fails with the path and count.

### User Story 3 - Preserve bounded remediation

As a maintainer, I need each violation to name a remediation issue.

**Independent Test**: Remove, corrupt, or duplicate a baseline issue entry and verify that the guard fails.

## Requirements

- **FR-001**: The guard MUST read tracked Python paths with `git ls-files`.
- **FR-002**: The guard MUST build directory prefixes from those paths.
- **FR-003**: The guard MUST exclude `src` from the measured directory count.
- **FR-004**: The guard MUST count direct Python modules except `__init__.py`.
- **FR-005**: The guard MUST count immediate child directories with Python descendants.
- **FR-006**: The guard MUST not use `__init__.py` to discover the directory set.
- **FR-007**: The baseline MUST record each active path, child count, and remediation issue.
- **FR-008**: The remediation issue MUST be a positive integer.
- **FR-009**: The guard MUST reject an unknown violation.
- **FR-010**: The guard MUST reject an increased grandfathered count.
- **FR-011**: The guard MUST reject an increased total excess.
- **FR-012**: The guard MUST reject a stale entry when a path reaches five children.
- **FR-013**: The guard MUST fail when the baseline is missing or malformed.
- **FR-014**: The guard MUST report directories examined, violations, and total excess.
- **FR-015**: The baseline MUST preserve 170 directories, 36 violations, and 243 total excess on the measured main commit eee43c248. The Decisions section records the accepted Juniper RMA debt.
- **FR-016**: The implementation MUST not edit `.github/copilot-instructions.md` while PR #4124 owns that file.

## Data Contract

The baseline is a JSON object with version `1`, source root `src`, maximum child count `5`, and a sorted `violations` list.
Each violation has `path`, `child_count`, and `remediation_issue`.

## Decisions

- **2026-10-10**: The Juniper RMA packages and the export increase are accepted debt. Issue #4168 tracks the RMA packages, and issue #3824 tracks export. Any further increase needs a new decision and a baseline update.

## Out of Scope

- Moving source modules.
- Rewriting either performance catalog.
- Network validation of GitHub issue existence.
- Changes to `.github/copilot-instructions.md`.
