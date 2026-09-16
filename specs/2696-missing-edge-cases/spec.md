# Feature Specification: Missing Edge Case Triage

**Feature Branch**: `chore/2696-missing-edge-cases`

**Created**: 2026-09-16

**Status**: Implemented

**Input**: User description: "Triage issues #2696 through #2699 together in one pull request. Re-measure the analyzer counts. Repair the highest-risk subset and defer the remainder with evidence."

## User Scenarios & Testing

### User Story 1 - Report only meaningful edge-case gaps (Priority: P1)

A maintainer runs `python -m tools.test_quality_analyzer` and sees only missing edge-case findings that have an explicit input-domain marker.

**Why this priority**: The old rule inferred input domains from incidental literals. It reported impossible edge cases for HTTP statuses, mock calls, and fixture builders.

**Independent Test**: Run `python -m tools.test_quality_analyzer` and confirm the four issue rules report zero unmarked findings.

**Acceptance Scenarios**:

1. **Given** a test file has no edge-case marker, **When** the analyzer scans it, **Then** it emits no `missing_ec_*` finding.
2. **Given** a test file uses mock assertions or response helpers, **When** it has a numeric marker, **Then** the analyzer ignores those support calls.
3. **Given** a test file has a collection marker and only a non-empty list input, **When** the analyzer scans it, **Then** it reports `missing_ec_empty_input`.

### User Story 2 - Preserve valid opt-in coverage checks (Priority: P2)

A future maintainer can mark a test file with an input domain when a missing edge case is meaningful.

**Why this priority**: The repair must narrow false positives without deleting the rule family.

**Independent Test**: Run the detector fixture tests and confirm the bad numeric fixture still reports missing zero and negative cases.

**Acceptance Scenarios**:

1. **Given** a fixture has `test-quality: edge-case-required=numeric`, **When** it tests only a positive integer, **Then** the analyzer reports zero and negative gaps.
2. **Given** the same fixture adds zero and negative tests, **When** the analyzer scans it, **Then** it reports no gap.

### Edge Cases

- If a marker names an unknown domain, ignore that domain.
- If a marker requests `collection`, do not require numeric cases.
- If a marker requests `numeric`, do not require collection cases.
- If a call target is a mock helper, a fixture factory, or an HTTP response helper, do not treat it as the source under test.

## Requirements

### Functional Requirements

- **FR-001**: The analyzer MUST require an explicit `test-quality: edge-case-required=` marker before it emits a `missing_ec_*` finding.
- **FR-002**: The analyzer MUST support the `numeric`, `collection`, and `none` marker domains.
- **FR-003**: The analyzer MUST ignore test support calls when it builds the edge-case coverage profile.
- **FR-004**: The analyzer MUST keep valid opt-in findings for numeric and collection gaps.
- **FR-005**: The analyzer MUST leave the committed baseline unchanged unless the pull request intentionally records baseline entries.

### Key Entities

- **Edge-case marker**: A comment or docstring token that declares the input domain where missing edge cases are meaningful.
- **Coverage profile**: The per-file evidence that a marked test file exercises numeric, collection, or `None` inputs.
- **Support call**: A pytest, mock, factory, or helper call that must not create an edge-case obligation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Re-measurement before repair reports 76 `missing_ec_empty_input`, 214 `missing_ec_negative_value`, 135 `missing_ec_none_input`, and 158 `missing_ec_zero_value` findings.
- **SC-002**: Re-measurement after repair reports zero findings for all four rules.
- **SC-003**: `tests\tools\test_quality_analyzer\test_meta_fixtures.py` passes.
- **SC-004**: `python -m tools.guard_proof_audit` passes.

## Assumptions

- The four issue groups share one false-positive cause in `MissingEdgeCaseDetector`.
- The highest-risk repair is the analyzer rule, not a broad test sweep.
- No baseline entry changes are necessary for this pull request.
