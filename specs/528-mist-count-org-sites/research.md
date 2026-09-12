# Phase 0 Research: countOrgSites

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call `mistapi.api.v1.orgs.sites.countOrgSites(apisession, org_id,
distinct=None, start=None, end=None, duration="1d", limit=100)` directly. The SDK
returns a `mistapi.APIResponse` instance whose `.data` attribute holds the parsed
JSON envelope documented in
`documentation/api/orgs/GET_orgs_org_id_sites_count.md`. The envelope has six
required keys -- `distinct`, `end`, `limit`, `results`, `start`, `total` -- where
`results` is an array of count buckets shaped `{ "count": <int>, "<distinct_field>":
"<value>" }`. The bucket's distinct-field key name varies by the request's
`distinct` parameter (for example `country_code`, `sitegroup_id`, `rftemplate_id`,
`org_id`); this is captured by the OpenAPI `additionalProperties: { type: "string" }`.

**Rationale**: The enriched per-endpoint document is the authoritative SDK contract
under the constitution. It explicitly names the SDK module
`mistapi.api.v1.orgs.sites.countOrgSites()` and lists all five query parameters with
their defaults. No new dependency or transport layer is needed -- this is identical
to how every other `*OrgSites*` export in `SiteExportUtils` already calls into
`mistapi`.

**Alternatives Considered**:

- *Direct `requests.get()` against `/api/v1/orgs/{org_id}/sites/count`*: rejected
  because the constitution requires `mistapi` as the sole Mist Cloud interface and
  using `requests` directly would bypass the SDK's session refresh, rate-limit
  retry, and pagination helpers.
- *Wrap multiple distinct calls in a loop to fetch every aggregation in one menu
  click*: rejected because it would inflate the method past the 5-Item Rule and
  blur the spec's single-endpoint scope. Users wanting multiple aggregations can
  invoke the menu multiple times.

## Research Task 2: Primary Key Strategy

**Decision**: Use a hybrid pair:

- Envelope row: `composite_pk` on `(org_id, distinct, start, end)` -- a single
  envelope describes one count snapshot for one org / one distinct field / one time
  window.
- Bucket row: `composite_pk` on `(org_id, distinct, start, end, bucket_key)` --
  where `bucket_key` is the value of the dynamic distinct attribute (for example
  `country_code="US"`).

Both rows also store the operation's primary natural identifier `org_id` as a
foreign key for graph backends and as a SQLite index for fast filtering.

**Rationale**: The Mist API count endpoint does not return a stable artificial
identifier. It returns an aggregation snapshot whose identity is (org, distinct
field, time window). Composite PK on those four fields plus `bucket_key` for the
results array yields idempotent upserts on repeated runs and matches the existing
`composite_pk` pattern used by the `searchOrg*Events` family.

**Alternatives Considered**:

- *`natural_pk` on `total` or `distinct`*: rejected -- neither is unique across
  runs or distinct values.
- *`auto_increment_with_unique`*: rejected -- the natural composite is well-defined
  and gives free idempotency. Auto-increment would silently duplicate rows on every
  re-run, defeating the constitution requirement that "rows upsert by the
  configured primary key strategy (no duplicates)" from spec FR-005.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV filenames (under `data/`):
  - `org_<org_id>_sites_count_summary.csv`
  - `org_<org_id>_sites_count_results.csv`
- SQLite tables (in `data/mist_data.db`):
  - `org_sites_count_summary`
  - `org_sites_count_results`
- ArangoDB collections (when polyglot backend is active):
  - `org_sites_count_summary`
  - `org_sites_count_results`
  - Edge `org_HAS_sites_count_summary` from `orgs/<org_id>` to the summary doc.

**Rationale**: Filenames follow the existing `org_<id>_<operation>.csv` convention
visible across the `SiteExportUtils` outputs. Two tables (summary + results) match
the two-entity shape of the response envelope and keep flat-CSV consumers happy
(no JSON columns).

**Alternatives Considered**:

- *Single denormalized CSV duplicating envelope fields on every bucket row*:
  rejected because it bloats SQLite storage and complicates SQL joins for analysts.
- *Pickle / JSON-blob single column*: rejected -- violates the constitution's
  preference for queryable flat tables.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Menu number **58**. Category **Safe Org Exports** (1-59), Misc
sub-cluster (56-59). Insert immediately after the existing `listOrgSites`-family
operations so the count operation sits next to its corresponding list/search
siblings in the menu output.

**Rationale**: The agents.md menu map (1-59 Safe Org Exports / Sites 1-7 / Misc
56-59) reserves the 56-59 slot for org-scoped aggregates and counts that are not
strict per-site listings. The count endpoint is read-only and harmless, so it
trivially qualifies as a safe export. 58 is the lowest free integer documented in
the worktree's spec branch ledger at planning time. If a parallel branch claims 58
before merge, the implementer increments to 59 without re-planning.

**Alternatives Considered**:

- *Reserve a number in the 100s (Interactive)*: rejected -- there is nothing
  interactive about this endpoint; user input is one set of prompts at the start.
- *Re-use an existing menu number by collapsing list + count*: rejected -- the
  spec is explicitly scoped to ONE operationId and the count endpoint has its own
  failure modes and PK strategy.

## Research Task 5: Required User Prompts

**Decision**: The menu method collects four user-supplied values and one
configuration value:

1. `org_id` -- prompt via `safe_input("Org ID (UUID): ", context="count_org_sites:
   org_id")`. Default from `os.environ.get("MIST_ORG_ID")` when running with
   `--test`; otherwise the user must supply.
2. `distinct` -- prompt via `safe_input("Distinct field (default country_code): ",
   context="count_org_sites:distinct")`. If empty, use `"country_code"` as the
   sensible default (every site has a country code; gives the most universally
   useful aggregation).
3. `duration` -- prompt via `safe_input("Duration (default 1d, e.g. 7d, 2w): ",
   context="count_org_sites:duration")`. If empty, omit so the SDK applies its
   `1d` default.
4. `limit` -- prompt via `safe_input("Limit (default 100, max 1000): ",
   context="count_org_sites:limit")`. If empty, omit so the SDK applies its `100`
   default. Validate as integer; on parse error log a warning and use `100`.
5. `MIST_HOST` and `MIST_API_TOKEN` come from `.env` via the existing
   `mistapi.APISession` -- never prompted, never logged.

**Rationale**: Mapping prompts to query parameters one-to-one keeps the method
discoverable. Defaulting `distinct` to `country_code` matches the most common NOC
use case ("how many sites do we have per country?") and avoids an empty 400-Bad-
Syntax response. `start` / `end` are intentionally not prompted to keep the prompt
count at four; users who need a custom window use `duration` (which the Mist API
supports as a relative form like `7d`, `2w`).

**Alternatives Considered**:

- *Prompt for every query parameter including `start` and `end`*: rejected -- five
  prompts is too noisy for a junior-NOC audience and `duration` covers 99% of real
  queries.
- *Read `distinct` from `.env`*: rejected -- it is a per-invocation analytical
  choice, not a deployment setting.
