# Feature Specification: Answer an unknown run ID with a 404 error page

**Issue**: #3276
**Feature Branch**: `fix/3276-unknown-run-page`
**Status**: Implemented
**Found by**: the cross-cut journey of #3200, screenshot `missing-run-error-page-01-missing-run.png`

## Problem

The portal shows three pages for one run: the run page `/runs/<run_id>`, the
options page `/runs/<run_id>/options`, and the confirmation page
`/runs/<run_id>/confirm`. Each page read `load_run(run_id) or {}`. So an
unknown run ID rendered an empty page with status 200.

An operator who opens a mistyped link then reads an "Upgrade run" page with
no devices and no phases. The page looks like a real run that holds nothing.
The operator cannot tell a mistyped link from a run that failed.

The portal has the shared template `error.html`, but no route renders it.
Every error handler answers the JSON envelope (#3274).

## User Story (P3): An operator learns that a run link is wrong

**Acceptance scenarios**:

1. **Given** a signed-in operator, **When** the operator opens
   `/runs/not-a-real-run`, **Then** the portal answers status 404 with an
   HTML error page.
2. **Given** that error page, **When** the operator reads it, **Then** the page
   names the run ID `not-a-real-run`, shows the error code `run_not_found`, and
   gives a link to the site list.
3. **Given** an unknown run ID, **When** the operator opens the options page
   or the confirmation page of that ID, **Then** the portal answers the same
   404 page.
4. **Given** a run that the store holds, **When** the operator opens any of the
   three pages, **Then** the portal answers status 200 with the same page as
   before.

## Requirements

- **FR-001**: The run page, the options page, and the confirmation page MUST
  answer status 404 with `error.html` when the store holds no run with the ID.
- **FR-002**: The error page MUST name the run ID, the status code, and the
  error code `run_not_found`. The page MUST link to the site list.
- **FR-003**: The error page MUST show no control that writes to a run. No
  version picker, no start control, and no stop control can appear.
- **FR-004**: Jinja MUST escape the run ID. A run ID that holds markup must
  show as text.
- **FR-005**: A known run MUST keep status 200 and its current page.
- **FR-006**: One shared builder MUST render `error.html`, so #3275 and #3274
  can reuse it for the CSRF refusal and for an unknown URL.
- **FR-007**: The log line for an unknown run MUST hold ASCII only. It passes
  the run ID through `ascii()`, so a line break in the path cannot write a
  second log line.

## Non-goals

- The JSON answer of an API path. `run_not_found()` still answers the JSON
  envelope for every `/api/runs/...` path.
- The error handler for an unknown URL. Issue #3274 holds that change.
- The CSRF refusal page. Issue #3275 holds that change.
