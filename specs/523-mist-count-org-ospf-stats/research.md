# Phase 0 Research: countOrgOspfStats

All five research tasks below use the Decision / Rationale / Alternatives
Considered format mandated by `.specify/templates/plan-template.md`.

## Research Task 1: SDK Function Signature & Behaviour

**Decision**: Invoke
`mistapi.api.v1.orgs.stats_-_ospf.countOrgOspfStats(apisession, org_id,
distinct=None, start=None, end=None, limit=100, sort="timestamp",
search_after=None)`. The MistHelper menu method will pass the active
`mistapi.APISession` (already constructed at process startup), the
user-supplied `org_id`, the user-supplied `distinct` field, and an optional
`start`/`end` time window. `limit` defaults to 100; `sort` defaults to
`timestamp`; `search_after` is reserved for follow-up pagination calls and is
populated automatically from the previous response's `next` URL by
`mistapi.get_all()` -- the menu method does **not** construct it manually.

**Rationale**: The enriched contract at
`documentation/api/orgs/GET_orgs_org_id_stats_ospf_peers_count.md` lists six
query parameters (`distinct`, `start`, `end`, `limit`, `sort`,
`search_after`) and one required path parameter (`org_id`). The endpoint
returns an aggregate envelope (`distinct`, `start`, `end`, `limit`, `total`,
`results[]`) where each `results[]` item has a required `count: integer`
plus arbitrary string-valued `additionalProperties` matching the distinct
field (e.g. `neighbor`, `state`, `vrf_name`, `area_id`, `device_mac`).
mistapi exposes the function under the slug
`mistapi.api.v1.orgs.stats_-_ospf.countOrgOspfStats` per the SDK section of
the contract doc.

**Alternatives Considered**:
- Calling the raw REST URL via `requests` -- rejected: violates the
  constitution's "mistapi is the sole permitted interface" rule.
- Iterating each `distinct` value with separate calls -- rejected: the
  endpoint already aggregates server-side; client-side iteration would
  burn API quota.

## Research Task 2: Primary Key Strategy

**Decision**: `auto_increment_with_unique`. The endpoint returns an aggregate
count payload where there is no natural per-result UUID and the same
(`org_id`, `distinct`, `value`, `count`) tuple may legitimately recur on
subsequent runs with the same data. A surrogate `misthelper_internal_id`
integer is the primary key; indexed columns are `org_id` and `distinct`
for query performance.

This matches the **already-present** entry at `MistHelper.py` line 4456:

```python
"countOrgOspfStats": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["org_id", "distinct"],
    "unique_constraints": [],
    "description": "OSPF statistics count aggregates",
},
```

The plan formalises and uses this entry; no edit is needed unless task
generation discovers a missing `unique_constraints` requirement. Sibling
count endpoints (`countOrgBgpStats` line 4351, `countOrgPeerPathStats`
line 4470, `countOrgOtherDeviceEvents` line 4463) use the identical shape,
confirming the precedent.

**Rationale**: Aggregate/summary data without stable upstream IDs is the
documented use case for `auto_increment_with_unique` per the project's
hybrid PK strategy (see `.github/copilot-instructions.md` Database
Strategy section).

**Alternatives Considered**:
- `natural_pk` on `["org_id", "distinct", "value"]` -- rejected: the
  `value` field name is dynamic (the API uses the `distinct` parameter to
  decide which attribute name appears in each result row), so a fixed
  natural key cannot be declared up front.
- `composite_pk` with `timestamp` -- rejected: the count endpoint returns
  one aggregate per call, not time-series data; a composite-with-timestamp
  PK would treat every run as a new row even when nothing changed, which
  is the desired behaviour for this endpoint but is better expressed by
  the surrogate-id pattern that all other `count*` endpoints already use.

## Research Task 3: Output Filename & SQLite Table

**Decision**: Two output artefacts per backend, paralleling the existing
`countOrgBgpStats` pattern:

- CSV (DataExporter default backend):
  - `data/OrgOspfStatsCountSummary.csv` -- one row per invocation with
    columns `org_id, distinct, start, end, limit, total, fetched_at`.
  - `data/OrgOspfStatsCountResults.csv` -- one row per `results[]` entry
    with columns `misthelper_internal_id, org_id, distinct, value, count,
    fetched_at` plus any other dynamic `additionalProperties` keys
    flattened.
