# Feature Specification: Portal Run Evidence Isolation

**Feature Branch**: `jmorrison-juniper-fix-4024-portal-run-isolation`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Issue #4024: Preserve concurrent legacy web portal operations while ensuring each run receives only its own `log_messages`, `debug_messages`, `output_files`, and first previewable result file. Bind log capture and tracked writes to the operation worker owner. Reject ambiguous file evidence while scanners overlap. Preserve single-run fallback behavior for untracked writers. Do not serialize portal runs or change the shared data directory contract."

## User Scenarios & Testing

### User Story 1 - Trust each concurrent run record (Priority: P1)

As a network operator, I need each concurrent portal run to show only its own evidence so I can trust its status and result.

**Why this priority**: Foreign logs or files can hide a failure, report false success, or show data from the wrong operation.

**Independent Test**: Start two synchronized operations with distinct log lines, debug lines, and output files. Each completed run contains only its own evidence.

**Acceptance Scenarios**:

1. **Given** two operation workers pause at a synchronization point, **When** both emit distinct user-facing logs before either finishes, **Then** each run stores only its worker's `log_messages`.
2. **Given** the same synchronized runs, **When** both emit distinct internal logs, **Then** each run stores only its worker's `debug_messages`.
3. **Given** both runs publish live events, **When** a client reads each run's server-sent event stream, **Then** each stream contains only events for its requested run identifier.
4. **Given** one run exceeds its bounded log capacity and the other does not, **When** both status records are read, **Then** only the first run reports its discarded log count.
5. **Given** both runs complete, **When** their status records are compared, **Then** no log entry, debug entry, output file, or discard count crosses between runs.

---

### User Story 2 - Preview the correct operation result (Priority: P1)

As a network operator, I need the Results panel to open the first previewable file from my run so I do not inspect another operation's data.

**Why this priority**: A foreign result table can cause an operator to make a decision from unrelated data.

**Independent Test**: Run two overlapping operations that create distinct result files and optional cache files. Each run lists and previews only its own result.

**Acceptance Scenarios**:

1. **Given** two overlapping workers write distinct files through tracked writers, **When** both runs finish, **Then** each run lists only files owned by its worker.
2. **Given** each run writes one previewable result and one lower-priority file, **When** output files are ordered, **Then** each run's first previewable file belongs to that run.
3. **Given** a file appears while two scanners overlap but no worker owner can be proved, **When** output evidence is collected, **Then** neither run claims that file from timestamp evidence.
4. **Given** one active scanner and an untracked writer, **When** a new file or in-place rewrite meets the existing fallback rules, **Then** the run still reports the file.
5. **Given** a run has no owned output and no valid no-output reason, **When** completion is assessed, **Then** foreign or ambiguous files do not make the run successful.

---

### User Story 3 - Preserve concurrency and scanner lifecycle (Priority: P2)

As a portal maintainer, I need isolation without serializing operations or leaving process hooks active after a run.

**Why this priority**: The portal must retain concurrent legacy operations and must restore shared process behavior after capture ends.

**Independent Test**: Hold two workers in an overlap, release them in both completion orders, and repeat with one failure. Concurrency remains active and hooks clean up correctly.

**Acceptance Scenarios**:

1. **Given** two safe legacy operations, **When** both workers reach a synchronization point, **Then** both remain active at the same time.
2. **Given** two overlapping scanners, **When** the first scanner stops, **Then** write tracking remains available for the second scanner.
3. **Given** the last active scanner stops, **When** cleanup completes, **Then** each process-wide file hook returns to its pre-run value.
4. **Given** an operation raises an exception, **When** its capture scope exits, **Then** its log handler and scanner registration are removed.
5. **Given** one run finishes before another, **When** the remaining worker emits logs and writes files, **Then** its evidence collection continues without loss or foreign attribution.

### Edge Cases

- A worker creates a file with the same name that another worker used in an earlier run.
- Two workers open the same path for writing during one overlap.
- A file write occurs on a child thread with no provable operation owner.
- A non-Python writer creates a new file while two scanners overlap.
- A non-Python writer changes an existing file while one scanner is active.
- One scanner stops while another scanner records a write.
- A worker fails during logging, file creation, or cleanup.
- A run reaches the log or output-file capacity while another run remains below its capacity.
- A stale server-sent event subscriber remains connected after its run completes.
- The shared data directory contains preexisting files with recent timestamps.

## Requirements

### Functional Requirements

