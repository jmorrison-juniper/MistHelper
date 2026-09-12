# Phase 0 Research: getOrgApplicationList

Branch: `597-mist-get-org-application-list`
Date: 2026-06-29
Source endpoint: `GET /api/v1/orgs/{org_id}/wxtags/apps`
Enriched doc: `documentation/api/orgs/GET_orgs_org_id_wxtags_apps.md`

This document resolves the five Phase 0 research tasks listed in the plan. Each task
records a Decision, a Rationale, and the Alternatives Considered.

---

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke
`mistapi.api.v1.orgs.wxtags.getOrgApplicationList(apisession, org_id)`.

The function takes the active `mistapi.APISession` (already constructed at MistHelper
startup from `MIST_HOST` + `MIST_API_TOKEN`) plus the path parameter `org_id`. It
returns a `mistapi.APIResponse` object whose `.data` attribute is a Python `list[dict]`
of application catalog entries. Each entry has three required string fields: `group`,
`key`, `name`. The endpoint is **not paginated** -- the entire catalog is delivered in
a single response. No query parameters exist. Standard error semantics apply: 400 bad
syntax, 401 unauthorized, 403 forbidden, 404 unknown org, 429 rate limited.

**Rationale**: The enriched doc at
`documentation/api/orgs/GET_orgs_org_id_wxtags_apps.md` states the SDK path as
`mistapi.api.v1.orgs.wxtags.getOrgApplicationList()`. The Mist API spec shows a single
required path parameter (`org_id`) and zero query parameters. Calling the function once
per `org_id` therefore exhausts the endpoint contract. The response schema is a flat
array of `search_wxtag_apps_item` objects -- no nested structures, so no flattening
helper beyond an `org_id` enrichment column is required.

**Alternatives Considered**:

1. *Treat the SDK call as paginated and loop with `mistapi.get_all()`*. Rejected: the
   enriched doc explicitly states "Pagination: Not paginated." `get_all()` would issue
   redundant calls and add complexity without benefit.
2. *Call the raw REST URL with `requests` to bypass the SDK*. Rejected: violates the
   project rule that all Mist Cloud interaction goes through `mistapi`, and would
   bypass the existing adaptive delay / retry machinery.
3. *Cache the catalog locally and skip the call on subsequent runs*. Rejected: caching
   policy is a future concern. The endpoint is cheap (one GET, bounded payload), and a
   stale cache could hide upstream catalog updates.

---

## Research Task 2: Primary Key Strategy

**Decision**: Use `composite_pk` with primary key columns `['org_id', 'group', 'key']`
and a secondary index on `name` for human-friendly lookups.

```python
'getOrgApplicationList': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'group', 'key'],
    'indexes': ['name'],
},
```

**Rationale**: The response objects do not contain an `id` field, so a `natural_pk`
strategy keyed on `id` is not viable. The Mist API contract guarantees `group`, `key`,
and `name` are all present (the schema marks them required). The `key` field alone is
not guaranteed unique across `group` boundaries (e.g. a `key` like `web` could plausibly
appear under both `Web` and `Streaming`), so a single-column `key` PK would be unsafe.
The `(group, key)` pair is the natural identity for an application signature within an
org's catalog. Adding `org_id` to the PK is required because the SQLite table stores
results from multiple orgs across runs and a bare `(group, key)` could collide between
tenants. The `name` index supports the common NOC-engineer query "find me the app whose
name contains 'zoom'".

**Alternatives Considered**:

1. *`auto_increment_with_unique`*. Rejected: adds a synthetic `misthelper_internal_id`
   column that is never useful for joins or upserts, and forces every re-run to mint
   new IDs even though the underlying data is identical. The composite natural key is
   stable, deterministic, and cheap.
2. *`natural_pk` on `key` alone*. Rejected: cross-group collisions are possible and the
   resulting duplicate-key upsert would silently overwrite the wrong row.
3. *`composite_pk` on `(group, key)` without `org_id`*. Rejected: a multi-tenant SQLite
   table (one DB per MistHelper installation, many orgs over time) requires `org_id`
   in the PK to prevent cross-tenant collisions during upsert.

---

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- Output filename: `org_wxtag_applications_<org_id>_<timestamp>.csv`.
- SQLite table: `org_wxtag_applications`.
- ArangoDB collection: `org_wxtag_applications` (vertex collection); no edges introduced
  by this endpoint.

