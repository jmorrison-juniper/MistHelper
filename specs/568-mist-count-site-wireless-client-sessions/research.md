# Phase 0 Research: countSiteWirelessClientSessions

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/sites/GET_sites_site_id_clients_sessions_count.md` (enriched
OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors
the OpenAPI URL:
`mistapi.api.v1.sites.clients.sessions.count.countSiteWirelessClientSessions(apisession, site_id, distinct=None, ap=None, band=None, client_family=None, client_manufacture=None, client_model=None, client_os=None, ssid=None, wlan_id=None, start=None, end=None, duration="1d", limit=100)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single JSON object (not a list, not paginated), with the
following top-level keys per the doc:

- `distinct` (string -- the attribute the API grouped by, echoed from the query)
- `start` (int32 epoch seconds -- start of the time window the count covers)
- `end` (int32 epoch seconds -- end of the time window the count covers)
- `limit` (int32 -- max rows returned in `results`, default 100)
- `total` (int32 -- total number of unique values seen for the distinct attribute)
- `results` (array of objects with one required `count` field plus additional
  string-typed properties whose key is the `distinct` attribute name and whose
  value is the observed grouping value -- e.g. for `distinct=ssid` each result is
  `{"count": 42, "ssid": "Guest-WiFi"}`)

Required path parameter: `site_id` (UUID string).
Required from a user POV: `distinct` (the attribute to group by). The SDK marks it
optional, but the result is materially less useful without it because the API
applies an internal default; MistHelper makes it a required prompt with a sensible
default of `ssid`.
Optional query parameters (passed through when set): `ap`, `band`, `client_family`,
`client_manufacture`, `client_model`, `client_os`, `ssid`, `wlan_id`, `start`,
`end`, `duration`, `limit`.

**Rationale**:
The mistapi SDK organizes modules by URL path, not OpenAPI tag (verified by the
URL `/sites/{site_id}/clients/sessions/count` -> module
`mistapi.api.v1.sites.clients.sessions.count`). The spec.md explicitly names this
module path and it matches the URL one-for-one. The enriched per-endpoint doc
lists a slightly different SDK hint
(`mistapi.api.v1.sites.clients_-_wireless.countSiteWirelessClientSessions()`),
but that is a tag-derived alias and the URL-derived path is canonical. Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.clients.sessions import count; help(count)"`
inside the venv.

The `results` array uses `additionalProperties: { type: string }` so the grouping
field name is dynamic: each result object always contains `count` plus one extra
string-typed key whose name equals the `distinct` value. MistHelper flattens this
into a fixed-shape table with columns `distinct_field` (the grouping attribute
name) and `distinct_value` (the observed value), keeping the SQLite schema stable
regardless of which distinct attribute the user chose.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/clients/sessions/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the tag-derived SDK path (`...sites.clients_-_wireless...`).* Rejected --
   the SDK organizes modules by URL path; the URL-derived path matches the spec
   and every adjacent count/search endpoint follows the same convention.
3. *Map every distinct attribute to its own SQLite column.* Rejected -- explodes
   to one schema per `distinct` value (ssid, ap, band, ...) and forces ALTER
   TABLE on every new value. The two-column normalized shape
   (`distinct_field`, `distinct_value`) is portable and SQL-friendly.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `site_wireless_session_count_summary`: PK =
  `(site_id, distinct_field, start, end)` -- one row per (site, grouping
  attribute, time window).
- `site_wireless_session_count_results`: PK =
  `(site_id, distinct_field, start, end, distinct_value)` -- one row per distinct
  value within that summary.

Both registrations use type `composite_pk` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
`site_id` is injected by MistHelper before the upsert (Mist does not return it
in the body but MistHelper always knows which site the call targeted).

**Rationale**:
The endpoint returns an aggregate count over a *site*, grouped by a *distinct*
attribute, over a specific *start/end* window. Re-running the same
(site, distinct, window) tuple must update the existing rows rather than append
duplicates. `start` and `end` are returned in the response body, so they are
reliable PK fields rather than client-supplied parameters that could drift. The
detail table's PK extends the summary PK with `distinct_value`, which is exactly
one row per observed grouping value. `INSERT OR REPLACE` upserts every poll's
view of the same window cleanly.

**Alternatives Considered**:

1. *`auto_increment_with_unique` on a single combined table.* Rejected -- would
   let repeated polls accumulate duplicate snapshots of the same window,
   defeating the upsert behavior the spec requires (FR-005, FR-003).
2. *Single combined table with summary fields denormalized onto every result
   row.* Rejected -- wastes storage, blocks clean summary-only queries, and
   mixes two grain levels (per-window vs per-distinct-value).
3. *PK on (site_id, distinct_field, distinct_value) without time window.*
   Rejected -- two calls with different `duration` values would conflict on the
   same key and overwrite each other, losing the previous window.
4. *`natural_pk` on a single derived hash of all PK fields.* Rejected -- opaque
   keys block ad-hoc SQL queries; composite_pk keeps every PK field
   query-friendly.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary):
  `data/site_<site_id_short>_session_count_<distinct_field>_summary.csv`
- CSV (results):
  `data/site_<site_id_short>_session_count_<distinct_field>_results.csv`
