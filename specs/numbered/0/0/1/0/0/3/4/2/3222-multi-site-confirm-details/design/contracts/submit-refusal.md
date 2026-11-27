# Contract: Submit Refusal for an Incomplete Plan

This contract covers the refusal that the submit route returns for a saved plan that fails a completeness rule. The route is `POST /api/org-upgrades`, handled by `submit_upgrade()` in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.

## Trigger

The refusal applies when all three conditions hold.

1. The stored options name an owned durable plan. The read occurs at line 2163.
2. The stored plan holds at least one child record.
3. The completeness rules of `data-model.md` fail for the plan.

## Position in the Route

The refusal runs after the owned plan read at line 2163. It runs before the pre-check gate, before the site locks, and before any submit call. The existing replay and claim checks run after it.

## Response

| Field | Value |
| - | - |
| HTTP status | 409, the existing `CONFLICT_STATUS` constant |
| Error code | `org_upgrade_plan_incomplete` |
| Message | The saved plan lacks a required detail. Save the options again before you confirm. |
| Body | The existing JSON error envelope produced by `json_error()` |

The message does not name a MAC address, a token, or a site identifier. The page shows those values in the missing-detail list.

## Side Effects

The refusal has no side effect.

- No record changes.
- No site lock is taken.
- No pre-check capture is read.
- No cloud call is made.
- No child job is created.

## Logging

- Before the decision: one info line. It states that the submit check starts for the plan.
- On refusal: one warning line. It reports the count of missing details only.
- The lines use ASCII only.

## Test Evidence

- Contract test C3 posts an incomplete saved plan and asserts the status, the code, and the absence of any upgrade service call.
- Contract test C5 posts a plan with no child record and asserts the existing AP-only path.
