# History scope contract

## Request and source contracts

`GET /history` retains its signed organization selection.
The optional `site_id` narrows that organization's records.
History APIs retain their existing response fields, totals, order, and page bounds.
No reader body or query changes.
Only the existing history page context wiring receives the new card scope.

## Description contracts

Each card supplies a note lead, caption lead, and empty statement.
The [data model](../data-model.md) defines the three keys.

| Card | Site scope | Organization scope |
| --- | --- | --- |
| Runs | The single-site upgrade runs of the selected site. | The single-site upgrade runs of the selected organization. |
| Multi-site upgrades | The multi-site upgrades that include the selected site. | The multi-site upgrades of the selected organization. |
| Audit log | The site lock actions of the selected site. | The site lock actions of the selected organization. |

If the existing scoped capture rows supply a name, substitute that name for "the selected site".
Never substitute a name from an organization page's first row.
Never substitute a query-supplied name.

Each empty statement describes the visible page.
This statement remains true after an offset exceeds the matching record count.
The existing unavailable-operation message stays distinct from an empty operation list.

## Browser contracts

The new note identifiers are `history-run-note`, `history-operation-note`, and `history-audit-note`.
The existing table identifiers remain unchanged.
Each table retains its accessible `caption`.
The existing empty-row identifiers remain unchanged.

A Chromium journey must open both `/history?site_id=<site>` and `/history`.
Required cases must fail instead of skipping when their expected page or records are unavailable.

## Unchanged behavior

Keep capture counts, identifiers, site columns, UTC moments, and page links.
Keep run counts, identifiers, attribution, capture links, and stale policy.
Keep operation membership, order, attribution, and owner-only progress links.
Keep audit order, organization filtering, site filtering, inference, and digest-only operator text.
Keep authentication and signed-cookie refusals before source reads.
