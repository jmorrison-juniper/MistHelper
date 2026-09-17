# Feature Specification: Unattended Interactive-Safe Test Run

**Feature Branch**: `feat/1785-testinteractive`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #1785, "`--testinteractive` cannot run unattended, so 67 operations have no automated coverage".

## User Scenarios & Testing

### User Story 1 - Run interactive-safe tests unattended (Priority: P1)

A maintainer runs `--testinteractive` in an unattended shell. The runner supplies deterministic answers to prompts.

**Why this priority**: CI cannot type answers. The suite must never wait for a human.

**Independent Test**: Run a unit test that patches `InputUtils.safe_input` and proves the handler receives a generated answer.

**Acceptance Scenarios**:

1. **Given** an interactive-safe handler asks for a device index, **When** the runner invokes it, **Then** it receives `0`.
2. **Given** an interactive-safe handler asks for a zone type, **When** the runner invokes it, **Then** it receives `zones`.

---

### User Story 2 - Refuse unsafe operations (Priority: P1)

The runner refuses any operation that is not classified as `interactive_safe`.

**Why this priority**: An unattended run must never reach a destructive operation.

**Independent Test**: Use a registry test double that exposes menu `154` as a candidate. Assert the handler is not called.

**Acceptance Scenarios**:

1. **Given** a destructive menu number appears in the candidate list, **When** the runner validates the list, **Then** it fails closed.
2. **Given** zero operations appear in the candidate list, **When** the runner starts, **Then** it returns failure.

---

### User Story 3 - Report real measurement (Priority: P2)

The runner reports how many operations it exercised and why each skipped operation did not run.

**Why this priority**: A green result that measures nothing hides defects.

**Independent Test**: Run unit tests that assert non-empty skip reasons and zero-count failure.

**Acceptance Scenarios**:

1. **Given** a safe operation is skipped by `--testinteractive`, **When** the runner prints skips, **Then** the reason names `--test`.
2. **Given** a prompt has no safe answer rule, **When** the handler asks it, **Then** the runner reports a prompt harness failure.

### Edge Cases

- If no API token exists, the normal credential path still prevents live Mist API calls.
- If a prompt has a default value, the input provider uses that value first.
- If a required prompt has no safe rule, the input provider raises a prompt error instead of waiting.
- If the registry changes, the runner validates the final candidate list before it calls a handler.

## Requirements

### Functional Requirements

- **FR-001**: The runner MUST install an input provider only while one menu option runs.
- **FR-002**: The input provider MUST restore `InputUtils.safe_input` after each option.
- **FR-003**: The runner MUST refuse any candidate whose category is not `interactive_safe`.
- **FR-004**: The runner MUST fail when it would exercise zero operations.
- **FR-005**: The summary MUST report exercised operations and prompt harness failures.
- **FR-006**: Each skipped operation MUST have a non-empty reason.
- **FR-007**: EOF-safe input behavior MUST remain the default outside the test invocation.

### Key Entities

- **Unattended input provider**: Generates safe answers from prompt text and context.
- **Interactive test runner**: Validates candidates, runs operations, and reports measurement.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The focused interactive runner unit test file passes.
- **SC-002**: A destructive candidate test proves menu `154` is not called.
- **SC-003**: A zero-candidate test returns failure.
- **SC-004**: The summary contains an exercised-operation count.

## Assumptions

- The current registry has 92 `interactive_safe` entries. Issue #1785 named 67 before later menu additions.
- Generated prompt answers are safer than answer files because they use the existing `InputUtils.safe_input` seam.
- Prompts without a safe generated answer must fail as harness defects, not as silent skips.
