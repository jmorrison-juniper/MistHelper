# Phase 0 Research: getOrgMxEdgeUpgrade

This file resolves the open questions in the Technical Context section of
`plan.md`. Each task uses the Decision / Rationale / Alternatives Considered
format. All citations point at real files in this worktree.

---

## Research Task 1: SDK function signature and behavior

**Decision**: Invoke the endpoint via
`mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgrade(mist_session, org_id,
upgrade_id)`. The function returns a `mistapi.__api_response.APIResponse`
object whose `.data` attribute contains the upgrade job JSON. Both
`org_id` and `upgrade_id` are required path parameters; there are no query
parameters and no request body.

**Rationale**: The Mist API path
`GET /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}` is exposed by the
`mistapi` SDK at module path `mistapi.api.v1.orgs.mxedges` -- the same module
that already exposes `cancelOrgMxEdgeUpgrade(mist_session, org_id,
upgrade_id)` and `updateOrgMxEdgeUpgrade(mist_session, org_id, upgrade_id,
body)`, both documented in
`documentation/api/orgs/SDK_cancelOrgMxEdgeUpgrade.md` and
`documentation/api/orgs/SDK_updateOrgMxEdgeUpgrade.md`. The companion GET
operation `getOrgMxEdgeUpgrade` follows the same module layout and parameter
order, so the call signature is symmetric: `(mist_session, org_id,
upgrade_id) -> APIResponse`. No OpenAPI document is currently shipped for
this exact operation (the enriched-doc generator only emitted the two write
siblings), so the SDK is authoritative for shape. The API reference page is
linked from Juniper documentation under
`utilities/upgrade/get-org-mx-edge-upgrade`.

**Alternatives Considered**:
- *Direct `requests.get(...)` against `MIST_HOST + path`*: Rejected -- the
  constitution mandates `mistapi` as the sole permitted interface to Mist
  Cloud. Re-implementing transport bypasses adaptive delay, retry, and
  pagination plumbing.
- *Use `listOrgMxEdgeUpgrades` and filter client-side*: Rejected -- that
  endpoint returns the full collection of upgrade jobs for the org, which
  is wasteful when the caller already knows the specific `upgrade_id`. The
  per-id GET is the right operation.
- *Wait for the OpenAPI document to be published before cataloging*:
  Rejected -- the SDK is the contract MistHelper actually depends on, and
  the same pattern was used for spec 500 (claim status) when its OpenAPI
  doc was sparse.

---

## Research Task 2: Primary Key Strategy

**Decision**: Use `type='natural_pk'` with primary key
`['org_id', 'upgrade_id']` for the summary table, and
`type='composite_pk'` with primary key
`['org_id', 'upgrade_id', 'mxedge_id']` for the per-Mist-Edge progress
table. Both are registered under the single operationId
`getOrgMxEdgeUpgrade` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, using the
multi-table strategy form already in use for split summary/detail outputs.

**Rationale**: A single Mist Edge upgrade job is uniquely identified within
an org by its `upgrade_id` (a UUID the API generates when the upgrade is
launched). It is stable across polls and re-fetches, so the summary row is
naturally keyed by `(org_id, upgrade_id)`. The job may track multiple Mist
Edges in parallel (a typical Mist Edge cluster upgrade), so each entry in
the response's per-edge progress array must be keyed by
`(org_id, upgrade_id, mxedge_id)` to upsert correctly when the user
re-runs the menu item mid-upgrade. Using `INSERT OR REPLACE` on these
keys gives the desired "latest state wins" semantics without duplicate
rows.

**Alternatives Considered**:
- *Single flat table with one row per (upgrade, mxedge) combination*:
  Rejected -- it would force NULL-padding of job-level fields like
  `target_version` and `status` on every row, and would mix two
  granularities in one table, hurting CSV readability for NOC engineers.
- *`auto_increment_with_unique` keyed on `id`*: Rejected -- there is no
  artificial `id` field; the API provides stable natural keys.
- *Composite key including `start_time` or `last_modified`*: Rejected --
  those fields can update during an in-progress upgrade, breaking
  idempotent upserts on re-poll.

---

## Research Task 3: Output filename and SQLite table

**Decision**:
- Summary file: `data/org_<org_id>_mx_edge_upgrade_<upgrade_id>_summary.csv`
  and SQLite table `org_mx_edge_upgrade_summary`.
- Per-edge file: `data/org_<org_id>_mx_edge_upgrade_<upgrade_id>_progress.csv`
  and SQLite table `org_mx_edge_upgrade_progress`.

