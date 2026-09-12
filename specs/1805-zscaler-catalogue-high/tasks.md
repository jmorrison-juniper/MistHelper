# Tasks: Clear the Structural High-Severity Violations in zscaler_catalogue.py

**Spec**: `specs/1805-zscaler-catalogue-high/spec.md`
**Issue**: #1000

## Phase 1: Baseline

- [X] T001 Record the score, grade, and violation breakdown before the change.

## Phase 2: Structural fixes

- [X] T002 Extract `_stamp_observation_bag` from the closure in `_merge_observations_into_cenr`.
- [X] T003 Extract `_stamp_city_bags` for the per-city walk.
- [X] T004 Reduce `_merge_observations_into_cenr` to three delegating calls.
- [X] T005 Add `_MergeAccumulators` bundling the proxy set, VPN set, and by-city map.
- [X] T006 Thread the bundle through `_absorb_city_records`, taking it from 6 parameters to 4.
- [X] T007 Thread the bundle through `_walk_city_map`, taking it from 5 parameters to 3.
- [X] T008 Extract `_build_cenr_document` from `merge_clouds`.

## Phase 3: Comments

- [X] T009 Add inline comments to the import block and the module logger.

## Phase 4: Verification

- [X] T010 Confirm all three structural high-severity violations are gone.
- [X] T011 Confirm the compliance score rose.
- [X] T012 Run ruff, black, and mypy on the changed file.
- [X] T013 Run the zscaler and CENR tests.
- [X] T014 Run the full unit suite.
