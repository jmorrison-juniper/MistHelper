# Implementation Plan: The pre-check captures of a multi-site upgrade

**Issue**: #3243
**Spec**: [spec.md](./spec.md)

## Technical context

- Python 3.13, Flask 3, Jinja templates, and one browser script, `portal.js`.
- The view layer is `src/upgrade_portal/upgrade/`. It makes no cloud call and no write.
- The change adds no dependency, no environment variable, and no schema change. The operation record gains the list `pre_captures`. An older record without the list stays valid.
- The session is the signed cookie of Flask. The portal has no session on the server.

## The current behavior

1. `confirm_page` in `org_upgrade.py` renders `org_confirm.html`. The confirmation field is disabled only when the write gate is closed.
2. `submit_upgrade` applies the write gate, the replay guard, the typed word, and the operator address. It then loads the context, checks each site lock, and submits the durable plan.
3. `_acquire_operation_locks` refuses a lock of the same operator that names another run. A lock with no run counts as another run.
4. The capture route `start_capture` takes the site lock and stores one copy of the lock in the session cookie.
5. `store.latest_standalone_precheck` returns the whole capture document. The adopter keeps two fields of it.

## Measured facts that drive the design

- A lock record in the session costs 268 bytes of JSON. With a lock copy for each site, the session cookie holds 2775 bytes at 20 sites and 3920 bytes at 30 sites. A browser drops a cookie above 4096 bytes. The portal has no limit on the site count. The endpoint therefore keeps no lock copy in the session.
- The confirm page reads one pre-check for each site. The start route reads them again. The reader must return a small row, not a whole capture document.

## The design

### Part 1. The gate in the view layer

The new module `src/upgrade_portal/upgrade/org_precheck.py` holds three classes.

| Class and member | Purpose |
| - | - |
| `SitePrecheck` | One site: `site_id`, `site_name`, `capture_id`, and `tier`. The property `ready` is true when the capture identifier is not empty. |
| `SitePrecheck.stored()` | Return the entry of the list `pre_captures`. |
| `OrgPrecheckState` | The tuple of sites. The property `ready` is true when one or more sites exist and each site is ready. |
| `OrgPrecheckState.missing` | Return the sites that hold no capture. |
| `OrgPrecheckState.missing_names()` | Return the names of those sites, joined with a comma. |
| `OrgPrecheckState.stored()` | Return the list `pre_captures`. |
| `OrgPrecheckGate(reader)` | Hold the reader of one site. The reader returns the capture identifier and the tier. |
| `OrgPrecheckGate.read(site_ids, names)` | Return the state of the sites, in the order of the selection. A reader fault counts as a missing capture. |
| `OrgPrecheckGate.rows_of(record)` | Return the stored rows of one operation record for the progress page. |

### Part 2. The confirm page and the start route

`org_upgrade.py`:

1. `precheck_gate()` builds the gate from `upgrade_routes.precheck_adopter()` and `upgrade_routes.read_precheck_pair`. With no adopter, the gate has no reader, and each site counts as missing.
2. `confirm_page` reads the state and passes it to the template as `prechecks`.
3. `submit_upgrade` reads the state after `_load_submission_context`. If the state is not ready, the route answers 409 `pre_capture_missing` before any lock.
4. `_submit_aggregate` takes the state. After `_record_operator`, the new `_record_prechecks` stores the list with one compare-and-set write. The write happens while the operation is planned and holds no submission claim.
5. `_acquire_operation_locks` moves the choice for one site into `_operation_lock`. A lock of the same owner with no run goes to `_bind_precheck_lock`. That function calls `held.bound_to_run(operation_id)` and `lock.refresh_site_lock`. The refresh compares the token, so it works for a quiet lock too. A lock of the same owner that names another run still answers 409 `site_lock_wrong_run`.
6. `_aggregate_record_view` adds the field `prechecks` from `OrgPrecheckGate.rows_of`.

### Part 3. The endpoint

