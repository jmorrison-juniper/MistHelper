# Research: A short inventory read never looks complete

**Issue**: #3424 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Measured facts

- `_read_paged` (`src/upgrade_portal/upgrade/options.py`) keeps the rows that
  `mistapi.get_all` returned. It then calls `guard_page_count`
  (`src/upgrade_portal/capture/devices.py`).
- `guard_page_count` returns one of three reasons. A refusal status and an
  unknown answer shape each come with no rows. A short read
  (`page_count_mismatch`) comes when the row count is less than the reported
  total.
- A read that holds one or more rows and one or more reasons is therefore a
  short read. A read with no rows and a reason is a failed read.
- A reason entry holds `section`, `reason`, and `http_status` only. It holds no
  count, so the page cannot state how many devices the read lost.
- `build_options_view` and `build_options_record` read `records` only. No code
  in `options.py` reads `partial_reasons` after the read.
- The single-site `save_options` answers each `ValueError` with status 400 and
  the code `bad_option`. The multi-site `save_options` translates each
  `BadOptionError` into the name of a control on the multi-site page.
- `OrgRetryPlan.narrow` copies the whole view, so a retry view keeps each
  field of the view.
- `portal.css` prepends "Caution: " to each `flash-warning` item. The capture
  page uses that rule for its partial capture banner.

## Measured facts from the code review

- `getOrgInventory` answers a JSON list, not a map. A read-only live probe on
  2026-09-26 asked for 3 rows. The first page held 3 rows, and the header
  `X-Page-Total` held 15. `listOrgDevicesStats` also answers a list with that
  header.
- `mistapi` 0.64.0 builds the `next` link from the headers `X-Page-Total`,
  `X-Page-Limit`, and `X-Page-Page`. `_reported_total` reads a total from a map
  body only. The short-read branch of `guard_page_count` therefore never runs
  for a list answer.
- `mistapi.get_all` adds the body of each later page to the rows. It does not
  check the status of the page (`__pagination.py`, lines 56 to 62).
- An HTML error page leaves an empty body and no `next` link. The loop stops,
  and the read keeps the rows of the pages before that page with no reason.
- A JSON error page adds the key names of its map to the rows. The row copy
  `dict(record)` then raises `ValueError` outside the guarded block. The red
  run gave that error for a JSON 429 page and for a text row.
- The options page does not catch that error, so it answers status 500. Each
  save answers status 400 with the raw error text.
- The probe organization holds no virtual chassis. Nobody measured how the
  header counts a stack when the read does not ask for `vc`.

## Decisions

### D1: Refuse the save. Do not offer a confirmation.

A confirmation asks the operator to accept a list with an unknown gap. The
operator cannot see which devices the read lost. Those devices stay on the old
firmware, and no record names them. A reload of the page is a cheap recovery.
Issue #3389 set the same rule for a site that the save cannot read.

**Rejected**: a confirmation control on the options page.

### D2: Keep the empty-read rule.

`build_options_record` returns an empty mapping when the read holds no row.
The single-site route then keeps the rows of the browser body (#3389 FR-007).
A unit test and two docstrings depend on that rule. Issue #3435 records the
defect of that fallback. This change does not alter it.

### D3: Raise a new `ValueError`, not a `BadOptionError`.

The multi-site save translates each `BadOptionError` into the name of a
control. A short read names no control, so a translation would name the wrong
control. A plain `ValueError` keeps the single-site answer at 400
`bad_option`, so `contracts/http-api.md` needs no change. The multi-site route
catches the new class before it reaches the translation.

### D4: Show a banner, and keep the rows.

The operator can still read the devices and the options on the page. The save
makes the decision, because the save reads the site again.

### D5: The multi-site view read decides first.

A short view stops that site before the second read. That saves one read, the
same way as the #3389 rule for an empty view. A complete view read and a short
save read also stop the save, through the refusal of `build_options_record`.

### D6: Refuse in the order unread, short, unplanned.

An unread site hides every device of the site, so its refusal comes first. A
short site hides part of the devices. An unplanned site comes from a choice of
the operator, so its refusal comes last. A short site stops a retry too,
because a retry device can sit on a lost page.

### D7: Use the signal word Caution.

The operator can recover with a reload, so the risk is recoverable. The banner
uses the `flash-warning` rule, which prepends "Caution: ".

### D8: Walk each page. Do not compare the header total.

The new function `read_every_page` asks for each later page. It checks the
status and the body of each page. A lost page gives the reason
`page_count_mismatch` with the status of that page, so the save refuses the
site. The walk makes the same count of cloud calls as `mistapi.get_all`.

Rejected: read `X-Page-Total` in `_reported_total`. Nobody measured how the
header counts a stack in a read without `vc`. A wrong count can refuse every
site that holds a stack. That change also alters the capture and the gate.

Rejected: change the capture reads and the gate read in this fix. Those reads
feed other pages and other tests. Issue #3436 records that work.

### D9: Copy the rows inside the guarded block.

The read copies each record inside the `try` block of `_read_paged`. A record
that is not a map then gives the reason `read_failed`, and the read never
raises (FR-014).
