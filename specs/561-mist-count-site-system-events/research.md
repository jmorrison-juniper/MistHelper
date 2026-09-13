# Phase 0 Research: countSiteSystemEvents

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/sites/GET_sites_site_id_events_system_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.sites.events.system.count.countSiteSystemEvents(
apisession, site_id, distinct=None, type=None, start=None, end=None, duration="1d",
limit=100)`. The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the
parsed JSON body. The body is a single JSON object with these top-level keys per the
doc:

- `distinct` (string) -- echoes the distinct attribute requested.
- `start` (int32 epoch seconds) -- start of the count window.
- `end` (int32 epoch seconds) -- end of the count window.
- `limit` (int32) -- bucket cap (default 100).
- `total` (int32) -- total events counted in window across all buckets.
- `results` (array of objects, unique) -- one object per distinct-value bucket. Each
  object has `count` (int32, required) plus arbitrary additional string properties
  (the distinct attribute value, e.g., `type`, `device_type`, `model`).

Required path parameter: `site_id` (UUID string).
Optional query parameters:

- `distinct` (string) -- attribute to bucket by. No documented enum; common values
  align with the searchable event fields (`type`, `device_type`, `model`, etc.).
- `type` (string) -- event type filter (cross-reference List Device Events Definitions).
- `start` (epoch seconds or relative string like `-1d`, `-1w`).
- `end` (epoch seconds or relative string like `-1h`, `now`).
- `duration` (string, default `1d`) -- like `7d`, `2w`.
- `limit` (int, default 100).

**Rationale**:
The spec.md explicitly names the SDK module path
`mistapi.api.v1.sites.events.system.count`, which mirrors the OpenAPI URL one-for-one
(`/sites/{site_id}/events/system/count`). The enriched per-endpoint doc shows the SDK
as `mistapi.api.v1.sites.events.countSiteSystemEvents()`, which appears to be an
abbreviated form. The mistapi SDK consistently generates module paths from the URL
path, so the spec's URL-derived path is authoritative. Final verification happens at
implementation time via `python -c "from mistapi.api.v1.sites.events.system import
count; help(count)"` inside the venv; if the SDK actually exposes the function at
`mistapi.api.v1.sites.events.countSiteSystemEvents`, the import is adjusted in one
line.

**Alternatives Considered**:

1. *Direct `requests.get` against `https://{host}/api/v1/sites/{site_id}/events/system/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the abbreviated path from the doc (`...sites.events.countSiteSystemEvents`).*
   Deferred -- accepted as a fallback if the URL-derived path is not exposed at
   import time. The spec's path is tried first per its authoritative status.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on one output table
`site_system_events_count` with the natural-business-key tuple
`(site_id, distinct_attribute, window_start, window_end, distinct_value)`.

- `site_id` -- supplied by MistHelper context (the API does not echo it in the body).
- `distinct_attribute` -- echoes the `distinct` field from the response.
- `window_start` -- epoch seconds from response `start`.
- `window_end` -- epoch seconds from response `end`.
- `distinct_value` -- the bucket key (e.g., `type=AP_RESTART`). Since each item in
  `results[]` carries the bucket key as an arbitrary string property whose name
  equals `distinct`, MistHelper extracts it during flatten.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` with
`primary_key = ['site_id', 'distinct_attribute', 'window_start', 'window_end',
'distinct_value']`.

**Rationale**:
The endpoint produces a snapshot of grouped counts for a given site, distinct
attribute, and time window. Re-running the same query (same site, same `distinct`,
same window) must overwrite the previous snapshot rather than accumulate duplicates,
because Mist's underlying event store may report adjusted counts as late events
arrive. The five-tuple key captures every dimension that defines a bucket. SQLite
`INSERT OR REPLACE` then upserts cleanly on every poll.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- duplicates would accumulate on every
   poll and break the upsert contract in the spec.
2. *Drop `window_start` / `window_end` from the PK and rely on time-of-poll.*
   Rejected -- two distinct windows over the same site and same distinct attribute
   would collide on the PK and the second window would overwrite the first, losing
   data.
3. *`natural_pk` on a Mist-supplied id.* Rejected -- the response carries no
   per-bucket id; the only stable identifier is the composite tuple above.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/site_<site_id_short>_system_events_count_<distinct>_<window>.csv`
- SQLite table: `site_system_events_count`
- `site_id_short` is the first 8 hex characters of the site UUID -- matches the
  convention used by adjacent site exports for shell-history-safe filenames.
- `<distinct>` is the URL-safe form of the distinct attribute (e.g., `type`,
  `device_type`). When the user supplies no distinct, the literal `default` is used.
- `<window>` is the duration string supplied (e.g., `1d`, `7d`, `2w`). When the user
  supplies explicit start/end timestamps instead, the literal `custom` is used.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countSiteSystemEvents"` (matches the operationId exactly). The DataExporter
