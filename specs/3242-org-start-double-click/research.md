# Research: Close the multi-site Start button on the first click

**Issue**: #3242

## What the journey found

The journey of #3200 double-clicked Start on the multi-site confirm page. The
journey replaced the server answer with a fixed 409 refusal, so it counted the
requests of the browser. The browser sent two requests.

`sendOrgForm` and `initOrgUpgradeForms` in `portal.js` send every multi-site
form. Neither function closes a button. A refusal only calls
`showRequestError`, so the Start button and the typed word stay as they were.

The single-site pages close each start button while the request runs. For
example, `startUpgradeFromCapture` writes `button.disabled = true` before its
request, and `startUpgrade` does the same on the confirm page.

## How the server refuses a replay today

Two paths answer 409 `org_upgrade_already_submitted`.

1. The aggregate path. The saved options hold an `operation_id`. The
   aggregate service claims the parent record with a compare-and-set write. A
   second start raises `ValueError`, and `_send_aggregate` maps that error to
   the 409 answer. The service text is "This aggregate upgrade has an active
   submission claim." or "This aggregate upgrade has no untouched child."
2. The legacy access point path. The saved options hold no `operation_id`.
   `_submission_guard` reads the browser marker `org_upgrade_last_job`. The
   marker holds the cloud job identifier after a known answer. The marker
   holds no identifier after an unknown answer.

A third 409 answer uses the same code: "The confirmed aggregate plan no longer
matches." That answer names no started job, so it gets no link.

Neither 409 answer carries the identifier of the job. The page therefore
cannot link to the job, even after the script reads the answer.

## Decisions

### D1: Close the submit buttons and the typed-word fields only

The script closes each open submit button and each open typed-word field of
the form. It keeps a list of the controls that it closed, and it opens only
those controls again.

Rejected: close every control of the form. The options form hides the
controls of each device family that the operator did not select, and it
disables those controls. A later open step would then need to know which
controls the page closed for another reason.

### D2: A replay refusal keeps the form closed

A replay refusal means that this confirmation can never start a new job. The
script keeps the Start button and the field closed, and it clears the typed
word. A closed field also keeps the typed-word gate closed, because
`applyConfirmGate` keeps the button locked while its field is disabled.

Rejected: open the button again after each refusal. The operator can then
click again, and the server refuses each new try with the same answer.

### D3: The refusal carries `upgrade_id` and `next`

The two keys match the words that the portal already uses. The status answer
names the job in `upgrade_id`. A start answer names the next page in `next`.
`build_error_envelope` already accepts a `details` object.

### D4: The script accepts only a progress page of this portal

The script builds the link only when `next` matches
`^/upgrade/org/jobs/[A-Za-z0-9_-]+$`. A value from a damaged answer, a
`javascript:` value, or an address on another host then makes no link. The
script builds the anchor with `createElement`, and it writes the identifier
with `textContent`.

### D5: An unknown answer gets its own sentence

After an unknown cloud answer, the marker names no job. The old sentence said
that the request "already started an organization upgrade", but no code knows
that fact. The new sentence says that the answer is unknown, and it tells the
operator to reconcile the job history first. The 503 answer of the first
request uses the same cure.

### D6: The durable record decides the link, not the error text

The aggregate service raises `ValueError` for a replay. It also raises
`ValueError` from `check_write_session` when the cloud session can retry a
write. That second refusal starts no job. The route therefore reads the
durable record again after the refusal. The record shows a start when its
state is `submission_claimed`, or when a child left the `planned` state. Only
a start gets the link and the operator sentence. Any other refusal keeps the
service text.

The service text "This aggregate upgrade has no untouched child." uses words
that a junior engineer does not know. A start therefore gets the sentence
"This confirmed request already started a multi-site upgrade."

### D7: A restored page loads again

The browser can keep a page in its back-forward cache. The portal sends
`Cache-Control: no-store`, and most browsers then keep no copy. A browser can
still restore the page, and the restored page keeps a closed Review button. The
script listens for the `pageshow` event. If the event reports a restored page
and a form of the page sent a request, the script loads the page again.

## Residual risk

The legacy access point path keeps its guard in the signed session cookie. Two
requests that leave the browser at the same moment carry the same cookie, so
both requests pass the guard. The current page sends the family list, so the
current page never uses this path. A script or an old page can still use it.
A separate issue tracks this risk.

## Performance

The change adds no request and no store read. The close step visits the
controls of one form, and a form holds fewer than 30 controls. The refusal
builds one dictionary with two keys.
