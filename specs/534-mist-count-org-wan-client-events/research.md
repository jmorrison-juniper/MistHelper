# Phase 0 Research: countOrgWanClientEvents

**Feature**: 534-mist-count-org-wan-client-events
**Spec**: [spec.md](./spec.md)
**Date**: 2026-06-29

This document captures the five research tasks that gate Phase 1 design.
Each task is recorded as a Decision / Rationale / Alternatives Considered
triad. All decisions are firm; there are no NEEDS CLARIFICATION markers.

## Research Task 1: SDK Function Signature and Behavior

**Decision**: The implementation calls the `mistapi` SDK function
`countOrgWanClientEvents` exposed under the SDK module path
`mistapi.api.v1.orgs.wan_client.events.count`. The exact Python call is:

```python
response = mistapi.api.v1.orgs.wan_client.events.count.countOrgWanClientEvents(
    apisession=self._apisession,   # existing mistapi.APISession from .env
    org_id=org_id,                 # validated UUID supplied by the user
    distinct=distinct_attr,        # e.g. "type", "mac", "gateway"
    type=event_type_filter or None,  # optional event-type filter, None passes through
    start=time_window["start"],    # epoch seconds or relative string ("-1d")
    end=time_window["end"],        # epoch seconds or relative string ("now")
    duration=time_window["duration"],  # default "1d" if start/end omitted
    limit=time_window.get("limit", 100),  # default 100 per Mist doc
)
body = response.data  # mistapi returns a Response object; .data is the JSON dict
```

The response body is a single JSON object with the shape:

```json
{
  "distinct": "<echo of request>",
  "start":    <int epoch>,
  "end":      <int epoch>,
  "limit":    <int>,
  "total":    <int>,
  "results":  [ { "count": <int>, "<distinct_attr>": "<value>" }, ... ]
}
```

**Rationale**: The enriched per-endpoint doc
`documentation/api/orgs/GET_orgs_org_id_wan_client_events_count.md` records
both the HTTP contract and the response schema verbatim from the Mist OpenAPI
3 spec. The doc lists six query parameters (`distinct`, `type`, `start`,
`end`, `duration`, `limit`) and one path parameter (`org_id`). The 200 schema
has six required fields (`distinct`, `end`, `limit`, `results`, `start`,
`total`); `results` is an array whose items have a required `count` integer
plus `additionalProperties` of type `string`, allowing the grouping attribute
to appear as a sibling key. The spec.md for this feature mirrors the same
parameter set. Using the SDK rather than raw `requests` is mandated by the
constitution (`mistapi` is the sole permitted Mist interface).

**Alternatives Considered**:

1. Use the operationId-based shortcut `mistapi.api.v1.orgs.clients_-_wan.countOrgWanClientEvents()` listed in the enriched doc. Rejected because the
   path-based form `mistapi.api.v1.orgs.wan_client.events.count.countOrgWanClientEvents` matches the SDK's directory layout exactly and is what the
   spec.md cites; the hyphen-containing alias is an alternate import that
   varies between SDK versions and is fragile.
2. Hand-roll the HTTP request via `requests.get(...)` to control headers
   manually. Rejected because the constitution forbids bypassing `mistapi`
   and because the SDK already handles rate-limit headers, 5xx retries, and
   the authentication header injection.
3. Use the synchronous-iterator pagination helper. Rejected because this
   endpoint returns a bounded, server-aggregated payload (one envelope + at
   most `limit` result rows) -- iteration is unnecessary; a single call is
   sufficient.

## Research Task 2: Primary Key Strategy

