# Research: Take a post-check capture of each site of a multi-site upgrade

**Issue**: #3244 | **Spec**: [spec.md](spec.md)

## Decision 1: The post-check capture names no run

**Decision**: Each post-check capture is a capture with no run. Its key is
`cap-<nonce>-02`, its ordinal is 2, its role is `post`, and its `run_id` is
empty text.

**Rationale**: The capture page reads `run_id` from the stored capture. If
the capture names a run, the page offers the button "Continue the retry" with
`data-run-id` set to that key. The function `startUpgradeFromCapture` of
`portal.js` then opens `/runs/<key>/options`. That page is the single-site
options page. An operation key there would open a page that cannot work.

**Rejected option**: A capture that names the operation key. The reason is
the page hazard above.

**Evidence**:

- `collector.capture_identity` keeps the ordinal of a job with no run.
- `assembly.role_for_ordinal(2)` returns `post`.
- The pre-check query `_PRECHECK_QUERY` reads the role `pre` only. The gate
  of #3243 therefore never adopts a post-check capture as a baseline.
- `capture.record_status` attaches a verified capture to a run only for the
  role `pre`. A post-check capture changes no run record.

## Decision 2: One site at a time

**Decision**: The stage takes the captures one site at a time, in the order
of the site selection.

**Rationale**: One capture reads the whole site through many API calls. One
API token serves every operator and every agent. Two captures at the same
time would double the rate of calls.

## Decision 3: A stop takes the captures too

**Decision**: A cancel during the start wait and a cancel during a phase both
run the stage before the stopped state.

**Rationale**: The single-site driver calls `_stop` only in its phase loop,
after the cloud accepted the write. Its `_stop` takes the post-check capture
(FR-038g). The multi-site walk starts only after the cloud accepted a child
job. So each multi-site stop sits at the same point of the flow.

## Decision 4: A site with no accepted write gets no capture

**Decision**: If the cloud accepted no child job that holds a device of a
site, the stage writes the row state `skipped` for that site.

**Rationale**: A single-site run whose write the cloud refused fails before
its phase loop, so it takes no post-check capture. The skip also saves the
API calls of a capture that can show no change.

The access point child job has the organization scope. Its target rows carry
the `site_id` of each device. The stage reads the site of each target row of
each accepted child job.

## Decision 5: The bridge opens the progress record

**Decision**: The new bridge opens the progress record of each capture. It
runs the runner inside a fresh application context through
`capture.worker_body`. It reads the verdict from the progress record, or from
the stored capture when the progress store dropped the record.

**Rationale**: The capture page then shows the live progress of each
post-check capture. The single-site `CaptureBridge` opens no progress record
and pushes no context. That gap is part of #3355, and this change does not
copy it.

## Decision 6: The site locks stay unchanged

**Decision**: The stage takes no site lock and renews no site lock.

**Rationale**: The capture contract allows a capture with no lock. Issue
#3333 holds the renewal of the multi-site locks. A comment on #3333 records
the new rule: when the cascade thread renews the locks, the release must wait
until the stage ends.

## Decision 7: The manual mode holds each capture

**Decision**: If `CAPTURE_POST_CHECK_MODE` reads `manual`, the stage takes no
capture and writes the row state `held`.

**Rationale**: The single-site driver marks the run with
`post_capture_pending` in the manual mode, and no page reads that mark. The
multi-site row states the hold in one sentence, so the operator knows why no
comparison exists.
