# Phase 0 Research: getOrgSecIntelProfile

Feeds Phase 1 design decisions in `data-model.md`, `quickstart.md`, and
`contracts/get_org_sec_intel_profile.md`.

## Research Task 1: SDK Function Signature & Behavior

- **Decision**: Call
  `mistapi.api.v1.orgs.secintel_profiles.getOrgSecIntelProfile(apisession, org_id, secintelprofile_id)`
  and use `response.data` (Python dict) as the source of truth.
- **Rationale**: The enriched endpoint doc at
  `documentation/api/orgs/GET_orgs_org_id_secintelprofiles_secintelprofile_id.md`
  documents the SDK path as
  `mistapi.api.v1.orgs.secintel_profiles.getOrgSecIntelProfile()`. The
  operationId (`getOrgSecIntelProfile`), HTTP verb (`GET`), path
  (`/api/v1/orgs/{org_id}/secintelprofiles/{secintelprofile_id}`), path
  parameters (`org_id`, `secintelprofile_id` -- both required), lack of query
  parameters, and non-paginated response together match the standard
  single-object read pattern used elsewhere in MistHelper (e.g. `getSiteInfo`,
  `getOrgLicensesSummary`). Wrapping the SDK function is consistent with
  Constitution Principle II (no wrappers, class methods only) because the
  MistHelper method is a menu-facing class method, not a wrapper.
- **Alternatives Considered**:
  - **Direct `requests` call** -- rejected. Bypasses `mistapi.APISession`
    rate limiting, retry, and auth token management. Violates the
    "single-permitted-interface" constraint.
  - **Batch fetch via list endpoint** -- rejected. The list endpoint
    (`GET /api/v1/orgs/{org_id}/secintelprofiles`) is a separate operationId
    (`listOrgSecIntelProfiles`) and a separate spec. This spec is scoped to
    the per-object GET only.

## Research Task 2: Primary Key Strategy

- **Decision**: **`natural_pk`** using `secintelprofile_id` as the primary key
  for the summary row and a **composite_pk** using
  `(secintelprofile_id, category)` for the rule detail rows.
- **Rationale**: SecIntel profiles are org-scoped Mist configuration objects
  identified by a stable UUID that the API accepts as a path parameter. The
  same UUID round-trips as the object's `id` on list/read/update/delete, so
  `natural_pk` is appropriate for the header row. The nested `profiles` array
  contains at most one rule per `category` enum value (`CC`, `IH`, `DNS`), so
  `(secintelprofile_id, category)` is a valid natural composite for the
  detail rows and prevents duplicates on re-run. Both strategies match
  precedents already in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (natural PK for
  configuration objects, composite PK for nested per-item detail rows).
- **Alternatives Considered**:
  - **`auto_increment_with_unique`** -- rejected. Would generate synthetic
    surrogate keys and lose upsert semantics; re-runs would append duplicates.
  - **Single flat table with array serialized to JSON string** -- rejected.
    Makes the data unqueryable from SQL and inconsistent with the
    two-table pattern already used for `LicenseExportUtils` claim status
    (spec 500).

## Research Task 3: Output Filename and SQLite Table

- **Decision**:
  - CSV summary: `data/org_secintel_profile_summary_{org_id}_{secintelprofile_id}.csv`
  - CSV detail: `data/org_secintel_profile_rules_{org_id}_{secintelprofile_id}.csv`
  - SQLite tables: `org_secintel_profile_summary` and
    `org_secintel_profile_rules`
  - `api_function_name` argument passed to
    `DataExporter.write_with_format_selection()`: `getOrgSecIntelProfile`
- **Rationale**: File naming follows the existing pattern
  `data/{operation_object}_{scope_id}.csv`. Including both `org_id` and
  `secintelprofile_id` in the CSV filename lets the user retain per-profile
  exports without collision. The SQLite table names are shared across all
  invocations because rows carry both IDs as columns, so upserts by natural
  PK work correctly. Passing the operationId as `api_function_name` lets
  `DataExporter` look up the PK strategy in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` without extra plumbing.
- **Alternatives Considered**:
  - **Single table with wide columns** -- rejected. Nested `profiles` array
    would force per-row JSON serialization; loses SQL queryability.
  - **Timestamp-suffixed CSV filenames** -- rejected. Breaks idempotent
    re-runs; the user cannot easily overwrite a stale export.

## Research Task 4: Menu Category Placement and Next Available Menu Number

- **Decision**: Menu number **89**, in the **Safe Org Exports (1-89)** cluster,
  adjacent to other per-object org read endpoints and near existing
  org-security configuration reads.
- **Rationale**: The `.github/copilot-instructions.md` menu range table lists
  1-89 as safe org exports (single-request configuration reads). SecIntel
  profiles are org-scoped, read-only in this spec, and non-destructive -- a
  clean fit for that cluster. Menu number 89 is chosen as the next
  currently-unused slot below the resource-intensive block that begins at 97.
  The number will be re-verified at `/speckit.tasks` time against the
  authoritative menu registration in `MistHelper.py`; if 89 is taken by
  another in-flight branch, the next free integer in the same cluster is
  used.
- **Alternatives Considered**:
  - **Menu 100+ (Destructive block 154-194)** -- rejected. The endpoint is
    strictly read-only; placement in the destructive block would mislead the
    junior NOC audience.
  - **Menu 60-96 (Interactive Safe cluster)** -- rejected. That cluster is
    reserved for site-scoped operations. SecIntel profiles are org-scoped
    configuration objects.

## Research Task 5: Required User Prompts

- **Decision**: Prompt the user for **two identifiers** via `safe_input()`:
  1. `org_id` -- if `.env` supplies `MIST_ORG_ID`, present it as the default
     and accept an empty response to reuse it; otherwise require entry.
  2. `secintelprofile_id` -- always prompt (no sensible `.env` default
     because a user typically has many profiles; a new optional
     `MIST_SECINTEL_PROFILE_ID` env var is honored when the operation runs
     under `--test` for CI, but never pre-fills the interactive prompt
     silently).
- **Rationale**: Consistent with the safety-first prompt pattern already
  used for org-scoped per-object reads. Not silently defaulting the profile
  ID prevents the junior NOC engineer from accidentally querying the wrong
  profile when multiple exist. `.env` fallback for the profile ID only under
  `--test` keeps automated CI runs deterministic without weakening the
  interactive UX.
- **Alternatives Considered**:
  - **Auto-discover profile IDs via `listOrgSecIntelProfiles`** -- rejected
    for this spec. Adds an extra API call and pulls in a dependency on the
    list endpoint (separate spec). Can be added in a follow-up "picker" spec
    once both list and get endpoints exist.
  - **Accept profile name instead of UUID** -- rejected. The Mist API
    requires the UUID; adding a name-to-ID lookup would again require the
    list endpoint. Deferred.
