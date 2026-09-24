# Tasks: Refuse a multi-site job view that another browser started

**Issue**: #3241 | **Plan**: [plan.md](plan.md)

- [x] T001 Add `_unowned_job_refusal` and call it in `job_page` and `upgrade_status`.
- [x] T002 Contract test for both paths, with no cloud read.
- [x] T003 Set the owned marker in the existing status test.
- [x] T004 Guard proof: the new tests fail on the old code.
- [ ] T005 Remove the strict xfail of #3241 from the journeys of #3200 after this change merges.
