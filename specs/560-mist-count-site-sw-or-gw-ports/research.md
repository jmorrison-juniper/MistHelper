# Phase 0 Research: countSiteSwOrGwPorts

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/sites/GET_sites_site_id_stats_ports_count.md` (enriched OpenAPI
doc, lines 1-164).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.sites.stats.ports.count.countSiteSwOrGwPorts(apisession,
site_id, distinct=None, **filters, start=None, end=None, duration="1d", limit=100)`.
The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the parsed
JSON body. The body is a single JSON object (an envelope), not a paginated list,
shaped per the 200 schema in the doc:

- `distinct` (string) -- echoes the requested distinct field.
- `start` (int epoch seconds) -- start of the window the count covers.
- `end` (int epoch seconds) -- end of the window the count covers.
- `limit` (int) -- echoes the requested limit (default 100).
- `total` (int) -- total number of distinct buckets across all pages.
- `results` (array of `count_result` objects) -- one entry per bucket. Each item is
  `{ "count": <int>, ...additional string properties... }`, where the additional
  properties carry the bucket label(s) for the chosen distinct field (for example
  `{"count": 142, "up": "true"}` when `distinct=up`).

Required path parameter: `site_id` (UUID string). All other parameters are optional
query filters that the SDK serializes as URL query keys. Pagination is offered via
`limit` plus `page` (per the enriched doc); MistHelper exposes the first page only in
the initial implementation since the `total` field tells the user whether deeper
pages are warranted -- a future task can add a `--paginate` flag.

**Rationale**:
The mistapi SDK organizes modules by URL path, not by OpenAPI tag. The enriched doc
explicitly lists the SDK as `mistapi.api.v1.sites.stats_-_ports.countSiteSwOrGwPorts()`
which is a hyphenation artifact of the tag `Sites Stats - Ports`. The actual Python
module path uses underscore-only naming derived from the URL segments, matching the
spec.md SDK module declaration `mistapi.api.v1.sites.stats.ports.count`. Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.sites.stats.ports import count; help(count)"` inside
the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/sites/{site_id}/stats/ports/count`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`...sites.stats_-_ports...`).* Rejected --
   the hyphen artifact is purely a documentation render. The URL-based path is
   canonical for every other endpoint in the SDK.
3. *Paginate eagerly across all pages on first invocation.* Rejected -- the endpoint
   is a count primitive, not a record-export primitive. Most operators want the
   summary, not 10,000+ buckets, so the first-page-plus-total contract matches the
   intent. A follow-up spec can add deep pagination behind an opt-in flag.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `site_port_count_summary`: PK = `(site_id, distinct_field, window_start,
  window_end)` -- one envelope row per (site, distinct dimension, time window).
- `site_port_count_results`: PK = `(site_id, distinct_field, window_start,
  window_end, bucket_label)` -- one bucket row per envelope. `bucket_label` is the
  stringified value of the bucket-defining property in each `count_result` element
  (for example `"true"`, `"1000"`, `"Kumar-Acc-SW.mist.local"`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registrations use type `composite_pk` for both
tables. MistHelper injects `site_id`, `distinct_field`, `window_start`, `window_end`
before each upsert (Mist returns them in the envelope; `distinct_field` echoes the
user-supplied parameter and is rewritten to the canonical lowercase form before use).

**Rationale**:
The endpoint reports counts as of a specific time window for a specific distinct
dimension. Re-running with the same (site, distinct, window) inputs must update the
existing rows rather than append duplicates -- the bucket counts may have changed
because new port stats arrived from the line cards. `(site_id, distinct_field,
window_start, window_end)` is the natural key for the envelope; appending
`bucket_label` gives a stable, unique row per bucket inside that envelope. `INSERT OR
REPLACE` semantics make every poll idempotent.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would accumulate duplicate snapshots on
   every poll and defeat the upsert behavior FR-003 (rate limiting) and FR-004
   (multi-backend write) require.
2. *Single flat table with envelope columns repeated on every bucket row.* Rejected --
   wastes storage, denormalizes the envelope, and complicates the SQLite schema by
   forcing nullable envelope fields when the bucket is absent.
3. *`natural_pk` on a server-generated id.* Rejected -- the response contains no
   server-side id for either the envelope or individual buckets; only the bucket
   contents themselves are identifying.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/site_<site_id_short>_port_count_summary.csv`
