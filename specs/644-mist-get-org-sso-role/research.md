# Phase 0 Research: getOrgSsoRole

**Feature**: 644-mist-get-org-sso-role
**Endpoint**: `GET /api/v1/orgs/{org_id}/ssoroles/{ssorole_id}`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Use `mistapi.api.v1.orgs.sso_roles.getOrgSsoRole(apisession, org_id, ssorole_id)`
as the sole transport into Mist Cloud. The call returns a `mistapi.APIResponse` whose
`.data` attribute is a single JSON object (not a list) matching the OpenAPI
`sso_role` schema documented at
`documentation/api/orgs/GET_orgs_org_id_ssoroles_ssorole_id.md`.

**Rationale**:
- The enriched endpoint doc explicitly names the SDK path
  `mistapi.api.v1.orgs.sso_roles.getOrgSsoRole()` (line 174 of the doc). Note the
  underscore in `sso_roles`: the OpenAPI tag uses `ssoroles` but the Python module
  splits the tokens per PEP 8, matching Thomas Munzer's mistapi package convention.
- The response is a single object (not paginated), so no `mistapi.get_all()` wrapper
  is needed and no pagination loop is required.
- The 200 response schema has two required top-level fields (`name`, `privileges`) plus
  read-only metadata (`id`, `org_id`, `msp_id`, `created_time`, `modified_time`,
  `for_site`). `privileges` is an array (`minItems: 1`, `uniqueItems: true`) whose
  items include `role`, `scope`, and optional scope-specific ids (`org_id`, `site_id`,
  `sitegroup_id`) plus a `views` array of custom-role UI-view enum values.
- Standard 5000-req/hour rate limit applies. Adaptive delay via `delay_metrics.json`
  handles 429s without menu-item awareness.

**Alternatives Considered**:
- **Raw `requests.get()` with manual auth**: Rejected. The project constitution and
  agent instructions mandate `mistapi` as the sole Mist Cloud transport so that
  session pooling, retries, and rate-limit metrics all remain centralized.
- **Fetch the full list via `listOrgSsoRoles` and filter client-side**: Rejected.
  Wasteful of API quota; the single-role endpoint is the correct primitive when the
  user already knows a `ssorole_id`.

## Research Task 2: Primary Key Strategy

**Decision**: Two natural-PK tables using the strategy type
`natural_pk`. `org_sso_role_summary` uses `['org_id', 'id']` as its composite natural
key. `org_sso_role_privileges` uses a `composite_pk` with
`['org_id', 'ssorole_id', 'scope', 'scope_target_id', 'role']` because privileges are
inline array items without their own ids.

**Rationale**:
- `id` on the top-level SSO role is a stable Mist-Cloud-generated UUID
  (`contentEncoding: uuid`, `readOnly: true`), which fits `natural_pk` cleanly.
  Prefixing with `org_id` prevents cross-org collisions if a user exports multiple
  orgs into the same SQLite file.
- Privileges are embedded array items with no `id`. Their identity is defined by the
  tuple `(scope, scope_target_id, role)` where `scope_target_id` denormalizes
  `org_id` / `site_id` / `sitegroup_id` into a single column based on the value of
  `scope`. Adding `ssorole_id` and parent `org_id` to the composite key namespaces the
  row to its parent, allowing safe upsert.
- `INSERT OR REPLACE` on the composite key gives idempotent re-runs.

**Alternatives Considered**:
- **`auto_increment_with_unique` for privileges**: Rejected. Rerunning the export
  would create duplicate privilege rows on every invocation because the surrogate id
  differs each time. Composite natural keys are the project convention for embedded
  array items.
- **Single flat table with role and privileges joined**: Rejected. Cartesian
  duplication of role-level metadata (`name`, `for_site`, `created_time`, ...) across
  every privilege row bloats storage and breaks downstream tooling that expects one
  role row per role.

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- CSV filenames: `data/org_sso_role_summary_<org_id_short>_<ssorole_id_short>.csv`
  and `data/org_sso_role_privileges_<org_id_short>_<ssorole_id_short>.csv` (short
  id = first 8 hex chars of the UUID).
