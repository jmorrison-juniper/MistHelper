# Feature Specification: Edge-Case Detector Scope

**Feature Branch**: `fix/2736-edge-case-scope`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2736 reports that `missing_edge_case` inspects no real
test modules after pull request #2734 added a required opt-in marker.

## User Scenarios & Testing

### User Story 1 - Infer Edge-Case Applicability (Priority: P1)

The test quality analyzer must decide when an edge-case rule applies without a
manual opt-in marker.

**Why this priority**: The current marker makes the rule measure only fixtures,
so the guard can pass while it measures nothing.

**Independent Test**: Run the analyzer on the repository. The report must show a
positive `MissingEdgeCaseDetector.inspected_modules` count.

**Acceptance Scenarios**:

1. **Given** a source-under-test parameter with a numeric annotation, **When**
   tests omit zero and negative calls, **Then** the analyzer reports the numeric
   edge-case findings.
2. **Given** a source-under-test parameter named `items`, **When** tests omit an
   empty container call, **Then** the analyzer reports the empty-input finding.
3. **Given** a source-under-test parameter with `None` in its annotation, **When**
   tests omit a `None` call, **Then** the analyzer reports the None-input finding.

---

### User Story 2 - Keep Pull Request 2734 Noise Reductions (Priority: P2)

The detector must keep the helper-call and status-code exclusions from pull
request #2734.

**Why this priority**: The exclusions removed real noise and made the rule safer.

**Independent Test**: Run the detector unit tests that cover support calls and
HTTP status-code parameters.

**Acceptance Scenarios**:

1. **Given** an assertion helper or mock helper call, **When** the detector scans
   the test module, **Then** it emits no edge-case finding for that helper.
2. **Given** a `status_code` integer parameter, **When** the detector scans the
   test module, **Then** it does not require zero or negative status-code tests.

---

### User Story 3 - Reject Empty Detector Scope (Priority: P3)

The guard proof audit must fail when an analyzer rule reports zero real files
inspected.

**Why this priority**: Issue #2654 requires a guard to prove that it measured its
input.

**Independent Test**: Run the guardrail negative test with a synthetic analyzer
report that states `MissingEdgeCaseDetector.inspected_modules` is zero.

**Acceptance Scenarios**:

1. **Given** an analyzer report with a zero inspected-module metric, **When** the
   guard proof audit reads it, **Then** the audit blocks the merge.
2. **Given** an analyzer report with a positive inspected-module metric, **When**
   the guard proof audit reads it, **Then** the audit reports no new failure.

### Edge Cases

- If the analyzer cannot infer a source-under-test parameter domain, the detector
  must not emit a finding for that call.
- If the analyzer report lacks detector metrics, the guard proof audit must fail.
- If the analyzer report cannot be read, the guard proof audit must fail.
- If a parameter is `status` or `status_code`, the detector must treat it as a
  categorical code.

## Requirements

### Functional Requirements

- **FR-001**: The detector MUST infer numeric applicability from type
  annotations, numeric default values, or numeric parameter names.
- **FR-002**: The detector MUST infer collection applicability from collection
  annotations, collection default values, or collection parameter names.
- **FR-003**: The detector MUST infer optional applicability from `None`
  annotations, `Optional` annotations, `None` defaults, or optional parameter names.
- **FR-004**: The detector MUST keep the support-call exclusions from pull
  request #2734.
- **FR-005**: The detector MUST keep the `status` and `status_code` exclusion
  from pull request #2734.
- **FR-006**: The analyzer report MUST include the number of modules inspected by
  `MissingEdgeCaseDetector`.
- **FR-007**: A real repository analyzer run MUST fail when
  `MissingEdgeCaseDetector` inspects zero modules.
- **FR-008**: The guard proof audit MUST fail when a detector metric reports zero
  inspected real files.
- **FR-009**: The guard proof audit MUST include a negative test for the zero
  detector scope.

### Key Entities

- **EdgeCaseDomain**: The inferred obligations for one source-under-test
  parameter.
- **SourceSignature**: The domain map for one callable source-under-test object.
- **EdgeCaseCoverage**: The observed and required edge-case coverage for one test
  module.
- **Detector metrics**: The report fields that prove detector scope was measured.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The analyzer reports more than zero inspected modules for
  `MissingEdgeCaseDetector` on the repository test suite.
- **SC-002**: The re-measured missing-edge-case finding total is more than zero
  and less than 583.
- **SC-003**: `python -m tools.guard_proof_audit` fails on a synthetic zero-scope
  analyzer report.
- **SC-004**: `git grep -rn "edge-case-required" -- src tests` reports no match.

## Assumptions

- Source files remain available in the same repository checkout as the tests.
- The detector can skip dynamic calls when no source signature can be read.
- The analyzer fixture roots can keep independent test behavior without real
  repository-scope enforcement.
