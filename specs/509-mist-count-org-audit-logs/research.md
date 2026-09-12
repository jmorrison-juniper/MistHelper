# Phase 0 Research: countOrgAuditLogs

This document captures the design decisions made before Phase 1 artifact generation.
Each task uses the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke
`mistapi.api.v1.orgs.logs.count.countOrgAuditLogs(apisession, org_id, distinct=None,
admin_id=None, admin_name=None, site_id=None, message=None, start=None, end=None,
duration="1d", limit=100)` exactly once per menu run. The function returns an
`mistapi.APIResponse` whose `.data` attribute is a dict with the shape
`{ "distinct": str, "start": int, "end": int, "limit": int, "total": int, "results":
[ { "count": int, "<distinct_field>": str }, ... ] }`. The `results` array is a list of
distinct-bucket records where the additional key is the field named in `distinct` (per
the OpenAPI `additionalProperties: { type: string }` clause on the `count_result`
schema).

**Rationale**: The enriched documentation file
`documentation/api/orgs/GET_orgs_org_id_logs_count.md` (read on 2026-06-28) confirms the
HTTP contract, parameter set, default values (`duration=1d`, `limit=100`), and the 200
response schema. The `mistapi` SDK convention (verified on adjacent count endpoints such
as `countOrgEvents`, `countOrgDevices`) is `module.<operationId>(apisession, <path
params>, **<query params as kwargs>)`. The response wrapper is the standard
`APIResponse` so the existing rate-limit / retry / pagination plumbing in MistHelper
applies without change.

**Alternatives Considered**:

- *Loop over every supported `distinct` value in one menu run*: rejected -- it would
  fire 4+ API calls per invocation, multiplying token cost and rate-limit pressure;
  better to let the user pick one bucket field per run.
- *Call the unaggregated `listOrgAuditLogs` and aggregate client-side*: rejected --
  defeats the entire purpose of the count endpoint, blows past the rate-limit window
  on busy orgs, and duplicates server logic.
- *Skip the SDK and hit the REST endpoint directly with `requests`*: rejected --
  violates the project rule that `mistapi` is the sole permitted interface to the Mist
  Cloud.

## Research Task 2: Primary Key Strategy

**Decision**: Use **`composite_pk`** for the bucket detail rows, with the composite key
`(org_id, distinct, bucket_value, window_start, window_end)`. The summary row uses a
separate single-row table keyed by `(org_id, distinct, window_start, window_end)`.

**Rationale**: The count endpoint has no API-provided UUID and no monotonic timestamp;
it is a server-side aggregation over a window. Two runs with the same `org_id`,
`distinct`, and time window must upsert the same rows -- not duplicate them -- so
`auto_increment_with_unique` would either drop history or accumulate duplicates. The
composite key captures every parameter that changes the aggregation, allowing the
SQLite table to hold a clean time-series of count snapshots over time. `natural_pk` is
not viable because the API never returns a primary identifier for a count bucket.

**Alternatives Considered**:

- *`auto_increment_with_unique` on `(org_id, distinct, bucket_value)`*: rejected --
  rerunning for a different time window would either overwrite the previous window's
  count or silently dedupe across windows, losing the trend.
- *`natural_pk` on `bucket_value`*: rejected -- `bucket_value` is not globally unique;
  the same admin_name can appear under two different orgs.
- *Single flat table with no summary row*: rejected -- the summary row's `total`
  field is operationally useful and would be repeated on every bucket row otherwise,
  inflating storage and obscuring the canonical total.

## Research Task 3: Output Filename and SQLite Table

**Decision**: CSV / file output uses two files per run:
`data/org_audit_logs_count_summary_<org_id>_<distinct>_<window>.csv` and
`data/org_audit_logs_count_buckets_<org_id>_<distinct>_<window>.csv`. SQLite uses two
tables: `org_audit_logs_count_summary` and `org_audit_logs_count_buckets`. ArangoDB
collections use the same two names.

**Rationale**: Mirroring the two logical entities (summary + buckets) into two output
sinks keeps each row shape uniform across all three backends -- a pure CSV file with a
single header line, a single SQLite schema, and a single ArangoDB document type per
collection. The `<org_id>_<distinct>_<window>` filename suffix lets a user accumulate
multiple windows in `data/` without overwriting earlier runs while the SQLite tables
hold the consolidated history via composite-key upsert. Filenames follow the existing
MistHelper convention (`<entity>_<scope>_<filter>.csv`).

