# Feature Specification: Performance monitoring modules

**Feature Branch**: `2533-perf-monitoring`

**Created**: 2026-09-15

**Status**: Draft

**Input**: GitHub issue #2533 asks for opt-in performance monitoring modules.

## User Scenarios & Testing

### User Story 1 - Keep monitoring off by default (Priority: P1)

A NOC engineer runs MistHelper with no performance setting. MistHelper records no performance event.

**Why this priority**: The safe default prevents latency cost and unwanted files.

**Independent Test**: Create the default recorder, run a span, and assert that the sink stays empty.

**Acceptance Scenarios**:

1. **Given** no performance setting, **When** code opens a span, **Then** the recorder emits no event.
2. **Given** the off level, **When** code asks for a resource family, **Then** the recorder returns a null span.

---

### User Story 2 - Measure one selected boundary (Priority: P1)

A developer enables a level for a cataloged boundary. The span records wall time and process CPU time.

**Why this priority**: A useful monitoring base needs measured duration values.

**Independent Test**: Enable the base level, run an operation span, and inspect the JSON Lines output.

**Acceptance Scenarios**:

1. **Given** the base level, **When** an operation span exits, **Then** the event has wall nanoseconds and CPU nanoseconds.
2. **Given** a forbidden family, **When** code asks for a span, **Then** no clock is read.

---

### User Story 3 - Store only safe records (Priority: P1)

A record contains an adversarial label. The sink stores a JSON Lines record without private data.

**Why this priority**: MistHelper handles API tokens, MAC addresses, and tenant identifiers.

**Independent Test**: Feed each forbidden value type to the recorder and read the stored line.

**Acceptance Scenarios**:

1. **Given** a label that contains a token, **When** the sink flushes, **Then** the file contains no token value.
2. **Given** a label that contains a MAC address, **When** the sink flushes, **Then** the file contains no MAC address.
3. **Given** a label that contains SQL text, **When** the sink flushes, **Then** the file contains no SQL text.

### Edge Cases

- If the sink path rejects a write, the sink counts the failure and the caller result does not change.
- If repeated writes fail, the sink opens its circuit and skips later writes.
- If a label key is not in the allowlist, the privacy policy drops it.
- If a count becomes a label, the privacy policy stores only a fixed bucket.

## Requirements

### Functional Requirements

- **FR-001**: The package MUST import from `src.utils.performance`.
- **FR-002**: The default recorder MUST emit no event.
- **FR-003**: A level MUST select the event families that can emit.
- **FR-004**: A span MUST measure wall time with `time.perf_counter_ns()`.
- **FR-005**: A span MUST measure process CPU time with `time.process_time_ns()`.
- **FR-006**: The sink MUST store bounded JSON Lines records under `data/`.
- **FR-007**: The sink MUST bound memory by event count and estimated bytes.
- **FR-008**: The sink MUST open a circuit after repeated write failures.
- **FR-009**: The privacy policy MUST drop labels that are not allowlisted.
- **FR-010**: The privacy policy MUST not store secrets, personal data, raw paths, URLs, SQL text, IP addresses, MAC addresses, UUIDs, or tokens.
- **FR-011**: Count labels MUST use fixed buckets.
- **FR-012**: Status labels MUST use fixed families.

### Key Entities

- **Recorder**: The object that owns settings, the level gate, the sampler, and the sink.
- **Span**: The context manager that measures one boundary.
- **Performance event**: The bounded record that the sink writes as JSON Lines.
- **Privacy policy**: The deny-by-default filter for labels and source data.
- **Bounded sink**: The in-memory queue and JSON Lines writer.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The default recorder records zero events in the default unit test.
- **SC-002**: The enabled span records a positive wall duration and a nonnegative CPU duration.
- **SC-003**: One storage test exists for each forbidden data category.
- **SC-004**: The new package coverage stays at or above 80 percent.
- **SC-005**: The disabled span cost is measured and reported in the pull request.

## Assumptions

- The first delivery adds the shared modules and tests. It does not add every hook from issue #2482.
- The hook catalog in `specs/2448-misthelper-performance-monitoring/` remains the source for later hook placement.
- The package uses the existing Python test and quality gates.
