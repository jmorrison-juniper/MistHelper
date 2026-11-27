# Verification Checklist: Site export write results

**Purpose**: Record the evidence that each verification step needs.

**Created**: 2026-11-26

**Feature**: [Site export write results](../../spec.md)

## Remote Evidence

- [x] Blob SHAs for the three owned paths are recorded. See `design/research.md` rows 1 to 3.
- [x] Menu handler lines on `main` are recorded. See rows 5 and 6.
- [x] The CI rollup for PR #4847 is read. Each gate check outside the auto-merge and close-linked jobs is SUCCESS. See E-34a and E-35.
- [x] The latest commit on each owned path is `db06604d18`. See row 29.

## Local Evidence

- [x] Local HEAD equals the remote `main` commit for the cited files. See the Local Evidence section.
- [ ] The offline harness output is recorded. Explained: task T010 has not run.
- [ ] The route check output under `pwsh` is recorded. Explained: task T011 has not run.
- [ ] The comment scan output is recorded. Explained: tasks T007 to T009 have not run.
- [ ] The local gate outputs are recorded in the pull request body. Explained: task T-LOCAL-GATES has not run.

## Documentation Evidence

- [x] The operator guide line 120 is read. See row 8.
- [x] The menu reference rows for menus 213 and 214 are read. See row 9.
- [x] The changelog guard is reviewed. See row 22.