- SQLite (`data/mist_data.db`):
  - Table `org_ospf_stats_count_summary` -- same columns as the summary
    CSV; PK = `misthelper_internal_id`.
  - Table `org_ospf_stats_count_results` -- same columns as the results
    CSV; PK = `misthelper_internal_id`; FK `org_id` referencing
    `org_ospf_stats_count_summary(org_id)` for graph joins.
- ArangoDB + Redis: handled transparently by
  `DataExporter.write_with_format_selection(api_function_name="countOrgOspfStats")`
  -- the existing polyglot adapter consults
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` to derive collection and key names.

**Rationale**: PascalCase camel-style filenames are the convention for
all org-stats exports (see `OrgOspfStats.csv` already produced by
`OrgExportUtils.ospf_stats()`). Splitting summary from results avoids
ragged-row CSVs and gives ArangoDB a clean parent/child relationship.

**Alternatives Considered**:
- One flat CSV with summary fields repeated on every results row --
  rejected: violates DataExporter's "one table = one entity" convention
  and complicates SQLite upserts.
- Separate file per `distinct` value -- rejected: explodes the file count
  on disk; the table-with-`distinct`-column form is queryable and
  compact.

## Research Task 4: Menu Category Placement & Next Available Number

**Decision**: Menu number **195**. The current menu cap in `MistHelper.py`
is 194 (verified by grep for `"194": (`). 195 is the next sequential
integer.

Category: Safe read-only org stats. Conceptually the item belongs in the
Org Stats cluster (operations ~80-91 per `.github/copilot-instructions.md`
menu table) alongside `searchOrgOspfStats`, `countOrgBgpStats`, and
`countOrgPeerPathStats`. Because that cluster is full and the destructive
band (154-194) is reserved for write/reset operations, the new safe-read
operation is placed at 195 to grow the safe-read tail beyond the
destructive cluster. The README operation count is bumped from 194 to 195
with an explicit category label "Safe Org Exports (cont.)" so junior
NOC engineers can locate the item.

**Rationale**: Sequential numbering avoids collisions with in-flight
feature branches that may also be adding new menu items. Re-organising
the destructive cluster to push safe items into the 80-91 range would
require renumbering ~40 unrelated entries -- out of scope for this
single-endpoint cataloging feature.

**Alternatives Considered**:
- Reusing an unused slot in 80-91 -- rejected: verification of "unused"
  requires reading every entry in `_dispatch_menu_action()`; lower risk
  to take 195.
- Placing at 96 (immediately after the safe cluster, before resource-
  intensive) -- rejected: 96 is already taken by an existing operation
  (verified at runtime; if task generation finds 96 free the slot may
  be reconsidered).

## Research Task 5: Required User Prompts

**Decision**: Three prompts collected via `safe_input()`, all with explicit
`context=` strings for SSH/container EOF handling:

1. `safe_input("Org ID (UUID, blank for .env default): ",
   context="count_org_ospf_stats:org_id")` -- if blank, falls back to
   `MIST_ORG_ID` from `.env` via the existing `mistapi.APISession`
   helper. Validates against the Mist UUID shape before the SDK call.
2. `safe_input("Distinct field (one of: neighbor, state, area_id,
   vrf_name, device_mac) [neighbor]: ",
   context="count_org_ospf_stats:distinct")` -- defaults to
   `neighbor` when blank; logged and passed to the SDK as the
   `distinct` query parameter.
3. `safe_input("Time range -- e.g. -1d, -1w, or blank for endpoint default: ",
   context="count_org_ospf_stats:time_range")` -- parsed to `start`
   (relative or epoch seconds) with `end="now"`. Blank skips the
   parameter so the API default is used.

API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) come from `.env`
loaded by `python-dotenv` at process startup -- never prompted, never
logged.

**Rationale**: Three prompts keep the interaction short for junior NOC
engineers while covering the three knobs that actually change query
behaviour. UUID validation and `.env` fallback prevent the most common
operator error (mistyped org id). All other query parameters (`limit`,
`sort`, `search_after`) keep their SDK defaults; pagination is handled
by `mistapi.get_all()` so the operator never sees a cursor.

**Alternatives Considered**:
- Prompt every query parameter -- rejected: violates safety-first
  ergonomics and inflates the function past the 25-line limit.
- Read `distinct` from a CSV / config file -- rejected: adds a new
  config surface for one new menu item; out of scope.
- Skip prompts entirely and read everything from `.env` -- rejected:
  prevents ad-hoc operator queries which are the primary use case for
  read-only count endpoints.