- SQLite tables: `org_sso_role_summary` and `org_sso_role_privileges` inside
  `data/mist_data.db`.
- `api_function_name="getOrgSsoRole"` is passed to
  `DataExporter.write_with_format_selection()` so PK strategy lookup succeeds.

**Rationale**:
- Names follow the snake_case pattern already used by adjacent exporters
  (`org_admin_summary`, `org_admin_privileges`). Suffixing the CSV with short
  org/role ids lets a user run the export against several roles in the same session
  without overwriting the previous file.
- Two tables mirror the two-entity model (see `data-model.md`) and keep the flat
  CSVs Excel-friendly for the target junior-NOC audience.
- `data/` is the enforced output root; no writes escape it.

**Alternatives Considered**:
- **Single JSON blob per role**: Rejected. The multi-backend `DataExporter` contract
  expects tabular records; JSON blob output would bypass SQLite/ArangoDB
  normalization.
- **Filename keyed only on `ssorole_id`**: Rejected. Users often run against multiple
  orgs; org context in the filename prevents ambiguity.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Register as **menu number 46** under the Config/Admin cluster
(operations 42-50 per `.github/copilot-instructions.md`).

**Rationale**:
- The Config/Admin cluster is the documented home for admin, token, and
  identity-related operations. SSO roles map IdP group attributes to Mist RBAC
  privileges, which is squarely an admin/identity concern -- exactly the
  responsibility of `OrgAdminExporter` (line ~11857 in `MistHelper.py`).
- 46 is the first empty slot adjacent to existing admin operations. If a merge-time
  collision is detected (another in-flight PR grabs 46 first), the implementer picks
  the next free integer inside 42-50 (47, 48, 49, or 50) without needing a plan
  revision.
- Placing SSO-role reads in the safe-org-export band (<= 89) keeps the operation
  inside the default `--test` sweep, guaranteeing regression coverage.

**Alternatives Considered**:
- **Menu 45**: Rejected as first choice because 45 has historically been claimed by
  existing admin operations in adjacent feature branches; 46 is safer.
- **Move into 51-59 (Misc)**: Rejected. Misc is a catch-all for operations that do
  not fit an existing cluster; admin/identity data has a proper home.
- **New cluster 200+ for SSO-only operations**: Rejected. One endpoint does not
  warrant a new cluster; the OrgAdminExporter class is already the correct container.

## Research Task 5: Required User Prompts

**Decision**: Two `safe_input()` prompts collected in order:
1. `org_id` -- default suggestion pulled from `MIST_ORG_ID` in `.env` via
   `ConfigUtils.get_default_org_id()` when set; empty input accepts the default.
2. `ssorole_id` -- no default; the user must supply a UUID (this is the primary
   selector for the endpoint).

Neither prompt reads any secret material. The API token itself is loaded exclusively
by `mistapi.APISession` from `MIST_API_TOKEN` in `.env` and never surfaces to the user
or to logs.

**Rationale**:
- `MIST_HOST` and `MIST_API_TOKEN` are already `.env`-managed for the whole app; the
  new menu inherits that path without change.
- `MIST_ORG_ID` is a documented convenience default for repeat single-org users. If
  present it becomes the prompt default; if absent the user must type the UUID.
- `ssorole_id` is intentionally not a `.env` default: SSO roles are typically
  short-lived / per-tenant, and hard-coding one would encourage stale data.
- Both prompts route through `safe_input(prompt, context="...")` so container/SSH
  EOF exits with code 0 and no traceback (Principle III).
- Both UUIDs are validated via `ValidationUtils` before the SDK call so a mistyped
  id produces a clean logged warning rather than a stack trace from mistapi.

**Alternatives Considered**:
- **Interactive picker driven by `listOrgSsoRoles`**: Rejected for this spec. It
  doubles API traffic and belongs in a separate feature (a menu wrapper that lists
  then drills down). This spec catalogs a single endpoint.
- **Positional CLI args instead of prompts**: Rejected as the primary path. The
  existing pattern is interactive prompts by default; the `--menu 46 --org <id>
  --ssorole <id>` non-interactive equivalent falls out naturally from the same
  `safe_input()` calls when stdin is a pipe, per the existing `safe_input` behavior.
