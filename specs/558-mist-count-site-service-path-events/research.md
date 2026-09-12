# Phase 0 Research: countSiteServicePathEvents

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/sites/GET_sites_site_id_services_events_count.md` (enriched
OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that
mirrors the OpenAPI URL:
`mistapi.api.v1.sites.services.events.count.countSiteServicePathEvents(
apisession, site_id, distinct=None, type=None, text=None, vpn_name=None,
vpn_path=None, policy=None, port_id=None, model=None, version=None,
timestamp=None, mac=None, start=None, end=None, duration="1d", limit=100)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the
parsed JSON body. The body is a single JSON object (count envelope, not a
list and not deeply paginated), with the following top-level keys per the
enriched doc:

- `distinct` (string) -- the field the API grouped by (echoes the query
  parameter).
- `start` (int32 epoch seconds) -- start of the query window the server
  evaluated.
- `end` (int32 epoch seconds) -- end of the query window the server
  evaluated.
- `limit` (int32) -- the `limit` the server applied (defaults to 100).
- `total` (int32) -- total event count matching the filter, summed across
  all buckets.
- `results` (array, unique) -- one element per distinct bucket. Each element
  has the required `count` (int32) plus an additional string property whose
  key equals the value of the `distinct` field and whose value is the bucket
  label. For example with `distinct=type`, each bucket looks like
  `{"count": 42, "type": "GW_SERVICE_PATH_DOWN"}`.

Required path parameter: `site_id` (UUID string).
Optional query parameters: `distinct`, `type`, `text`, `vpn_name`,
`vpn_path`, `policy`, `port_id`, `model`, `version`, `timestamp`, `mac`,
`start`, `end`, `duration` (default `1d`), `limit` (default 100).

**Rationale**:
The enriched per-endpoint doc lists the SDK module signature as
`mistapi.api.v1.sites.services.countSiteServicePathEvents()`, while the spec
.md (the authoritative feature contract) names
`mistapi.api.v1.sites.services.events.count`. The mistapi SDK historically
generates module paths from the URL, not the OpenAPI tag, and the URL is
`/api/v1/sites/{site_id}/services/events/count` -- which maps one-for-one to
`mistapi.api.v1.sites.services.events.count`. We follow the spec. Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.services.events import count;
help(count)"` inside the venv; if the actual SDK exposes the function under
the shorter `mistapi.api.v1.sites.services` namespace (the form used by some
older mistapi releases), the import statement is adjusted before commit and
the contract file is updated accordingly.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/services/events/count`.* Rejected --
   the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc's SDK line
   (`mistapi.api.v1.sites.services`).* Rejected as primary -- the URL-derived
   path matches the SDK's generation rule. Kept as a documented fallback if
   the runtime `help()` check shows the older layout.
3. *Wrap the call in a generic "count-by-distinct" helper shared across all
   `/count` endpoints.* Rejected for this spec -- premature generalization;
   would violate the spec's "one menu item, one method" scope and the
   constitution's class-based principle. Future deduplication is a separate
   refactor.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`site_service_path_events_count`:

- PK = `(site_id, distinct_field, distinct_value, start, end)` -- one row per
  bucket per query window per site.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`,
with `site_id`, `distinct_field`, `start`, and `end` injected by MistHelper
before the upsert (Mist returns `distinct`, `start`, and `end` in the
envelope but does *not* return `site_id` in the body -- MistHelper always
knows which site the call targeted).

**Rationale**:
The endpoint reports aggregated counts for a caller-chosen time window and a
caller-chosen `distinct` field. Re-running the same query (same site, same
distinct, same window) against the same site must *replace* the prior result
rather than append a duplicate -- counts may shift as Mist post-processes
late-arriving events. The five-tuple
`(site_id, distinct_field, distinct_value, start, end)` uniquely identifies
a single bucket within a single query. Pairing all five guarantees one row
per (site, distinct field, bucket value, window) and lets `INSERT OR REPLACE`
upsert every poll. Cross-window snapshots are preserved because `start`/`end`
are part of the key -- the user can re-run the menu for yesterday and today
and both windows are retained.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls of
   the same window accumulate duplicate snapshots, defeating the upsert
   behavior the spec requires.
2. *`natural_pk` on a server-side bucket id.* Rejected -- the API response
   does not include a stable bucket id; only the `distinct` field value
   (which is not unique across distinct types).
3. *Single-column synthetic key built by hashing the five-tuple.* Rejected
   -- harder to query (no per-site WHERE), and the composite PK is already
   supported by the existing PK strategy framework.
