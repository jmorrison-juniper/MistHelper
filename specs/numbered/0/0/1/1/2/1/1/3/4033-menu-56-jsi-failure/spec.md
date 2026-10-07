# Feature Specification: Menu 56 Delay Metrics Integrity

**Feature Branch**: Current existing branch

**Created**: 2026-10-06

**Status**: Draft

**Input**: MistHelper issue #4033 requires a root-cause repair for concurrent delay metrics writes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve Delay History During Concurrent Writes (Priority: P1)

As a MistHelper operator, I need concurrent menu operations to preserve each complete delay
history row. This behavior prevents a damaged history file from causing menu 56 failures.

**Why this priority**: Concurrent writers can corrupt the shared history and cause a visible
warning during normal operation.

**Independent Test**: Start coordinated writers against one delay history file. Confirm that
the final file contains every expected complete row and remains readable.

**Acceptance Scenarios**:

1. **Given** two or more processes update one delay history file, **When** their write cycles
   overlap, **Then** one process lock serializes the complete read-modify-write cycle.
2. **Given** each process adds a unique history row, **When** all processes finish, **Then** the
   destination contains each expected row exactly once as complete JSONL.
3. **Given** the current behavior has no serialization, **When** the red proof coordinates
   concurrent writers, **Then** the test reproduces corruption and captures the exact warning
   text `File I/O: Failed to read data/delay_metrics.json`.

---

### User Story 2 - Keep the Previous File After a Failed Replacement (Priority: P2)

As a MistHelper operator, I need a failed history update to leave the previous destination
unchanged. This behavior keeps valid rate-limit history available after a file-system error.

**Why this priority**: A failed final replacement must not damage the last valid history.

**Independent Test**: Force the destination replacement to fail. Confirm that the previous
destination content remains unchanged and that no temporary file remains.

**Acceptance Scenarios**:

1. **Given** the destination contains valid history, **When** the atomic replacement fails,
   **Then** the previous destination remains byte-for-byte unchanged.
2. **Given** a same-directory temporary file was written, **When** any write cycle step fails,
   **Then** the repair removes that temporary file.

---

### User Story 3 - Accept an Empty History File (Priority: P3)

As a MistHelper operator, I need an empty delay history file to act as an empty history.
This behavior lets the next valid update restore normal data without a read failure.

**Why this priority**: An empty file is a recoverable starting state and must not block a new
complete history row.

**Independent Test**: Start with a zero-byte history file. Add one row and confirm that the
result is valid JSONL with no stale temporary file.

**Acceptance Scenarios**:

1. **Given** a zero-byte destination file, **When** MistHelper records the next delay metric,
   **Then** it treats the previous history as empty and writes one complete row.
2. **Given** the empty-file update succeeds, **When** the destination is read again, **Then**
   the reader receives the new complete history without a corruption warning.

### Edge Cases

- Multiple processes start from the same valid destination state before either process writes.
- The destination exists but has zero bytes.
- The temporary file write fails before the replacement starts.
- The replacement fails after the temporary file contains the complete new history.
- Cleanup runs when the temporary file does not exist or was already removed.
- A successful replacement leaves no same-directory temporary file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The change MUST remain limited to
  `src/foundation/support/utils/rate_limiting.py` and
  `tests/unit/test_rate_limiting.py`.
- **FR-002**: The change MUST NOT modify `web_portal/services/operation.py`.
  Issue #3168 owns the typed outcome repair in that file.
- **FR-003**: Before the repair, a red proof MUST coordinate concurrent writers and reproduce
  delay history corruption.
- **FR-004**: The red proof MUST capture the exact warning text
  `File I/O: Failed to read data/delay_metrics.json`.
- **FR-005**: One process lock MUST serialize the full delay history read-modify-write cycle.
- **FR-006**: A writer MUST hold the same process lock from the destination read through the
  final replacement or failure cleanup.
- **FR-007**: The writer MUST create the temporary file in the destination directory.
- **FR-008**: The writer MUST write the complete new JSONL history to the temporary file before
  it changes the destination.
- **FR-009**: Each persisted history row MUST be complete and independently valid JSON.
- **FR-010**: The writer MUST use `os.replace` to replace the destination only after the
  temporary file write completes.
- **FR-011**: If replacement fails, the previous destination MUST remain unchanged.
- **FR-012**: If any write cycle step fails after temporary file creation, the writer MUST
  remove the temporary file.
- **FR-013**: A successful write MUST leave no temporary file.
- **FR-014**: A zero-byte destination MUST be treated as an empty history.
- **FR-015**: Tests MUST prove concurrent complete-row preservation.
- **FR-016**: Tests MUST prove previous-destination integrity after replacement failure.
- **FR-017**: Tests MUST prove that a failed write leaves no orphaned temporary file.
- **FR-018**: Tests MUST prove the empty-file history behavior.
- **FR-019**: Existing rate-limit behavior outside delay history persistence MUST remain
  unchanged.

### Key Entities

- **Delay history destination**: The `data/delay_metrics.json` file that holds complete JSONL
  history rows.
- **Delay history row**: One complete JSON object that represents one persisted delay metric.
- **Process lock**: The single process-level synchronization boundary for one complete
  read-modify-write cycle.
- **Temporary history file**: A same-directory file that holds the complete replacement content
  before the atomic replacement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The red proof fails before the repair and captures the exact required warning.
- **SC-002**: In the concurrent writer test, 100 percent of expected unique rows remain complete
  and readable after all writers finish.
- **SC-003**: In the empty-file test, the first update produces one complete readable row.
- **SC-004**: In the replacement failure test, 100 percent of the previous destination bytes
  remain unchanged.
- **SC-005**: Successful and failed write tests find zero orphaned temporary files.
- **SC-006**: All targeted tests in `tests/unit/test_rate_limiting.py` pass after the repair.

## Assumptions

- The issue requires process-level serialization for concurrent work in one MistHelper process.
- The existing delay history row shape and retention rules remain unchanged.
- The destination directory already exists when the write cycle starts.
- The specification does not include the typed outcome work owned by issue #3168.
- No Mist Cloud transport changes are required.