uses that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by sibling site-events exports in MistHelper. A
single table holds all buckets across all (site, distinct, window) tuples because the
composite PK already discriminates rows. The filename includes the distinct attribute
and window so a directory listing immediately shows which queries were run; the
SQLite table consolidates for easy SQL.

**Alternatives Considered**:

1. *One SQLite table per distinct attribute (e.g., `site_system_events_count_type`,
   `site_system_events_count_device_type`).* Rejected -- explodes the table count for
   no query benefit; the composite PK already separates rows cleanly.
2. *Full site UUID in the filename.* Rejected -- leaks UUIDs into shell history and
   `ls` output unnecessarily; the short form is enough for local disambiguation.
3. *JSON-encoded `results[]` column in a single row per query.* Rejected -- breaks
   SQL queryability and conflicts with the flattening convention used everywhere
   else in MistHelper.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 89**, sitting inside the Interactive Safe
Stats subcluster (80-91). The category label is "Interactive Safe -- Site Stats &
Counts".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe (with 73-79 Insights, 80-91 Stats,
92-96 Viewers), 97-101 + 153 Resource Intensive, 102-123 WebSocket, 124-152
Interactive, 154-194 Destructive. This endpoint is site-scoped and produces an
aggregated stat-style count, so the 80-91 Stats subrange is the natural home. 89 is
the next available integer below the boundary at 92 (Viewers) and well clear of the
resource-intensive block at 96-101. The number is provisional -- at `/speckit.tasks`
time, MistHelper.py is grep'd for the latest allocated menu integer and 89 is shifted
forward if a conflict exists.

**Alternatives Considered**:

1. *Slot in the org-events range (20-26).* Rejected -- this endpoint is site-scoped,
   not org-scoped. Junior NOC engineers expect site-scoped operations under
   Interactive Safe.
2. *Append to the end (e.g., 195).* Rejected -- placing a read-only safe operation
   above the destructive block (154-194) visually mis-signals the risk level.
3. *Resource Intensive cluster (96-101).* Rejected -- this is a single GET with a
   small bounded payload (default 100 buckets); no pagination iteration required.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for up to **four** values via `safe_input()`. The
first is mandatory; the other three have safe defaults and accept Enter-to-skip.

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_system_events_count:site_id"`. Default: the value of `MIST_SITE_ID` in
   `.env` if present. Validated via the existing `is_valid_uuid()` helper before the
   API call; on failure, log `WARNING` and return early.
2. `distinct` -- prompt: `"Distinct attribute (e.g., type, device_type, model)
   [type]: "`, context: `"site_system_events_count:distinct"`. Default: `type`.
   Passed straight through to the SDK as the `distinct` query parameter.
3. `event_type` -- prompt: `"Filter by event type (blank for all): "`, context:
   `"site_system_events_count:type"`. Default: empty string (omit the query
   parameter when blank). Passed as the `type` query parameter when non-empty.
4. `time_window` -- prompt: `"Time window (e.g., 1d, 7d, 2w) [1d]: "`, context:
   `"site_system_events_count:duration"`. Default: `1d`. Passed as the `duration`
   query parameter. The lower-level `start` and `end` epoch parameters are *not*
   exposed to the menu in the first iteration -- they are an advanced use case that
   can be added later without breaking the contract.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

**Rationale**:
The Mist endpoint is site-scoped and supports six optional query parameters. Exposing
all six as prompts would violate the 5-Item Rule on prompt count and overwhelm a
junior NOC engineer. The four chosen prompts cover the >90% case (site, distinct
attribute, optional type filter, time window) while keeping the menu interaction
short. Advanced epoch-precise start/end can be added later by accepting `--start`
and `--end` flags in non-interactive mode without changing the interactive prompt
sequence.

**Alternatives Considered**:

1. *Always pass `distinct=type` without prompting.* Rejected -- the value of this
   endpoint comes from the ability to pivot the count on different attributes; a
   fixed `distinct` would hide most of the API's capability from the operator.
2. *Add explicit `start` and `end` epoch prompts.* Rejected for the first iteration --
   accepting epoch seconds at an interactive prompt is error-prone for a junior NOC
   engineer; the `duration` shorthand covers the dominant use case.
3. *Read all four prompt defaults from a single `.env` block.* Rejected -- `.env`
   leakage of distinct/type/duration would silently change menu behavior across
   environments; only `MIST_SITE_ID` is allowed as a default.
