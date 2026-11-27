# Feature Specification: Hardware Manifest Finalization After a File Lock

**Feature Branch**: `fix/4780-manifest-finalization`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4780: "Runtime: concurrent hardware manifest publication fails on Windows." A refused manifest replace leaves the durable manifest at `writing`. The run then reports no durable final state.

## Clarifications

### Session 2026-11-26

- Q: Must one refused in-run manifest write stop the later target saves? → A: No. A refused in-run write defers to finalization while the record stays writable. Quota and link refusals still fail the record. (D-2, D-3)
- Q: How long may finalization wait for a manifest lock? → A: Up to seven waits, 6.35 seconds in total. Finalization runs after every target stops, so the wait blocks no target. (D-4)
- Q: What does an operator see when finalization fails? → A: The parent state is FAILED. The CLI prints `Run status: partial` and the run folder name. The run folder holds `finalization-failed.json`, and every native file stays. (D-5, D-6)
- Q: Which process holds the lock? → A: This record does not name the holder. Runtime evidence decides it. (D-1)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report a truthful final state (Priority: P1)

An operator starts a hardware collection. Windows refuses the final manifest replace for longer than the retry budget. The portal and the CLI report failed output. They do not report a complete run.

**Why this priority**: A false complete status hides missing data from the operator. The operator then acts on incomplete results.

**Independent Test**: Simulate a final manifest replace that stays refused. Verify the parent state, the CLI status line, the finalization marker, and the saved native files.

**Acceptance Scenarios**:

1. **Given** every target saved, **When** the final replace stays refused past its budget, **Then** the artifact status reads failed and the parent reads FAILED.
2. **Given** the final manifest replace fails, **When** the CLI prints the run result, **Then** the CLI prints `Run status: partial` and the run folder name.
3. **Given** the final replace clears within its budget, **When** finalization ends, **Then** the artifact status reads ready.

### User Story 2 - Keep saving after one short lock (Priority: P1)

A refused manifest replace during the run does not stop the later targets. Each native file that saves stays on disk. After finalization succeeds, the final manifest lists every saved file.

**Why this priority**: One short lock must not end the rest of a batch. Without this change, the operator loses every target after the lock.

**Independent Test**: Admit a hardware run with two targets. Refuse the first in-run manifest replace. Verify that the second target saves and that the final manifest lists both files.

**Acceptance Scenarios**:

1. **Given** the first in-run manifest replace is refused, **When** the second target saves its native file, **Then** the save succeeds and the record stays writing.
2. **Given** a native file publishes before a refused snapshot, **When** the run continues, **Then** the file stays on disk and its format reads completed.
3. **Given** a quota or link refusal occurs during the run, **When** the refusal happens, **Then** the record fails and no later target saves.

### User Story 3 - Identify the lock holder from evidence (Priority: P2)

An operator reads one error event for each refused write. The event gives the exception name and the error numbers. It holds no path. The operator uses these values with a read-only handle listing to find the holder.

**Why this priority**: The lock holder is not known. Evidence must come before any holder is named or fixed.

**Independent Test**: Force one refused write in a unit test. Verify that the error event contains `errno` and holds no local path.

**Acceptance Scenarios**:

1. **Given** a refused manifest replace, **When** the error event is written, **Then** the event contains the exception name, `errno`, and `winerror` when Windows gives one.
2. **Given** a refused replace, **When** the event is read, **Then** the event holds no local path and no secret.

### Edge Cases

- The lock clears after the first in-run refusal. The final manifest write then publishes ready.
- The lock stays through finalization, and the marker write refuses too. Both errors log, and the run fails with the contract error.
- The staged temporary path is a directory. The staged write fails, and cleanup does not remove the directory.
- The manifest path is a symbolic link. The write refuses before the replace, and the link target does not change.
- The quota refuses the final manifest. The record fails, and the marker is written.
- The process restarts after a deferred write. The orphan scan keeps the durable run folder.
- The report publish fails during finalization. The final manifest records the failed status.
- A JSON Lines batch finalizes. It uses the finalization budget too.
- The operator stops the batch during a finalization wait. The wait still ends within 6.35 seconds.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST keep the in-run replace budget of four waits, 0.75 seconds in total.
- **FR-002**: The system MUST use a finalization replace budget of seven waits, 6.35 seconds in total.
- **FR-003**: The system MUST defer a refused in-run manifest write when the record stays writable.
- **FR-004**: The system MUST try each later in-run manifest write once after one deferred write.
- **FR-005**: The system MUST keep the record writable for native saves after a deferred in-run write.
- **FR-006**: The system MUST set the artifact status to ready only after the final manifest replace succeeds.
- **FR-007**: The system MUST set the artifact status to failed and partial when finalization fails.
- **FR-008**: The system MUST try to write `finalization-failed.json` with status failed when finalization fails.
- **FR-009**: The system MUST remove its staged temporary file after a refused write when the removal succeeds.
- **FR-010**: The system MUST NOT delete a completed native file during a manifest failure, expiry, or cleanup.
- **FR-011**: The system MUST log each refused write with the exception name, `errno`, and `winerror` when present, and no path.
- **FR-012**: The system MUST set the parent session state to FAILED when finalization fails.
- **FR-013**: The CLI MUST print `Run status: partial` and the run folder name when a run output is not final.
- **FR-014**: The system MUST replace the manifest atomically. Readers MUST NOT see partial manifest content.
- **FR-015**: The change MUST NOT add a Mist REST request, a WebSocket transport, or a device command.
- **FR-016**: The change MUST NOT name a lock holder until runtime evidence identifies one.
- **FR-017**: The regression tests MUST inject refusals and record waits. They MUST NOT sleep or lock a real file.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- Not applicable. This change alters local manifest persistence only. No mistapi REST method and no WebSocket transport change. The constitution exception for an owned WebSocket transport does not apply.

### Key Entities *(include if feature involves data)*

- **Batch artifact record**: The in-memory state of one run folder. It holds the status, the partial flag, the complete flag, the manifest stale flag, the saved files, and the target outcomes.
- **Durable manifest**: The file `manifest.json` in the run folder. It holds the last complete manifest that a replace stored.
- **Finalization marker**: The file `finalization-failed.json` in the run folder. It records that finalization failed.
- **Native file**: One saved XML or JSON reply of one target. It stays on disk after any manifest failure.
- **Batch run result**: The CLI result of one organization. It holds the run folder name and the artifact readiness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A final manifest refusal that clears within 6.35 seconds gives artifact status ready in every simulated run.
- **SC-002**: A final manifest refusal that stays gives artifact status failed, a marker file, and a partial CLI status in every simulated run. Every native file stays on disk.
- **SC-003**: One refused in-run manifest write stops no later native save in the same run.
- **SC-004**: Each refused manifest write logs one error event with integer codes and no path.
- **SC-005**: The new and revised tests pass without a real sleep and without a real file lock.

## Assumptions

- The Windows lock lasts a short time in some runs and a longer time in others. Runtime evidence decides which case applies.
- Finalization starts after every target stops. The factory docstring states this rule at `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py:346`.
- Operators read the parent state and the CLI status line. No other tool reads the manifest bytes.

## Out of Scope

- Naming or fixing the lock holder before runtime evidence exists.
- A new output format, a new menu operation, or a new Mist endpoint.
- Any change to the owned WebSocket transport.
- Any change to report content, as defined by issues #4920 and #4933.
- A timed retry for the whole batch.
