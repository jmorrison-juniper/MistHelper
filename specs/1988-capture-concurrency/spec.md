# Feature Specification: Capture portal concurrency evaluation

**Feature Branch**: `chore/1988-capture-concurrency`

**Created**: 2026-09-16

**Status**: Complete

**Input**: GitHub issue #1988 asks for measured evaluation of concurrency headroom in the capture firmware update portal.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review measured evidence (Priority: P1)

A maintainer can read one evaluation and decide whether a capture portal concurrency change is justified.

**Why this priority**: The issue asks for evaluation before any optimization.

**Independent Test**: Run `python scripts\benchmarks\bench_capture_concurrency.py` and inspect the raw JSON Lines artifact.

**Acceptance Scenarios**:

1. **Given** the unchanged portal model, **When** the benchmark runs, **Then** it records current elapsed time and result count.
2. **Given** a candidate with eight capture workers, **When** the same workload runs, **Then** it records elapsed time and result count.
3. **Given** a candidate with parallel store writes, **When** the same workload runs, **Then** it records elapsed time and result count.

---

### User Story 2 - Keep safety constraints visible (Priority: P2)

A reviewer can see how the rate limiter, the site lock, complexity gates, and shared stores affect the decision.

**Why this priority**: More concurrency can make a cloud run slower or less safe.

**Independent Test**: Read `plan.md` and verify that each constraint has one finding.

**Acceptance Scenarios**:

1. **Given** the evaluation, **When** a reviewer reads the plan, **Then** the plan states the rate-limit risk.
2. **Given** the evaluation, **When** a reviewer reads the plan, **Then** the plan states the site-lock risk.
3. **Given** the evaluation, **When** a reviewer reads the plan, **Then** the plan states the complexity and store contention risks.

---

### User Story 3 - Repeat the measurement (Priority: P3)

A later engineer can repeat the measurement with the same local synthetic workload.

**Why this priority**: A repeatable artifact prevents an assumption from replacing a measurement.

**Independent Test**: Delete `specs\1988-capture-concurrency\measurements\raw-data.jsonl`, run the benchmark, and compare the first line.

**Acceptance Scenarios**:

1. **Given** a clean worktree, **When** the benchmark runs, **Then** it writes raw rows and recorder events.
2. **Given** the artifact, **When** a reviewer checks the content, **Then** it contains no site identifier or token.

### Edge Cases

- If a synthetic worker fails, the reading must record an error count and not hide other results.
- If the recorder rejects a label, the privacy filter must redact it before disk storage.
- If the shared store serializes writes, more store workers must not be counted as useful concurrency.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The evaluation MUST measure the unchanged capture pool with four workers.
- **FR-002**: The evaluation MUST measure a candidate capture pool with eight workers.
- **FR-003**: The evaluation MUST measure a candidate that parallelizes store writes.
- **FR-004**: The evaluation MUST record elapsed wall time, process CPU time, result count, and error count.
- **FR-005**: The evaluation MUST use the existing performance recorder and privacy filter.
- **FR-006**: The evaluation MUST store raw measurement data under `specs\1988-capture-concurrency\measurements\`.
- **FR-007**: The recommendation MUST state whether production code should change.
- **FR-008**: The recommendation MUST state findings for rate limiting, the site lock, complexity gates, and store contention.

### Key Entities

- **Scenario**: One measured worker configuration and its store configuration.
- **Reading**: One raw timing row with counts and error status.
- **Summary**: One derived median table for the measured scenarios.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The benchmark records at least one reading for each scenario.
- **SC-002**: Each scenario returns the same result count.
- **SC-003**: The candidate must improve median wall time by at least 5 percent before a production change is recommended.
- **SC-004**: The artifact must contain no raw path, URL, IP address, MAC address, UUID, token, or site identifier.

## Measurement Result

The benchmark used three runs of each scenario. Each run used four wave-one reads, four tier-three reads, and three store writes.

| Scenario | Median wall time | Median CPU time | Result count | Error count |
| - | - | - | - | - |
| Current capture pool, 4 workers | 5381.7857 ms | 31.25 ms | 12 | 0 |
| Candidate capture pool, 8 workers | 5243.8340 ms | 31.25 ms | 12 | 0 |
| Candidate parallel store writes | 5318.1114 ms | 15.625 ms | 12 | 0 |

The eight-worker candidate saved 137.9517 ms. That is a 2.56 percent change, which does not meet SC-003.

The parallel store candidate saved 63.6743 ms. That is a 1.18 percent change.

## Recommendation

Do not change the production capture portal concurrency model for issue #1988.

The current implementation satisfies the existing threaded capture requirement. `src\upgrade_portal\capture\collector.py` runs wave one through `CapturePool`. `src\upgrade_portal\runtime\pools.py` caps the pool at four workers. `BoundedFanOut` already runs tier-three subcalls with a four-call cap.

## Assumptions

- The benchmark uses a synthetic workload, because the issue asks for safe measurement and no live customer site is approved.
- The synthetic workload models I/O waits and store waits. It does not model cloud-side rate-limit behavior.
- The branch uses the `chore/` prefix because `test/` is not an allowed branch prefix in the git-flow instructions.


