# Feature Specification: Report a missing latest WAN rate

**Feature Branch**: `fix/4682-wan-missing-latest-rate` (planned, created after pull request 4208 merges)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue 4682, "Runtime: WAN dashboard reports an earlier rate when the latest sample is missing"

## Context

The rate sample builder reads the last valid value as the latest value. When the latest interval has no value, an earlier rate appears as current. Operators must see the latest value as unavailable instead.

The builder exists in two places. On main, it is at `src/interfaces/wan_performance/collection/snapshot_client.py` line 241. On the pull request 4208 head, it is at line 282. On main, no portal route calls the builder.

Pull request 4208 owns the file. Its owner blocked the fix until the pull request merges or releases the file. The owner recorded this on 2026-11-08 in issue 4682.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Show no earlier rate as current (Priority: P1)

An operator views a WAN rate for a selected port. When the latest interval has no value, the rate shows as unavailable. No earlier value appears as current.

**Why this priority**: A wrong current rate hides a live fault. This story fixes the reported defect.

**Independent Test**: Run the two defect tests with mocked mistapi responses. No live Mist call runs.

**Acceptance Scenarios**:

1. **Given** a ten-minute response with a valid earlier interval and a null latest item, **When** the builder runs, **Then** `value` is None and the earlier value remains only in `raw_values`.
2. **Given** a ten-minute response without the latest interval, **When** the builder runs, **Then** `value` is None and `missing_reason` is a non-empty string.

### User Story 2 - Explain the missing value (Priority: P2)

An operator reads why the latest value is missing. The reason states that the latest interval has no value when an earlier valid value exists.

**Why this priority**: The reason lets an operator judge the gap without reading a log file.

**Independent Test**: Run the null-latest test and the all-null test. Check the `missing_reason` text in each test.

**Acceptance Scenarios**:

1. **Given** an earlier valid value and a null latest item, **When** the builder runs, **Then** `missing_reason` is "The latest interval has no value."
2. **Given** only null items, **When** the builder runs, **Then** `missing_reason` is "The API snapshot has no value.", the existing text.

### User Story 3 - Keep the documented rule current (Priority: P3)

A maintainer reads the rule for missing values in the WAN performance guide. The guide states that only the latest interval sets the current value.

**Why this priority**: The guide must match the code. A mismatch leads operators to wrong conclusions.

**Independent Test**: The STE writing gate passes for `documentation/wan-performance.md`. The new sentence matches `design/contracts/rate-sample.md`.

**Acceptance Scenarios**:

1. **Given** the guide after the change, **When** a reader checks the missing-value rule, **Then** the rule states that a missing latest interval gives no current value.

### Edge Cases

- A latest measured zero stays a valid value. It does not become missing.
- Reversed response order selects the interval by its start time, not by its array position.
- All items are null. The result is None with the existing reason text.
- A misaligned array or an out-of-window timestamp still raises the existing ValueError.
- An unsupported interval name still raises the existing ValueError.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The rate sample MUST take `value` from the latest expected interval only.
- **FR-002**: The rate sample MUST set `value` to None when the latest interval has a null item.
- **FR-003**: The rate sample MUST set `value` to None when the response omits the latest interval.
- **FR-004**: The rate sample MUST NOT use an earlier valid value as `value`.
- **FR-005**: The rate sample MUST set `missing_reason` to None when `value` is a number.
- **FR-006**: The rate sample MUST set `missing_reason` to a non-empty string when `value` is None.
- **FR-007**: The implementation MUST select the latest interval by its expected start time, not by array position.
- **FR-008**: The implementation MUST keep a measured zero as a valid value.
- **FR-009**: The implementation MUST keep `raw_values`, `sample_count`, `coverage_fraction`, `points`, and the snapshot `partial` rule unchanged.
- **FR-010**: Tests MUST use mocked mistapi responses. No test MUST call the live Mist API.
- **FR-011**: Each touched line MUST carry an inline comment. Each touched function MUST carry action logging.
- **FR-012**: The change MUST update `documentation/wan-performance.md` and add one release-note fragment.

### Mist Cloud Transport Requirements

- The feature calls one existing mistapi method, `getSiteInsightMetricsForGateway`. The method is defined at `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py` line 290.
- The feature adds no request, no owned transport, and no direct HTTP call.
- Contract-test evidence is the selected-port test group in `tests/unit/wan_performance/test_gateway_insights.py`.
- Secret redaction: the change adds no log field that holds a credential.

### Key Entities

- **Latest interval**: The source interval at the last expected start in the requested hour. Ten-minute port data uses the sixth start. Hourly gateway data uses the only start.
- **Source interval**: One position in the `rt` array and the matching position in the `results` array.
- **Valid value**: A source value that is not null and passes the existing numeric check.
- **Rate sample**: The normalized record for one metric in one requested hour.
- **Missing latest value**: The state in which the latest interval is absent or holds a null item.

## Success Criteria *(mandatory)*

- **SC-001**: Five new tests exist. Two defect tests fail before the change. Three guard tests pass before and after the change.
- **SC-002**: Every test in `tests/unit/wan_performance/test_gateway_insights.py` passes after the change. No existing expected value changes.
- **SC-003**: The symbol gate reports no module-level name changed in `snapshot_client.py`.
- **SC-004**: Zero live Mist calls occur during the tests and the local gates.
- **SC-005**: The change adds no parameter to any function. Each touched function keeps 25 lines or fewer.

## Out of Scope

- Editing `snapshot_client.py` before pull request 4208 merges or releases the file.
- Changing the snapshot-level `partial` rule on the selected-port path.
- Changing the coverage calculation on main at line 244. Pull request 4208 replaces that code.
- Changing the metric-name array read on main at line 251. Pull request 4208 replaces that code.
- Splitting `GatewayInsights._sample` to meet the parameter limit. A separate issue records that debt.
- Adding a stale label to rate samples. The guide uses stale labels for snapshots only.
- Issue 4681, which covers duplicate WAN samples and utilization coverage.

## Assumptions

- The `rt` array marks the start of each interval. The current code already requires this. Unverified item U-1 records the risk.
- The fix lands after pull request 4208 merges. The target lines then change, so task T001 re-verifies them.
- Mist returns `results` and `rt` with equal length. The current code rejects other lengths.
- Null items may appear in `results`. The current code accepts them. The OpenAPI schema documents none.

## Clarifications

- **Q1**: Which value does a missing latest interval show? **A**: None, with a reason. An earlier value never becomes current (D-2).
- **Q2**: Does an absent latest interval count as missing? **A**: Yes. It follows the same rule as a null item (D-3).
- **Q3**: Which code receives the change? **A**: The pull request 4208 version after its merge. Main changes only after the owner transfers the file or the pull request closes unmerged (D-1).
- **Q4**: Does the snapshot `partial` flag change? **A**: No (D-6).
- **Q5**: Which test file receives the tests? **A**: `tests/unit/wan_performance/test_gateway_insights.py` after the merge (D-7).
