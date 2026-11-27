# Process Checklist: SQLite Device Event Identity

**Purpose**: Check that the change follows the repository process before the pull request opens.
**Created**: 2026-11-26
**Feature**: `tasks.md` in this record.

## Repository Rules

- [x] CHK001 The change adds no direct child to a folder that already holds more than five children. Source: `plan.md` Five-Item Rule Check.
- [x] CHK002 The new package holds four children. Source: `plan.md` File-by-File Change Map.
- [x] CHK003 The change adds one changelog fragment with the issue name in its file name. Source: `changelog.d/README.md` (R47).
- [x] CHK004 The commit uses the Conventional Commits format. The task T-PR names the format.
- [x] CHK005 The pull request body contains `Closes #4723`. The task T-PR names the text.

## Coordination

- [x] CHK006 The open pull request #4813 touches a file that this change does not edit. Source: research S-3.
- [x] CHK007 The shared writer file needs a handoff before the edit. The task T002 records the handoff.
- [x] CHK008 Issues #4724 and #4725 own the Redis and ArangoDB keys. The spec keeps those keys unchanged.
- [x] CHK009 Issue #4721 and #4722 keep ownership of the menu 97 exporter file. The change does not edit that file.

## Gates

- [x] CHK010 Each task names one verification command from the local gates table.
- [x] CHK011 The safe sweep covers menu 21 after the change. The task T-MERGE names the command.
- [x] CHK012 The documentation changes pass the STE gate. The tasks T013 to T016 name the command.
- [x] CHK013 Auto-merge waits for a human review of the migration module. The task T-MERGE names this condition.