The new route module `src/upgrade_portal/app/routes/org_precheck.py` holds the blueprint `org_precheck_bp`. The factory registers it after `org_controls`.

| Function | Purpose |
| - | - |
| `start_site_precheck(site_id)` | The route. It applies the refusals of FR-010 in order, then calls `capture.launch_capture`. |
| `_precheck_scope(site_id)` | Return the organization and the site record, or the refusal. |
| `_precheck_lock_refusal(org_id, site_id)` | Read the lock and choose one of the three paths below. |
| `_own_lock_refusal(held, operation_id)` | Keep a lock of the operator with no run or with this run, without a renewal. Refuse a lock of another run. |
| `_take_free_lock(org_id, site_id, client)` | Take the lock of a free site with no run and no session copy. |

The route sends the body `{"role": "pre"}` to `launch_capture`. `build_job` then builds a job with no run and a new capture identifier.

### Part 4. The templates and the script

- `org_confirm.html` gains the card of FR-001 and FR-005. The confirmation field is disabled unless the write gate is open and the state is ready. The card holds the hint of FR-004 when the state is not ready.
- `org_progress.html` gains the card of FR-015.
- `portal.js` gains `initOrgPrecheckCard`. It reads the rows of the card and runs one capture at a time. It sends the POST through `fetchJson`, reads the status every 3 seconds, and paints the state of the row. When each capture verifies, it loads the page again. When one capture fails, it stops, shows the cause, and enables the buttons again.

### Part 5. The reader of the capture store

`_PRECHECK_QUERY` in `capture/store.py` ends in `RETURN KEEP(doc, ...)` with seven fields: `capture_id`, `site_id`, `role`, `run_id`, the state field, `tier`, and `started_at`. The single-site adopter reads two of them, so its behavior stays the same.

### Part 6. The browser harness

- `stand_in_capture_runner` in `tests/e2e/upgrade_portal/conftest.py` stores a verified capture document for a pre-check with no run. It stores the document only for a site other than the first stand-in site. The first site keeps its seeded captures. The single-site journeys, the history page, and the comparison picker then read the same records in any test order.
- The new helper `tests/e2e/upgrade_portal/org_precheck_steps.py` holds the class `OrgPrecheckSteps`. Each multi-site journey that starts an upgrade calls it before the typed word. If the gate is closed, the helper pushes "Take the missing pre-checks" and waits for the page to load again.
- The new journey `tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py` sorts before the other multi-site journeys that start an upgrade. It sees the second site with no capture, takes the capture, and starts the upgrade. It cancels at the end, so both sites go back for the later journeys.

## Performance

- Each load of the confirm page reads one small row for each site. Each start reads them again. The projection of Part 5 removes the device list and the client list from each read.
- The plan measures one read with the whole document and one read with the projection on the live store. The pull request states both numbers.
- A single query for all sites is a possible follow-up. The measured time decides whether the portal needs it.

## Risks

| Risk | Answer |
| - | - |
| A pre-check lock stays after the operator leaves the page. | The lock goes quiet after the cooldown of 300 seconds. Another operator can then take it with the word `CONFIRM`. The lock ends after 3600 seconds. |
| A capture of many sites takes longer than the lock life. | The start route takes a fresh lock for a site whose lock ended. |
| The store fails during the read. | The site counts as missing. The operator sees "None saved" and cannot start. |
| An older browser script posts the start with no card. | The start route refuses with 409 `pre_capture_missing`. |

## Test plan

- Unit: `tests/unit/upgrade_portal/test_org_precheck.py` covers each class of Part 1 and the projection of Part 5.
- Contract: `tests/contract/upgrade_portal/test_org_precheck_routes.py` covers the card, the gate, each refusal of the endpoint, the 202 answer, the lock bind, the stored list, and the progress card.
- Parity: `tests/contract/upgrade_portal/test_org_precheck_parity.py` proves that both modes refuse with `pre_capture_missing`.
- The four contract files that start a multi-site upgrade gain a stand-in adopter with a capture for each site.
- Browser: the journey of Part 6, with screenshots before and after the capture.
