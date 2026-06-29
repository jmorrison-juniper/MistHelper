# Phase 0 Research: countOrgTickets

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
research task uses the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_tickets_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.tickets.countOrgTickets(apisession, org_id,
distinct=None, limit=100)`. The SDK returns a `mistapi.APIResponse` object whose
`.data` attribute is the parsed JSON body. The body is a single JSON object (not a
list, not paginated by `page`) with the following top-level keys per the doc:

- `distinct` (string) -- echo of the distinct field used for grouping.
- `start` (int, epoch seconds) -- start of the result window.
- `end` (int, epoch seconds) -- end of the result window.
- `limit` (int) -- echo of the limit applied (default 100).
- `total` (int) -- total number of distinct buckets matched.
- `results` (array, uniqueItems=true) -- one object per bucket. Each item has a
  required `count` (int) field plus open-ended `additionalProperties` of type string
  -- the bucket key, e.g. `{"count": 42, "status": "open"}` when
  `distinct=status`.

Required path parameter: `org_id` (UUID string).
Optional query parameters: `distinct` (string, default unset -- API may return a
server-chosen default field), `limit` (int, default 100).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.tickets.countOrgTickets()`. The mistapi SDK organizes module
paths from the OpenAPI URL, not the OpenAPI tag (verified by inspecting adjacent
endpoints under `/orgs/{org_id}/tickets/...`). The URL is
`/api/v1/orgs/{org_id}/tickets/count`, which maps one-for-one to
`mistapi.api.v1.orgs.tickets.countOrgTickets`. The spec.md authoritative module path
agrees. Final verification happens at implementation via
`python -c "from mistapi.api.v1.orgs import tickets; help(tickets.countOrgTickets)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against the URL.* Rejected -- the constitution forbids
   direct HTTP calls when a mistapi method exists.
2. *Use a tag-derived module path (e.g., `...orgs.orgs_tickets.count`).* Rejected --
   the SDK organizes by URL path, not tag, and the spec confirms the URL-based path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `org_tickets_count_summary`: PK = `(org_id, distinct_field, polled_at_utc)` -- one
  row per (org, distinct selection, poll). `org_id` is injected by MistHelper;
  `distinct_field` is the value the user supplied (or `"__server_default__"` when the
  user omitted it); `polled_at_utc` is the ISO8601 UTC timestamp captured by
  MistHelper at call time. This gives a stable audit row per poll without
  overwriting historical totals.
- `org_tickets_count_results`: PK = `(org_id, distinct_field, bucket_value)` --
  one row per (org, distinct selection, bucket value). `bucket_value` is the
  string value of the bucket key (e.g., `"open"`, `"closed"`, `"in_progress"` when
  `distinct=status`). Re-polling the same org with the same `distinct` field
  upserts the counts in place.

Both registrations use type `composite_pk`. `org_id` is injected by MistHelper before
the upsert (the Mist response does not echo `org_id`).

**Rationale**:
The endpoint reports an aggregated snapshot. The *results* are inherently keyed by
the bucket value -- re-running the same query with the same `distinct` field should
update the existing per-bucket count, not append a duplicate row. A *summary* row
captures audit information (total, limit, time window, poll timestamp) that is
useful to preserve across polls for trend analysis, so the summary table keeps
`polled_at_utc` in its key. This mirrors the split-summary-and-detail pattern used
by other aggregate exports in MistHelper (notably the license claim status export
under spec 500). `INSERT OR REPLACE` cleanly handles both behaviors via the
established `composite_pk` machinery.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on both tables.* Rejected for the results table --
   would let repeated polls accumulate duplicate per-bucket rows, defeating the
   upsert behavior the spec requires. Accepted as an alternative for the summary
   table but rejected because the audit utility of `polled_at_utc` as part of the
   PK is more valuable than a synthetic row id.
2. *Single combined table with `bucket_value` plus `polled_at_utc` as PK.* Rejected
   -- mixes the "current count per bucket" view (which should upsert) with the
   "snapshot per poll" view (which should accumulate), defeating both use cases.
3. *`natural_pk` on `total` or `distinct` alone.* Rejected -- neither field is
   unique across orgs, and `total` is not stable across polls.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_tickets_count_summary.csv`
