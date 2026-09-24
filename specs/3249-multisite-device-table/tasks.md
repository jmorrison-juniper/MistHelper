# Tasks: Multi-site device table and version check

**Issue**: #3249

- [x] T001 Write the failing unit tests for `org_devices.py` and `org_versions.py`: the state order, the failure reason, the fallback rows, the version check, and the read budget.
- [x] T002 Write the failing unit tests for the service: the access point target records, `record_device_versions`, and the `updated_at` rule.
- [x] T003 Write the failing contract tests for the page, the poll answer, and the operator record.
- [x] T004 Save the red proof of T001 to T003.
- [x] T005 Add `src/upgrade_portal/upgrade/org_devices.py` for the rows and `src/upgrade_portal/upgrade/org_versions.py` for the reads.
- [x] T006 Change the aggregate service for D2, D3, and D4.
- [x] T007 Change the routes for the summary, the version refresh, and the operator record.
- [x] T008 Add the device table, the account, the address, and the age to `org_progress.html`.
- [x] T009 Add `paintOrgUpgradeDevices` and the age repaint to `portal.js`.
- [x] T010 Change the browser stand-ins, and extend the browser test.
- [x] T011 Run the gates: compile, ruff, black, mypy, the tests, the ratchet, and the STE linter.
- [x] T012 Take and read the browser screenshots of the multi-site progress page.
- [x] T013 Add the release note fragment `changelog.d/issue-3249-multisite-device-table.md`.