**Alternatives Considered**:

- *Single flattened table*: rejected for the same reason as the PK strategy -- the
  summary row's `total` would either repeat on every bucket row or be lost entirely.
- *One file with both summary and buckets concatenated*: rejected -- mixed-shape rows
  in a single CSV break naive consumers (pandas, Excel) and complicate the SQLite
  schema.
- *Timestamped filenames* (`..._<epoch>.csv`): rejected -- the window already
  uniquely identifies the snapshot; an extra epoch tag would clutter `data/` without
  adding information.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new menu item at **operation 89**, inside the
"Interactive Safe Org / Site Exports" cluster (60-91) next to the existing audit-log
items. The label in the menu is `Count Org Audit Logs (by distinct field)`.

**Rationale**: The endpoint is read-only, org-scoped, and returns aggregate data -- the
same operational profile as the other items in the 60-91 cluster. Audit-log list and
search items already live in that range, so a count variant alongside them is the
least-surprising placement for a NOC engineer scanning the menu. Operation 89 is the
next free integer in that cluster at the time of writing; the exact integer is
re-verified at `/speckit.tasks` time and shifted to the next free integer in the same
cluster if a parallel feature branch claims 89 first.

**Alternatives Considered**:

- *Slot in the 51-59 SLE / org-summary block*: rejected -- audit logs are an
  admin / compliance concern, not an SLE/performance metric; the user-mental-model
  match is weaker.
- *Slot in the 124-150 Interactive Diagnostics block*: rejected -- diagnostics are
  device/network operations, not org admin reporting.
- *Slot in the 154-194 Destructive block*: rejected -- the endpoint is HTTP GET with
  zero side effect.

## Research Task 5: Required User Prompts (Which IDs from the User, Which from .env)

**Decision**: Collected from `.env` via existing `mistapi.APISession`: `MIST_HOST`,
`MIST_API_TOKEN`. Collected from the user via `safe_input()` in this order:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context
   `"org_audit_logs_count:org_id"`. Validated against the Mist UUID shape; on
   failure log a warning and return.
2. `distinct` -- prompt: `"Distinct field [admin_id|admin_name|message|site_id]
   (default: admin_name): "`, context `"org_audit_logs_count:distinct"`. Empty
   input defaults to `admin_name`. Validated against the enum; on failure log a
   warning and return.
3. `duration` -- prompt: `"Duration window (e.g. 1d, 7d, 2w) (default: 1d): "`,
   context `"org_audit_logs_count:duration"`. Empty defaults to `1d`. Passed
   through to the SDK as-is (Mist parses the relative format server-side).
4. `limit` -- prompt: `"Result limit (default: 100): "`, context
   `"org_audit_logs_count:limit"`. Empty defaults to `100`. Parsed as `int`; on
   parse failure log a warning and fall back to `100`.

Optional filters (`admin_id`, `admin_name`, `site_id`, `message`, `start`, `end`) are
not prompted in the v1 menu to keep the interactive flow under the 5-block / 5-param
budget (Principle I). A power user can pass them by re-running with overrides at a
later iteration; v1 documents this as a known limitation in the README row.

**Rationale**: Three prompts cover the 80% case (org, what to group by, how far back).
Adding every optional filter would inflate the prompt sequence past the 5-Item Rule
budget and overwhelm a junior NOC engineer. `safe_input()` with explicit `context=`
strings ensures container/SSH EOF exits cleanly. The API token never appears at a
prompt -- it lives in `.env`.

**Alternatives Considered**:

- *Prompt for every optional filter in sequence*: rejected -- adds 6 more prompts,
  busts the Five-Item Rule budget on the calling method, and clutters the UX.
- *Pull `org_id` from `.env` (e.g. `MIST_DEFAULT_ORG_ID`)*: rejected -- the rest of
  MistHelper consistently prompts per run because users routinely operate across
  multiple orgs; silent defaulting would surprise them.
- *Skip validation and let the SDK reject bad input*: rejected -- the SDK error path
  produces stack traces in interactive mode, violating the safety-first principle.
