# Specification Quality Checklist: Editor Import Diagnostics

**Purpose**: Check the specification, the plan, the tasks, and the research before the pull request.
**Created**: 2026-11-26
**Feature**: `spec.md` in this folder

- [x] CHK001 Every functional requirement from FR-001 to FR-017 has at least one task and one acceptance check. Source: `analysis.md` coverage summary.
- [x] CHK002 Every task names exact repository paths or the worktree root. Source: `tasks.md`.
- [x] CHK003 Every remote claim cites a ref, a blob SHA, and a line or the absence of a line. Source: `design/research.md` section 3.
- [x] CHK004 The route equals the route that the route script computes for issue 4126. Source: research rows R67 and R71.
- [x] CHK005 Each directory on the route holds five children or fewer. Source: research rows R72, R73, and the feature root count.
- [x] CHK006 No placeholder token appears in any record file. A placeholder token is a missing value, a deferred value, or an unfinished text marker.
- [x] CHK007 The remote check count matches in the status file, the research table, and the summary. Source: 91 rows.
- [x] CHK008 The decision count matches in the status file, the research file, and the summary. Source: 11 decisions.
- [x] CHK009 The pull request uses `Refs #4126`. The closure hold appears in decision D-6.
- [x] CHK010 The record names no credential, no environment variable value, and no user-profile path segment. Source: acceptance check AT-07 runs after the pull request body exists.
- [x] CHK011 Assumptions, out-of-scope items, and edge cases appear in `spec.md`.
- [ ] CHK012 The STE score of each changed file is 80 or above. Explanation: this agent does not run the STE linter (rule 2). Task T-LOCAL-GATES measures the score.
- [ ] CHK013 The live editor evidence exists for all 27 current paths. Explanation: the live check is blocked by a missing native permission (comment of 2026-10-31). Task T010 tracks it.
