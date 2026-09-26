# Research: A later site check names an incomplete site list

**Issue**: #3439 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Measured facts

### The site checks

- The function `find_site` in `src/upgrade_portal/app/routes/select.py` reads
  `listOrgSites` and returns the record of one site. It returns None when no
  record matches. It does not read the partial reasons of the answer.
- Four routes reach `find_site`. The inventory page calls it directly. The
  inventory answer calls it through `site_belongs_to_org`. The capture start
  and the pre-check start call it through `capture.permitted_site`.
- The function `upgrade.readable_site_name` also calls `find_site`. It catches
  each exception and keeps the site identifier. The run creation therefore
  needs no change.
- The function `selected_rows` in
  `src/upgrade_portal/app/routes/org_upgrade.py` reads `build_site_rows`. It
  returns an empty list when the list does not hold a selected site. Four
  steps call it: the options page, the options save, the confirm page, and the
  retry.
- The function `site_choice_refusal` reads `build_site_rows`. It answers 404
  `site_not_found` when the list does not hold a chosen site. The method
  `PickerRefusal.answer` sends a browser back to the site picker with a Caution
  message.

### The site read

- The flag `SiteList.sites_complete` is false when the site read lost a page.
  If the first page fails, the read holds no row and one partial reason. Issue
  #3438 added both rules.
- The function `default_cloud_read` keeps a whole read for 60 seconds. It never
  keeps a read that lost a page. After a lost page, a reload reads the cloud
  again.

### The state changes

- The route `save_options` maps `BadOptionError`, `TypeError`, `ValueError`,
  `OverflowError`, and `RuntimeError` to a 400 refusal. The helper
  `_aggregate_saved_options` calls `selected_rows` before it builds or stores
  the plan.
- A save request with no `selected_types` field makes no site check today.
  This change keeps that rule.
- The pre-check start calls `capture.permitted_site` before
  `PrecheckSiteLock.claim`. A refusal at the site check therefore takes no
  lock.
- The route `open_retry` calls `selected_rows` before `_open_retry_scope`. A
  refusal at the site check therefore changes no stored selection.

### The error answers

- The table `factory.ERROR_CODES` holds no 503 entry. The helpers `json_error`
  and `error_page` accept an explicit code and an explicit sentence.
- The handler `security.csrf_error_response` answers a page or an envelope. It
  reads `wants_browser_page` and `form_return_path`. The new handler uses the
  same rule.
- The shared error page always shows the link to the site list. It shows the
  link back to the form only when the route supplies a form path.

### The page script

- The page script sends each multi-site form with `fetch` and the script
  header. A refused answer shows the sentence in the message region. The form
  keeps each typed value.
- The capture page shows a refused start in the capture error region. The
  pre-check card shows a refused start in its own error region.
- The pre-check card starts the captures one site at a time, in the order of
  the selection. For a plan that holds one site of page two, the refusal comes
  at the first start.

## Decisions

### D1: Raise one error class at the check.

The functions `find_site` and `selected_rows` raise `SiteListIncompleteError`
when the site read lost a page and the list does not hold a named site. The
error goes to the error handler, and the six callers need no change.

**Rejected**: a third kind of result, in addition to the record and None. Each
of the six callers would need a new branch. A caller without the branch would
answer "no such site" again.

### D2: Do not subclass a built-in value error.

The error subclasses `Exception` only. The route `save_options` catches
`TypeError`, `ValueError`, `OverflowError`, and `RuntimeError`, and it answers
each one as a bad option with the status 400. A subclass of one of them would
give the wrong status and the wrong sentence.

### D3: Answer the error in one application error handler.

The select blueprint registers the handler with `app_errorhandler`, so the
handler covers the routes of each blueprint. A browser receives the shared
error page. A script receives the error envelope. The token check handler in
`security.py` uses the same rule.

**Rejected**: a new 503 entry in `factory.ERROR_CODES`. That entry would give
each 503 fault one code, and the lock store faults use other codes.

### D4: Use the status 503.

The site read did not complete, and a later read can pass. The status 503
names a service that cannot answer now. The portal already uses 503 for a lock
store fault.

**Rejected**: 404. The site can exist, so 404 names the wrong cause.

**Rejected**: 409. No value of the request conflicts with a stored value.

### D5: The site choice post keeps its own refusal path.

The helper `site_set_refusal` returns the 503 envelope and the path of the site
picker. The check does not raise, because `PickerRefusal` must send a browser
back to the site picker with a Caution message. The error page holds no site
check boxes, so the operator cannot correct the choice there.

### D6: A check with a whole list keeps the answer of today.

A whole list proves that the organization does not hold the site. Each step
then answers as before, so no script and no page changes for a stale
identifier.

### D7: The link back of the error page.

After a refused form post, the error page holds a link back to the form. The
helper `form_return_path` supplies that link. After a refused page request, the
error page holds no link back, because a reload repeats the check. Each error
page keeps the link to the site list.

### D8: The browser harness loses a page on request.

The browser server runs in a child process, so a test sets a flag through one
request header, `X-MistHelper-E2E-Lose-Page`. Only the stand-in reader for the
organization of this test reads the header. With the header, that reader runs
the real page walk of `default_cloud_read` over a cloud session that loses
page two. Without the header, it answers the whole list, and no cache entry
forms. The portal code does not read the header.

**Rejected**: a lost page on each read, as for the organization of issue #3438.
The picker would then never show a site of page two, and no journey could
select it.

### D9: Each site of the new organization holds its own devices.

A multi-site plan can hold two sites. If the two sites held the same device
addresses, two rows of the table would get the same test identifier. Each of
the three sites therefore gets its own address digit in the device series of
the harness.

### D10: The pre-check journey plans one site of page two.

The card starts the captures in the order of the selection. A plan with a site
of page one first would start a real capture of that site before the refusal.
A plan that holds only the site of page two meets the refusal at once, and the
journey starts no capture.