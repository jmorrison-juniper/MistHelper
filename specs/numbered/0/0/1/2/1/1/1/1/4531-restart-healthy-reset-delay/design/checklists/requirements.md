# Requirements Checklist: Restart healthy reset test repair

**Purpose**: Check the spec, plan, tasks, and research for completeness before the record moves into the repository.

**Created**: 2026-11-26

**Feature**: `spec.md` in the record folder

## Content quality

- [x] CHK001 The spec states the user problem and the affected test without implementation details beyond the named test IDs.
- [x] CHK002 Each user story has a priority, an independent test, and acceptance scenarios.
- [x] CHK003 All mandatory sections of the spec template are filled. The Mist transport section is omitted because no Mist API call is part of this issue (see Assumptions).

## Requirement completeness

- [x] CHK004 Each FR-### requirement uses MUST and names one testable behavior.
- [x] CHK005 Each FR-### requirement maps to at least one task in `tasks.md` and at least one test in the restart class.
- [x] CHK006 Success criteria SC-001 to SC-004 are measurable.
- [x] CHK007 Edge cases name the boundary, the stall, the clock exhaustion, and the environment mismatch.
- [x] CHK008 Out-of-scope items name the production script, the shared helper, the cache slice, the other failing test, and the defaults.

## Evidence and traceability

- [x] CHK009 The failing test ID, the baseline line 283, the assertion, and both tuples appear in `design/research.md`.
- [x] CHK010 The CI reproduction result is recorded. 167 failed runs were scanned, and 16 contain the restart test. No restart case failed.
- [x] CHK011 The legacy record search is recorded. No folder starts with 4531, so the record reuses nothing.
- [x] CHK012 Each code claim cites a path and a line range on main. Each remote check appears in the research table and in `remote_checks`.
- [x] CHK013 Each unverified claim appears in the Unverified list with a reason.

## Constitution and standards

- [x] CHK014 The plan checks all seven principles and the technology constraints.
- [x] CHK015 The Five-Item Rule violation of `TestSessionRestarts` is justified in the Complexity Tracking table, with remediation R-1.
- [x] CHK016 Principle IV steps 10 to 12 are recorded as not applicable, with a check in T-MERGE (decision D-6).
- [x] CHK017 The changelog decision names the reason (decision D-7).
- [x] CHK018 The writing rules hold: no semicolons, no contractions, no Latin abbreviations, and American spelling.

## Decisions and review

- [x] CHK019 Each decision names two or more alternatives, the chosen option, the reason, and the risk.
- [x] CHK020 No decision needs a human decision marker. The four categories in brief section 6 do not apply.
- [x] CHK021 The merge waits for a human review because of the `needs-human-review` label (decision D-9).
