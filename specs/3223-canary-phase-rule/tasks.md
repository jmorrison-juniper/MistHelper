# Tasks: One canary phase rule for both modes

**Issue**: #3223 | **Plan**: [plan.md](plan.md)

- [x] T001 Add `_PHASE_LOWEST` and `_check_phase_order` in `src/upgrade_portal/upgrade/options.py`.
- [x] T002 Call `_check_phase_order` in `_read_canary`.
- [x] T003 State the rule in the `canary_phases` help text.
- [x] T004 Contract test: four refused single-site bodies in `REFUSED_ADVANCED_BODIES` (`tests/contract/upgrade_portal/test_upgrade_options.py`).
- [x] T005 Contract test: the current multi-site body refuses four phase lists and builds no plan (`tests/contract/upgrade_portal/test_org_upgrade_routes.py`).
- [x] T006 Guard proof: 5 checks fail on the old code, and 83 tests pass on the new code.
- [ ] T007 Remove the strict xfail markers of #3223 from the journeys of #3200 after this change merges.
