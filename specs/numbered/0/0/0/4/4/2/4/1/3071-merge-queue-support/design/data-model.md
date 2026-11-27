# Data model: Merge queue rollout and acceptance

This record has no product data model. The entities below describe the workflow state and the rollout state. Each entity has a natural key, required fields, and validation rules.

## Entities

| Entity | Natural key | Fields | Validation |
| - | - | - | - |
| Queue candidate | The queue branch name, which starts with `gh-readonly-queue/main/pr-`, plus the pull request number and the candidate commit SHA | Pull request number, candidate commit SHA, queue branch name, state, and the result of each required context | Each required context reports on the candidate commit SHA. Checkouts use the event commit (R-06). |
| Required context | The workflow file and job ID for CI contexts. The application name for the `CodeQL` context. | Display name, reporting workflow, and conclusion | The display names match the 14 names that `tests/guardrails/test_ci_gate_triggers.py` pins (R-31). The `CodeQL` context is checked live only (U-3). |
| Serial merge slot | The single slot on `main` | Holder pull request number and status (free or held) | One holder at a time. Issue #3070 is closed, so the slot is free (R-57). |
| Activation evidence | The comment identifier on issue #3071 | Queue commit SHA, the conclusion of each required context, the merge commit SHA, the main run ID, and the recorded time in UTC in ISO 8601 form | Each field holds an observed value. No field holds an estimate. |
| Owner decision | The decision identifier in `design/research.md` | Decision text, the approval reference (an issue comment link), and the date | The approval reference links to an issue comment. |

## State transitions: owner activation

The rollout moves through these states in order.

1. `serial`: the serial merge slot is in use. This is the state on 2026-11-26.
2. `preparation_on_main`: the merge queue triggers are on `main`. PR #4362 reached this state on 2026-10-20 (R-48).
3. `review_rule_confirmed`: the owner confirms the review rule (owner step O-1).
4. `queue_active`: the owner enables "Require merge queue" on `main` (owner step O-3).
5. `candidate_1_verified`: the first verification candidate merges, with each required context successful (owner step O-4).
6. `candidate_2_verified`: the second verification candidate merges, with each required context successful (owner step O-5).
7. `serial_retired`: a documentation pull request retires the serial merge slot text (owner step O-6).
8. `issue_closed`: the owner closes issue #3071 after the evidence is recorded (owner step O-7).

The rollback transition goes from `queue_active` back to `serial`. The owner disables "Require merge queue" and keeps strict protection and the 15 required contexts (`plan.md`, rollback step 2).

## State transitions: queue candidate

1. `queued`: the pull request enters the merge queue.
2. `checks_requested`: GitHub starts a `merge_group` run on the queue branch (R-61, R-64).
3. `unresolved`: a required context reports canceled, timed out, stale, or skipped. The owner reads the result, and the candidate does not count as passed.
4. `passed`: every required context reports success.
5. `merged`: the candidate lands on `main`.
6. `removed`: a failing candidate leaves the queue (R-62). The author repairs the pull request and adds it to the queue again.
