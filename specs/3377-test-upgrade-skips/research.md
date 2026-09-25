# Research: The single-site upgrade journey measures every step

**Issue**: #3377 | **Spec**: [spec.md](spec.md)

## Decision 1: The stand-in view answers the shipped shape

**Evidence**: a direct call on the base commit gave this result.

```text
stand-in keys: ['targets', 'versions_by_model']
row targets: [('ap', '0.15.1'), ('gateway', '0.15.1'), ('switch', '0.15.1')]
shipped selector: {'ap': ['0.15.1', '0.14.29216'], 'switch': ['0.15.1', '0.14.29216'], 'gateway': ['0.15.1', '0.14.29216']}
```

- The shipped `build_options_view` in `src/upgrade_portal/upgrade/options.py`
  calls `TypedVersionSelector().select(...)`. It passes the selections to
  `build_version_options` and answers `type_selections`.
- `options_view` in `src/upgrade_portal/app/routes/upgrade.py` reads
  `type_selections` from the seam answer. A missing field reads as `{}`.
- `options.html` draws each type control from the `candidates` of its
  selection. An empty map gives each control the empty prompt only.
- `_chose_one_version_for_every_device` in `test_upgrade.py` then finds no
  second option, and `_saved_options` answers False before the save click.

**Decision**: one helper in `conftest.py` builds the view of a device list with
the two shipped helpers in the shipped order. The single-site stand-in and the
multi-site stand-in both call it. The multi-site route ignores the new field,
so its pages do not change.

**Alternative rejected**: write a fixed `type_selections` map in the stand-in.
A fixed map proves a shape that only the test file builds.

## Decision 2: The journey owns a third stand-in site

**Evidence**:

- The create route checks the site lock and the live run rule of FR-037 only.
  It does not read the site list.
- `live_run_at_site` counts every run that has not reached a final state. Two
  seeds hold the first site: `e2e-stale-precloud-0001` in
  `awaiting_confirmation` and `e2e-stale-stopping-0001` in `stopping`.
- The seed thread writes after the server binds its port. An early test can
  therefore get 201 on the first site, and a later test gets 409. The result
  depends on the test order.
- The capture route calls `permitted_site`, which calls `find_site`. That
  reader and the site picker both read `listOrgSites`. A site that the capture
  route accepts is therefore a row of the picker.
- The seeded sites `PREPARED_SITE_ID` and `START_READY_SITE_ID` do not appear
  in `listOrgSites`. Their runs carry a seeded pre-check, so no capture call
  reads the site list. The journey takes a real capture, so it needs a listed
  site.

**Search for a test that a third row can break**:

- Every module that reads the picker rows reads the first row only:
  `test_stop.py`, `test_two_operators.py`, `test_history.py`,
  `test_site_selection.py`, `test_narrow_action_cells.py`, and
  `test_browser_token_signin.py`.
- Every multi-site journey checks each site control by its identifier. No
  journey selects every row.
- No test counts the site rows, the site controls, or a site total.
- The picker keeps the cloud order. The new site is the last entry, so the
  first row does not change.

**Decision**: add `JOURNEY_SITE_ID` and `JOURNEY_SITE_NAME` to `conftest.py`,
and list the site third in `listOrgSites` and `listOrgSiteStats`.

**Alternatives rejected**:

- Use `SECOND_SITE_ID`. The multi-site journeys write runs on that site, so the
  same order problem returns.
- Move the stale seeds to their own site. The multi-site journeys still write
  runs on the first site.

## Decision 3: The module reuses its own run

**Evidence**:

- The `run_id` fixture has the function scope. The first test of the module
  gets 201 on the journey site. Each later test gets 409, and the refusal
  names the first run.
- `save_options` accepts a new save in every state. `prepare_confirmation`
  moves a run from `created` to `awaiting_confirmation` when the run holds a
  plan and a pre-check. A repeated save keeps the stage.
- `capture_conflict` refuses a capture when another operator holds the site,
  or when the run already started. The journey run never starts, so each
  confirm test can take a new pre-check capture.
