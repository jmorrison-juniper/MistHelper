# Phase 0 Research: getOrgSiteGroup

**Feature**: `640-mist-get-org-site-group`
**Endpoint**: `GET /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}`
**Date**: 2026-06-30

Five discrete research tasks were performed to unblock Phase 1 design. Each task
records a Decision, its Rationale, and the Alternatives Considered so future
readers can trace the reasoning without re-doing the work.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Use `mistapi.api.v1.orgs.sitegroups.getOrgSiteGroup(mist_session,
org_id, sitegroup_id)` unchanged. Return object is a `mistapi.APIResponse` whose
`.data` attribute is a single JSON object matching the OpenAPI schema
(`created_time`, `id`, `modified_time`, `name`, `org_id`, `site_ids[]`). The
call is non-paginated.

**Rationale**: The enriched documentation file
`documentation/api/orgs/GET_orgs_org_id_sitegroups_sitegroup_id.md` confirms:

- HTTP: `GET /api/v1/orgs/{org_id}/sitegroups/{sitegroup_id}`
- Two required path params (`org_id`, `sitegroup_id`), no query params, no body.
- 200 response is a single object (not an array).
- SDK entry point: `mistapi.api.v1.orgs.sitegroups.getOrgSiteGroup()`.
- Not currently used by MistHelper (confirmed in "MistHelper Notes" section).

Constitution Principle II (Class-Based / No Wrappers) and the project rule that
`mistapi` is the sole permitted transport to Mist Cloud both require using this
signature verbatim. Since the response is a single object, no pagination loop
is needed and no `.next` traversal helper is invoked.

**Alternatives Considered**:

- *Direct `requests.get()` call*: Rejected. Violates the "mistapi is the sole
  Mist Cloud interface" rule; bypasses the session's built-in adaptive
  back-off, retry, and 429 handling.
- *Use the list endpoint `listOrgSiteGroups` and filter client-side*: Rejected.
  Wastes bandwidth (returns every group in the org) and defeats the point of a
  single-record read; the by-id endpoint returns exactly one document.

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with `primary_key=['id']` and secondary indexes on
`org_id` and `name`. Register in `ENDPOINT_PRIMARY_KEY_STRATEGIES` under key
`getOrgSiteGroup`.

**Rationale**: The 200 response schema (see documentation file, lines 44-53)
declares `id` as a stable, API-provided UUID -- the canonical Mist identity
field. `natural_pk` is the correct strategy per the project's Database Strategy
table because:

- The site group has an immutable UUID assigned at creation time.
- Repeated reads should upsert (INSERT OR REPLACE) into the same row rather
  than accumulate duplicates.
- `org_id` is needed for JOINs against org tables; `name` supports human
  lookup.

The `site_ids` array is flattened to a `;`-delimited string in the same row
(no separate join table for Phase 0) because the array is small (typically
under a few hundred site UUIDs) and CSV / SQLite / Arango parity is easier
with a single denormalized column. A future enhancement could split into a
`org_site_group_members` many-to-many table if graph queries demand it, but
that is out of scope for this spec.

**Alternatives Considered**:

- *`composite_pk` on `['org_id', 'id']`*: Rejected. Site group IDs are
  globally unique UUIDs, so the extra column adds noise without preventing
  collisions.
- *`auto_increment_with_unique`*: Rejected. Loses the natural upsert
  semantic; would require a synthetic `misthelper_internal_id` column with no
  business meaning.
- *Two tables (`org_site_groups` + `org_site_group_members`)*: Rejected for
  Phase 0. Adds a second CREATE TABLE, a second write, and a new FK -- all
  premature until a graph-query workload proves the need. The `;`-delimited
  string keeps parity with existing MistHelper flatten patterns.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV filename: `data/org_site_group_<org_id>_<sitegroup_id>.csv`
- SQLite table: `org_site_groups`
- ArangoDB collection: `org_site_groups`

**Rationale**: The naming pattern follows the established MistHelper convention
(`<scope>_<entity>_<id>.csv`) so users can find the file with `ls
data/org_site_group*`. Because the endpoint returns exactly one record per
call, embedding both IDs in the filename keeps parallel invocations from
overwriting each other. The SQLite table name is plural (`org_site_groups`)
matching the endpoint's plural resource segment (`sitegroups`) and the
existing pattern used for `org_sites`, `org_devices`, etc. All three backends
share the same table/collection name so a NOC engineer switching backends
sees identical schemas.

