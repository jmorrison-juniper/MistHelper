# Checklist: evidence

**Purpose**: Confirm that each fact in this record has a source and a check.
**Created**: 2026-11-26
**Feature**: [research.md](../research.md)

## Remote evidence

- [x] CHK001 The verified commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on main. The local HEAD has the same SHA (research.md, Scope).
- [x] CHK002 Each remote row has a path, a ref, a blob or commit SHA, a result, and a line (research.md, Remote verification).
- [x] CHK003 The remote row count matches the `remote_checks` count in `1794-STATUS.json` (129 rows, both).
- [x] CHK004 The result counts match: 98 present, 24 stale, 2 partial, and 5 absent (research.md, Remote verification).
- [x] CHK005 Each held commit exists as a commit object, and its ancestry was checked against main (RC-103 to RC-127).
- [x] CHK006 The Mist SDK claims cite the local pinned source file, not a repository path (RC-092 to RC-094).
- [x] CHK007 The ruff rule claims cite the upstream page that was fetched (RC-095).

## Repository and issue evidence

- [x] CHK008 The issue body and all 62 comments were read through `gh` (research.md, Scope).
- [x] CHK009 The legacy records and their nine files were read. Each claim that uses them cites a file and a line (analysis.md, Defects).
- [x] CHK010 The linked pull requests were searched and their state was recorded (research.md, GitHub state).
- [x] CHK011 The local working-tree copy of `logger_utils.py` differs from main. The record does not use it (U-6).

## Limits of this record

- [x] CHK012 No build, test, linter, formatter, install, or repository script ran (brief rule 2).
- [x] CHK013 No file under the repository changed. Each write went to the draft folders (brief rule 1).
- [x] CHK014 No GitHub item changed. Each `gh` call was a read (brief rule 5).
- [x] CHK015 No secret value appears in any deliverable. Secrets appear by name only (brief rule 4).
- [x] CHK016 Each unverified item appears in research.md, with its reason (U-1 to U-15).
