# Phase 0 Research: countSiteWanUsage

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/sites/GET_sites_site_id_wan_usages_count.md`
(enriched OpenAPI doc) and the related search endpoint
`documentation/api/sites/GET_sites_site_id_wan_usages_search.md`.

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.sites.wan_usages.count.countSiteWanUsage(apisession,
site_id, distinct=None, mac=None, peer_mac=None, port_id=None, peer_port_id=None,
policy=None, tenant=None, path_type=None, start=None, end=None, duration="1d",
limit=100)`. The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is
the parsed JSON body. The response body is a single JSON object envelope with the
following top-level keys (per the doc, all required):

- `distinct` (string) -- the field that the API was asked to group by.
- `start` (int32, epoch seconds) -- effective start of the time window.
- `end` (int32, epoch seconds) -- effective end of the time window.
- `limit` (int32) -- effective page size used by the server (default 100).
- `total` (int32) -- total number of distinct rows the server has available.
- `results` (array of `count_result` objects, `uniqueItems=true`) -- each item has at
  least `count` (int32) plus arbitrary string-typed properties whose names depend on
  the `distinct` field value (e.g., when `distinct=mac` the items also contain a
  `mac` string).

Required path parameter: `site_id` (UUID string).
Query parameters (all optional): `mac`, `peer_mac`, `port_id`, `peer_port_id`,
`policy`, `tenant`, `path_type`, `distinct`, `start`, `end`, `duration`, `limit`.

**Rationale**:
The enriched per-endpoint doc lists the SDK as
`mistapi.api.v1.sites.wan_usages.countSiteWanUsage()`, and the spec.md confirms the
SDK module path `mistapi.api.v1.sites.wan_usages.count`. The mistapi SDK historically
generates one Python module per OpenAPI path segment, so the URL
`/api/v1/sites/{site_id}/wan_usages/count` maps cleanly to
`mistapi.api.v1.sites.wan_usages.count` with the function exposed at the operationId
name (`countSiteWanUsage`). Final verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.wan_usages import count; help(count)"` inside
the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/wan_usages/count`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Use the related search endpoint
   (`mistapi.api.v1.sites.wan_usages.search.searchSiteWanUsage`) and post-process the
   results client-side to derive a count.* Rejected -- doubles the API call cost, loses
   the server-side `distinct` grouping, and ignores the explicit count endpoint that
   the Mist API already provides for exactly this purpose.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`site_wan_usage_counts`. The PK is the tuple
`(site_id, distinct_field, window_start, window_end, distinct_value)`:

- `site_id` (TEXT, MistHelper-injected) -- supplied by the caller; required for
  multi-site MistHelper installs.
- `distinct_field` (TEXT) -- copied verbatim from the API response `distinct` key.
- `window_start` (INTEGER) -- copied from the API response `start` key.
- `window_end` (INTEGER) -- copied from the API response `end` key.
- `distinct_value` (TEXT) -- the value of the grouping field on each row of the
  `results[]` array (e.g., the MAC string when `distinct=mac`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry uses `type=composite_pk`. Mist does not
return `site_id` in the body, but MistHelper always knows which site the call
targeted and injects it before the upsert -- the same pattern other site-scoped count
endpoints already use.

**Rationale**:
The Mist response is a *grouped* count: one row per distinct value of whichever field
the caller asked for. Re-running the menu with the same `site_id` and `distinct_field`
over the same time window must update the existing rows rather than append duplicates.
The five-tuple captures the natural business identity: which site, which grouping
dimension, over which window, for which dimension value. SQLite `INSERT OR REPLACE`
gives clean upsert semantics on this composite key.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on a generated row ID.* Rejected -- repeated polls
   over the same window would accumulate duplicate snapshots, defeating the upsert
   behavior the spec requires.
2. *`natural_pk` on `distinct_value` alone.* Rejected -- a single MistHelper instance
   may target multiple sites; `distinct_value` is not unique across sites or across
   `distinct_field` choices (the same MAC string can appear for `distinct=mac` and
   `distinct=peer_mac`).
3. *Two tables: an envelope row (site_id, distinct, start, end, total, limit) plus a
   detail row per `results[]` entry.* Rejected -- the envelope columns (`start`,
   `end`, `limit`, `total`) are already cheap to duplicate on every detail row, and a
   single-table design keeps downstream SQL queries trivial. The reference
   `getOrgLicensesSummary` pattern shows the same flattening choice.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV filename: `data/site_<site_id_short>_wan_usage_counts.csv`
- SQLite table: `site_wan_usage_counts`
- `site_id_short` is the first 8 hex characters of the site UUID -- the convention
  already used by adjacent site-scoped exports in MistHelper for human-readable
  filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"countSiteWanUsage"` (matching the
operationId). The DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent site-scoped count endpoints already in
MistHelper. A single output file and single SQLite table simplifies downstream
analytics for junior NOC engineers: one CSV per (site, run) and one DDL table to query.

