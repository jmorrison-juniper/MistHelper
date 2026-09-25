# Implementation Plan: Take a post-check capture of each site of a multi-site upgrade

**Issue**: #3244 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The phase watch thread of #3245 gets one more stage. After the last phase
ends, or after a cancel, the stage takes one capture of each site with no run
and with the ordinal 2. The operation record keeps one row for each site. The
progress page and the status poll show each row, with a link to the capture
and a link to the comparison.

## Technical context

- Python 3.13, Flask 3.1, and Jinja with autoescape.
- The walk runs in one daemon thread for each operation. It writes the record
  through `OrgPhaseStore`, a bounded compare-and-set with five tries.
- The capture route owns the progress store, the runner seam, and the key
  builder. The new bridge reuses them, so a post-check capture follows the
  same path as a capture that the operator starts.
- `routes/capture.py` imports `select` and `upgrade`, and not `org_upgrade`.
  So `org_upgrade` can import the new bridge with no import cycle.

## Design

### 1. `src/upgrade_portal/upgrade/org_postcheck.py` (new, pure)

- `POSTCHECK_FIELD = "post_captures"`, the five row states, and the sentences.
- `PostCheckSite`: the site, the site name, the tier, and a flag for an
  accepted write. `row()` builds a stored row, and `ended_row(result)` builds
  the final row of one capture.
- `PostCheckResult`: the capture key, the verdict, and one sentence.
- `PostCheckTaker`: the protocol of the bridge. It has `mode`,
  `new_capture_id()`, and `take(site, capture_id)`.
- `OrgPostCheckRows`: `sites_of`, `of`, `stored`, `put`, and `first_failure`.
  These read the sites of a record, read and write the rows, and name the first
  failed capture.

### 2. `src/upgrade_portal/upgrade/org_postcheck_view.py` (new, pure)

- `OrgPostCheckView.rows(record, active)` returns one row for each site with
  the state, the label, the sentence, the capture link, and the comparison
  link. The caller passes `active` from the phase view, so the two cards agree.
- A site with no stored row reads "Waiting" while the watch is active. It
  reads "Not taken" when the watch can no longer run.
- A row that holds `running` after the watch ended reads "Failed", because no
  thread takes that capture any more.

### 3. `src/upgrade_portal/upgrade/org_cascade/close.py` (new)

- `OrgPostCheckStage` writes the watch note, then takes each site in order.
  The stage is re-entrant. A final row stays, and a `running` row is taken
  again (FR-008).
- `OrgCascadeClose` owns the end of the watch:
  - `finish()` runs the stage, then writes the finished state. The reason is
    the first failed phase, or else the first failed capture.
  - `stop()` runs the stage, then writes the stopped state.
  - `end(record, state, note)` puts each waiting phase back to pending and
    writes the state. It is the old `OrgCascade._end`.

### 3a. `src/upgrade_portal/upgrade/org_cascade/walk.py`

- `OrgCascadeDeps` gets the field `post_check`, with the default None.
- `OrgCascade.run()` calls `finish()` and `stop()` in place of `_finish` and
  `_stop`. `OrgCascade.fail()` calls `OrgCascadeClose.end`.

### 4. `src/upgrade_portal/capture/assembly.py`

- `standalone_capture_key(ordinal=FIRST_ORDINAL)` gets the ordinal parameter.
  The default keeps every current caller unchanged.

### 5. `src/upgrade_portal/app/routes/org_postcheck.py` (new)

- `OrgPostCheckBridge.bind(operation, cloud_session)` runs inside the request.
  It keeps the bound method `current_app.app_context`, the runner of
  `capture.capture_runner()`, the mode of `read_post_check_mode()`, and the
  shared job fields.
- `take(site, capture_id)` builds the job with eleven fields. It opens the
  progress record and runs the runner through `capture.worker_body` inside a
  fresh context. Then it reads the verdict.
- Warning: the bridge holds the cloud session. No log line may hold the job or
  the bridge, because a log of either can leak the API token.

### 6. `src/upgrade_portal/app/routes/org_upgrade.py`

- `_bind_post_check(operation, cloud_session)` calls
  `OrgPostCheckBridge.bind`. If the bind raises, the guard logs a warning and
  returns None, so the watch still starts with no post-check stage (FR-011).
- `_start_phase_watch` passes `post_check=_bind_post_check(...)`.
- `_aggregate_record_view` builds the phase view one time. It adds the field
  `postchecks`, with `active` from that phase view.

### 7. The page

- `org_progress.html` includes the new partial `partials/org_postcheck_list.html`
  after the pre-check card.
- `portal.js` gets `paintOrgPostChecks(status)`. `paintOrgUpgradeStatus` calls
  it on each poll. The function writes text and link targets only.

### 8. The browser seams

- `stand_in_capture_runner` stores a capture with no run for the role `post`
  too, with the newer stand-in version.
- `ScriptedCascadeStarter` ends each phase as before. When every phase ended,
  or when the operator cancelled, it calls the production `OrgCascadeClose`.

## Test plan

| Test | Proves |
| - | - |
| `tests/unit/upgrade_portal/test_org_postcheck.py` | FR-003 to FR-011 and FR-018 for the stage and the rows. |
| `tests/unit/upgrade_portal/test_org_postcheck_view.py` | The view states, the labels, and the links of FR-012 and FR-013. |
| `tests/unit/upgrade_portal/test_org_cascade_close.py` | FR-001, FR-002, FR-011, and FR-015 through the walk. |
| `tests/unit/upgrade_portal/test_org_postcheck_bridge.py` | FR-003, FR-004, and FR-017 for the bridge. |
| `tests/unit/upgrade_portal/test_capture_standalone_key.py` | The key form with the ordinal 2. |
| `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` | FR-011 to FR-016 through the routes. The five new tests sit beside the phase watch tests, because they share the starter seam. |
| `tests/e2e/upgrade_portal/test_org_postcheck_journey.py` | The operator journey in a real browser, with screenshots. |

Guard proof: the new unit and contract tests fail on the old code, because no
stage, no field, and no card exist there.

## Risks

- The stage runs inside the watch thread. A capture takes minutes, so the
  finished state arrives later than before. The watch stays active, so the
  poll continues and the page shows each row.
- A portal restart during the stage leaves a row in `running`. The next poll
  starts a new walk, and the walk takes a new capture for that row (FR-008).
