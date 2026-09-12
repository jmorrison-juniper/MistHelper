# Phase 0 Research: GetOrgTicketAttachment

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-28

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_tickets_ticket_id_attachments_attachment_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.tickets.attachments.getOrgTicketAttachment(
apisession, org_id, ticket_id, attachment_id, start=None, end=None, duration="1d")`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single JSON object with one documented top-level key:

- `content_url` (string -- a forward-download URL of the form
  `https://api.mist.com/api/v1/forward/download?jwt=...` containing an embedded JWT
  that authorizes a one-shot, time-limited fetch of the underlying attachment binary)

Required path parameters: `org_id` (UUID), `ticket_id` (UUID), `attachment_id` (UUID).
Optional query parameters: `start` (epoch seconds or relative like `-1d`), `end` (epoch
seconds or relative like `now`), `duration` (relative like `7d`, `2w`; SDK default
`1d`). The query params bound the time window over which the URL is valid -- they do
not filter the response shape.

**Rationale**:
The enriched per-endpoint doc lists the SDK module string as
`mistapi.api.v1.orgs.tickets.GetOrgTicketAttachment()`. That path does not mirror the
OpenAPI URL, which contains `attachments` as a segment. The spec.md (the authoritative
feature contract) names the URL-based path
`mistapi.api.v1.orgs.tickets.attachments`. The mistapi SDK historically generates
module paths from the URL, not from the OpenAPI tag (verified by inspecting adjacent
endpoints under the same URL: `POST /orgs/{org_id}/tickets/{ticket_id}/attachments`
lives at `mistapi.api.v1.orgs.tickets.attachments`). We therefore follow the spec.md
and the URL-based convention. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.tickets import attachments; help(attachments)"`
inside the venv; if the SDK on disk exposes the alternative path the doc suggests,
implementation switches to that path and notes the deviation in the CHANGELOG.

**Alternatives Considered**:

1. *Direct `requests.get` against the URL.* Rejected -- the constitution forbids direct
   HTTP when a mistapi method exists.
2. *Use the path implied by the doc string
   (`mistapi.api.v1.orgs.tickets.GetOrgTicketAttachment`).* Rejected -- the SDK
   organizes modules by URL path, not OpenAPI tag; the spec.md authoritative path is
   URL-based; and the adjacent POST endpoint under the same URL confirms the
   `attachments` sub-module exists.
3. *Auto-download the binary referenced by `content_url`.* Rejected for this spec --
   the endpoint contract returns only the URL. Auto-download is a separate concern
   (potentially a future menu item) and would change risk classification because the
   download path requires a second HTTP call against an external forwarder.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table:

- `org_ticket_attachments`: PK = `(org_id, ticket_id, attachment_id)` -- one row per
  attachment per ticket per org. These three IDs uniquely identify the attachment
  globally; the `content_url` field is overwritten on every poll (the JWT expires, so
  every fresh poll yields a new URL but for the same attachment identity).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`. `org_id`,
`ticket_id`, and `attachment_id` are all supplied by the user (and stored in
MistHelper's per-call context) before the upsert -- Mist does not echo these IDs back
in the response body, so MistHelper injects them.

**Rationale**:
The endpoint returns a single attachment's signed download URL. The signed URL itself
is *not* a stable identifier (the JWT rotates every poll), so it cannot be a primary
key. The three path-parameter UUIDs together uniquely identify the attachment and are
stable across polls. `INSERT OR REPLACE` keyed on the triple ensures re-running the
menu item against the same attachment refreshes the stored `content_url` and
`polled_at_utc` columns without creating duplicate rows.

**Alternatives Considered**:

1. *`auto_increment_with_unique` keyed on `content_url`.* Rejected -- `content_url`
   rotates every poll, so each poll would produce a new "unique" row, defeating the
   upsert behavior the spec requires and bloating SQLite over time.
2. *`natural_pk` on `attachment_id` alone.* Rejected -- a single MistHelper deployment
   may target multiple orgs, and Mist does not guarantee `attachment_id` is unique
   across orgs (it is unique within a ticket). Pairing all three IDs is the safe
   composite key.
3. *Two tables (attachment metadata + history of polled URLs).* Rejected -- the spec
   asks for upsert behavior; a history table is out of scope and can be added later as
   a separate spec if audit-trail data becomes a requirement.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_ticket_<ticket_id_short>_attachment_<attachment_id_short>.csv`
