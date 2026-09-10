# Feature Specification: Compliance analyzer parallel jobs

**Feature Branch**: `feat/2428-parallel-compliance-analyzer`

**Created**: 2026-09-09

**Status**: Implemented

**Input**: User description: "Analyze the entire repository for Python parallelization opportunities, then implement and test proven changes."

## User Scenarios and Testing

### User Story 1 - Run a large compliance scan faster (Priority: P1)

A maintainer can run the compliance analyzer over the repository with worker jobs.

**Why this priority**: The repository-wide scan is the measured bottleneck that exceeded the acceptance threshold.

**Independent Test**: Run the same scan with `--jobs 1` and `--jobs 8`. Confirm that the Markdown reports match.

**Acceptance Scenarios**:

1. **Given** a repository with more than 200 Python files, **When** the maintainer runs `--jobs 8`, **Then** the analyzer uses worker processes.
2. **Given** the same repository input, **When** the maintainer compares sequential and parallel reports, **Then** the report content is identical.

---

### User Story 2 - Keep small scans simple (Priority: P2)

A maintainer can scan a small file set without worker startup cost.

**Why this priority**: The measurement showed that spawned workers are slower for small scans.

**Independent Test**: Run a scan below the file floor with `--jobs 8`. Confirm that the sequential path runs.

**Acceptance Scenarios**:

1. **Given** fewer than 200 Python files, **When** the maintainer requests worker jobs, **Then** the analyzer uses the sequential path.

---

### User Story 3 - Preserve failure behavior (Priority: P3)

A maintainer gets the same parse-error report and missing-file exception type in both modes.

**Why this priority**: Parallel execution must not hide or reshape failures.

**Independent Test**: Run tests with a syntax-error file and a missing collected file.

**Acceptance Scenarios**:

1. **Given** a syntax-error file, **When** either mode analyzes it, **Then** the result contains the same `PARSE-ERROR` report.
2. **Given** a missing collected file, **When** either mode analyzes it, **Then** the same exception type reaches the caller.

### Edge Cases

- If `--jobs` is negative, the analyzer raises a clear value error.
- If `--jobs` is `0`, the analyzer selects a bounded automatic worker count.
- If a worker fails, the analyzer cancels pending work and raises the original error.
- If the input order changes, the report content changes. The implementation must preserve order.

## Requirements

### Functional Requirements

- **FR-001**: The analyzer MUST keep sequential mode as the default.
- **FR-002**: The CLI MUST accept `-j` and `--jobs`.
- **FR-003**: The analyzer MUST use explicit `spawn` for process workers.
- **FR-004**: The analyzer MUST cap automatic workers at 8.
- **FR-005**: The analyzer MUST keep scans below 200 files sequential.
- **FR-006**: The analyzer MUST preserve report order and report values.
- **FR-007**: The analyzer MUST cancel pending worker work after a worker failure.
- **FR-008**: The analyzer MUST keep file collection and `git check-ignore` sequential.

### Key Entities

- **FileReport**: The per-file analyzer result. It must remain picklable and order-preserving.
- **Worker batch**: A list of file paths processed by one worker task.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The repository-wide scan is at least 1.5 times faster with the accepted worker count.
- **SC-002**: Sequential and parallel reports are byte-identical for the repository scan.
- **SC-003**: The parallel path uses no more than 8 automatic workers.
- **SC-004**: The 8-worker path uses acceptable memory for a developer tool.
- **SC-005**: The unit test suite covers order, parity, fallback, parse errors, and failure behavior.

## Assumptions

- The target interpreter is CPython 3.13.3 on Windows.
- Worker processes use `spawn`.
- The accepted workload is a repository-wide scan with more than 200 Python files.
- No live Mist API call is part of this feature.
