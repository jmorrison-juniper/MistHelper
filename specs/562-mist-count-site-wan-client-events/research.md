# Phase 0 Research: countSiteWanClientEvents

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/sites/GET_sites_site_id_wan_client_events_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that
mirrors the OpenAPI URL:

```python
from mistapi.api.v1.sites.wan_client.events import count as wan_event_count
response = wan_event_count.countSiteWanClientEvents(
    apisession,
    site_id,
    distinct=None,   # optional grouping field
    type=None,       # optional Mist event type filter
    start=None,      # optional epoch seconds or relative string
    end=None,        # optional epoch seconds or relative string
    duration="1d",   # default per OpenAPI doc
    limit=100,       # default per OpenAPI doc
)
```

The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the
parsed JSON body. The body is a single JSON object (not paginated by `page=`
cursor; `limit` caps the size of the `results` array on the server). Top-level
keys per the doc:

- `distinct` (string -- echoes the field used for grouping)
- `start` (int epoch seconds)
- `end` (int epoch seconds)
- `limit` (int -- result cap echoed back)
- `total` (int -- total events counted across the window before grouping)
- `results` (array of objects: each has a required `count` integer plus
  arbitrary `additionalProperties` of type string -- the actual grouped
  attribute name/value pair, e.g. `{"count": 42, "type": "WAN_EDGE_PORT_DOWN"}`)

Required path parameter: `site_id` (UUID string).
Optional query parameters: `distinct`, `type`, `start`, `end`, `duration`,
`limit`. The `type` enum values come from
`mistapi.api.v1.consts.events.listDeviceEventsDefinitions` (cross-referenced in
the enriched doc).

**Rationale**:
The enriched doc names the SDK as
`mistapi.api.v1.sites.clients_-_wan.countSiteWanClientEvents()`, but Python
modules cannot contain hyphens, so that string is an OpenAPI-tag-derived
display name, not the importable path. The mistapi SDK historically generates
module paths from the URL, not the tag (verified against adjacent endpoints
under the same base, e.g. `searchSiteWanClientEvents` at
`mistapi.api.v1.sites.wan_client.events.search`). The spec.md explicitly names
`mistapi.api.v1.sites.wan_client.events.count`, which matches the URL one-for-one,
so we follow the spec. Final import verification happens at implementation time:

```powershell
python -c "from mistapi.api.v1.sites.wan_client.events import count; help(count.countSiteWanClientEvents)"
```

**Alternatives Considered**:

1. *Direct `requests.get` against the full URL.* Rejected -- the constitution
   forbids direct HTTP when a mistapi method exists.
2. *Use the tag-derived display name verbatim.* Rejected -- the string contains
   hyphens and is not a valid Python identifier; the SDK organizes modules by
   URL, not tag.
3. *Call the matching POST `searchSiteWanClientEvents` and count client-side.*
   Rejected -- moves aggregation off the Mist server, costs paging, and
   wastes the dedicated count endpoint that already returns the same shape in
   one round trip.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`site_wan_client_events_count`:

```python
'countSiteWanClientEvents': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'distinct', 'group_value', 'start', 'end'],
    'indexes': ['site_id', 'distinct'],
    'table': 'site_wan_client_events_count',
}
```

- `site_id` is injected by MistHelper (the Mist response does not echo it).
- `distinct` is the grouping field echoed by the server (e.g. `"type"`).
- `group_value` is the value of that grouping field on each result row
  (extracted from `results[i].additionalProperties` -- the single non-`count`
  key/value pair per row).
- `start` / `end` are the resolved epoch-second window boundaries echoed by
  the server. They make the same `(site, distinct)` pair distinct across
  different time windows.

When `results` is empty (no events matched the filter) MistHelper writes a
single sentinel row with `group_value=NULL` and `count=0` so the SQLite upsert
still records that the poll happened.

**Rationale**:
The endpoint is a stateless aggregation, not a stable entity, so neither
`natural_pk` (no API-issued UUID exists) nor `auto_increment_with_unique`
(would cause duplicate rows across polls) fits. The natural key is the tuple
that uniquely identifies one cell in the count cube:
`(site, distinct field, distinct value, time window start, time window end)`.
`INSERT OR REPLACE` upserts the latest count on every poll, which is the
desired semantic: the row always reflects the most recent observation for that
cell.

**Alternatives Considered**:

1. *natural_pk on a server-issued id.* Rejected -- no such id is returned;
   the endpoint is purely a roll-up.
2. *auto_increment_with_unique on (site, distinct, value, start, end).*
   Rejected -- composite_pk is simpler and produces the same upsert behavior
   with one fewer column.
3. *Two-table split (summary + results).* Rejected -- the summary fields
   (`total`, `limit`) are derivable from the result rows; splitting adds an
   extra table for no read-time benefit. The summary scalars are denormalized
   onto every result row instead.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV filename: `data/site_<first-8-of-site-uuid>_wan_client_events_count.csv`