- SQLite table: `org_ticket_attachments`
- `*_id_short` is the first 8 hex characters of the respective UUID -- already the
  convention used by adjacent exports in MistHelper for human-readable filenames
  without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"getOrgTicketAttachment"` (matching the operationId). The DataExporter uses that
string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by other ticket-scoped exports (spec 188 introduced
`org_<id>_tickets.csv` and `org_<id>_ticket_<id>_comments.csv`). A single output file /
single SQLite table is sufficient because the response holds only one logical entity
(an attachment URL). The filename includes all three IDs so a user can run the menu
item against multiple attachments in the same ticket without filenames colliding.

**Alternatives Considered**:

1. *Combine all attachments of a ticket into one file.* Rejected -- this endpoint
   returns a single attachment per call, and aggregating across calls would require
   client-side multi-call orchestration that is out of scope for this spec (and is
   already provided by a future bulk-list endpoint when one is cataloged).
2. *Full UUIDs in the filename.* Rejected -- leaks IDs into shell history and `ls`
   output unnecessarily. The 8-character short form is sufficient to disambiguate
   locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting at the top of the Interactive
Safe cluster (60-96) immediately below the resource-intensive cluster that begins at
97. The category label is "Interactive Safe -- Support Tickets".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. This endpoint requires THREE
user-supplied UUID prompts (org, ticket, attachment), placing it firmly in the
interactive-safe block rather than the safe-org-export block (which expects only an
org_id). Spec 500 reserved 95 for a license export inside the safe-org cluster; 96 is
the next contiguous integer and is the highest number still inside the interactive-safe
range. The number is provisional -- at `/speckit.tasks` time, `MistHelper.py` is
grep'd for the latest allocated menu integer and 96 is shifted forward if a conflict
exists.

**Alternatives Considered**:

1. *Slot inside Safe Org Exports (1-59) at the next free integer.* Rejected -- the
   safe-org-export category convention is that the operation prompts for `org_id`
   only. This endpoint prompts for three IDs and would mis-signal the interactive cost
   to a junior NOC engineer scrolling the menu.
2. *Append at the very end (e.g., 195).* Rejected -- placing a read-only ticket query
   above the destructive block at 154-194 visually mis-signals the risk level to a
   junior NOC engineer.
3. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns one tiny JSON object (a single URL string), with no pagination and
   no long-running work. It belongs in the interactive-safe block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **four** values via `safe_input()`. The first
three are mandatory IDs; the fourth is an optional time-filter shortcut.

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_ticket_attachment:org_id"`. Default: the value of `MIST_ORG_ID` in `.env` if
   present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and return
   early.
2. `ticket_id` -- prompt: `"Ticket ID (UUID): "`, context:
   `"org_ticket_attachment:ticket_id"`. No `.env` default. Validated via
   `is_valid_uuid()`; on failure, log `WARNING` and return early.
3. `attachment_id` -- prompt: `"Attachment ID (UUID): "`, context:
   `"org_ticket_attachment:attachment_id"`. No `.env` default. Validated via
   `is_valid_uuid()`; on failure, log `WARNING` and return early.
4. `time_filter` -- prompt: `"Time filter (start|end|duration, blank = SDK default 1d): "`,
   context: `"org_ticket_attachment:time_filter"`. Default: blank (use SDK default of
   `duration=1d`). The user may type a duration string like `7d`, `2w`, `-1h` and it is
   forwarded as the `duration` query parameter. Empty input results in no query
   parameter overrides being sent.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The Mist attachment endpoint is scoped by three path IDs that nothing else in
MistHelper currently caches per-session, so the user must supply them each call. The
time-window query parameters are optional in the API; collapsing them into one
"time_filter" prompt keeps the menu lightweight while still letting an operator widen
or narrow the validity window when needed. The four-prompt UX matches the pattern set
by other multi-ID interactive-safe menu items.

**Alternatives Considered**:

1. *Skip the time-filter prompt entirely and always accept the SDK default.* Rejected
   -- some support cases need to fetch attachments older than the default 1-day window;
   forcing operators to edit code or `.env` to widen the window contradicts the
   "junior NOC engineer" target audience.
2. *Three separate prompts for `start`, `end`, and `duration`.* Rejected -- three
   prompts for a feature 90% of users won't touch adds keystrokes without operational
   value. Collapsing to a single optional `duration`-style prompt (with the option to
   leave blank) handles the common case efficiently.
3. *Cache `org_id` + `ticket_id` from a prior `getOrgTickets` call in the same
   session.* Rejected -- cross-menu session state does not exist in MistHelper today
   and introducing it is out of scope for this spec. Adding a `.env` default for
   `ticket_id` or `attachment_id` is rejected for the same reason (those IDs are
   highly transient and not session-stable).
