# Phase 0 Research: countOrgJsiAssetsAndContracts

**Feature**: Mist API GET `/api/v1/orgs/{org_id}/jsi/inventory/count`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_jsi_inventory_count.md`

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke the endpoint through the `mistapi` SDK via
`mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts(apisession, org_id,
distinct=None, limit=100)`.

**Rationale**: The enriched per-endpoint doc
(`documentation/api/orgs/GET_orgs_org_id_jsi_inventory_count.md`) declares the SDK call
as `mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts()`. Mist SDK functions in
this module follow a consistent pattern: first positional argument is the
`mistapi.APISession`, then the path parameter(s), then keyword query parameters.
The endpoint has:

- One path parameter: `org_id` (string, required).
- Two query parameters: `distinct` (string, optional, names the field to bucket by)
  and `limit` (integer, optional, server default 100).
- No request body (GET).
- Standard 200 response is a `Result of Count` envelope: `{distinct, end, limit,
  results: [{count, ...}], start, total}`.

The MistHelper wrapper method calls this SDK function once per user invocation. The
return value is a `mistapi.APIResponse`-like object whose `.data` attribute is the
JSON dict described above. The method extracts `data["results"]` for the bucket rows
and the top-level keys (`total`, `distinct`, `start`, `end`, `limit`) for the summary
row.

**Alternatives Considered**:

- *Calling `requests.get(...)` directly with a hand-built URL*. Rejected: violates
  the MistHelper-wide rule that `mistapi` is the sole permitted interface to the
  Mist Cloud. The SDK handles `APISession` cookies, automatic 429 back-off, and
  endpoint URL changes. Bypassing it would re-implement (and likely break) the
  adaptive delay system already keyed off SDK calls.
- *Driving the existing generic `getOrgInventoryCount` method*. Rejected: that
  method targets `/api/v1/orgs/{org_id}/inventory/count`, not the JSI variant
  `/api/v1/orgs/{org_id}/jsi/inventory/count`. The two endpoints have different
  back-end data sources (Mist inventory vs. JSI purchase records) and different
  400-error semantics ("no Juniper Account Linked" is unique to the JSI variant).

## Research Task 2: Primary Key Strategy

**Decision**: Use `auto_increment_with_unique` for the bucket-results table, with a
composite unique constraint on `(org_id, distinct_field, distinct_value)`. The
summary envelope is stored in a separate table also keyed by `auto_increment_with_unique`
with a unique constraint on `(org_id, distinct_field, retrieved_at_epoch)`.

**Rationale**: The endpoint is a server-side aggregate -- it does not return entities
with stable Mist UUIDs. Each row in `results[]` is `{count: int, <distinct_field>:
<bucket_value>}` where the additional property is dynamic (driven by the user's
`distinct` query argument). There is no `id`, no timestamp on the row itself, and no
foreign key to a concrete device. The only stable natural identifier per bucket is
the tuple `(org_id, distinct_field, distinct_value)`; that tuple plus the
`auto_increment_with_unique` strategy gives clean SQLite upserts (`INSERT OR
REPLACE`) on repeated runs while still letting the row carry a synthetic
`misthelper_internal_id`. For the summary envelope -- which has no stable identifier
at all -- the retrieved-at epoch second is added so re-runs both upsert the latest
snapshot and preserve previous snapshots if the user changes `distinct` between
runs.

**Alternatives Considered**:

- *natural_pk on `(org_id, distinct, distinct_value)`*. Rejected: the dictionary
  schema in `ENDPOINT_PRIMARY_KEY_STRATEGIES` requires a single physical PK column
  for the natural type. The composite is better expressed as a UNIQUE INDEX on top
  of the synthetic auto-increment, which is exactly what
  `auto_increment_with_unique` provides.
- *composite_pk including a timestamp*. Rejected: composite_pk is reserved for
  time-series event/stat data where every snapshot matters. Counts are point-in-
  time aggregates; the user expects the *latest* result for `(org_id, distinct,
  bucket)` to win, not a row-per-poll history.

## Research Task 3: Output filename and SQLite table

**Decision**:

- **CSV filename (results)**:
  `data/org_<org_id_short>_jsi_inventory_count_<YYYYMMDD_HHMMSS>.csv`
- **CSV filename (summary)**:
  `data/org_<org_id_short>_jsi_inventory_count_summary_<YYYYMMDD_HHMMSS>.csv`
- **SQLite table (results)**: `org_jsi_inventory_count_results`
- **SQLite table (summary)**: `org_jsi_inventory_count_summary`
- `<org_id_short>` is the first 8 characters of the org UUID (existing MistHelper
  convention for filename brevity).

**Rationale**: The names follow the existing MistHelper pattern for org-scoped
exports (`org_<id>_<operation>_<timestamp>.csv`) and the SQLite naming convention of
lower-snake-case operation identifiers without timestamps. Two physical tables
mirror the two-tier response (envelope + bucket rows), giving downstream tooling
clean SQL joins (`JOIN ... ON summary.org_id = results.org_id AND summary.distinct
= results.distinct`). `DataExporter.write_with_format_selection(...,
api_function_name="countOrgJsiAssetsAndContracts")` dispatches both writes
correctly because the new
`ENDPOINT_PRIMARY_KEY_STRATEGIES["countOrgJsiAssetsAndContracts"]` entry declares
the two-table fan-out (see `data-model.md`).

**Alternatives Considered**:

- *Single flat table with nullable columns*. Rejected: collapses two semantically
  different rows (one envelope, N bucket rows) into one table, hurting query
  ergonomics and introducing NULL-heavy storage for every bucket row.
- *JSON column dump*. Rejected: defeats the point of SQLite as a queryable
  backend.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **96**, in the Safe Org Exports cluster.

**Rationale**: The MistHelper menu category table (per
`.github/copilot-instructions.md`) reserves 1-59 for Safe Org Exports and 60-96 for
Interactive Safe operations, with 97-101 being the resource-intensive block.
JSI-count is read-only, light, and parameter-driven -- prompting for `org_id`,
`distinct`, and `limit`. That places it cleanly in the upper Interactive Safe slot
just before the resource-intensive boundary. Position 96 is the last slot before
the resource-intensive cluster, keeping JSI counts grouped with adjacent inventory
viewers. If 96 is taken by another in-flight spec at task-generation time, the
next free integer in the 60-96 cluster is used; if the cluster is exhausted, a new
slot is requested at the bottom of 80-91 (Stats viewers, which are conceptually
similar).

**Alternatives Considered**:

- *Place in 1-59 Safe Org Exports*. Rejected: counts that take optional grouping
  parameters are interactive, not pure dumps. The 1-59 cluster is for unattended
  bulk exports.
- *Place in 97-101 resource-intensive*. Rejected: the endpoint is a small
  aggregate that completes in seconds. Marking it resource-intensive would
  mislead users and cause it to be excluded from the default `--test` sweep.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**:

| Input            | Source              | Prompt? | Default if blank        |
|------------------|---------------------|---------|-------------------------|
| `org_id`         | `safe_input()` then `.env` (`MIST_ORG_ID`) | Yes | `os.getenv("MIST_ORG_ID")` |
| `distinct`       | `safe_input()`      | Yes     | `None` (server returns un-bucketed total only) |
| `limit`          | `safe_input()`      | Yes     | `100` (server default; clamped to 1..1000)     |
| `MIST_HOST`      | `.env`              | No      | n/a (loaded by mistapi.APISession)             |
| `MIST_API_TOKEN` | `.env`              | No      | n/a (loaded by mistapi.APISession)             |

**Rationale**: MistHelper convention is to source the API host and token from
`.env` (never prompt, never log), and to prompt the user for any per-invocation
scope identifier. `org_id` is per-invocation but very often constant for a given
operator, so the prompt accepts an empty input and falls back to `MIST_ORG_ID` from
`.env` if set -- this matches the existing pattern in `LicenseExportUtils` and
`InventoryExportUtils`. `distinct` is left blank by default because the endpoint
returns a valid (unbucketed) result without it. `limit` is clamped to `1..1000` to
prevent accidentally sending `limit=0` (returns nothing) or absurdly large values
that the server would reject. All three prompts use `safe_input()` with explicit
`context=` strings so EOF in SSH / container sessions exits cleanly.

**Alternatives Considered**:

- *Require all three on the command line / non-interactive only*. Rejected:
  breaks the menu-driven UX expected by junior NOC engineers and violates the
  "Interactive Safe" cluster contract.
- *Skip the `.env` fallback for `org_id`*. Rejected: forces operators to retype
  the same UUID for every menu invocation, against established MistHelper
  ergonomics.