- CSV (results): `data/org_<org_id_short>_tickets_count_results.csv`
- SQLite tables: `org_tickets_count_summary` and `org_tickets_count_results`
- `org_id_short` is the first 8 hex characters of the org UUID -- the convention
  already used by adjacent org-level aggregate exports in MistHelper for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countOrgTickets"` for the summary table (matching the operationId) and the
MistHelper-internal sub-table identifier `"countOrgTicketsResults"` for the
per-bucket results table. The DataExporter uses these strings as lookup keys into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by other org-level aggregate exports (e.g.,
`getOrgLicensesSummary`, `getOrgLicensesBySite`, the spec-500 claim-status exports).
Two output files and two SQLite tables keeps the schema clean and lets a user
query the buckets without joining when they don't need the per-poll audit envelope.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `results` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used elsewhere in
   MistHelper.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell
   history and `ls` output unnecessarily. The 8-char short form is enough to
   disambiguate locally.
3. *Include `distinct` field in the filename.* Rejected -- the value can change
   across runs; using `distinct` as part of the PK is sufficient and keeps the
   filename stable so re-runs replace prior CSV exports.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org
Exports cluster in the Misc sub-range (56-59). The category label is "Safe Org
Exports -- Tickets".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports (with 56-59 being Misc), 60-96 Interactive Safe, 97-101 + 153
Resource Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive.
The `countOrgTickets` operation is a single read-only GET that returns an aggregate
bucket count -- exactly the profile of a Misc Safe Org Export. Menu 58 is the next
available integer in the 56-59 sub-cluster. The destructive cluster (154-194) is
far away, so a junior NOC engineer scrolling the menu sees no risk signal for this
operation. The number is provisional -- at `/speckit.tasks` time, `MistHelper.py`
is grep'd for the latest allocated menu integer and 58 is shifted forward if a
conflict exists.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only count above the destructive block visually mis-signals
   the risk level to a junior NOC engineer.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a single
   GET returning a small JSON object with no pagination and no long-running work.
   It belongs in the safe block.
3. *Slot inside the Interactive Safe block (60-96).* Rejected -- this menu item is
   not interactive beyond two short prompts. The Safe Org Exports range is the
   correct semantic home.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly three** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_tickets_count:org_id"`. Default: the value of `MIST_ORG_ID` in `.env` if
   present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and
   return early.
2. `distinct` -- prompt:
   `"Distinct field (e.g., status, type, created_by; blank for API default): "`,
   context: `"org_tickets_count:distinct"`. Default: empty string. When empty, the
   query parameter is omitted from the SDK call so the Mist API picks its
   server-side default; the PK strategy records the literal string
   `"__server_default__"` so re-polls with no value still upsert correctly.
3. `limit` -- prompt: `"Limit (1-1000, default 100): "`, context:
   `"org_tickets_count:limit"`. Default: 100. The raw input is coerced via
   `int(...)` inside a `try / except ValueError` guard; on coercion failure, the
   method logs a `WARNING`, falls back to 100, and continues.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The Mist count endpoint is org-scoped only -- no site, device, or template ID is
required. The `distinct` parameter materially changes which buckets are returned,
so asking the user keeps the menu item useful for ad-hoc reporting (counting by
status one run, by type the next). The `limit` parameter is exposed because an
operator investigating a large ticket queue may want to widen the default 100
buckets; defaulting to 100 keeps casual use cheap.

**Alternatives Considered**:

1. *Hard-code `distinct=status` to keep the prompt count to one.* Rejected --
   forces every operator into the same view and wastes the flexibility the API
   exposes.
2. *Drop the `limit` prompt and always use the API default.* Rejected -- some
   orgs have hundreds of ticket-status buckets when `distinct=created_by`;
   forcing the default 100 would silently truncate the result set.
3. *Add a fourth prompt for time window (`start` / `end`).* Rejected -- the
   endpoint accepts no explicit `start` / `end` query parameters; those fields in
   the response are server-computed. Adding prompts that map to nothing would
   confuse the user.
