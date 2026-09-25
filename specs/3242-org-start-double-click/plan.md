# Implementation Plan: Close the multi-site Start button on the first click

**Issue**: #3242 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The page script closes the submit buttons and the typed-word fields of each
multi-site form while the request of that form runs. The server refusal of a
repeated start names the job that started, and the page links to its progress
page. Any other refusal opens the closed controls again.

## Technical context

- Python 3.13, Flask 3.1, and the page script `portal.js` with no framework.
- `initOrgUpgradeForms` sends every form whose action starts with
  `/api/org-upgrades`. The Review form, the Start form, the start time form,
  the cancel form, the retry form, and the reconcile form all use it.
- `applyConfirmGate` keeps a button locked while its field is disabled.
- `build_error_envelope` in `factory.py` accepts a `details` object.

## Design

### 1. The server refusal: `OrgReplayRefusal` in `routes/org_upgrade.py`

- `answer(message, upgrade_id)` builds the 409 answer with the code
  `org_upgrade_already_submitted`. A known job adds
  `details = {"upgrade_id": id, "next": "/upgrade/org/jobs/<id>"}`.
- `legacy()` reads the browser marker. A marker that names a job keeps the old
  sentence and adds the link. A marker with no job gets the sentence about an
  unknown cloud answer.
- `aggregate(operation_id, error)` reads the durable record again after the
  service refusal. The record shows a start when its state is
  `submission_claimed`, or when a child left the `planned` state. A start gets
  the sentence "This confirmed request already started a multi-site upgrade."
  and the link. Any other refusal keeps the service text and gets no link.
- `_submission_guard` calls `legacy()`. `_send_aggregate` calls `aggregate()`.
  The refusal of a mismatched plan does not change.

### 2. The page script: `portal.js`

- `closeOrgForm(form)` records the form state `sending` in
  `data-org-form-state`. It closes each open submit button and each open
  typed-word field, and it returns the list of the closed controls.
- `openOrgForm(form, closed)` opens each control of that list, removes the
  state, and applies each typed-word gate of the form.
- `showOrgReplayRefusal(form, error)` keeps the form closed with the state
  `closed`, and it clears each typed word. It shows the sentence of the server.
  If `details.next` is a progress page path, it adds a link with the test
  identifier `org-upgrade-job-link`, and it moves the focus to the link.
- `sendOrgForm(form)` builds the body first, because a closed control leaves
  the form data. Then it closes the form and sends the body. A replay code
  calls `showOrgReplayRefusal`. Any other refusal opens the form and calls
  `showRequestError`.
- The submit handler ignores a form that holds a state.
- A `pageshow` event with `persisted` loads the page again when a form holds a
  state. The browser can restore a page from its back-forward cache, and the
  restored page would keep a closed Review button.

### 3. Tests

- Contract tests in `tests/contract/upgrade_portal/test_org_upgrade_routes.py`:
  - A legacy replay carries the job details.
  - A legacy replay after an unknown answer carries no details, and it names
    the unknown answer.
  - A durable replay carries the details of the operation.
  - A service refusal on an untouched plan carries no details.
- Browser journeys in `tests/e2e/upgrade_portal/test_org_start_double_click.py`:
  - A double click on Review, on Start, and on the cancel button sends one
    request each.
  - A start from a second tab gets the replay refusal and a working link.
  - A fault refusal opens the Start button again, and the next start works.
  - A restored page with a sent form loads again.

## Risks

- A closed field leaves the form data. The body therefore comes first.
- The link accepts only a relative path to a progress page. The script builds
  the link from nodes and writes the identifier as text.

## Performance

The change adds one store read to the refusal path of a durable replay. The
success path adds no request. The close step visits fewer than 30 controls.
