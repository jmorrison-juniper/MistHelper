# Safety Checklist: Stranded Branch Preservation

**Purpose**: Check that the procedure cannot delete, rewrite, or expose branch work or a credential.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

**Note**: `[x]` means the procedure rule exists in this record. It does not mean that the procedure ran.

## Git Actions

- [x] SAF001 No task deletes, renames, or force-pushes a branch. Reason: FR-007 forbids these actions, and tasks T010 to T023 name none of them.
- [x] SAF002 The close command omits `--delete-branch`. Reason: `design/contracts/preservation-pull-request.md` section "Close Request" forbids the option.
- [x] SAF003 No task runs a checkout of a stranded branch. Reason: decision D-10 in `design/research.md` allows read-only `git log` and `git diff` only.
- [x] SAF004 No task merges or pushes a stranded branch. Reason: FR-007 forbids both actions.

## Concurrency and Limits

- [x] SAF005 At most one preservation pull request stays open. Reason: FR-004 and the steps in `design/quickstart.md` section "Preserve One Branch".
- [x] SAF006 A held branch waits for its blocking pull request. Reason: FR-003 and FR-013 define the hold and its release.
- [x] SAF007 A failed close stops the run. Reason: FR-010 blocks the next create after a failed close.
- [x] SAF008 HTTP 403 or 429 triggers a bounded backoff. Reason: FR-010 names waits of 60, 120, and 240 seconds, then a stop.

## Secrets and Record Content

- [x] SAF009 The record names only the token variable. Reason: `design/quickstart.md` section "Token Setup" sets the variable and never prints its value.
- [x] SAF010 The record pull request merges only after the final scope check. Reason: FR-014 and task T-MERGE require the check first.
