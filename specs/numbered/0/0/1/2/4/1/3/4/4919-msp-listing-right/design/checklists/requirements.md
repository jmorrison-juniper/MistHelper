# Specification Quality Checklist: MSP organization list skipped without the listing right

## Content Quality

- [x] The spec names the user problem: the report sends a listing call that fails with HTTP 403.
- [x] The spec names the controlling privilege, the grant `scope` value `msp`, and cites the evidence in `design/research.md`.
- [x] The spec avoids the implementation detail that is not needed by a reader.
- [x] Each user story has a priority, an independent test, and acceptance scenarios.
- [x] The spec states its out-of-scope items in a Non-Goals section.

## Requirement Completeness

- [x] Each requirement uses MUST and has an ID from FR-001 to FR-014.
- [x] Each success criterion has a measurable check (SC-001 to SC-006).
- [x] Edge cases cover a missing `scope` key, duplicate MSP ids, a mixed MSP id, and an empty profile.
- [x] The role threshold is not decided. Item U1 explains the gap, and Decision D2 records the choice.
- [x] The live Mist behavior is not checked. Items U2 and U4 explain the gap.
- [x] Each assumption is listed in the Assumptions section.

## Feature Readiness

- [x] Each functional requirement maps to at least one task and at least one test (`analysis.md`, Consistency Review).
- [x] The success criteria can be checked by the tasks in `tasks.md`.
- [x] The spec names no change to the status file column set. Decision D4 records the reason.
- [x] The spec names the human decision D8 before any implementation starts.

## Notes

- Items that describe an unchecked live Mist behavior stay open in `design/research.md` as Unverified items U1, U2, U3, and U4. Each item states its reason.
- The unit tests cannot prove the live role threshold. The operator check in `design/quickstart.md` Scenario 5 records that proof when a token exists.
