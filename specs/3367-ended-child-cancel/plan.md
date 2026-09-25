# Implementation Plan: Send no cancel request to a child job that already ended

**Issue**: #3367 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Technical context

- Python 3.13, Flask, Jinja templates, and the portal page script.
- The service `AggregateUpgradeService` owns each child cancel. The method
  `_cancellation_result` already returns a result with no cloud call for a
  child job with no upgrade identifier.
- The module `org_cancel_outcomes.py` builds the rows of the cancel outcome
  panel. The class `OrgCancelText` builds the Cancellation cell (issue #3225).
- No schema change. The stored cancel result gets one new status word,
  `already_ended`, and one new field, `state`.

## Changes

1. `src/firmware/aggregate_upgrade_service.py`
   - Add `ENDED_CHILD_STATUS = "already_ended"` and `ENDED_CHILD_TEXT`.
   - In `_cancellation_result`, keep the identifier check first. Then, if the
     stored child state is in `FINAL_CHILD_STATES`, return the ended result
     with no cloud call.
2. `src/upgrade_portal/upgrade/org_cancel_outcomes.py`
   - Add `ENDED_NOTE`.
   - `OrgCancelLists.lists` returns three empty lists and `ENDED_NOTE` for a
     result with the status `already_ended`.
   - `OrgCancelOutcomes._row` adds the boolean `ended`.
3. `src/upgrade_portal/app/assets/templates/upgrade/org_progress.html`
   - Show the three lists only when `outcome.ended` is false.
4. Tests
   - `tests/unit/firmware/test_aggregate_upgrade_service.py`: the mixed test
     now proves no access point cancel call for the completed child job.
   - `tests/unit/firmware/test_aggregate_ended_child_cancel.py` (new).
   - `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`: the ended row.
   - `tests/contract/upgrade_portal/test_org_cancel_outcomes_routes.py`: the
     rendered panel and the Cancellation cell of an ended child job.
   - `tests/e2e/upgrade_portal/org_cancel_seeds.py` and `conftest.py`: one
     more seeded operation with a completed access point child job.
   - `tests/e2e/upgrade_portal/test_org_cancel_outcomes_journey.py`: the new
     journey.
5. `documentation/upgrade_capture_portal.md` and
   `changelog.d/issue-3367-ended-child-cancel.md`.

## Risks

- A stored state can lag the cloud by one poll interval. The spec records
  this limit, and the single-site stop has the same limit.
- The row of the outcome panel gets a new key. The unit test that compares a
  full row changes with it.
