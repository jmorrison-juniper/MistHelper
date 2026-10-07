# Research: Menu 56 Delay Metrics Integrity

## Decision 1: Use one process-wide thread lock

**Decision**: Add one module-level `threading.Lock` for delay history persistence.

**Rationale**: Menu operations can share one Python process.
One lock can serialize the complete read-modify-write cycle for that shared destination.

**Alternatives considered**:

- A lock around the write only does not protect the prior read.
- A lock for each method call permits lost updates between separate lock regions.
- A platform file lock adds cross-platform complexity outside the approved scope.

## Decision 2: Use same-directory atomic replacement

**Decision**: Create a named temporary file in the destination directory.
Write all retained JSONL rows, close the file, and call `os.replace`.

**Rationale**: A same-directory replacement stays on one filesystem.
Readers see the old complete file or the new complete file.

**Alternatives considered**:

- Direct overwrite exposes an empty or partial destination.
- A temporary file in the system directory can cross filesystems.
- Append-only writes do not enforce the existing retention cap.

## Decision 3: Make the concurrent proof deterministic

**Decision**: Use thread events and a controlled write handle.
Pause the first writer after it exposes an incomplete direct write.
Start the second writer while the first writer is paused.

**Rationale**: The proof must reproduce the exact warning without a timing guess.
Events give explicit progress points and bounded waits.

**Alternatives considered**:

- Repeated stress loops can pass by chance.
- Fixed sleeps make the test slow and unstable.
- A mocked warning does not prove the real unsafe read path.

## Decision 4: Keep empty history valid

**Decision**: Treat a missing or zero-byte destination as an empty entry list.

**Rationale**: Both states contain no prior complete rows.
The next update can create one valid JSONL row.

**Alternatives considered**:

- Logging a corruption warning for zero bytes repeats the reported failure.
- Deleting the destination first weakens destination integrity.

## Decision 5: Use narrow, visible exception handling

**Decision**: Catch only expected JSON and filesystem failures at their owning boundary.
Bind each exception and use it in the related log record.

**Rationale**: Narrow catches preserve programming failures.
Used exception values give the operator the failure cause.

**Alternatives considered**:

- `except Exception` can hide a defect.
- An unused bound exception fails the requested code-quality rule.
- Silent cleanup can hide an orphaned temporary file.

## Decision 6: Preserve the existing public behavior

**Decision**: Keep the row shape, retention cap, method signatures, and nonfatal write behavior.

**Rationale**: Issue #4033 concerns delay history persistence only.
Issue #3168 owns the web portal terminal-outcome repair.

**Alternatives considered**:

- Editing `web_portal/services/operation.py` exceeds the approved scope.
- Changing row fields can break existing history readers.
- Adding a new persistence service adds files and unnecessary architecture.
