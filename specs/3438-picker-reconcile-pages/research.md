# Research: The site picker and the reconciliation read name a lost page

**Issue**: #3438 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Measured facts of the picker read

- `default_cloud_read` (`src/upgrade_portal/app/routes/select.py`) asks for the
  first page with a limit of 1,000 records. It then passes that page to
  `collect_pages` for the later pages.
- `collect_pages` calls the helper `mistapi.get_all` for the later pages. That
  helper adds each page with no status check. Lines 56 to 62 of
  `__pagination.py` hold that loop.
- `collect_pages` keeps the first page when the helper returns fewer rows than
  the first page. A lost later page adds nothing, so the helper returns the
  rows of the first page. That count is not less than the first page, so the
  floor does not see the loss. The read then looks whole.
- The picker never reads the status of the first page. A refused first page
  gives an empty list, and the page shows no note.
- `CLOUD_READ_CACHE` keeps each non-empty answer for one minute. A short answer
  is then kept too. A reload within that minute shows the same short list.
- `APIResponse._check_next` builds the `next` link from the `X-Page-Total`,
  `X-Page-Limit`, and `X-Page-Page` headers. The rule is the same for every
  list read, so `listOrgSites` and `listOrgSiteStats` follow it.
- Five places call `build_site_rows`: `sites_page`, `site_choice_refusal`, and
  `list_sites` in `select.py`, and `selected_rows` and `_site_labels` in
  `org_upgrade.py`.
- `find_site` reads the site list through `as_records`. That reader already
  accepts a `DeviceRead`.
- The `MIST_READER` seam check reads the call shape only. Each stand-in of the
  tests answers a plain list.
- `select.py` already imports `normalize_device_mac` from `capture.devices`. A
  second import from that module adds no import cycle.

## Measured facts of the reconciliation read

- `SiteStatsFirmwareEvidenceReader.read`
  (`src/upgrade_portal/api/run_controls/routes.py`) passes the first page to
  `mistapi.get_all`. A lost later page leaves some targets with no fresh row.
- `_target_evidence_row` then fills the running version with the stored
  `version_after`. It sets the task state and the write state to `unknown`.
  The service then reports `cloud_evidence_incomplete`.
- A refused first page makes `_read_site_statistics` return None. The helper
  `mistapi.get_all` then raises `AttributeError`. The service catches it, logs
  a traceback, and marks every target unavailable.
- A stored run target holds the normalized MAC address and no device
  identifier. The target builder is in `upgrade/options.py`. The reader keys
  each fresh row by the normalized MAC address. The lookup of a stored target
  therefore matches.
- `_evidence_result` reports `cloud_evidence_unavailable` when a target holds
  the task state or the write state `unavailable`.
- The browser harness answers reconciliation through the scripted
  `CLOUD_EVIDENCE` seam. A browser journey therefore never reaches the reader.

## Decisions

### D1: Walk each page of the picker read.

`collect_pages` calls `read_every_page`, the walk of issue #3424. The walk
checks the status and the body of each later page. It keeps the rows of the
pages before a lost page, and it names the loss. The walk makes one call for
each page, the same count as `mistapi.get_all`.

**Rejected**: keep the first-page floor. The floor cannot see a lost later
page.

### D2: Name a fault of the first page.

`guard_page_count` names a refused first page, a first page with no status,
and a body that the portal cannot read. The capture uses the same guard, so
one rule names each fault class.

### D3: Return a `DeviceRead`, and keep a whole read only.

`default_cloud_read` returns the records and the partial reasons together. The
cache keeps a read only when it holds no partial reason. A kept short read
would show the note for one minute, and the reload step would not recover.

**Rejected**: a new result type. `DeviceRead` already holds the two fields,
and `as_records` already reads it.

### D4: `build_site_rows` returns a `SiteList`.

The new type holds the rows and one flag for each read. The five callers move
to the new type in this change. The constitution forbids a compatibility shim.
A plain list from a stand-in reads as a whole read.

### D5: Show two Caution notes on the site picker.

The single-site mode and the multi-site mode use one template, so one change
covers both modes. The `flash-warning` class prepends "Caution:" in
`portal.css`. The notes keep the rows, because the operator can still choose a
site of the first page.

### D6: Add two fields to the site list answer.

`GET /api/sites` adds `site_list_complete` and `device_counts_complete`. A new
field keeps each old script working. The shared contract file names both
fields.

### D7: Mark each target of a lost page as unavailable.

The reader walks each page of the statistics read. A target with no fresh row
after a lost page holds the task state and the write state `unavailable`. A
target with a fresh row keeps its evidence. The service then reports
`cloud_evidence_unavailable`, and no stored version shows as a running
version.

**Rejected**: raise an error to reach `_unavailable_targets`. That path drops
each fresh row, and it logs a traceback for a known cloud fault.

**Rejected**: keep the stored fallback. That fallback shows a stored version
as the running version of a target.

### D8: Leave the later site checks out of scope.

A later site check still refuses a site of a lost page with "no such site".
An honest refusal needs a new status code in the factory and changes in four
files. Issue #3439 tracks that work.