- CSV (buckets): `data/site_<site_id_short>_port_count_results.csv`
- SQLite tables: `site_port_count_summary` and `site_port_count_results`
- `site_id_short` is the first 8 hex characters of the site UUID -- already the
  convention used by adjacent site-stats exports in MistHelper for human-readable
  filenames without leaking full UUIDs into shell history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"countSiteSwOrGwPorts"` (matching
the operationId) for the summary write, and a MistHelper-internal key
`"countSiteSwOrGwPortsResults"` for the buckets write. The DataExporter uses those
strings as lookup keys into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `searchSiteSwOrGwPorts` (the sibling
record-export endpoint referenced by Menus 14, 29, 31). Two output files / two
SQLite tables keeps the schema clean and lets an operator query the summary without
joining when they only want the total or distinct-field echo, while still allowing
bucket-level analytics on the second table.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `results` column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used everywhere else
   in MistHelper.
2. *Full site UUID in the filename.* Rejected -- leaks the site UUID into shell
   history and `ls` output unnecessarily. The short form is enough to disambiguate
   locally.
3. *One combined table with envelope columns duplicated on every bucket row.*
   Rejected (see Research Task 2) -- denormalizes the envelope without benefit.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 89**, sitting inside the Stats cluster
(80-91). The category label is "Stats -- Site Port Counts". This places it next to
the existing port-search and switch-metrics operations referenced by Menus 14, 29,
and 31 in the enriched API doc.

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the menu ranges as:
1-59 Safe Org Exports, 60-96 Interactive Safe (with 80-91 = Stats and 92-96 =
Viewers), 97-101 + 153 Resource Intensive, 102-123 WebSocket, 124-152 Interactive,
154-194 Destructive. Site-level port counts are a stats primitive (not a viewer,
not a destructive op, not WebSocket), so the 80-91 Stats cluster is the correct
placement. 89 is the next contiguous integer that keeps the new op visually adjacent
to its siblings. The number is provisional -- at `/speckit.tasks` time MistHelper.py
is grep'd for the highest allocated integer in the 80-91 range and 89 is shifted
forward if a conflict exists.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- 154-194 is the destructive cluster,
   and placing a read-only count above the destructive block visually mis-signals
   the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns at most `limit=100` bucket rows in one call; no long-running
   work, no eager pagination in the initial implementation. It belongs in the safe
   Stats block.
3. *Slot inside Viewers (92-96).* Rejected -- this is a write-to-disk export, not an
   interactive viewer that renders to the terminal. The Stats cluster matches the
   write-to-disk pattern.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for up to **three** values via `safe_input()`:

1. `site_id` -- prompt: `"Site ID (UUID): "`, context: `"site_port_count:site_id"`.
   Default: the value of `MIST_SITE_ID` in `.env` if present (pressing Enter accepts
   the default). Validated via the existing `is_valid_uuid()` helper before the API
   call; on failure, log `WARNING` and return early.
2. `distinct_field` -- prompt: `"Distinct field (press Enter for default 'up'): "`,
   context: `"site_port_count:distinct"`. Default: `up`. Validated against the
   spec.md query-parameter enum (`full_duplex`, `mac`, `neighbor_mac`,
   `neighbor_port_desc`, `neighbor_system_name`, `poe_disabled`, `poe_mode`,
   `poe_on`, `port_id`, `port_mac`, `power_draw`, `tx_pkts`, `rx_pkts`, `rx_bytes`,
   `tx_bps`, `rx_bps`, `tx_mcast_pkts`, `tx_bcast_pkts`, `rx_mcast_pkts`,
   `rx_bcast_pkts`, `speed`, `stp_state`, `stp_role`, `auth_state`, `up`) before
   the SDK call; on invalid value, log `WARNING` and return early.
3. `duration` -- prompt: `"Window duration (default '1d'): "`, context:
   `"site_port_count:duration"`. Default: `1d` (matches the OpenAPI doc default).
   Passed verbatim to the SDK.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_SITE_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is site-scoped, so `site_id` is non-negotiable. The `distinct` parameter
materially changes the meaning of the response (each value buckets the count by a
different port attribute) and is the operator's primary lever for asking a useful
question, so it gets its own prompt. `duration` is the most-commonly-tuned time-range
parameter and has a sensible default (`1d`); the lower-level `start`/`end` epoch
parameters are not prompted in the initial implementation because they overlap with
`duration` and add cognitive load for a junior NOC engineer. They can be exposed via
a follow-up spec if operators ask for them.

**Alternatives Considered**:

1. *One prompt only (site_id), hard-code distinct=up.* Rejected -- the endpoint's
   value lies in the user choosing the bucket dimension. Locking it to `up` reduces
   the menu to a one-trick boolean count of up/down ports, which barely exceeds
   what `searchSiteSwOrGwPorts` already provides.
2. *Prompt for all 28 query parameters.* Rejected -- violates Five-Item Rule on user
   experience (an operator should not face 28 sequential prompts) and almost all
   filters are rarely used. The spec already calls out `safe_input()` for prompts
   and a small set is consistent with adjacent menu items.
3. *Expose `limit` as a prompt.* Rejected -- the OpenAPI default of 100 covers the
   common case; an operator who needs more can edit the constant on a one-line
   patch, and a future paginated variant will own deeper retrieval.
