# Tasks: Keep a running multi-site job active

**Issue**: #3220 | **Plan**: [plan.md](plan.md)

- [x] T001 Add the cloud word sets and `_child_state` in `src/firmware/aggregate_upgrade_service.py`.
- [x] T002 Apply `_child_state` and keep `cloud_status` in `_read_org_child` and `_read_device_child`.
- [x] T003 Use `CLOUD_RUNNING_WORDS` in `_combined_site_status`.
- [x] T004 Add `FINAL_WRITE_STATES` and read each child in `_operation_is_settled` (`src/upgrade_portal/app/routes/org_upgrade.py`).
- [x] T005 Add `cloud_status` to `_aggregate_child_summary`.
- [x] T006 Show the cloud word in `org_progress.html` and in `paintOrgUpgradeSites` of `portal.js`.
- [x] T007 Keep the poll for `attention_required` in `portal.js`.
- [x] T008 Unit tests: each running word, each final word, an unknown word, a re-read after `upgrading`, and an invalid answer (`tests/unit/firmware/test_aggregate_upgrade_service.py`).
- [x] T009 Unit tests: the lock release rule (`tests/unit/upgrade_portal/test_org_upgrade_lock_release.py`).
- [x] T010 Contract test: a cancel keeps the locks until every child is final (`tests/contract/upgrade_portal/test_org_upgrade_routes.py`).
- [x] T011 Guard proof: the new tests fail on the old code (26 failed) and pass on the new code.
- [ ] T012 Remove the strict xfail markers of #3220 from the journeys of #3200 after this change merges.
