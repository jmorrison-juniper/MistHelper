# Research: The capture walk ends each run that it builds

**Issue**: #3511

## R1. The source of the leftover run

**Decision**: The walk and the refusal test record each run key, and the teardown ends each live run.

**Evidence**:

- `test_capture.py`: the fixture `walking_page` yields the page, and then it calls `_release_the_site(page)` only. That helper clicks `lock-release-button`, and it never fails.
- The walk reads `run_id` from the options address, and then it reports a skip at "The options page offered no version" (#3380). The run stays in the state `created`.
- The refusal test accepts 201 or 409 for its first create call. After a 201, it records no run key.
- `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`: `live_run_at_site` reads `site_run_records`, and it returns the first row for which `run_is_live` is true. `run_is_live` reads `RunStateMachine.read_state`. A `RunTransitionError` means not live. Any state outside `RunStateMachine.TERMINAL` is live.
- A cancel moves a `created` run to `cancelled`, which is a final state.

**Alternatives rejected**:

- A release of the site lock alone. The live run, and not the lock, causes the 409.
- A new seed site for the walk. The walk must use the first row of the picker, because SC-018 asks for a walk by clicks alone.

## R2. The source of the check

**Decision**: The check reads `GET /api/sites/<site_id>/runs/history` for each site of the picker.

**Evidence**:

- `review.py`: the route `run_history` has `@identity.require_session`. FR-032 keeps it free of the site lock. It answers `{"runs": [...], "total": N}` with the raw rows.
- The refusal reads `run_store().runs_for_site(site_id)`. The history reads `run_lister()`.
- `tests/support/upgrade_portal_e2e/__init__.py`: the test portal binds `run_store` and `run_lister` to the same `PortalRecordStore`.
- `PortalRecordStore.runs_for_site` keeps each row whose top-level `site_id` matches. `PortalRecordStore.list_runs` also skips each row with an `operation_id`.
- A multi-site operation record holds `site_ids` and no top-level `site_id`. The seed `OrgControlSeeds.operation` shows that shape. So `runs_for_site` never reads an operation record, and the two readers agree on each row that can block a create.

**Alternatives rejected**:

- A create call as a probe. A 201 builds a run, so the probe would change the state that it measures.
- A read of the store from the test process. The store lives in the process of the test portal.

## R3. The paging rule

**Decision**: The reader asks for 200 rows for each page. It reads the next page while a page is full, and it stops at a bound of 50 pages.

**Evidence**:

- `review.py`: `LARGEST_HISTORY_LIMIT = 200` and `LARGEST_HISTORY_OFFSET = 1_000_000`.
- `read_store_page` reads `total` from the store page. If the page holds no `total`, it reports the length of the page.
- `PortalRecordStore.list_runs` returns a plain list. So the test portal reports the page length as `total`, and a reader that stops at `total` would miss each row after the first page.

## R3a. The live rule of the check

**Decision**: `LiveRun.from_row` calls the portal helper `run_is_live` itself.

**Evidence**:

- `run_is_live` is a module function of `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`. The refusal helper `live_run_at_site` calls it for each row.
- The e2e conftest already imports that module, and 15 other test files import it too.

**Alternatives rejected**:

- A copy of the rule with `RunStateMachine.read_state` and `RunStateMachine.TERMINAL`. A copy can drift from the portal, and FR-005 then fails with no signal.

## R4. The baseline of the first module

**Decision**: The scan before the first module is empty.

**Evidence**:

- The seeds write on a background thread when the child starts (`_seed_fixture_runs`).
- The seeds on a site of the picker are final. The failed seed and the stopped seed sit on site `2222`. Every live seed sits on a site that the picker does not list, which is the rule of #3507.
- So a live seed on a site of the picker fails the first module, and the message names the seed run. That failure is correct, because such a seed blocks a create.

## R5. The client of the check

**Decision**: The reader sends each read with `urllib`, through an opener with no proxy, to the loopback address of the test portal. It sends the two session cookies of the first stand-in operator.

**Evidence**:

- The conftest holds no HTTP client. It probes the port with `socket` only.
- `urllib` reads the proxy variables of the environment. A proxy on a work machine must not see a loopback read.
- `operator_session_cookies` builds the signed session cookie and the `browser_id` cookie. `identity.current_session` needs both.
- Bandit excludes `tests/`, and the address is the fixed loopback address of the run.

## R6. The home of the page teardown

**Decision**: A new helper `_end_the_walk_runs(page, ledger)` in `test_capture.py` reads the token of the page and calls `SiteRelease.end_runs`. This is the form of `_free_the_site` in `test_existing.py`.

**Evidence**:

- `RunLedger` already holds five members: `RUN_FIELD`, `__init__`, `runs`, `record`, and `record_from_url`. A sixth member breaks the 5-item rule.
- `SiteRelease` already holds seven methods.
- The direct tests of `test_e2e_site_lock.py` already prove the cancel decision of `SiteRelease.end_runs`. One new direct test proves a ledger with a live run and a final run.
- The helper holds two new decisions only: an empty ledger sends no call, and a page with no token fails. The red and the green browser runs prove both.

**Alternatives rejected**:

- A new method `RunLedger.end_runs_on(page)`. It breaks the 5-item rule, and it adds a page type to a class that holds keys only.

## R6a. The order of the cancel and the release

**Decision**: The teardown cancels each live run first, and then it gives the site back.

**Evidence**:

- `cancel_run` calls `stop_lock_refusal`, which calls `lock_refusal`.
- `lock_refusal` refuses only when another operator holds the site, or when the lock store does not answer.
- So a cancel from the browser that holds the site passes. `SiteRelease.end_runs` and `SiteRelease.free_site` use the same order in `test_existing.py`.
- `layout.html` alone publishes `csrf-meta`. Each page of the walk extends the layout, so the page of the teardown holds the token.

## R7. The refusal test

**Decision**: The refusal test requires 201 for its first create call. It then checks that the refusal names its own run.

**Evidence**: After the fix of R1, no earlier module leaves a live run on the first site. A 409 on the first call then names a leak, and the module check of the leaking module names the same run.

## R8. The adoption of a live run on a 409 in other modules

**Decision**: This change keeps the 409 adoption paths of `test_existing.py`, `test_stop.py`, `test_upgrade.py`, `test_two_operators.py`, and `test_short_inventory_read.py`. The module check makes each leak visible. If the full run shows another leak, FR-009 applies.

**Evidence**: Each adoption path opens the run that the refusal names, as the portal instructs an operator. The fault of #3511 is the leak, and not the adoption. The module check fails the module that left the run.
