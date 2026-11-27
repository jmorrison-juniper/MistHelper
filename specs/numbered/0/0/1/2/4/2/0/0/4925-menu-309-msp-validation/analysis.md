# Specification Analysis Report: Validate menu 309 with an MSP login

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-01 | medium | The 4920 contract wording for the 403 note differs from the code. The contract says the run continues with the organization of the credential. The code says the run uses one organization. | R-27, R-28, R-30, R-83 | Decision D-5. A follow-up issue owns the fix. |
| A-02 | low | The operator guide states that Mist refuses the requests after the session lifetime. No source states this. | R-33, R-62, R-87, U-02 | Task T009 removes the sentence. |
| A-03 | medium | 4920 FR-040 limits live validation to one organization. Issue #4925 asks for a run that covers every organization of an MSP login. | R-78, issue #4925 task 5 | The owner asks for the wider run in issue #4925. The spec records this exception in its clarifications. |
| A-04 | medium | The brief rule requires `Closes #4925` in the pull request body. Issue #4925 must stay open until task 5 passes. | Issue #4925 acceptance | Decision D-3. The pull request body uses `Refs #4925`. |
| A-05 | low | 4920 task T067 is still open on `main`, although the pull request merged. | R-82 | Unresolved item U-3. The owner or the orchestrator updates the task. |
| A-06 | medium | No automated test names the MSP sign-in section of the operator guide. | U-07 | Unresolved item U-6. The owner live check is the only proof of that section. |
| A-07 | low | The owner's estimate of about three requests per site has no source. | U-01 | The spec uses the threshold, not the estimate (FR-007). |
| A-08 | medium | Issue #4925 does not define "covers every organization". | Issue #4925 task 5 | Decision D-2. Step 2 lines define the rule. |
| A-09 | medium | Issue #4925 does not define the outcome row rule for a failure in step 4. | R-07, R-13 | Decision D-6. |
| A-10 | low | MSP scope needs at least one listed organization. An MSP login with no listed organization shows organization scope. | R-29 | Edge case in the spec. The owner records the cause. |
| A-11 | low | The handoff from the launcher to the portal is not re-read in this record. | U-05, R-81 | Task T012 checks the handoff live. |
| A-12 | low | The cloud choice prompt is not located in the login files that this record cites. | U-04 | The owner reads the prompt during the live check. |
| A-13 | low | The 4920 requirement FR-039 forbids a tight retry loop after HTTP 429. | R-77 | FR-007 and the risk table of the plan. |

## Coverage Summary

- FR-001 to FR-019 each map to at least one task and at least one test (traceability in `tasks.md`).
- SC-001 to SC-004 map to task T011 and task T012.
- SC-005 maps to task T001.
- SC-006 maps to tasks T001 to T008, which run before the owner starts.

## Constrained-Field Coverage

- The status values in `tasks.md` are `verified-present`, `partial`, and `open`. Tasks T001 to T008 are `verified-present`. Task T009 is `partial`. The others are `open`.
- The labels in decision D-7 exist in the repository label list: `in-progress`, `needs-human-review`, `chore`, `docs`, and `MistHelper.py`.

## Constitution Alignment

- `plan.md` has no FAIL result.
- Principle IV has one exception. The pull request keyword differs for this issue (decision D-3).

## Unmapped Tasks

None. Each task maps to at least one requirement in `tasks.md`.

## Metrics

- Requirements: 19.
- Success criteria: 6.
- Tasks: 16. Twelve are implementer or human tasks. Four are delivery tasks.
- Tests and gates: 14. Twelve run as automated tests or gates. Two are human-only.
- Remote checks: 93.
- Decisions: 8. One requires a human decision.
- Unverified items: 8.

## Unresolved Items

- U-1: The owner result for task 5 is open. The owner owns it.
- U-2: The follow-up issue for finding A-01 is not filed. The owner or the implementer files it. One issue holds one concern.
- U-3: The 4920 task T067 is open (finding A-05).
- U-4: The session lifetime behavior is unverified (findings A-02 and U-02, U-03, U-06).
- U-5: Issue #4936 stays out of scope.
- U-6: No automated guard covers the MSP sign-in section (finding A-06).
- Decision D-1 is marked HUMAN-DECISION-REQUIRED. It covers the use of a live credential.
