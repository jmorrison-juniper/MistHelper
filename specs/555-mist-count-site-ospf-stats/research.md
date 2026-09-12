# Phase 0 Research: countSiteOspfStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/sites/GET_sites_site_id_stats_ospf_peers_count.md` (enriched OpenAPI
doc) and the related `GET_sites_site_id_stats_ospf_peers_search.md` for parameter
parity verification.

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.sites.stats.ospf_peers.count.countSiteOspfStats(
apisession, site_id, distinct=None, start=None, end=None, limit=None, sort=None,
search_after=None)`. The SDK returns a `mistapi.APIResponse` whose `.data` attribute is
the parsed JSON body. The body is a single JSON object (not a bare list) with the
following top-level keys per the enriched doc:

- `distinct` (string) -- echoes the distinct attribute requested.
- `start` (int epoch seconds) -- echoes the requested window start.
- `end` (int epoch seconds) -- echoes the requested window end.
- `limit` (int) -- echoes the requested page size (default 100).
- `total` (int) -- total number of distinct buckets matching the query across all pages.
- `results` (array of `count_result`) -- one element per distinct bucket. Each element
  has a required `count` field (int) plus arbitrary string properties whose names
  depend on the requested `distinct` attribute (for example a `distinct=neighbor` query
  yields a `neighbor` field on each bucket; a `distinct=state` query yields a `state`
  field; an unspecified `distinct` yields whatever default Mist groups by, observed in
  practice to be `neighbor`).

Required path parameter: `site_id` (UUID string).
Optional query parameters (all per the enriched doc):

- `distinct` -- attribute to group counts by. Default left to Mist server.
- `start`, `end` -- time window. Accept epoch seconds or relative strings like `-1d`,
  `-1w`, `-2h`, `now`. MistHelper passes these through verbatim; the SDK forwards them.
- `limit` -- page size, default 100.
- `sort` -- sort field, default `timestamp`; `-prefix` flips to DESC.
- `search_after` -- opaque pagination cursor. Pulled by MistHelper from the Mist
  `next` URL on each page response; never hand-constructed.

The endpoint is cursor-paginated: MistHelper reads `response.next` (a URL containing
the next `search_after` token) and re-invokes the SDK with that cursor until `next` is
absent or the cumulative row count reaches `total`.

**Rationale**:
The enriched doc lists the SDK module as
`mistapi.api.v1.sites.stats_-_ospf.countSiteOspfStats()` (with an ASCII-art separator
from the OpenAPI tag `Sites Stats - Ospf`). The mistapi SDK generates module names
from URL paths, not OpenAPI tags -- verified by inspecting adjacent endpoints under
the same path: `searchSiteOspfStats` lives at `mistapi.api.v1.sites.stats.ospf_peers.
search`. The spec.md names `mistapi.api.v1.sites.stats.ospf_peers.count`, which
matches the URL one-for-one, so we follow the spec. Final verification happens at
implementation time via
`python -c "from mistapi.api.v1.sites.stats.ospf_peers import count; help(count)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/sites/{site_id}/stats/
   ospf_peers/count`.* Rejected -- the Constitution forbids direct HTTP when a mistapi
   method exists.
2. *Use the tag-implied path `mistapi.api.v1.sites.stats_-_ospf`.* Rejected -- the
   SDK organizes modules by URL path, not OpenAPI tag, and the spec.md (the
   authoritative feature contract) names the URL-based path.
3. *Skip pagination and treat `results[]` as a single page.* Rejected -- the API
   returns `total` separately and emits a `next` URL when more pages exist; ignoring
   pagination would silently truncate aggregates for sites with many distinct values.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on one output table `site_ospf_peers_count`:

- PK = `(org_id, site_id, distinct_attribute, bucket_key, window_start, window_end)`
- `org_id` is injected by MistHelper from the active session context (Mist does not
  return `org_id` in the body, but MistHelper always knows the org of the active
  `mistapi.APISession`).
- `site_id` is the path parameter the user supplied.
- `distinct_attribute` is the value of the `distinct` query parameter (or the literal
  string `default` when the user did not supply one) -- this is what each bucket is
  grouped by.
- `bucket_key` is the value of that distinct attribute in the current bucket (for
  example the actual neighbor router-id when `distinct=neighbor`). MistHelper extracts
  it by looking up `bucket[distinct_attribute]` on each `results[]` entry.
- `window_start`, `window_end` are the echoed `start` / `end` fields of the response,
  normalized to epoch seconds (resolved client-side from any relative strings before
  the call so they are stable).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`.

**Rationale**:
A count endpoint returns aggregates that are *time-window-relative* -- the same
`(site, distinct, bucket_key)` triple has different counts for different windows.
Including `window_start` / `window_end` in the PK lets a NOC engineer poll the same
site over multiple windows (last hour, last day, last week) and accumulate a history
in SQLite without one window's rows overwriting another's. Pairing `org_id` plus
`site_id` keeps rows from different sites and different orgs cleanly separated even
when a single MistHelper instance targets multiple tenants. `INSERT OR REPLACE`
upserts every re-poll of the *same* window.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls of the same
   window accumulate duplicate snapshots, defeating the upsert behavior the spec
   requires (FR-005 + acceptance scenario 3).