**Alternatives Considered**:

1. *Single output file with a JSON-encoded `results` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used everywhere else in
   MistHelper.
2. *Full site UUID embedded in the filename.* Rejected -- leaks the site UUID into
   shell history and `ls` output unnecessarily. The 8-character short form is enough
   to disambiguate locally.
3. *Per-`distinct_field` filenames (e.g., `..._wan_usage_counts_by_mac.csv`).*
   Rejected -- the `distinct_field` is already a column in the table, so multiple
   groupings coexist in the same SQLite table without collision and a stable filename
   is friendlier for automation.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 91**, sitting inside the interactive-safe
Stats sub-cluster (80-91) of the broader Interactive Safe range (60-96). The category
label is "Interactive Safe -- Site Stats / Counts".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe (with Site devices 60-72, Insights
73-79, Stats 80-91, Viewers 92-96), 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. WAN usage counts are
site-scoped read-only stats queries, so the Stats sub-cluster is the correct home.
Menu 91 is the next available integer at the end of the Stats range, immediately
before the Viewers block at 92. The number is provisional -- at `/speckit.tasks` time
MistHelper.py is grep'd for the latest allocated menu integer and 91 is shifted
forward if a collision exists.

**Alternatives Considered**:

1. *Append to the end of the menu (e.g., 195).* Rejected -- the destructive cluster
   ends at 194, and placing a read-only stats query above it visually mis-signals the
   risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns a small envelope with a bounded `results[]` array (server-side
   `limit` defaults to 100). It is not long-running or paginated; it belongs in the
   safe block.
3. *Slot inside Safe Org Exports (1-59).* Rejected -- the endpoint is site-scoped,
   not org-scoped; placement in the org block would surprise users who expect a site
   prompt only inside the 60-96 range.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly three** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context: `"site_wan_usage_count:site_id"`.
   Default: the value of `MIST_SITE_ID` from `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before the API
   call; on failure, log `WARNING` and return early.
2. `distinct_field` -- prompt: `"Group by (mac / peer_mac / port_id / peer_port_id /
   policy / tenant / path_type) [mac]: "`, context:
   `"site_wan_usage_count:distinct"`. Default: `mac`. The user's answer is
   lowercased and validated against the closed set of seven allowed values; an
   unrecognized value defaults back to `mac` with a `WARNING` log line. The value is
   passed to the SDK as the `distinct` query parameter.
3. `duration` -- prompt: `"Duration (e.g. 1d, 7d, 2w) [1d]: "`, context:
   `"site_wan_usage_count:duration"`. Default: `1d` (matches the Mist API default).
   The string is passed unchanged to the SDK as the `duration` query parameter. No
   client-side regex validation is performed -- the API returns a 400 when the format
   is wrong and MistHelper logs a `WARNING` and returns early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

The remaining query parameters (`mac`, `peer_mac`, `port_id`, `peer_port_id`,
`policy`, `tenant`, `path_type`, `start`, `end`, `limit`) are *not* prompted for in
this menu item. They are advanced filters that materially complicate the prompt flow
and are better surfaced by a future "advanced" variant if user demand emerges. The
SDK is called with those parameters left at their defaults.

**Rationale**:
Mist's WAN-usage count endpoint is site-scoped. Three prompts are the minimum needed
to make the operation useful: the site, the grouping dimension, and the time window.
Adding ten more prompts for every optional filter would violate the junior-NOC-engineer
audience standard (the constitution's "Audience Standard" section) by burying the
common case under rarely used inputs. A short, opinionated prompt flow matches the
adjacent site stats menu items already in MistHelper.

**Alternatives Considered**:

1. *Single prompt for `site_id` only; hard-code `distinct=mac`, `duration=1d`.*
   Rejected -- removes the user's ability to group by other dimensions without code
   changes and makes the menu item nearly identical to existing items, providing
   little new value.
2. *Prompt for every query parameter (12 prompts).* Rejected -- adds keystrokes
   without operational value for the common case; defeats the junior-NOC-engineer
   audience standard. Operators with advanced filtering needs can call the SDK
   directly or wait for a future advanced variant.
3. *Add a fourth prompt for `limit`.* Rejected -- the API default of 100 is suitable
   for the common case (distinct values per site rarely exceed 100 for the
   recommended grouping fields), and increasing `limit` is a workaround for missing
   server-side pagination on this endpoint that is better solved by a follow-up
   feature.
