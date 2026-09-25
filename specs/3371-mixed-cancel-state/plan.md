# Implementation Plan: A cancel that stops part of the work makes the operation read cancelled

**Issue**: #3371 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Technical context

- Python 3.13 and the multi-site service `AggregateUpgradeService`.
- The method `_settled_state` maps the child states of a settled operation to
  one word. The method `_combined_site_status` maps the site states of an
  access point job to one word.
- No schema change, no route change, and no template change.

## Changes

1. `src/firmware/aggregate_upgrade_service.py`
   - Add the static helper `_final_word`. It returns `cancelled` if the set
     holds `cancelled`, and `completed` if it does not.
   - `_settled_state` and `_combined_site_status` call the helper.
2. Tests
   - `tests/unit/firmware/test_aggregate_mixed_cancel_state.py` (new): the word
     for each set, the path through the cancel and the status read, and the
     access point site mix.
   - `tests/e2e/upgrade_portal/org_ended_seeds.py`: one more seeded operation
     with its own child job identifiers.
   - `tests/e2e/upgrade_portal/test_org_mixed_cancel_state_journey.py` (new):
     the status card, the final note, and the history badge after the cancel.
3. `documentation/upgrade_capture_portal.md` and
   `changelog.d/issue-3371-mixed-cancel-state.md`.

## Risks

- An operation that a person cancelled in part in the Mist dashboard now reads
  `cancelled`. The spec records this result as correct.
- A reader that treats `completed` as the only success word now sees
  `cancelled` for a mixed operation. The research lists each reader, and each
  one treats both words as final.
