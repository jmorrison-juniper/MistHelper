# Feature Specification: Refuse a multi-site job view that another browser started

**Issue**: #3241
**Feature Branch**: `fix/3241-org-job-owner-check`
**Status**: Implemented
**Found by**: the multi-site journey explorer of #3200

## Problem

`job_page` and `upgrade_status` read the owned aggregate operation first. When
no owned operation matched the identifier, both fell back to the AP-only path,
which read the cloud job of any identifier. The page then rendered the job with
an armed cancel form. The cancel route already refused such a job through
`_owns_org_job`.

## User Story (P2): An operator sees only the jobs that the session started

**Acceptance scenarios**:

1. **Given** a job identifier that the signed session marker does not name,
   **When** the operator opens the job page or the status poll, **Then** the
   portal answers 409 `org_upgrade_job_not_owned` and reads no cloud job.
2. **Given** a job that the session started, **When** the operator opens the
   page, **Then** the page renders as before.

## Requirements

- **FR-001**: The job page and the status poll MUST apply `_owns_org_job`
  before the AP-only cloud read.
- **FR-002**: The refusal MUST match the cancel route: 409 and the code
  `org_upgrade_job_not_owned`.
- **FR-003**: An owned aggregate operation MUST keep its current path.

## Non-goals

- The portal answers JSON for every error today. An HTML error page for a
  browser belongs to a separate issue.