**Alternatives Considered**:

- *`site_group_<id>.csv` (drop org prefix)*: Rejected. Loses the org
  disambiguation when the same tool is pointed at multiple orgs in one
  session.
- *`org_sitegroups` (no underscore between "site" and "groups")*: Rejected.
  Existing exports use `site_group` as two words in table/column names; the
  API path collapses them but human-facing names should stay readable.
- *Timestamped filenames*: Rejected. `DataExporter` already handles overwrite
  vs. upsert; users can enable timestamped mode via the export
  configuration menu without hard-coding it here.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Menu number **95**, placed inside the Safe Org Exports cluster
(operations 1-95). Menu label: `Export single org site group by ID
(getOrgSiteGroup)`. Registered under the same dispatch section as existing
`listOrgSiteGroups` and other org-template read operations.

**Rationale**: The project's menu category table in `copilot-instructions.md`
(§ Menu System & Operations) places safe org exports in the 1-59 primary band
and continues the safe cluster through 95, with resource-intensive operations
starting at 96. Item 95 is the last free slot inside the safe range, which is:

- Read-only (matches spec's Priority P1 tag).
- Non-destructive (no confirmation prompt required).
- Adjacent to the related list endpoint if one already exists in the same
  cluster.

**Fallback policy**: If 95 is claimed by an in-flight feature branch at task
generation time, the next free integer inside the safe-exports cluster is
chosen (walk upward through 96-101 only if the resource-intensive block has
been re-partitioned; otherwise walk downward through the unused slots in the
40s / 50s). The chosen integer is recorded in `tasks.md` and referenced in
the CHANGELOG entry.

**Alternatives Considered**:

- *Slot in the 37-41 templates band*: Rejected. That band is already dense
  and adding an item there would require renumbering.
- *Slot in the 60-96 interactive-safe band*: Rejected. The interactive band
  is for menu items that require multi-step user interaction beyond a simple
  prompt; a single by-id GET fits the "safe exports" pattern better.
- *A new triple-digit slot (>200)*: Rejected. There is no established
  triple-digit block yet; introducing one for a single by-id GET is
  premature.

## Research Task 5: Required User Prompts

**Decision**: Two prompts total, both via `safe_input()`:

1. `org_id` -- default from `.env` variable `MIST_ORG_ID` if present; if the
   user presses Enter with no override the default is used. Context string:
   `"org_site_group:org_id"`.
2. `sitegroup_id` -- no `.env` default (there is no natural single default,
   since an org can have many site groups). Context string:
   `"org_site_group:sitegroup_id"`.

Both values are validated against the Mist UUID shape
(`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`) before the
SDK call. On validation failure the method logs a WARNING and returns early
(no exception, no traceback).

**Rationale**:

- `.env` fallback for `org_id` matches the project pattern established by
  operations 8-14 (inventory exports). Reduces prompt friction for engineers
  who work primarily in one org.
- No fallback for `sitegroup_id` is deliberate: unlike `org_id`, there is no
  canonical "default" site group. A stale `.env` value would silently return
  the wrong record, which is a NOC-safety anti-pattern.
- `safe_input()` is mandated by Constitution Principle III for every prompt.
- Explicit `context=` strings make SSH / container EOF logs
  self-documenting -- if the session drops mid-prompt, the log line names
  the exact prompt that lost input.
- Pre-flight UUID validation prevents avoidable 404s from Mist and gives a
  human-readable warning ("sitegroup_id does not look like a UUID -- got
  <value>") instead of a bare 404.

**Alternatives Considered**:

- *Also default `sitegroup_id` from an `.env` variable*: Rejected for safety
  reasons above.
- *Skip UUID validation and let Mist return 404*: Rejected. 404s cost an
  API-quota call and produce a less-helpful log message than a client-side
  format check.
- *Interactive picker (list all site groups, let user choose by number)*:
  Rejected for Phase 0. It requires an additional API call and turns a
  simple by-id read into a multi-step operation; better implemented as a
  separate menu item that composes `listOrgSiteGroups` + this endpoint if
  users request it later.