- **FR-001**: Each operation worker MUST have one stable owner identity for its capture lifetime.
- **FR-002**: Each captured log record MUST enter only the run owned by the worker that emitted the record.
- **FR-003**: Each captured debug record MUST enter only the run owned by the worker that emitted the record.
- **FR-004**: Log records with no provable active operation owner MUST NOT enter an operation run record.
- **FR-005**: Each server-sent log, debug, status, completion, and error event MUST identify and serve only its owning run.
- **FR-006**: Each run's `dropped_log_count` MUST count only entries discarded from that run's bounded log stores.
- **FR-007**: Each tracked writable path MUST be attributed only to the scanner owned by the worker that opened the path.
- **FR-008**: A tracked writable path with no provable active operation owner MUST NOT be attributed to any run.
- **FR-009**: A path that has more than one possible owner MUST NOT be used as output evidence for any overlapping run.
- **FR-010**: Directory-change and full-walk timestamp evidence MUST NOT be used when overlapping scanners make ownership ambiguous.
- **FR-011**: Directory-change and full-walk timestamp fallbacks MUST preserve their current behavior when exactly one scanner is active.
- **FR-012**: Each run's `output_files` MUST contain only files with unambiguous ownership or valid single-run fallback evidence.
- **FR-013**: Output ordering MUST select the owning run's first previewable result file before its lower-priority files.
- **FR-014**: Foreign or ambiguous output evidence MUST NOT satisfy a run's successful-completion check.
- **FR-015**: The portal MUST continue to execute independent legacy operations concurrently.
- **FR-016**: The feature MUST NOT add a global operation lock or otherwise serialize all portal runs.
- **FR-017**: The feature MUST preserve the shared data directory as the output location for legacy operations.
- **FR-018**: The feature MUST NOT require operation-specific output directories or change existing output path names.
- **FR-019**: Capture cleanup MUST remove a completed or failed run's handler and scanner ownership.
- **FR-020**: Process-wide file hooks MUST remain active while at least one scanner needs them.
- **FR-021**: Process-wide file hooks MUST return to their exact pre-capture values after the last scanner stops.
- **FR-022**: Cleanup MUST be safe for either overlap completion order and for operation exceptions.
- **FR-023**: Existing single-run log routing, output discovery, output ordering, caps, and no-output decisions MUST remain compatible.
- **FR-024**: Automated tests MUST synchronize two workers so overlap is proved and repeatable.
- **FR-025**: Automated tests MUST prove both isolation success and direct failure behavior for foreign or ambiguous evidence.

### Mist Cloud Transport Requirements

This feature does not add or change a Mist Cloud transport.

### Key Entities

- **Operation run**: One portal execution record with status, logs, output files, counts, and completion evidence.
- **Operation worker owner**: The identity that connects one executing worker to its run capture scope.
- **Run log capture**: The bounded collection of user-facing and debug records for one operation run.
- **Output scanner**: The capture scope that finds report files for one operation run.
- **Tracked write**: A writable file open whose operation worker owner is known.
- **Fallback evidence**: Directory or file timestamp evidence used for a writer that does not use tracked file opens.
- **Ambiguous evidence**: A log or file event that cannot be assigned to exactly one active operation run.
- **Previewable result**: The first owned result file that the Results panel can display as the run's table or file preview.
- **Server-sent event stream**: The live event channel that reports progress for one requested run identifier.
- **Capture hook**: A temporary process-level interception that supports file-write ownership tracking.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In 100 synchronized two-run test repetitions, each run contains zero foreign user-facing log entries.
- **SC-002**: In the same repetitions, each run contains zero foreign debug entries and zero foreign server-sent log events.
- **SC-003**: In the same repetitions, each run contains zero foreign output files, and its first previewable result belongs to that run.
- **SC-004**: A run that discards seven log entries reports seven discarded entries, while a concurrent run below its cap reports zero.
- **SC-005**: Every file with ambiguous ownership during scanner overlap is excluded from both run result lists.
- **SC-006**: Each existing single-run fallback test for new files and in-place rewrites passes without a contract change.
- **SC-007**: A two-worker synchronization test proves both workers are active before either worker can complete.
- **SC-008**: Hook lifecycle tests pass for both completion orders and for each worker failing first.
- **SC-009**: After the last scanner ends, the file-open functions equal the values captured before the first scanner started.
- **SC-010**: Existing focused portal tests for log routing, output discovery, output ordering, caps, completion, and event streaming pass.

## Assumptions

- One portal operation has one primary worker owner for its capture lifetime.
- Child work without inherited ownership is ambiguous and cannot contribute run evidence.
- Legacy operations continue to write into the shared data directory.
- Tracked writes are the authoritative file evidence during overlapping scans.
- Timestamp fallbacks remain necessary for untracked writers during a single active scan.
- A file with ambiguous ownership is safer to omit than to assign to the wrong run.
- Existing bounded stores, status response fields, and server-sent event formats remain in scope for compatibility.
- The feature changes portal evidence attribution only. It does not change Mist API behavior or operation business logic.
