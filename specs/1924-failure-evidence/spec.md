# Feature Specification: Failure Evidence Erasure Audit

**Feature Branch**: `chore/1924-failure-evidence`

**Created**: 2026-09-16

**Status**: Ready for Review

**Input**: GitHub issue #1924 requested a measured audit of failure paths that erase their own evidence.

## User Scenarios and Testing

### User Story 1 - Measure the pattern (Priority: P1)

A maintainer needs an inventory that separates real guard coverage from empty success.

**Why this priority**: The repository cannot plan repairs until it knows the count and the file set.

**Independent Test**: Read `inventory.md` and verify each required category has a method, a count, and a file set.

**Acceptance Scenarios**:

1. **Given** issue #1924, **When** the audit runs, **Then** it reports all five categories.
2. **Given** a later repair issue, **When** a maintainer opens the artifact, **Then** the artifact shows the target files.

---

### User Story 2 - Repair the highest-risk default (Priority: P1)

A maintainer needs package manifests that do not install an unverified major release.

**Why this priority**: A Mist SDK release broke all pull requests after an unbounded range accepted it.

**Independent Test**: Run `python -m tools.guard_proof_audit` and verify it checks dependency entries.

**Acceptance Scenarios**:

1. **Given** runtime dependencies, **When** the guard reads the manifests, **Then** each dependency has an upper bound.
2. **Given** a planted unbounded dependency, **When** the guard runs in a unit test, **Then** the guard fails.

---

### User Story 3 - Defer the rest safely (Priority: P2)

A maintainer needs follow-up issues for work that this audit does not repair.

**Why this priority**: The audit must not become a large sweep that hides a new defect.

**Independent Test**: Open issues #2750, #2751, #2752, and #2753.

**Acceptance Scenarios**:

1. **Given** remaining category findings, **When** this pull request merges, **Then** each category has a follow-up issue.

### Edge Cases

- If `MistHelper.py` contains a finding, record it and do not edit it.
- If a guard reads zero records, fail the guard and print the inspected count.
- If a dependency line cannot parse, fail the dependency guard.

## Requirements

### Functional Requirements

- **FR-001**: The audit MUST report a count for each of the five issue #1924 categories.
- **FR-002**: The audit MUST include a file list for each category that still has candidate records.
- **FR-003**: The repair MUST avoid `MistHelper.py`.
- **FR-004**: The repair MUST cap the change to a small file set.
- **FR-005**: The guard MUST fail when it inspects zero dependency entries.
- **FR-006**: The guard MUST fail when a runtime dependency has no upper bound.
- **FR-007**: The pull request MUST name deferred follow-up issues.

### Key Entities

- **Audit Category**: One pattern that can report success while it measures nothing.
- **Finding**: A candidate file and line that a later issue can review.
- **Dependency Decision**: A package specifier that must include a verified ceiling.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The inventory includes all five required categories.
- **SC-002**: `tools.guard_proof_audit` reports a nonzero dependency count.
- **SC-003**: A unit test proves a planted unbounded dependency fails the guard.
- **SC-004**: One follow-up issue exists for each unrepaired category.

## Confirmed Instances

- Issue #2717: broad handlers swallowed missing Mist SDK function failures.
- Issue #2689: the SDK compatibility guard skipped all seven tests.
- Issue #2736: analyzer rules inspected zero real modules.
- Issue #2632: browser tests passed before they reached the upgrade start path.

## Inventory Summary

| Category | Count | Method |
| - | -: | - |
| Broad handler that swallows | 412 | Issue #1794 baseline plus a current AST sample scan |
| Guard that cannot fail | 0 active | `tools.guard_proof_audit` checked 36 guard files and 1 analyzer rule |
| Success report that outruns work | 582 candidates | AST scan for success-word log calls |
| Retry or fallback that hides first failure | 835 candidates | AST scan for try blocks with retry or fallback language |
| Default that masks missing input | 3860 candidates | AST scan for code defaults after manifest repair |

Full details are in `inventory.md` and `inventory.json`.

## Repair and Deferral

This branch repairs dependency manifest defaults and adds a guard for that pattern.
It does not edit `MistHelper.py`.
It defers broad handlers to #2750, success reports to #2751, retries to #2752, and code defaults to #2753.