- pytest collects the files and the folders of one folder in name order.
  `test_upgrade.py` is the last module of the folder. The project installs no
  random order plugin and no parallel worker plugin.

**Decision**: keep the 409 path of the fixture. A 409 on the journey site names
a run of this module only.

## Decision 4: A broken step fails

**Evidence**: the module states its own rule. A portal that a browser test
cannot reach never reports a pass. The fixture starts its own portal and its
own stand-in cloud, so a plan that does not save is a fault of that portal.

**Decision**: the save helper, the capture helper, and the three tests fail
with the cause. The helper that reads the target table also fails when the
table is empty. The skip for a missing browser binary stays, because it
describes the workstation.

## Decision 5: Each confirm test frees the site at the end

**Evidence**: the first green attempt gave 8 passed and 6 errors in 202
seconds.

- The first confirm test passed. Each later confirm test and each progress
  test stopped in the save helper. The save control rendered `disabled` with
  `data-needs-lock`, and the click waited 30 seconds.

- The pre-check capture takes the site lock. `take_site_lock` in
  `src/upgrade_portal/app/routes/capture.py` stores the lock record in the
  signed session of the browser that sent the call.

- A lock names one operator and one browser. `LockRecord.held_by` in
  `src/upgrade_portal/runtime/lock.py` compares both halves. Each test of the
  module opens a new browser context, so a later test is a second browser of
  the same operator.

- `lock_banner_context` in `src/upgrade_portal/app/routes/select.py` reads
  `held` only when the session of this browser stores the token. Every other
  holder reads as `locked`, and issue #2200 turns the save control off.

- FR-080 lets the same operator take the site back from a second browser only
  after the first browser goes quiet. The lock module refuses that request
  while the first browser is live. The page therefore obeys the design.

- The release route `DELETE /api/sites/<site_id>/lock` compares the token in
  the request body with the session copy. The first draft of the release sent
  no body. The route then answered `lock_lost`, and the draft accepted that
  answer in silence. The second draft reads the token from the lock banner of
  the options page, as `releaseSiteLock` in `portal.js` does. The confirm page
  shows no lock banner.

**Decision**: the `confirm_page` fixture registers a release step before the
pre-check capture. The step opens the options page, reads `data-lock-token`
from the lock banner, and sends the release with that token. An empty token
means that the browser took no lock. A refusal of a real token fails the test.

**Result**: the module gave 14 passed, 0 skipped, and 0 errors in 23 seconds.

**Alternatives rejected**:

- Take the site back in each test with the word `continue`. The lock module
  refuses that word while the first browser is live, and a real wait lasts 5
  minutes.

- Share one browser context across the module. The sign-in seam signs one
  context for each test, and a shared context would change every fixture of
  the module.

## Decision 6: The screenshots found a new defect

The new type control test and the unlocked confirm test now save a full-page
screenshot under `tmp_path`. The options page screenshot shows the text `None`
under each type control. `TypedVersionSelector.select` writes `"warning":
None`, and `options.html` prints `selection.get('warning', <default>)`. Issue
#3381 holds the defect, because it is a product change outside this issue.

## Decision 7: Each journey test compares a real value

The test quality gate reported 7 new findings on the first run. Six findings
were old entries of the baseline. The baseline keys each entry by its line
number, so the new lines above them moved six old findings to new numbers. The
detector counts an `assert` statement, a mock `assert_` call, or
`pytest.raises`. The detector does not count a Playwright `expect` call. The
seventh finding was a bare truthiness check on the device rows of the progress
page.

**Decision**: add one comparison to each of the seven tests. Each comparison
reads a value that the "Why" of the test names. Examples are the count of
target rows, the count of checked choices in each radio group, the count of
warning lines, the empty confirm field, and the bare `disabled` attribute.

**Result**: the gate reported 0 findings, and the module gave 14 passed.

**Alternatives rejected**:

- Refresh the baseline entries of the file. That step hides six weak tests
  again, and the next edit above them moves them again.
