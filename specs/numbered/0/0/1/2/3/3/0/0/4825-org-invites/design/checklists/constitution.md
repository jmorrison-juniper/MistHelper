# Constitution Checklist: Organization Invites Export Handles a Missing mistapi Function

**Purpose**: Check the follow-up change against the MistHelper constitution and the repository rules.

**Created**: 2026-11-26

**Feature**: [plan.md](../../plan.md)

## Core Principles

- [x] CHK001 Principle I. Each record directory holds five children or fewer. The record root holds five children, and `design/` holds five children.
- [x] CHK002 Principle I. No direct child is added to a noncompliant parent.
- [x] CHK003 Principle II. No wrapper function is added. `_invites` stays a static method of `OrgExportUtils`.
- [x] CHK004 Principle III. The new log text holds no secret. It is a constant string.
- [x] CHK005 Principle IV. Each pipeline step is assigned to a task. T-LOCAL-GATES covers step 1, and T-MERGE covers steps 9 to 12.
- [x] CHK006 Principle V. The new log text uses ASCII only. Tasks T008 and T011 state this rule.
- [ ] CHK007 Principle VI. Inline comments on touched lines. Not met on GitHub main, at lines 727, 728, 729, 730, and 734 (RV-42). Task T010 meets it.
- [ ] CHK008 Principle VII. Action logs before and after the shared export call. Not met on GitHub main, at lines 733 to 735 (RV-43). Task T011 meets it.

## Technology Constraints

- [x] CHK009 mistapi is the only interface. No direct HTTP request is added.
- [x] CHK010 Python 3.15 or newer. `pyproject.toml` line 23 (RV-15).
- [x] CHK011 Podman and the compose group. Not applicable. No container runs for this change.
- [x] CHK012 File paths. The change adds no path.
- [x] CHK013 Output backends. The change keeps the shared export call. The backend path is outside this record (U-6).
- [x] CHK014 Primary key strategy. The absent path writes no row. The latent gap for a future write path is analysis item A-3.

## Development Workflow

- [x] CHK015 Security findings. The change adds no suppression (D-7).
- [x] CHK016 Release note. The existing fragment stays unchanged, and no new fragment is needed (D-11).
- [x] CHK017 README. Not applicable. No menu, command, or operator behavior changes.
- [x] CHK018 Escalation to a spec. This record exists because the change touches three or more files.
- [x] CHK019 Branch from GitHub main. The follow-up branch is new (D-10).
- [x] CHK020 File overlap. Seven open pull requests touch none of the target files (RV-44).
- [ ] CHK021 Claim the issue with the `in-progress` label. Not met yet. Task T015 meets it before the branch exists.
- [ ] CHK022 Automated tests for each requirement. Not met for FR-005, FR-008, and FR-009. Each one is verified by review of the diff, as the coverage table in `analysis.md` states.

## Notes

- Checked items name the evidence in the research and the tasks.
- Unchecked items name the task that meets each rule. Principles VI and VII fail on GitHub main today.
