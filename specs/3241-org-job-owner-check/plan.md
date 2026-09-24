# Implementation Plan: Refuse a multi-site job view that another browser started

**Issue**: #3241 | **Spec**: [spec.md](spec.md)

## Design

1. Add `_unowned_job_refusal(upgrade_id, org_id)` to
   `src/upgrade_portal/app/routes/org_upgrade.py`. It returns None when
   `_owns_org_job` accepts the job, and the cancel-route envelope otherwise.
2. Call it in `job_page` and in `upgrade_status`, after the owned aggregate
   lookup and before the AP-only cloud read.

## Tests

- New contract test: both paths refuse an unowned job and read no cloud job.
- Changed contract test: the status test now sets the owned marker, as the
  cancel test already does.
- Two moved `is not None` assertions now check real values (ratchet, #3102).

## Risks

- A browser that lost its session cookie loses the view of its AP-only job. The
  multi-site aggregate path keeps its durable owner record, so it is not
  affected.
