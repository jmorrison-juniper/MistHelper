# Research: Portal Run Evidence Isolation

## Decision 1: Use the worker thread identifier as the capture owner

**Decision**: Capture `threading.get_ident()` in the operation worker and use it for logs and tracked writes.

**Rationale**: `OperationExecutor` already runs each operation in a `ThreadPoolExecutor`.
`logging.LogRecord.thread` records the emitting thread identifier.
The file-open hooks also execute on the calling thread.
One identifier can therefore bind both evidence paths without serialization.

**Alternatives considered**:

- A global current-run value would race between workers.
- A process-wide operation lock would violate the concurrency requirement.
- A run identifier in every legacy writer would require broad product changes.
- A `contextvars.ContextVar` would not prove ownership for existing child threads.

## Decision 2: Filter logs before any run mutation

**Decision**: `_RunLogHandler.emit` will return when `record.thread` differs from its owner.

**Rationale**: The root logger attaches one handler for each active run.
Today, each handler receives every process log record.
An early filter prevents foreign log storage, output filename extraction, discard counts, and SSE publication.

**Alternatives considered**:

- Filtering only SSE events would leave foreign evidence in status responses.
- Filtering after storage would corrupt bounded counts.
- Logger-name filtering cannot distinguish two concurrent runs of the same code.

## Decision 3: Use one active scanner per owner thread

**Decision**: Replace scanner fan-out with an owner-keyed scanner registry.

**Rationale**: The current `_record_write_candidate` adds each writable path to every active scanner.
The calling thread identifies the worker that opened the path.
An owner-keyed lookup gives direct attribution and keeps hook cost bounded.

**Alternatives considered**:

- Keep the list and filter each scanner by owner.
  This keeps linear fan-out and permits duplicate owner registration.
- Store only path-to-run ownership.
  The scanner still needs lifecycle, limits, exclusions, and fallback state.

## Decision 4: Reject paths with multiple tracked owners

**Decision**: Mark a path ambiguous for every active scanner that tracked it.

**Rationale**: A file can be opened by two workers during one overlap.
The final content cannot be assigned safely from open order or modification time.
Omission is safer than a false result.

**Alternatives considered**:

- Last writer wins.
  The final timestamp does not prove which run produced the displayed result.
- First writer wins.
  A later worker can replace the content before preview.
- Assign the path to both runs.
  This repeats the foreign evidence defect.

## Decision 5: Disable timestamp fallback after any scanner overlap

**Decision**: A scanner that overlaps another scanner will use tracked evidence only.

**Rationale**: Directory marks and full walks identify time, not ownership.
During overlap, a new file or rewrite can belong to either run.
The scanner must fail closed when ownership is not provable.

**Alternatives considered**:

- Enable fallback after the other scanner finishes.
  Files from the overlap remain indistinguishable.
- Compare worker start and end times.
  Both run windows overlap, so timestamps still match both runs.
- Remove fallback completely.
  Existing single-run non-Python writers would lose output evidence.

## Decision 6: Keep hooks active until the final scanner stops

**Decision**: Install hooks for the first scanner and restore them after the registry becomes empty.

**Rationale**: The current lifecycle already reference-counts through active scanner membership.
The owner-keyed registry can preserve this behavior and restore exact saved function objects.

**Alternatives considered**:

- Install hooks for each scanner.
  Nested wrappers can double-record writes and restore the wrong function.
- Remove hooks when any scanner stops.
  The remaining run would lose tracked writes.

## Decision 7: Keep public contracts unchanged

**Decision**: Add private ownership state only.

**Rationale**: Status responses and SSE payloads already contain `run_id`.
`PortalEventBus` already filters subscribers by that identifier.
The defect is capture attribution before publication.

**Alternatives considered**:

- Add an owner identifier to public responses.
  A thread identifier is an internal process detail and gives no operator value.
- Change output paths to per-run directories.
  The feature specification forbids this contract change.
