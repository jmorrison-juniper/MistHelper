# Feature Specification: WAN Duplicate Sample Coverage

**Feature Branch**: `fix/4681-wan-duplicate-sample-coverage`

**Created**: 2026-11-26

**Status**: Draft. Implementation waits for PR #4208 to release both affected files.

**Issue**: #4681

**Input**: Issue #4681 title: "Runtime: duplicate WAN samples overstate utilization coverage"

## Clarifications

### Session 2026-11-26

- Q: Does the defect exist on `main`? A: No. `main` rejects a gateway insight response with more than one timestamp. See `src/interfaces/wan_performance/collection/snapshot_client.py` line 219.
- Q: Does the defect exist on the PR #4208 head? A: Yes. Head `843be63bc837513b4442dae69da9f0db922e0ed1` accepts repeated timestamps and counts them. See lines 266, 285, 322, 357, and 435.
- Q: Should an identical duplicate fail? A: No. The fix keeps one point for that timestamp. The expected interval counts once.
- Q: Should a conflicting duplicate fail? A: Yes. The collection stops before publication and before history writes. See `src/interfaces/wan_performance/collection/live_service.py` lines 42, 48, and 77. PR #4208 documents the same rule for changed sample data at `documentation/wan-performance.md` line 441.
- Q: Can implementation start now? A: No. PR #4208 owns both affected files until it merges or releases them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Count each expected interval once (Priority: P1)

An engineer reviews WAN utilization for one gateway port. Mist repeats one timestamp and omits another. The snapshot counts only the known expected intervals.

**Why this priority**: Overstated coverage makes an incomplete hour look complete. This defect is the root cause for this issue.

**Independent Test**: Run the gateway insight unit tests with a mocked SDK response. The response repeats one timestamp and omits one.

**Acceptance Scenarios**:

1. **Given** six timestamps with one repeated and one missing, **When** the snapshot client builds samples, **Then** `sample_count` is 5 and `coverage_fraction` is 5/6.
2. **Given** a repeated timestamp with the same value, **When** the snapshot client builds samples, **Then** the expected interval counts once.
3. **Given** a repeated timestamp with different values, **When** the snapshot client builds samples, **Then** it raises `ValueError` and publishes no snapshot.

---

### User Story 2 - Exclude incomplete hours from congestion minutes (Priority: P1)

An operator reads congestion minutes for a date range. An hour with fewer than six known intervals adds no minutes and no complete hour.

**Why this priority**: The summary reports congestion minutes to operators. A false complete hour overstates congestion time.

**Independent Test**: Run the calendar summary unit tests with an hourly measurement. Its congestion metric has full coverage and five samples.

**Acceptance Scenarios**:

1. **Given** `sample_count` 5 and `coverage_fraction` 1.0, **When** the summary builds durations, **Then** the hour adds no minutes and no complete hour.
2. **Given** `sample_count` 6 and `coverage_fraction` 1.0, **When** the summary builds durations, **Then** the hour adds its minutes and one complete hour.

---

### User Story 3 - Fail visibly on conflicting data (Priority: P2)

An engineer reads the refresh log after a conflicting duplicate. The log names the failure. No new snapshot publishes.

**Why this priority**: Conflicting data has no safe value. The system must stop instead of choosing one value.

**Independent Test**: Run the gateway insight unit test with conflicting duplicate values. Assert that the log message names the conflict.

**Acceptance Scenarios**:

1. **Given** a conflicting duplicate timestamp, **When** the collection runs, **Then** the collection logs the conflict and raises before publication.

### Edge Cases

- What happens when a repeated timestamp and a null value share one hour? The hour is incomplete, and it reports no congestion value.
- What happens when a timestamp lies outside the requested hour? The existing membership check rejects the response.
- What happens when receive and transmit points repeat differently? The existing alignment check rejects the pair.
- What happens for the one-hour gateway window? Its single-timestamp rule stays unchanged.
- What happens when the summary receives two measurements for one hour? The existing duplicate-hour check rejects the input.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The snapshot client MUST count each expected interval once for each insight metric.
- **FR-002**: The snapshot client MUST keep one point for an identical duplicate timestamp.
- **FR-003**: The snapshot client MUST reject a conflicting duplicate timestamp before it publishes any sample.
- **FR-004**: The snapshot client MUST set `sample_count` and `coverage_fraction` from unique known intervals.
- **FR-005**: The snapshot client MUST mark an hour incomplete when any expected interval has no known value.
- **FR-006**: The utilization calculation MUST use aligned unique points only.
- **FR-007**: The congestion value MUST stay missing unless all six 10-minute intervals are known.
- **FR-008**: The summary MUST exclude an hour from congestion durations unless its metric has six samples and full coverage.
- **FR-009**: The fix MUST keep the Mist request, the mistapi method, and the query window unchanged.
- **FR-010**: The fix MUST log each duplicate decision before the decision and after it, with counts only.
- **FR-011**: The fix MUST add one changelog fragment and update the coverage rule in `documentation/wan-performance.md`.
- **FR-012**: The fix MUST NOT start before PR #4208 releases both affected files.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The feature uses these mistapi REST methods: `getSiteInsightMetricsForGateway`, `listOrgDevicesStats`, `listInsightMetrics`, and `searchOrgSwOrGwPorts`.
- The fix changes none of these methods. The fix adds no direct HTTP request and no owned transport.
- Contract evidence: `design/contracts/insight-sample.md` defines the response shape that the tests mock.
- SDK authentication: the fix reuses the existing session. SDK endpoint parity: the route matches the OpenAPI route at line 32714 of the local OpenAPI file. SDK insufficiency: not applicable, because the fix owns no transport.
- Failure safety: a conflicting duplicate raises before publication. Secret redaction: logs carry counts and timestamps only.

### Key Entities *(include if feature involves data)*

- **Expected interval**: One timestamp slot inside the requested hour. Six slots exist for 10 minutes and one slot for 1 hour.
- **Point**: One timestamp and value pair from one Mist response.
- **Insight sample**: The normalized result for one metric in one hour. It holds `sample_count` and `coverage_fraction`.
- **Congestion metric**: One minutes value for one threshold. It needs six known intervals.
- **Hourly measurement**: The summary input for one hour. It holds the metrics for that hour.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A response with one repeated and one missing interval yields `sample_count` 5 and `coverage_fraction` 5/6.
- **SC-002**: A response with six known unique intervals yields `sample_count` 6 and the expected congestion values.
- **SC-003**: A conflicting duplicate raises `ValueError` in the unit test, and no snapshot publishes.
- **SC-004**: The summary excludes an hour whose congestion metric has five samples and full coverage.
- **SC-005**: Each applicable local gate passes, and each required CI check succeeds on the fix pull request.
- **SC-006**: The unit tests make zero live Mist calls.

## Assumptions

- Mist can repeat a timestamp in one response. No live response proves this, and this issue makes zero live Mist calls.
- PR #4208 merges or releases both affected files before implementation starts.
- If PR #4208 closes without merging, the defect never reaches `main`. The issue then needs a new scope.
- The one-hour gateway path and its single-timestamp rule stay unchanged.
- The runtime pair is Python 3.15 and mistapi 0.64.1, within the pin `mistapi>=0.64.0,<0.65`.

## Out of Scope

- Changing the Mist query, interval, page size, or limit.
- Changing peer path or port quality statistics.
- Changing the web UI or its templates.
- Splitting the directories that PR #4208 leaves with six children. A separate issue owns that work.
- Running live Mist validation.
- Updating `documentation/architecture.md`, which describes an older `src/` layout.