- SQLite table: `site_wan_client_events_count`
- ArangoDB collection: `site_wan_client_events_count`
- Redis key prefix: `site_wan_client_events_count:<site_id>:<distinct>:<value>`

All paths are produced via `os.path.join(DATA_DIR, ...)` so Windows /
Linux container parity is preserved. The first-8-of-UUID prefix matches the
existing convention used by `searchSiteWanClientEvents` and adjacent site-WAN
exports.

**Rationale**:
The naming follows the established MistHelper convention
`site_<id-prefix>_<noun>_<verb>.csv` (e.g. `site_<id>_wan_clients_search.csv`,
`site_<id>_wan_clients_count.csv`). Using the same noun-phrase
`wan_client_events_count` keeps related files grouped lexicographically in
`data/` directory listings, which junior NOC engineers grep through manually.

**Alternatives Considered**:

1. *Use the full org or site UUID in the filename.* Rejected -- 36-char UUIDs
   make `data/` listings unreadable in narrow terminals; the existing 8-char
   prefix has been sufficient for disambiguation in practice.
2. *One file per `distinct` value.* Rejected -- doubles file count for no
   benefit; the `distinct` column inside the file is sufficient to filter.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Place the new operation at menu number **91**, inside the existing site-stats
cluster (operations 80-91 per the AI agent instructions). The label is
`Count Site WAN Client Events (by distinct attribute)`.

**Rationale**:
Per `.github/copilot-instructions.md` the menu ranges are:

- 60-72 Site devices
- 73-79 Insights
- 80-91 Stats <- this endpoint
- 92-96 Viewers
- 97-101 Resource intensive

`countSiteWanClientEvents` is a site-level aggregation read -- the textbook
fit for the Stats cluster. Menu 91 is the highest open integer in that
cluster, immediately adjacent to the existing related WAN-client search and
count endpoints, which gives a junior NOC engineer browsing the menu a
natural top-to-bottom progression: search events -> count events. The full
menu list will be re-verified at task generation time; if 91 is taken by
another in-flight feature branch the next free integer in the same cluster
(or 96 if Stats is full) is used.

**Alternatives Considered**:

1. *Place in 92-96 Viewers cluster.* Rejected -- this endpoint produces a
   data export, not an interactive viewer.
2. *Place in 73-79 Insights cluster.* Rejected -- Insights are AI-derived
   summaries; this is a raw count.
3. *Place at the very end of the safe range (e.g. 96).* Rejected -- breaks
   the "stats endpoints live in 80-91" semantic the menu relies on.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**:
The new method prompts the user via `safe_input()` for the following values
in this order, with the listed `.env` defaults:

| Prompt order | Variable     | Required | Default source           | Validation |
|--------------|--------------|----------|--------------------------|------------|
| 1            | `site_id`    | Yes      | `MIST_SITE_ID` from .env | UUID regex (`is_valid_uuid`); empty -> abort with logged warning |
| 2            | `distinct`   | No       | server default `type`    | Must match one of `{type, mac, hostname, ssid, ap, model, os}` (set echoed from existing WAN search menu); empty -> omit param |
| 3            | `type`       | No       | none                     | Free-form string (Mist event type); empty -> omit param |
| 4            | `duration`   | No       | server default `1d`      | Mist duration string like `1d`, `2h`, `30m`; empty -> omit param |
| 5            | `limit`      | No       | server default `100`     | Integer cast; non-numeric -> warn and use default |

Absolute `start` / `end` epoch parameters are exposed only when the user
answers `y` to a follow-up prompt; otherwise `duration` governs the window.
This keeps the prompt count at five for the common case and matches the
behavior of the adjacent `searchSiteWanClientEvents` menu item.

API authentication is loaded once at startup from `.env`:

- `MIST_HOST` (e.g. `api.mist.com`)
- `MIST_API_TOKEN` (Mist API token; never logged)
- `MIST_SITE_ID` (optional convenience default for prompt 1)

**Rationale**:
The Mist API token must come from `.env` (Principle III: never log secrets,
never store secrets in code). `site_id` is the only required value, and an
`.env` default for it is offered because junior NOC engineers typically
operate against a single home site -- prompting with a sensible default
removes a memorization burden. All five remaining inputs are optional; using
five total prompts keeps the method body small and well inside the 5-Item
Rule.

**Alternatives Considered**:

1. *Read everything from `.env` (no prompts).* Rejected -- spec.md acceptance
   scenario 2 mandates `safe_input()` prompts, and the user community expects
   menu items to be interactive.
2. *Combine `start`/`end`/`duration` into one freeform "time window" prompt.*
   Rejected -- the Mist API takes them as distinct query parameters and
   merging them client-side increases the chance of an off-by-one error in
   the resolved window.
3. *Move `distinct` to the top because it is the most important filter.*
   Rejected -- breaks the existing convention of "identifier first, filters
   second" used by every other site-stats menu item.
