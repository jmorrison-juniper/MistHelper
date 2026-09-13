# Feature Specification: Compliance/Decomposition Wave 1 (Safety Refactor, No Behavior Change)

**Feature Branch**: `192-compliance-decomposition-wave1`
**Created**: 2026-05-15
**Status**: Draft
**Input**: User description: "Create a new feature specification for MistHelper compliance/decomposition wave 1..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Safe Input Hardening for Production Paths (Priority: P1)

A junior NOC engineer runs MistHelper through interactive terminal and SSH/container sessions. All production user prompts in wave-1 scope must use EOF-safe input handling so sessions terminate cleanly and do not crash on disconnected input streams.

**Why this priority**: Input handling is a safety-critical control. Replacing raw production `input()` calls with `InputUtils.safe_input(..., context=...)` reduces operator-facing failures and enforces a single defensive input pattern.

**Independent Test**: Can be fully tested by running the application entry paths and targeted operation prompts to verify prompts still appear, accepted values route correctly, and EOF handling exits gracefully without behavior drift in normal usage.

**Acceptance Scenarios**:

1. **Given** a production prompt within wave-1 scope, **When** a user enters valid input, **Then** behavior matches baseline routing and operation flow exactly.
2. **Given** a production prompt within wave-1 scope, **When** EOF is encountered, **Then** the program follows the defined safe-input handling path and exits cleanly without unhandled exceptions.

---

### User Story 2 - Preserve Operation Safety Controls (Priority: P1)

A NOC engineer relies on MistHelper safety boundaries between non-destructive and destructive operations. During wave-1 refactor, entry routing and safety classification must remain unchanged and verifiable.

**Why this priority**: Safety classification drift could expose destructive operations through incorrect routing. Preventing this regression is mandatory for production trust.

**Independent Test**: Can be tested with guardrail tests that validate route-to-operation mapping and destructive/non-destructive classification logic for representative operation IDs.

**Acceptance Scenarios**:

1. **Given** a menu selection that maps to a non-destructive operation, **When** routing logic is evaluated, **Then** it resolves to the same operation handler as baseline.
2. **Given** a menu selection that maps to a destructive operation, **When** classification logic is evaluated, **Then** the operation remains classified as destructive and continues to require explicit safety flow.

---

### User Story 3 - Add Targeted Action Logging in Highest-Risk Touched Functions (Priority: P2)

An operator troubleshooting production behavior needs clear before/after logs around key actions in the highest-risk functions touched during wave 1.

**Why this priority**: Targeted observability improves incident triage without requiring a full-script log sweep in this phase.

**Independent Test**: Can be tested by executing touched high-risk paths and verifying expected before/after log envelopes are emitted around selected actions.

**Acceptance Scenarios**:

1. **Given** a high-risk function in wave-1 scope, **When** a meaningful action starts, **Then** a pre-action log entry is emitted.
2. **Given** the same action completes, **When** control returns from the action, **Then** a post-action summary log entry is emitted.

---

### User Story 4 - Tranche-Based Quality Gates (Priority: P2)

A maintainer applies wave-1 changes in small tranches and must run repository-standard quality gates between tranches to catch regressions early.

**Why this priority**: Incremental validation lowers integration risk in a large single-file codebase.

**Independent Test**: Can be tested by executing the required gate commands after each tranche and confirming successful completion before continuing.

**Acceptance Scenarios**:

1. **Given** tranche changes are applied, **When** compile/lint/type/test gates are run, **Then** all gates pass before the next tranche begins.
2. **Given** a gate fails, **When** validation is performed, **Then** tranche progression stops until the failure is resolved.

### Edge Cases