`DataExporter.write_with_format_selection(data, filename,
api_function_name="getOrgMxEdgeUpgrade")` is called twice -- once for the
summary row, once for the progress rows. The `api_function_name` argument
is what triggers PK strategy resolution in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**: The filename pattern matches the existing convention used by
other split summary/detail menu items (`spec 500` is the canonical
template: `org_<org_id>_claim_status_summary.csv` +
`_details.csv`). Including the `upgrade_id` in the filename prevents file
collisions when the user pulls multiple upgrade jobs in the same `data/`
directory. SQLite table names omit the per-run UUIDs because rows already
carry `org_id` and `upgrade_id` columns -- one table accumulates history
across runs and orgs.

**Alternatives Considered**:
- *Single combined CSV with one section header per granularity*: Rejected
  -- not parseable by `csv.DictReader` and breaks downstream pandas
  consumption.
- *Drop the `upgrade_id` from filenames*: Rejected -- two consecutive runs
  against different upgrade jobs in the same org would clobber each
  other's CSV output.
- *JSON-only output*: Rejected -- CSV/SQLite/ArangoDB triad is the
  documented baseline.

---

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place the new operation at menu number **96**, inside the
Interactive Safe Viewers cluster (92-96). Label: `View Mist Edge Upgrade
status (by org_id + upgrade_id)`.

**Rationale**: The menu categories table in
`.github/copilot-instructions.md` slots viewers at 92-96 and reserves
97-101 for resource-intensive operations. A single-object GET is light
enough to belong with the viewers, not with bulk operations. Adjacent
operations (Mist Edge stats viewers and similar org-scoped read endpoints)
already live in this cluster, so a NOC engineer scanning the menu will
find the new item next to its conceptual neighbors. Spec 500
(`getOrgLicenseAsyncClaimStatus`) proposed 95 in the same cluster; 96 is
the next free integer below the 97-101 boundary. If 96 turns out to be
claimed by an in-flight feature branch at task-generation time, the next
free integer is used and `plan.md` is updated.

**Alternatives Considered**:
- *Menu 154-157 (firmware destructive cluster)*: Rejected -- this is a
  read-only viewer, not a destructive firmware action. Sorting it next to
  Reboot/Upgrade would mislead a junior NOC engineer.
- *Menu 80-91 (stats cluster)*: Rejected -- the response is an upgrade-job
  object, not periodic statistics; placing it among recurring stats
  viewers would dilute that category's meaning.
- *Append at the next free integer past 194*: Rejected -- the existing
  range still has free slots in semantically appropriate clusters; pushing
  it to the end breaks discoverability.

---

## Research Task 5: Required user prompts (which IDs from user, which from .env)

**Decision**: The menu method collects exactly two values from the user via
`safe_input()`:

1. `org_id` -- prompted with `Enter org_id (UUID): `, context
   `"org_mx_edge_upgrade:org_id"`. Default is pre-filled from
   `MIST_DEFAULT_ORG_ID` in `.env` when present, matching the convention
   used by other org-scoped exports.
2. `upgrade_id` -- prompted with `Enter Mist Edge upgrade_id (UUID): `,
   context `"org_mx_edge_upgrade:upgrade_id"`. No `.env` default -- the
   value is per-run, and silently defaulting to a stale upgrade UUID
   would be misleading.

Credentials (`MIST_HOST`, `MIST_API_TOKEN`) are loaded by the existing
`mistapi.APISession` boot path from `.env`; the new method does not touch
secrets directly.

**Rationale**: The endpoint has two required path parameters and zero query
parameters. The `org_id` is the natural slot for an `.env` default because
a given operator usually works on one org at a time; the `upgrade_id` is
per-job and must be supplied fresh on each invocation. Both prompts go
through `safe_input()` so EOF in an SSH or container session exits cleanly
with code 0 (Constitution III). UUID-shape validation (regex match) is
performed before the SDK call to fail fast on typos without burning a
rate-limited API request.

**Alternatives Considered**:
- *Prompt for `upgrade_id` only and infer `org_id` from .env*: Rejected --
  the constitution's safety-first principle prefers explicit user
  confirmation of the destructive blast radius, even for read-only ops.
  Showing the org_id at the prompt avoids silent cross-tenant reads.
- *Read both IDs from a CSV input file*: Rejected -- adds I/O surface for
  a single-object GET; bulk operation pattern (CSV-driven) is reserved
  for the SSH runner cluster (175-176).
- *Accept comma-separated upgrade_ids and loop*: Rejected -- if a NOC
  engineer needs to poll many jobs, the `listOrgMxEdgeUpgrades` endpoint
  (separate spec) is the right primitive.
