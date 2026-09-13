# Phase 0 Research: countOrgClientFingerprints

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/sites/{site_id}/insights/fingerprints/count`
**Enriched doc**: `documentation/api/orgs/GET_sites_site_id_insights_fingerprints_count.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call the operation via
`mistapi.api.v1.orgs.nac_fingerprints.countOrgClientFingerprints(apisession,
site_id, distinct=None, start=None, end=None, duration="1d", limit=100)`
and treat the returned `mistapi.APIResponse.data` as a single dict with
keys `distinct`, `start`, `end`, `limit`, `total`, and `results`
(`results` is an array of `{count, <distinct_field>}` objects with the
distinct value attached as an arbitrary `additionalProperty` string).

**Rationale**: The enriched per-endpoint doc
(`documentation/api/orgs/GET_sites_site_id_insights_fingerprints_count.md`)
records the SDK path as
`mistapi.api.v1.orgs.nac_fingerprints.countOrgClientFingerprints()`.
Although the spec.md provisional SDK module
(`mistapi.api.v1.sites.insights.fingerprints.count`) tracks the URL path,
the OpenAPI tag is `Orgs NAC Fingerprints` and the doc's "Gotchas" entry
explicitly flags this: "This is a site-level endpoint but documented
under orgs." The authoritative resolution lives in the enriched doc, so
the implementation imports from the `orgs.nac_fingerprints` module. All
query parameters are optional except for the path `site_id`. The
response shape comes verbatim from the OpenAPI `200` schema captured in
the enriched doc.

**Alternatives Considered**:

- *Import from `mistapi.api.v1.sites.insights.fingerprints.count`* --
  rejected: that module path does not exist in mistapi 0.59; the SDK
  follows the OpenAPI tag (`orgs.nac_fingerprints`) rather than the URL
  path, as confirmed by the enriched doc.
- *Use `requests` directly against the URL* -- rejected: the
  constitution mandates `mistapi` as the sole interface to the Mist
  Cloud (Technology & Compatibility Constraints).
- *Wrap the call in a custom paginator* -- rejected: the doc notes
  pagination is supported via `limit` and `page`, but the response is a
  bounded aggregate (one summary + at most `limit` buckets, default
  100); the simple single-call path covers the common case.

## Research Task 2: Primary Key Strategy

**Decision**: Two related tables, each with a `composite_pk` strategy.

- `site_client_fingerprints_count_summary`: primary key =
  `(site_id, distinct, start, end)`.
- `site_client_fingerprints_count_buckets`: primary key =
  `(site_id, distinct, start, end, bucket_value)`.