2. *`natural_pk` on `bucket_key` alone.* Rejected -- the same `bucket_key`
   (for example a neighbor router-id) appears under multiple sites, multiple distinct
   attributes, and multiple time windows; without the rest of the composite the row
   is not unique.
3. *Omit `window_start` / `window_end` from the PK.* Rejected -- a user polling
   "last hour" then "last day" would silently overwrite the first snapshot. Audit
   history would be lost.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/site_<site_id_short>_ospf_peers_count_<distinct_attribute>.csv`
- SQLite table: `site_ospf_peers_count`
- `site_id_short` = first 8 hex characters of the site UUID (consistent with adjacent
  site-stats exports that already use this convention).
- `distinct_attribute` is the user-supplied distinct value, lowercased and sanitized
  to `[a-z0-9_]` (replace `-` with `_`, drop other characters). Default literal
  `default` is used when the user did not supply a value.

The `api_function_name` passed to `DataExporter.write_with_format_selection()` is
`"countSiteOspfStats"` (matches the operationId exactly). The DataExporter uses that
string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `searchSiteOspfStats` and `countSiteBgpStats`
(the two closest adjacent exports). Embedding the distinct attribute in the CSV
filename lets a user run the same menu item multiple times against the same site for
different group-by attributes and keep separate CSV outputs side by side, while still
upserting cleanly into a single SQLite table because `distinct_attribute` is part of
the SQLite primary key.

**Alternatives Considered**:

1. *One CSV per distinct attribute *and* one SQLite table per distinct attribute.*
   Rejected -- proliferates tables (one per attribute the user ever queries) and
   breaks cross-attribute SQL queries.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into shell
   history. The 8-character short form is enough to disambiguate locally.
3. *Single global CSV `site_ospf_peers_count.csv` shared across sites.* Rejected --
   makes per-site review harder for a junior NOC engineer who runs the menu item
   against one site at a time.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 89**, sitting inside the Safe Site Stats
cluster. Category label: "Safe Site Stats -- OSPF".

**Rationale**:
The Constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe (subdivided into site devices 60-72,
insights 73-79, stats 80-91, viewers 92-96), 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. OSPF count is a stats export, so
it belongs in the 80-91 stats sub-cluster. 89 is the next contiguous integer in that
band that does not collide with currently published menu items (final number confirmed
at `/speckit.tasks` time by greping `MistHelper.py` for the highest allocated integer
in the stats cluster).

**Alternatives Considered**:

1. *Append to the end (menu 195).* Rejected -- placing a read-only stats count above
   the destructive block visually mis-signals the risk level to a junior NOC engineer
   scrolling the menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a paginated
   GET with small per-bucket rows; total runtime is seconds, not the minutes that the
   resource-intensive cluster reserves.
3. *Use a free integer outside the 80-91 stats sub-cluster (e.g., 75 in the insights
   band).* Rejected -- mis-categorizes the operation; the next operator scanning the
   menu would look in the stats band first.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly four** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context: `"site_ospf_peers_count:
   site_id"`. Default: the value of `MIST_SITE_ID` in `.env` if present (pressing
   Enter accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `distinct_attribute` -- prompt: `"Distinct attribute (neighbor | state | area |
   vrf_name | mac) [default: server-default]: "`, context:
   `"site_ospf_peers_count:distinct"`. Default: empty string, which causes the SDK
   call to omit the `distinct` query parameter (Mist server picks its default,
   observed to be `neighbor`).
3. `time_start` -- prompt: `"Window start (epoch seconds or relative, e.g. -1d):
   "`, context: `"site_ospf_peers_count:start"`. Default: `-1d`. Resolved to epoch
   seconds client-side before the SDK call (and before being committed to the SQLite
   PK) so the PK is stable regardless of when the user runs the operation.
4. `time_end` -- prompt: `"Window end (epoch seconds or relative, e.g. now): "`,
   context: `"site_ospf_peers_count:end"`. Default: `now`. Resolved client-side the
   same way.

Sort and `search_after` are not user-facing: `sort` defaults to the API's `timestamp`
ordering, and `search_after` is set automatically by the pagination loop from each
prior response's `next` URL.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

**Rationale**:
This endpoint is site-scoped (no org prompt needed; org context comes from the
session). The `distinct` parameter materially changes the response shape, so making
it an explicit prompt with a short list of valid values keeps a junior NOC engineer
productive. Time-window prompts are required because count-style aggregates are
inherently time-window-relative; defaulting to the last 24 hours matches operational
expectations for OSPF flap analysis.

**Alternatives Considered**:

1. *Single prompt, hardcoded `distinct=neighbor` and `start=-1d, end=now`.*
   Rejected -- removes operational flexibility for area / state breakdowns and for
   wider or narrower windows.
2. *Add a prompt for `limit` and `sort`.* Rejected -- the API defaults (100 per page
   sorted by timestamp DESC) are the right choice for the operational case; adding
   prompts just adds keystrokes. Power users can re-run with a deeper window if they
   need more buckets.
3. *Prompt for a CSV filename override.* Rejected -- the deterministic filename
   scheme (Research Task 3) keeps outputs predictable and easy to find under
   `data/`.
