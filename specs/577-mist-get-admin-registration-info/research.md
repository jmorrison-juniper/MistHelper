# Phase 0 Research: getAdminRegistrationInfo

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/register/recaptcha` (operationId `getAdminRegistrationInfo`)
**Source doc**: `documentation/api/admins/GET_register_recaptcha.md`

## Research Task 1: SDK function signature & behavior

**Decision**: Call the endpoint through
`mistapi.api.v1.admins.admins.getAdminRegistrationInfo(apisession, recaptcha_flavor=None)`.

**Rationale**: The enriched per-endpoint doc
(`documentation/api/admins/GET_register_recaptcha.md`) explicitly lists the SDK path as
`mistapi.api.v1.admins.admins.getAdminRegistrationInfo()`. The Mist OpenAPI tag is
`Admins`, and the `mistapi` SDK groups functions by tag rather than URL path -- this is
why the file lives under `mistapi/api/v1/admins/admins.py` even though the URL is
`/api/v1/register/recaptcha`. The endpoint takes no path parameters and one optional
query parameter (`recaptcha_flavor`, free-form string, documented enum `google` |
`hcaptcha`). The first positional argument is always the live `mistapi.APISession`
instance (`self.api_session` inside `OrgExportUtils`). The response is a single JSON
object with three fields (`flavor`, `required`, `sitekey`); pagination does not apply.

**Alternatives Considered**:

1. **Hand-rolled `requests.get(...)` call against the bare URL**: Rejected -- violates
   the project rule that `mistapi` is the sole permitted interface to Mist Cloud, and
   loses the rate-limiter / retry / `delay_metrics.json` integration that
   `mistapi.APISession` provides for free.
2. **Treat the endpoint as authenticated and require `MIST_API_TOKEN`**: Rejected --
   the doc's Gotchas section states this is a public endpoint. The session still loads
   the token from `.env` if present (no behavior change), but the menu item must not
   abort when the token is missing.
3. **Use the spec.md path `mistapi.api.v1.register.recaptcha`**: Rejected -- the SDK
   does not expose functions under that module path. The spec text was inferred from
   the URL; the enriched doc is authoritative and points to
   `mistapi.api.v1.admins.admins`.

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` with primary key `['sitekey']`.

**Rationale**: The response object has exactly three fields:

| Field      | Type    | Stability                                                       |
|------------|---------|-----------------------------------------------------------------|
| `flavor`   | string  | Low cardinality (2 values today: `google` / `hcaptcha`).        |
| `required` | boolean | Two-valued.                                                     |
| `sitekey`  | string  | Tenant-unique, opaque, stable per (flavor) configuration.       |

The `sitekey` is the only field unique enough to serve as a natural identifier across
re-runs. Re-fetching with the same `recaptcha_flavor` should upsert the same row, not
duplicate it. Using `sitekey` as the PK lets `INSERT OR REPLACE` keep the table
single-row-per-configuration. A secondary index on `flavor` is added so the table can be
queried by flavor without a scan.

**Alternatives Considered**:

1. **`auto_increment_with_unique`**: Rejected -- the table would grow by one row on
   every run even though the underlying configuration almost never changes. Defeats the
   point of registering a PK strategy.
2. **`composite_pk` on `(flavor, sitekey)`**: Rejected -- redundant. `sitekey` is
   already unique per flavor; the composite adds no disambiguation and complicates
   upsert logic.
3. **No PK strategy entry (fall back to default)**: Rejected -- violates FR-005 and the
   Constitution's database-strategy requirement that every new operation register an
   explicit strategy.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV filename: `data/admin_registration_info.csv`
- SQLite table: `admin_registration_info`
- ArangoDB collection: `admin_registration_info`

**Rationale**: Follows the established convention: `data/<operation_id_snake_case>.csv`
and identical snake_case for SQLite and ArangoDB. `getAdminRegistrationInfo` ->
`admin_registration_info`. Short, unambiguous, matches the response payload shape
(one row per reCAPTCHA configuration). No org_id / site_id prefix is needed because the
endpoint is not org-scoped.