A single `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry registers the
operationId once with the bucket-table strategy (the primary persistence
target); the summary table is registered as a paired side-table via the
`related_tables` convention already used elsewhere in MistHelper.

**Rationale**: The endpoint has no API-supplied UUID -- the response is
a pure aggregate keyed by query parameters. The natural identity of one
result is "this site, grouped by *this* distinct field, over *this*
window", which is exactly the four-tuple
`(site_id, distinct, start, end)`. Each bucket row inside that aggregate
is uniquely identified by adding the bucket's distinct-value string
(e.g. `family=Apple`). Composite PK enables idempotent `INSERT OR
REPLACE` upserts on re-runs without artificial IDs.

**Alternatives Considered**:

- *`natural_pk` on `id`* -- rejected: the response has no `id` field;
  no API-provided UUID exists.
- *`auto_increment_with_unique` with a UNIQUE index on the same
  four/five-tuple* -- rejected: equivalent upsert semantics but
  pollutes downstream joins with an opaque surrogate key. Composite PK
  is the documented preference when natural keys exist.
- *Single flat table with one row per bucket and `distinct`,
  `start_ts`, `end_ts`, `bucket_value`, `count`* -- rejected: would
  lose the summary-only fields (`total`, `limit`) and force a redundant
  copy of those values on every bucket row.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV output filename root:
  `site_client_fingerprints_count_<site_id>_<YYYYMMDD_HHMMSS>` --
  produced by `DataExporter.write_with_format_selection()` from the
  `api_function_name="countOrgClientFingerprints"` parameter and the
  call-site context, matching the convention used by the adjacent
  insight exports.
- SQLite tables: `site_client_fingerprints_count_summary` and
  `site_client_fingerprints_count_buckets`, both created on first run
  by `DataExporter`.
- ArangoDB collection (when polyglot backend active):
  `site_client_fingerprints_count` (single document per `(site_id,
  distinct, start, end)` with embedded `results` array), per the same
  graph-edge convention used by spec 188.

**Rationale**: The filename root matches the operationId in snake_case,
prefixed with the entity type (`site_`) for grep-ability against the
existing `data/` listings. Two SQLite tables (summary + buckets) avoid
JSON columns and keep the schema queryable with standard SQL. The
ArangoDB representation embeds buckets because the aggregate is bounded
(default `limit=100`) and the document size stays well under the 16 MB
collection limit.

**Alternatives Considered**:

- *Single CSV with summary fields repeated on every bucket row* --
  rejected: violates 1NF and inflates file size; analysts would have to
  de-duplicate the summary columns to get a clean total.
- *Store the entire JSON blob in a `data` column* -- rejected: defeats
  the point of multi-backend output; SQL consumers would need
  `json_extract` everywhere.
- *Re-use an existing site-insights table* -- rejected: the existing
  insight tables have different schemas; bolting fingerprint counts on
  would break their PK strategies.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Add as menu item **79** in the "Insights" cluster
(operations 73-79 per the menu category table in
`.github/copilot-instructions.md`). At task-generation time, the menu
list is re-verified; if 79 is already claimed by an in-flight feature
branch, the next free integer is selected in this order:
(1) any free slot in 73-79, (2) the next free slot in the 80-91 Stats
cluster, (3) the next free slot in 92-96 (Viewers / Interactive Safe).

**Rationale**: The endpoint is a site-level insight aggregate, which is
the exact charter of the Insights cluster. Placing it at 79 keeps
related operations colocated for discoverability and avoids the
Resource-Intensive (97-101), WebSocket (102-123), Interactive (124-150),
Continuous (151-152), and Destructive (154-194) bands -- all of which
have stricter pre-flight requirements that this read-only call does not
trigger.

**Alternatives Considered**:

- *Place in 51-59 Misc-SLE band* -- rejected: that band is reserved for
  org-level SLE summaries, not site-level insight aggregates.
- *Place in 124-150 Interactive band* -- rejected: this operation has
  no interactive workflow beyond simple prompts; it belongs with the
  other one-shot insight exports.
- *Place above 195 (post-destructive)* -- rejected: leaves a gap in the
  Insights cluster and degrades menu locality for NOC engineers.

## Research Task 5: Required User Prompts (which IDs from the user, which from .env)

**Decision**: One required prompt and four optional prompts collected
via `safe_input()`; no values pulled from `.env` other than the
ambient `MIST_HOST` / `MIST_API_TOKEN` already loaded by
`mistapi.APISession`.

| Prompt | Required? | Source | Default | Notes |
|--------|-----------|--------|---------|-------|
| `site_id` | Yes | `safe_input(context="site_client_fingerprints_count:site_id")` | none | Validated against Mist UUID regex before SDK call; warning + early return on failure. |
| `distinct` | No | `safe_input(context="site_client_fingerprints_count:distinct")` | empty (server default) | Free-form string; common values are `family`, `model`, `os`, `manufacturer`. Empty input sends `None`. |
| `duration` | No | `safe_input(context="site_client_fingerprints_count:duration")` | `1d` | Mist-format duration string (`1d`, `7d`, `2w`). Empty input keeps server default. |
| `start` / `end` | No (alternative to `duration`) | two separate `safe_input` calls | empty | If both populated, override `duration`. Accepts epoch seconds or relative (`-1d`). |
| `limit` | No | `safe_input(context="site_client_fingerprints_count:limit")` | `100` | Cast via `int(...)` inside a `try/except ValueError` block; on parse failure log a warning and fall back to server default. |

**Rationale**: Only `site_id` is functionally required by the API.
Surfacing `distinct`, `duration`, `start`, `end`, and `limit` as
optional prompts lets NOC engineers grab the common case (last 24h, top
100 by no grouping) with a single Enter, while still permitting
custom windows and groupings without code edits. Sourcing nothing from
`.env` keeps the menu portable across orgs without per-org
configuration; the ambient `MIST_API_TOKEN` / `MIST_HOST` are loaded
once by `mistapi.APISession` at startup and do not require duplication
here.

**Alternatives Considered**:

- *Auto-select `org_id` from `.env`* -- rejected: this endpoint is
  site-scoped, not org-scoped; pulling an org ID from `.env` would be
  misleading and would not reduce required input.
- *Hardcode `distinct="model"`* -- rejected: NOC engineers value the
  flexibility to group by `family`, `os`, or `manufacturer`. The empty
  default delegates to the Mist server default behavior.
- *Skip `--test` non-interactive mode entirely* -- rejected: the
  default test sweep covers menus 1-89 minus the skip list; a
  non-interactive path using a known `site_id` from `.env`
  (`MIST_TEST_SITE_ID`) keeps the operation testable without manual
  intervention.
