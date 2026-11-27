# Persistence Checklist: Hardware Manifest Finalization After a File Lock

**Purpose**: Check the durable-state rules before implementation

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Durable State

- [x] CHK-P01 The manifest replace stays atomic (FR-014). The change keeps `os.replace` and the staged temporary file.
- [x] CHK-P02 The artifact status becomes ready only after a verified replace (FR-006).
- [x] CHK-P03 A failed finalization leaves a terminal state. The manifest holds status ready or failed, or the marker exists (FR-007, FR-008).
- [x] CHK-P04 No manifest failure, expiry, or cleanup deletes a completed native file (FR-010).
- [x] CHK-P05 A refused write removes its staged temporary file when the removal succeeds (FR-009).
- [x] CHK-P06 A directory at a staged path is not removed (TEST-04).

## Bounds

- [x] CHK-P07 In-run waits total 0.75 seconds for the first refusal (FR-001).
- [x] CHK-P08 Finalization waits total 6.35 seconds (FR-002).
- [x] CHK-P09 Later in-run writes do not wait after one deferred write (FR-004).

## Evidence and Privacy

- [x] CHK-P10 Refused-write events hold integer codes and no path (FR-011, `contracts/log-events.md`).
- [x] CHK-P11 The marker holds no path, no target identity, and no token (`contracts/manifest-json.md`).

## Parent and CLI

- [x] CHK-P12 The parent state is FAILED when finalization fails (FR-012, `contracts/cli-status.md`).
- [x] CHK-P13 The CLI prints the partial status and the run folder name when a run output is not final (FR-013).

## Notes

- Each item cites its requirement. The tests TEST-01 to TEST-11 in `plan.md` check each rule.