4. *Composite without `start`/`end`.* Rejected -- would clobber previous
   windows when the user re-runs with a different time range, losing
   historical snapshots.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/site_<site_id_short>_service_path_events_count_<distinct_field>.csv`
- SQLite table: `site_service_path_events_count`
- `site_id_short` is the first 8 hex characters of the site UUID -- already
  the convention used by adjacent site exports in MistHelper for
  human-readable filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is
`"countSiteServicePathEvents"` (matching the operationId). The DataExporter
uses that string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by adjacent site-events exports
(`searchSiteServicePathEvents` and friends). Embedding the `distinct_field`
in the CSV filename lets a user run the menu repeatedly with different
distinct selections without overwriting prior CSV output, while the single
SQLite table holds all distinct selections side by side (the `distinct_field`
column is part of the composite PK).

**Alternatives Considered**:

1. *One SQLite table per `distinct` field
   (`site_service_path_events_count_by_type`, `..._by_vpn_name`, ...).*
   Rejected -- table sprawl, harder to query across distinct dimensions, and
   the schema is identical so a single table with a `distinct_field` column
   is cleaner.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into
   shell history and `ls` output unnecessarily. The short form is enough to
   disambiguate locally.
3. *Single fixed filename
   (`data/site_service_path_events_count.csv`).* Rejected -- a user running
   for two different sites in the same session would clobber the first
   site's CSV.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting at the top of the
Interactive Safe / Viewers cluster (92-96), just below the Resource Intensive
block that begins at 97. The category label is "Interactive Safe -- Site
Stats / Service Path Events Count".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu
ranges as: 1-59 Safe Org Exports, 60-96 Interactive Safe (Site devices
60-72, Insights 73-79, Stats 80-91, Viewers 92-96), 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. This
endpoint is a site-scoped read-only count viewer that returns pre-aggregated
data -- it fits squarely in the Viewers sub-cluster (92-96). Slot 96 is the
next contiguous integer below the resource-intensive block at 97-101 and is
far from the destructive block at 154-194. The number is provisional -- at
`/speckit.tasks` time, MistHelper.py is grepped for the latest allocated
menu integer and 96 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside Site Stats (80-91).* Rejected -- the Stats cluster is
   primarily for raw stats endpoints (device/client metrics, port counters);
   service-path events are an event family, not a stat, and the Viewers
   cluster is the better semantic home.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is
   a single GET that returns a small pre-aggregated response, with no
   pagination and no long-running work. It belongs in the safe block.
3. *Append to the end of the destructive cluster (e.g., 195).* Rejected --
   the destructive cluster ends at 194, and placing a read-only viewer above
   the destructive block visually mis-signals the risk level to a junior NOC
   engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **four** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_service_path_events_count:site_id"`. Default: the value of
   `MIST_SITE_ID` in `.env` if present (pressing Enter accepts the default).
   Validated via the existing `is_valid_uuid()` helper before the API call;
   on failure, log `WARNING` and return early.

2. `distinct_field` -- prompt: `"Group by distinct field
   [type|vpn_name|vpn_path|policy|port_id|model|version|mac] (default:
   type): "`, context: `"site_service_path_events_count:distinct"`.
   Default: `type` (the most operationally useful grouping for a NOC
   engineer triaging service-path stability). Validated against the
   documented enum before the API call; unknown value -> log `WARNING` and
   return early.

3. `start` -- prompt: `"Start of window (epoch seconds OR relative like
   '-1d', '-1w'; blank for default 1d window): "`, context:
   `"site_service_path_events_count:start"`. Default: blank (the API uses
   `duration=1d` ending at "now" when both `start` and `end` are omitted).
   Passed through to the SDK unmodified; the mistapi SDK accepts both
   integer epoch values and relative strings.

4. `end` -- prompt: `"End of window (epoch seconds OR relative like 'now',
   '-1h'; blank for now): "`, context:
   `"site_service_path_events_count:end"`. Default: blank.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

No additional secondary filters (`type`, `text`, `vpn_name`, `vpn_path`,
`policy`, `port_id`, `model`, `version`, `timestamp`, `mac`) are prompted in
this menu's first iteration -- they are passed as `None` to the SDK and the
server returns all buckets. A future enhancement can add an optional
"additional filters" sub-prompt without breaking the contract.

**Rationale**:
The Mist count endpoint is site-scoped, so `site_id` is unavoidable. The
`distinct` parameter materially changes the response shape, so prompting
keeps the menu item useful across the eight documented distinct fields. Time
window prompts default to "blank" so a junior NOC engineer can press
Enter twice and get yesterday's stats with no thinking; the SDK supports
both epoch ints and relative strings (`-1d`, `now`), so we pass-through
without local parsing. Keeping the prompt count to four respects the
five-item rule and avoids prompt fatigue.

**Alternatives Considered**:

1. *Only prompt for `site_id`, hard-code `distinct=type`.* Rejected -- the
   `distinct` field is the entire point of a count endpoint; restricting it
   would defeat the menu's value.
2. *Prompt for every query parameter (all 14).* Rejected -- 14 prompts is
   prompt fatigue and violates the five-item-rule spirit (UX-level
   complexity). Secondary filters can be added in a follow-up menu item or
   an "advanced mode" toggle without breaking this contract.
3. *Use a single combined "time window" prompt accepting `duration` (e.g.,
   `7d`).* Rejected -- the spec lists `start`, `end`, and `duration` as
   peer parameters; users sometimes want absolute windows for incident
   forensics. Keeping `start`/`end` as the prompts and letting the SDK
   fall back to `duration=1d` when both are blank covers both use cases.