**Rationale**: The MistHelper convention is `<scope>_<resource>_<id>_<timestamp>.csv`
for org-scoped exports. `wxtag_applications` is the canonical resource name from the
URL path (`/wxtags/apps`). Keeping `wxtag_` as the prefix groups the new table next to
existing wxtag-related tables in SQLite, which aids manual exploration. The CSV
filename includes `org_id` so an engineer running against multiple orgs in one session
gets distinct files. `DataExporter.write_with_format_selection()` derives the SQLite
table name from the `api_function_name=` argument it receives; we will pass
`api_function_name='getOrgApplicationList'` and rely on the registered PK strategy to
materialize the table.

**Alternatives Considered**:

1. *Use `org_applications` (drop the `wxtag_` prefix)*. Rejected: the API path is
   explicitly under `/wxtags/`, and the resource is the application catalog *for*
   WxTags. Dropping the prefix would imply a broader scope than the endpoint actually
   provides and would conflict with any future `gateway-applications` table.
2. *Use one CSV file per org with a fixed name (no timestamp)*. Rejected: re-running
   the menu item would silently overwrite previous data. Timestamped filenames match
   the rest of the codebase and preserve history.
3. *Skip SQLite entirely and write only CSV*. Rejected: violates FR-004's requirement
   that all three backends receive consistent output.

---

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new menu item at number **58** within the misc safe-org-exports
cluster (56-59), labelled "Get Org WxTag Application List". Final integer to be
re-verified at `/speckit.tasks` time by grepping the live menu table.

**Rationale**: The MistHelper menu layout documented in `agents.md` reserves:
- 1-59 Safe Org Exports (with 56-59 = Misc),
- 60-96 Interactive Safe,
- 97-101 + 153 Resource Intensive,
- 102+ progressively more invasive.

The endpoint is a strictly read-only org-scoped export of a small configuration
catalog -- a textbook "misc safe org export". The 56-59 band is the correct home and
58 is the next free integer between 57 and 59 based on the most recent CHANGELOG
review. Adjacent operations (wxtag listing, wxrule listing) live nearby, so engineers
who land on this row will see contextually related options.

**Alternatives Considered**:

1. *Place inside the 37-41 Templates band*. Rejected: applications are not templates;
   they are reference data consumed by wxtags. The wxtag listing operations already
   live in the 56-59 band.
2. *Place at the next sequential integer after the highest existing menu number*.
   Rejected: that yields category drift (an org-export operation buried among
   firmware/destructive items). Slotting by category, not by sequence, is the project
   convention.
3. *Defer menu placement until `/speckit.tasks`*. Rejected: the plan requires a
   concrete proposal. 58 is the proposal; tasks.md confirms or shifts by one slot.

---

## Research Task 5: Required User Prompts (Which IDs From The User, Which From .env)

**Decision**: Prompt the user for **only** the `org_id` via `safe_input()`. Fall back
to `MIST_ORG_ID` in `.env` when the user submits an empty string. The API token and
host come from `.env` automatically via the existing `mistapi.APISession` -- they are
never prompted.

Prompt sequence:

1. `safe_input("Org UUID [default from .env MIST_ORG_ID]: ", context="org_application_list:org_id")`.
2. If the response is empty, use `os.environ.get("MIST_ORG_ID")`. If that is also
   empty, log a warning and return early.
3. Validate the resulting value against the Mist UUID regex (`^[0-9a-f-]{36}$`,
   case-insensitive). If invalid, log a warning and return early.

**Rationale**: The endpoint's only path parameter is `org_id`. There are no query
parameters, no per-site identifiers, and no device identifiers. The principle of least
prompting applies: prompt only for what the API requires, and let `.env` defaults
cover automation / `--test` paths where stdin is not available. `safe_input()` is
mandatory for SSH and container EOF safety. UUID validation prevents a malformed
prompt from being sent to Mist (which would return 400 / 404 and burn a rate-limit
slot).

**Alternatives Considered**:

1. *Also prompt for an output filename*. Rejected: the project's
   `DataExporter.write_with_format_selection()` already owns filename generation. A
   user-supplied filename would bypass the timestamp / org-id naming convention and
   could collide with other exports.
2. *Pull `org_id` from a globally cached session variable*. Rejected: MistHelper does
   not currently maintain such a global; introducing one for a single endpoint adds
   state without value. `.env` fallback is sufficient.
3. *Prompt for a `--detail` style flag*. Rejected: the endpoint has no query
   parameters and returns the full catalog unconditionally. There is nothing to vary.