**Decision**: Register `countOrgWanClientEvents` in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` as **`auto_increment_with_unique`** with two
logical tables:

```python
"countOrgWanClientEvents": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_constraints": [
        ["org_id", "distinct", "start", "end"],            # summary table
        ["org_id", "distinct", "start", "end", "value"],   # results table
    ],
    "indexes": ["org_id", "distinct", "start", "end"],
},
```

The "summary" table holds one row per (org_id, distinct, start, end) tuple --
the request envelope. The "results" table holds one row per group value
returned in `results[]`, keyed by the same window plus the grouping value.

**Rationale**: This endpoint is a server-side aggregation. The response
carries no stable identifier (no `id`, no `mac`, no `timestamp`) that
survives across calls -- the same window can be re-counted at any time and
will produce a new envelope. Natural-PK is therefore inappropriate. A
composite-PK on (org_id, distinct, start, end, value) would force the user's
exact window choices to be the key, which works when the user passes epoch
seconds but breaks when the user passes relative strings like `-1d` (the
server resolves them to different absolute epochs on every call, causing
duplicate rows). Auto-increment with a unique constraint on the meaningful
business tuple gives clean upserts when the user repeats the same query and
otherwise stores each new aggregation as a fresh row, which is the
established MistHelper convention for count / summary endpoints (matches
`getOrgLicensesSummary` and the other `*Count*` operations already in the
codebase).

**Alternatives Considered**:

1. `composite_pk` on (`org_id`, `distinct`, `start`, `end`, `value`).
   Rejected because relative time strings (`-1d`, `-1w`) are resolved
   server-side and produce a different absolute epoch on every call,
   defeating the upsert intent.
2. `natural_pk` on a synthesized hash of the request. Rejected because there
   is no Mist-supplied stable ID and the hash would have to live in user
   code, contradicting the "natural business keys from the API" rule in the
   constitution.
3. Store only the envelope and ignore `results[]`. Rejected because the
   `results[]` array is the entire purpose of the endpoint (the counts per
   distinct value) -- dropping it would deliver no useful data.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV output filename (DataExporter target): `org_wan_client_events_count`
  (DataExporter appends `_summary` and `_results` suffixes for the two
  logical tables, producing
  `data/org_wan_client_events_count_summary.csv` and
  `data/org_wan_client_events_count_results.csv` on disk).
- SQLite tables:
  - `org_wan_client_events_count_summary` (envelope rows)
  - `org_wan_client_events_count_results` (per-distinct-value rows, foreign
    key to the summary row via `summary_id`).
- ArangoDB collections (when polyglot backend is active): same names with
  edges from the summary document to each result document. Redis keys follow
  the existing `mh:wan_client_events_count:<org_id>:<distinct>:<window>`
  convention used by adjacent count operations.

**Rationale**: The naming follows the established MistHelper convention --
operationId is transformed by stripping the `count`/`get`/`list` verb prefix,
lowercasing, and inserting underscores at camel boundaries. This matches the
pattern used by `org_license_async_claim_status_summary` /
`_details` (spec 500) and other count endpoints. Keeping summary and results
in separate tables avoids variable-width rows in CSV (each `distinct` value
introduces a different schema for the results-row sibling key) and lets the
summary table be queried independently.

**Alternatives Considered**:

1. One flat table with `summary` and `results` collapsed by JSON-encoding
   `results` into a single column. Rejected because it breaks SQL filtering
   on per-distinct-value counts and contradicts the "flatten nested JSON"
   guidance in the AI-Agent Instructions.
2. Filename `wan_client_events_count_org` to keep alphabetical adjacency to
   other `wan_client_events_*` exports. Rejected because the canonical
   ordering is `org_<resource>_<operation>` so that all org-scoped exports
   sort together in `data/`.
3. Add the `distinct` value into the filename itself (e.g.
   `org_wan_client_events_count_by_type.csv`). Rejected because the same
   filename would proliferate into one-per-distinct, breaking the SQLite
   upsert convention and confusing the test harness.

## Research Task 4: Menu Category Placement and Menu Number

**Decision**: Place the new operation under the **Safe Org Exports / Org
Clients (WAN)** category in the README menu table and assign menu number
**195**. Internal source-code grouping in `MistHelper.py` sits adjacent to
the existing WAN-clients export methods (immediately after the
`searchOrgWanClientEvents` / `searchOrgWanClients` methods if present, or at
the end of the WAN-clients export cluster otherwise).

**Rationale**: The AI-Agent Instructions document the full menu map: 1-59
Safe Org Exports, 60-96 Interactive Safe, 97-101+153 Resource Intensive,
102-123 WebSocket, 124-150 Interactive, 151-152 Continuous, 154-194
Destructive. All slots 1-194 are reported as allocated, so **195** is the
next free integer. The operation is strictly read-only (GET), aggregates
data, and surfaces no destructive side effect, so it belongs in the safe
category regardless of its numerical position. The README menu table is
updated to record the assignment under the WAN-clients subsection of Safe
Org Exports. At task-generation time, an authoritative scan of the live
menu registry will reconfirm that 195 is free; if any in-flight branch
claims 195 first the next free integer is used and the README is updated to
match.

**Alternatives Considered**:

1. Reuse a destructive-cluster slot (154-194) freed by an earlier removal.
   Rejected because the existing menu numbers are stable and the constitution
   requires sequential additions, not reclamation, to keep prior CHANGELOG
   entries valid.
2. Insert into the 27-30 Clients sub-cluster of the safe exports. Rejected
   because renumbering existing operations breaks user automation scripts
   and the CHANGELOG -- the project's documented convention is to append at
   the end.
3. Use an alphanumeric suffix (e.g. `194a`). Rejected because the menu
   dispatcher uses integer `--menu` arguments and would have to be rewritten
   to accept string IDs.

## Research Task 5: Required User Prompts vs .env

**Decision**: The new menu method collects the following from the user via
`safe_input()`, in this order:

| Prompt | Source | Required | Validation |
|--------|--------|----------|------------|
| `org_id` | user (default from `.env` `MIST_ORG_ID` if set) | yes | Mist UUID regex |
| `distinct` | user (default `"type"`) | yes | one of the documented distinct attributes (`type`, `mac`, `gateway`, `port_id`, `wan_ip`) |
| `event_type` filter | user (blank skips) | no | non-empty string or empty |
| `time_window` | user (default `duration=1d`) | yes | accept either `start`/`end` pair or `duration` string; validate epoch / relative format |
| `limit` | user (default `100`) | no | integer 1..1000 |

The following come from `.env` and are never prompted:
`MIST_HOST`, `MIST_API_TOKEN`. The existing `mistapi.APISession`
construction in MistHelper already loads these.

**Rationale**: `org_id` is the only mandatory path parameter and the user
must explicitly choose which org to query, so it is prompted with the
`.env` value as a default convenience. `distinct` is mandatory for the
endpoint to do meaningful work (the entire endpoint is "count by distinct
attribute"), so it is prompted with the most common default (`type`).
`event_type` is a free-form filter -- blank passes `None` to the SDK.
`time_window` is the single source of confusion for non-expert users
(start/end vs duration); the prompt accepts either form and defaults to
`duration=1d` if the user just presses Enter, matching the Mist API's own
default. `limit` is exposed so power users can request more than the
100-row default; the cap of 1000 matches the upstream API limit.

**Alternatives Considered**:

1. Read `org_id` from `.env` only with no prompt. Rejected because
   multi-org users need to switch orgs interactively, and the existing safe
   exports always prompt for org.
2. Skip the `distinct` prompt and hard-code it to `type`. Rejected because
   the entire value of this endpoint is the choice of grouping attribute;
   forcing `type` makes the menu item duplicate existing event-search
   capabilities.
3. Pre-populate `start`/`end` from a configuration file. Rejected because
   the relative-string form (`-1d`, `-1w`) is already concise and reading
   another config layer adds complexity without user-visible benefit.