- A production prompt is reached in a non-interactive session where EOF occurs immediately.
- A routed operation is near safety boundaries (destructive range and adjacent non-destructive IDs) and must retain correct classification.
- Logging additions touch high-risk functions with multiple return paths; envelopes must still bracket meaningful actions.
- A tranche passes compile and lint but fails type or tests; progression must halt until fixed.
- Internal/developer-only paths not classified as production prompts should not be force-changed in wave 1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wave 1 MUST replace production-scope raw `input()` usage with `InputUtils.safe_input(..., context=...)` in touched paths without changing user-visible behavior.
- **FR-002**: Wave 1 MUST preserve existing entry routing outcomes for in-scope operations.
- **FR-003**: Wave 1 MUST preserve existing operation safety classification outcomes for in-scope operations.
- **FR-004**: Wave 1 MUST add targeted pre-action and post-action logging envelopes in highest-risk touched functions only.
- **FR-005**: Logging additions MUST avoid exposing secrets or sensitive values.
- **FR-006**: Wave 1 MUST include guardrail tests for entry routing invariants.
- **FR-007**: Wave 1 MUST include guardrail tests for operation safety classification invariants.
- **FR-008**: Wave 1 MUST execute compile, lint, type-check, and test gates between implementation tranches.
- **FR-009**: Wave 1 MUST keep behavior unchanged for successful user flows in touched paths.
- **FR-010**: Wave 1 MUST explicitly exclude full packet-capture decomposition.
- **FR-011**: Wave 1 MUST explicitly exclude a full-script global comment/log sweep.
- **FR-012**: Wave 1 MUST document verification commands aligned with repository standards.
- **FR-013**: Wave 1 MAY scope logging envelope expansion to selected high-risk touched functions, but every AI-touched executable line in modified blocks MUST still satisfy project comment/logging standards.

### Verification Commands (Repository Standard)

The feature is verified tranche-by-tranche using the standard command sequence below:

1. `python -m py_compile MistHelper.py`
2. `python -m ruff check MistHelper.py src tests`
3. `python -m black --check MistHelper.py src tests`
4. `python -m mypy src --config-file pyproject.toml`
5. `python -m pytest --cov=src --cov=tests --cov-report=term-missing`
6. `python MistHelper.py --test`

### Key Entities

- **Production Prompt Path**: A user-input path used during normal MistHelper operation that must use EOF-safe input handling.
- **Entry Routing Guardrail**: Expected mapping from menu/entry selection to operation handler.
- **Safety Classification Guardrail**: Expected destructive vs non-destructive classification for operations.
- **High-Risk Touched Function**: A function modified in wave 1 where action-level before/after logging envelopes are required.
- **Tranche Validation Record**: Evidence that compile/lint/type/test gates passed before progressing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of wave-1 production prompt paths touched by the refactor use safe input handling with context labels.
- **SC-002**: 0 confirmed behavior regressions are introduced in guardrail-tested entry routing and safety classification paths.
- **SC-003**: 100% of required tranche gate runs (compile, lint, type, test) complete successfully before subsequent tranche work proceeds.
- **SC-004**: 100% of selected high-risk touched functions emit both pre-action and post-action logging envelopes for meaningful actions.
- **SC-005**: At least one guardrail test suite run demonstrates stable operation safety boundaries across representative non-destructive and destructive operation IDs.

## Scope Boundaries

### In Scope

- Production-path raw `input()` replacement with `InputUtils.safe_input(..., context=...)` in wave-1 touched areas
- Targeted action logging envelopes in highest-risk touched functions
- Guardrail tests for entry routing and operation safety classification
- Tranche-based compile/lint/type/test validation
- No behavior change objective for touched production paths

### Out of Scope

- Full packet-capture decomposition
- Full-script global comment/log sweep
- Broad architecture decomposition outside wave-1 safety/compliance tranche
- Feature expansion or behavior redesign unrelated to safety/compliance hardening

## Assumptions

- `InputUtils.safe_input` already exists and is available for use in MistHelper production paths.
- Existing destructive operation boundaries and routing expectations are already defined in current behavior and can be asserted in tests.
- Wave 1 is implemented incrementally in tranches to control risk.
- Repository quality gates are authoritative for readiness between tranches.
- This phase prioritizes safety/compliance hardening over broad structural decomposition.
