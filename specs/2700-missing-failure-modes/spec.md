# Feature Specification: Missing failure mode triage

**Feature Branch**: `2700-missing-failure-modes`

**Created**: 2026-09-16

**Status**: Implemented

**Input**: Issues #2700, #2701, #2702, #2703, #2704, and #2705 require one pull request for related `missing_fm_*` rules.

## User Scenarios & Testing

### User Story 1 - Measure real failure-mode scope (Priority: P1)

A maintainer needs the analyzer to inspect tests that exercise source code with Mist, HTTP, or JSON response risk. The analyzer must not inspect unrelated tests only because they mention `status_code`.

**Why this priority**: A zero or false scope hides real network failure risk.

**Independent Test**: Run the analyzer and verify that `MissingFailureModeDetector.inspected_modules` is greater than zero.

**Acceptance Scenarios**:

1. **Given** a test imports a value object that stores `status_code`, **When** the detector runs, **Then** it reports no `missing_fm_*` finding.
2. **Given** a test imports a Mist SDK backed service, **When** the detector runs, **Then** it counts that module as inspected.

---

### User Story 2 - Repair the highest-risk gap (Priority: P2)

An operator needs `MistEndpointService` tests to prove that network and body failure modes reach the caller or the log.

**Why this priority**: The service calls Mist through the SDK, so hidden failure paths can return false success.

**Independent Test**: Run `mist-ops-platform\tests\unit\mist\test_endpoint_retry.py` and verify the new failure-mode assertions.

**Acceptance Scenarios**:

1. **Given** the SDK raises a timeout, **When** `read_entity` calls it, **Then** the timeout reaches the caller.
2. **Given** the SDK raises a connection error, **When** `read_entity` calls it, **Then** the connection error reaches the caller.
3. **Given** the SDK returns 500, **When** `read_entity` calls it, **Then** the 500 reaches the caller without a retry.
4. **Given** the SDK returns an empty body, **When** `read_entity` wraps it, **Then** the log reports the empty body.
5. **Given** the SDK raises a JSON parse error, **When** `read_entity` calls it, **Then** the parse error reaches the caller.

---

### User Story 3 - Record the triage and the cut (Priority: P3)

A later engineer needs to know which rule groups remain and why this pull request stops after the first high-risk repair.

**Why this priority**: Six rule groups hold too many findings for one safe pull request.

**Independent Test**: Read `specs\2700-missing-failure-modes\triage.md` and compare it with the analyzer report.

**Acceptance Scenarios**:

1. **Given** the pull request leaves findings, **When** the maintainer reads the triage, **Then** each rule has a reason and a follow-up issue.

## Edge Cases

- If a detector inspects zero real modules, the analyzer returns an error and `tools.guard_proof_audit` fails.
- If a test imports a large module only to read constants, the detector must not treat the whole module as a network source.
- If a source class calls Mist through dynamic import strings, the detector must still infer Mist API scope.

## Requirements

### Functional Requirements

- **FR-001**: The analyzer MUST infer failure-mode applicability from source code under test.
- **FR-002**: The analyzer MUST not require a hand-added opt-in marker.
- **FR-003**: The analyzer MUST report `MissingFailureModeDetector.inspected_modules`.
- **FR-004**: The analyzer MUST return an error when a real repository run inspects zero modules for a scoped detector.
- **FR-005**: The tests MUST prove that a `status_code` value object is outside the failure-mode rule.
- **FR-006**: The tests MUST prove that `MistEndpointService` exposes timeout, connection, 5xx, JSON parse, and empty-body behavior.
- **FR-007**: The pull request MUST defer the remaining findings to one follow-up issue per rule.

### Key Entities

- **FailureModeRisk**: The inferred source risk for network and JSON body failures.
- **FailureModeCoverage**: The failure modes that a test module already exercises.
- **Detector Metric**: The inspected module count that proves the detector measured real scope.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `python -m tools.test_quality_analyzer` prints `MissingFailureModeDetector.inspected_modules=117` or higher on the repaired tree.
- **SC-002**: `test_api_result.py` produces zero `missing_fm_*` findings.
- **SC-003**: `test_endpoint_retry.py` produces zero `missing_fm_*` findings.
- **SC-004**: `tools.guard_proof_audit` reports no new guard proof failures.

## Assumptions

- The six issue counts from 2026-09-15 are the original counts for comparison.
- The current main branch is the source of truth for re-measurement.
- The first pull request must stay below 20 changed files.
- Remaining valid findings will stay open through follow-up issues.
