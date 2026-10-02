# Research: Capture reads report a lost page

## Decision 1: Use the existing checked walk

`mistapi.get_all` does not check each later list response status.
An HTML error contributes no row.
A JSON error map can contribute key names and cause a row-copy error.
The existing `read_every_page` from issue #3424 checks native response status and list shape.
Use that walk, not another implementation.

Do not compare header totals.
`X-Page-Total` can count virtual-chassis members differently from collapsed rows.
Use real headers only to let the SDK construct native next links.
Keep the existing body-total guard.

## Decision 2: Keep failures inside the read boundary

A later transport exception carries no HTTP status.
Report `page_count_mismatch` with status `0` and retain earlier valid pages.
A malformed later record must not cause an exception outside the caller's boundary.
Do not concatenate error-map keys or silently discard malformed device records.

The first-page guard keeps its status, shape, and body-total responsibilities.
A valid empty list remains readable.

## Decision 3: Carry wireless reasons through the actual collector

`fetch_wireless_stats_rows` currently returns a list.
The real collector calls that reader, then gives its rows to the wireless join.
`collect_reasons` currently collects group, device, and extra reasons only.
The migration must carry both wireless rows and reasons.

Reuse the existing paged result instead of introducing a second result class.
Use a late import at the client collection boundary to avoid the existing import cycle.
The three map client reads keep their current `get_all` calls and visible exceptions.
The direct wireless reader must not return a complete-looking result after a partial statistics read.

## Decision 4: Carry tier 3 reasons beside retained rows

`_paged` currently catches a walk failure and returns the first page's status.
That status can be `200` after a later failure.
Its typed result must carry a reason and the failed page's status.
`_section_from_response` must keep the rows of that partial result.
The shared port result must feed identical reasons into `switch_ports` and `poe`.

## Decision 5: Preserve ownership and firmware policy

The issue claim reserves `collector.py`.
The public temporary handoff of `clients.py` permits only the wireless migration.
Do not change `page_limit`.
The later authorized rebase must retain issue #3395's bounded numeric reader.

No change to `assembly.py`, firmware writes, settle decisions, confirmations, or live services is necessary.
A human must review this firmware-evidence repair before merge.

## Rejected alternatives

| Alternative | Reason for rejection |
| - | - |
| Compare `X-Page-Total` to inventory row count | The issue explicitly forbids this comparison. |
| Keep the first page with status `200` after an error | The section would still appear complete. |
| Catch every error as `read_failed` | A later refusal must preserve its exact lost-page status. |
| Filter malformed rows as the device fix | The filter would hide an incomplete read. |
| Repair only the original three reads | The later issue comment requires wireless and tier 3 reads too. |
| Move the whole capture package into new classes | The broader refactor crosses reserved paths and changes unrelated structure. |
