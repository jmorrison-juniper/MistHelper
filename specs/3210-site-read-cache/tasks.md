# Tasks: Reuse the organization site reads for one minute

**Issue**: #3210 | **Plan**: [plan.md](plan.md)

- [x] T001 Add `CloudReadCache` in `src/upgrade_portal/runtime/cloud_cache.py`.
- [x] T002 Use the cache in `select.default_cloud_read`, with log lines before and after the cloud read.
- [x] T003 Unit tests for the cache rules and for the reuse in `default_cloud_read` (`tests/unit/upgrade_portal/test_cloud_cache.py`).
- [x] T004 Guard proof: the reuse tests cannot pass on the old `select.py`.
- [ ] T005 Part 2 of #3210: one organization inventory read for the multi-site options page.