**Alternatives Considered**:

1. **`data/register_recaptcha.csv`**: Rejected -- mirrors the URL rather than the
   operationId. The rest of the MistHelper export filenames key off operationId for
   consistency with `ENDPOINT_PRIMARY_KEY_STRATEGIES` lookups.
2. **`data/admin_registration.csv`**: Rejected -- ambiguous; "admin_registration" could
   imply POST `/register` (the actual create call). The `_info` suffix matches the
   operationId verb and signals read-only.
3. **Per-flavor filename suffix (e.g. `_google.csv`)**: Rejected -- the menu item makes
   one call per invocation. Splitting files by flavor would require multiple writes per
   run and defeat the single-row-per-configuration upsert model.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **59**, placed at the end of the "Misc Safe Org Exports
(56-59)" cluster.

**Rationale**: The repo-level menu range table
(`.github/copilot-instructions.md` -> Menu System & Operations) defines:

- 1-59  Safe Org Exports (Misc tail = 56-59)
- 60-96 Interactive Safe

This endpoint is read-only, takes no required org context, and produces a small public
configuration payload -- an excellent fit for the "Misc" tail of the safe exports block.
Slot 59 is the last available integer in that block before the Interactive Safe range
begins at 60. Placing it here keeps the existing range semantics intact and avoids
disturbing the WebSocket / Interactive / Destructive ranges. The final number is
re-confirmed at `/speckit.tasks` time against any in-flight branches; if 59 is taken,
the next free integer below 60 is used.

**Alternatives Considered**:

1. **Reuse a high number in Interactive Safe (e.g. 92-96 viewer block)**: Rejected --
   this is not a viewer; it's a one-shot export with no follow-up interaction.
2. **Place under Resource Intensive (97-101)**: Rejected -- the endpoint is a single
   non-paginated GET that completes in <=2 seconds. Resource Intensive is reserved for
   long-running bulk operations.
3. **Insert mid-range (e.g. 50.5)**: Rejected -- the menu dispatcher uses integer
   selection; non-integer slots are not supported.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**:

- **From `.env`**: `MIST_HOST` (mandatory for `mistapi.APISession`). `MIST_API_TOKEN` is
  loaded if present but the endpoint does not require authentication, so a missing
  token does not block the call (an INFO log line notes the unauthenticated mode).
- **From the user via `safe_input()`**: One optional prompt --
  `recaptcha_flavor` (default blank -> let the API choose). Accepted values are the
  documented enum `google` or `hcaptcha`; any other non-empty input is rejected with a
  WARNING and the override is dropped (the call proceeds with no flavor parameter).
- **Not prompted**: No org_id, site_id, or device_id is required -- the endpoint is
  org-agnostic, which is the unusual property that motivates the "Misc" placement.

**Rationale**: The endpoint signature shows zero path parameters and one optional query
parameter. Prompting for org context would mislead the user into believing the call is
org-scoped (it isn't) and would generate noise in audit logs. The single optional
prompt is implemented with a default-on-empty pattern so non-interactive `--test` runs
work without input. `safe_input()` is used for the prompt with
`context="admin_registration_info:recaptcha_flavor"` so SSH / container EOF surfaces as
a clean exit 0.

**Alternatives Considered**:

1. **Hard-code `recaptcha_flavor="google"` and skip the prompt**: Rejected -- removes
   user control over an officially documented parameter, and would silently drop
   `hcaptcha` data when Mist switches the default.
2. **Prompt for org_id "just in case future versions become org-scoped"**: Rejected --
   speculative. The current OpenAPI spec is the contract; adapt when the spec changes.
3. **Prompt for output filename**: Rejected -- the convention (operationId-based name
   under `data/`) is uniform across the codebase. Overriding adds inconsistency.
