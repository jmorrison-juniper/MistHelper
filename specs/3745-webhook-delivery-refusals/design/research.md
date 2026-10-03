# Research: Native webhook responses

## Decision: Read status before payload

The installed SDK is mistapi `0.64.0`.
`APIResponse.status_code` starts as `None`.
The constructor sets it from the actual Requests response before parsing the body.
The exporter must not turn unavailable status into HTTP `200`.

The unchanged first-page native `403` case returned `{"detail":"Forbidden"}` and `next=None`.
The SDK emitted two ERROR records. The exporter emitted zero ERROR records.
The actual persistence method ran once with zero rows.
The exporter printed its normal empty-data notice.
No final output, CSV, router, SQLite, database write, or exported-record success notice occurred.

The native `200` control retained one delivery row.
Actual final output returned `True`, and the real CSV writer wrote one temporary row.
The real polyglot callback returned `written=False` with `skip_reason="standalone_mode"`.
No database writer or router construction ran.

## Decision: Validate each native page

The SDK `get_all` accepts a list or a dictionary with `results`.
It calls `get_next` until the current response has no next link.
It does not inspect the HTTP status of later responses.
The exporter must collect accepted pages directly through real `get_next`.
It must defer persistence until every page passes.

Alternative rejected: Checking only the first page leaves later refusals unchecked.
Alternative rejected: A fake paginator or desired writer result cannot establish native behavior.
Alternative rejected: The unpublished issue #3699 reader belongs to another owner.

## Decision: Reuse the existing malformed-body signal

`ResponseIntegrityChecker` detects retained malformed body text with an empty parsed payload.
It deliberately treats missing or blank body text as an absent signal.
The exporter therefore needs an explicit readable, nonblank body decision before that check.
Supported successful data remains a list or a `results` list.

## Decision: Include directly coupled discovery

The actual class also calls native `listOrgWebhooks` and `get_all`.
A separate unchanged native `403` discovery case printed the configured-empty notice with zero exporter ERROR records.
Its native `200` list control retained the selected webhook identifier and name.
The discovery decision therefore has its own native evidence, separate from the delivery result.

## Measurement and limits

Four native cases used `api.mist.com`, the US cloud, and synthetic identifiers.
Each used actual Requests transport, SDK operations, and `APIResponse`.
Eight Requests sessions and four Responses closed.
All temporary directories and the control CSV were removed.
Live HTTP, DNS, socket, SQLite, router, and database operation counts were zero.
No resource warning occurred.

The base is `f48f653ae6145b0ea3aa82a76ffa4c6cf86897c0`.
Its complete tree is `c3655619bda6ac596aae45f994ae590189015e9d`.
Its raw sole parent is `0317b944388fb9f927ce4a20368070408542c4b1`.
The sixteen numeric-change paths do not include this exporter.

The unchanged full ratchet discovered 1,016 files and analyzed 968 files.
It retained 725 accepted findings with zero new findings and zero parse errors.
The existing webhook module retains one unrelated `weak_zero_assertions` finding at line 94.
This repair does not claim campaign #2746 completion.