- SQLite tables: `site_wireless_session_count_summary` and
  `site_wireless_session_count_results`
- `site_id_short` is the first 8 hex characters of the site UUID -- the
  convention already used by adjacent site-level exports in MistHelper for
  human-readable filenames without leaking full UUIDs into shell history.
- `<distinct_field>` is the literal grouping attribute (e.g. `ssid`, `ap`,
  `band`) so successive runs with different groupings produce side-by-side
  CSVs.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is
`"countSiteWirelessClientSessions"` for the summary write and
`"countSiteWirelessClientSessionsResults"` (a MistHelper-internal sub-table id)
for the results write. The DataExporter uses these strings as lookup keys into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by the adjacent `searchSiteClientSessions` and
other site-stats exports. Two output files / two SQLite tables keeps the schema
clean and lets a user query the per-distinct-value count without joining when
they don't need the summary metadata. Embedding `<distinct_field>` in the CSV
name avoids overwriting prior runs against the same site with a different
grouping attribute.

**Alternatives Considered**:

1. *Single output file with a JSON-encoded `results` column.* Rejected --
   breaks SQL queryability and conflicts with the flattening convention used
   everywhere else in MistHelper.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into
   shell history and ls output unnecessarily. The 8-char short form is enough
   to disambiguate locally.
3. *Omit `<distinct_field>` from the filename.* Rejected -- successive calls
   for the same site with different grouping attributes would overwrite each
   other, surprising the user.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 91**, sitting at the top of the
Site Stats cluster (80-91), adjacent to the existing site-level wireless
client and session statistics exports. The category label is "Interactive Safe
-- Site Stats".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu
ranges as: 1-59 Safe Org Exports, 60-96 Interactive Safe (with 80-91 Site
Stats and 92-96 Viewers), 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. A wireless-session
count aggregation is a read-only site stat, so it belongs in the 80-91 Site
Stats sub-cluster. 91 is the next available integer at the top of that
sub-cluster, comfortably below the Viewers block (92-96) and well below the
resource-intensive block (96-101). The number is provisional -- at
`/speckit.tasks` time, MistHelper.py is grep'd for the latest allocated menu
integer and 91 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a
   single GET that returns a small JSON object capped by `limit` (default
   100). It does not warrant the resource-intensive treatment.
2. *Slot inside Safe Org Exports (1-59).* Rejected -- the endpoint is
   site-scoped, not org-scoped; placing it in the org cluster mis-signals
   scope to a junior NOC engineer scrolling the menu.
3. *Append to the end (e.g. 195).* Rejected -- the destructive cluster ends at
   194, and placing a read-only site stat above the destructive block
   visually mis-signals the risk level.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly three** values via
`safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context:
   `"site_wireless_session_count:site_id"`. Default: the value of
   `MIST_SITE_ID` in `.env` if present (pressing Enter accepts the default).
   Validated via the existing `is_valid_uuid()` helper before the API call;
   on failure, log `WARNING` and return early.
2. `distinct_field` -- prompt:
   `"Distinct grouping (ssid|ap|band|client_family|client_manufacture|client_model|client_os|wlan_id) [ssid]: "`,
   context: `"site_wireless_session_count:distinct"`. Default: `ssid`.
   Validated against an allow list of exactly those eight values; any other
   value logs `WARNING` and the method returns early.
3. `duration` -- prompt:
   `"Duration (e.g. 1d, 7d, 2w, 1h) [1d]: "`, context:
   `"site_wireless_session_count:duration"`. Default: `1d`. Passed verbatim
   to the SDK as the `duration` query parameter; the Mist API performs its
   own parsing and rejection of malformed values.

The remaining optional filter parameters (`ap`, `band`, `client_family`,
`client_manufacture`, `client_model`, `client_os`, `ssid`, `wlan_id`,
`start`, `end`, `limit`) are NOT prompted. They are left at SDK defaults
(`None` / unset). A future spec can add an advanced-filter prompt path if
operators request it; for the initial menu item, three prompts keep the
operation simple and the method comfortably under the 5-Item Rule.

`.env` values used (loaded via the existing `python-dotenv` bootstrap,
never logged):

- `MIST_HOST` (e.g. `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

**Rationale**:
The Mist `count` endpoint is fundamentally parameterized by *which site*,
*which attribute to group by*, and *over what time window*. Those three
choices determine the result shape and are the minimum viable input set. The
remaining query parameters are server-side filters; defaulting them to unset
returns the full, unfiltered grouping -- which is what an operator
investigating a site almost always wants on first inspection. Asking for
every optional filter up front would balloon the prompt count past the
5-Item Rule on the method body and slow down the common case.

**Alternatives Considered**:

1. *Single prompt that accepts a JSON blob of filter overrides.* Rejected --
   junior NOC engineers (the target audience) should not need to compose
   JSON to run a stats query.
2. *Eight separate prompts for every optional filter.* Rejected -- explodes
   the method past the 25-line / 5-block ceiling, and most operators leave
   the filters at default on a first look.
3. *Hard-code `distinct=ssid` instead of prompting.* Rejected -- the
   endpoint's primary value is its ability to group by different attributes;
   forcing one value defeats the purpose.
