# Phase 0 Research: getOrgAptemplate

This document records the five Phase 0 research tasks resolved before any
Phase 1 design artifact was produced. Each task uses the Decision / Rationale /
Alternatives Considered format mandated by the constitution.

## Research Task 1: SDK function signature & behavior

**Decision**: Use the `mistapi` SDK function
`mistapi.api.v1.orgs.ap_templates.getOrgAptemplate(apisession, org_id,
aptemplate_id)`. The function takes the active `mistapi.APISession` plus two
required string UUID parameters and returns a `mistapi.APIResponse` whose
`.data` attribute is a single JSON object (one AP template record). No query
parameters. No pagination. Standard error envelope on 4xx / 5xx (`.status_code`,
`.data` may carry an `error` field).

**Rationale**: The enriched per-endpoint reference
`documentation/api/orgs/GET_orgs_org_id_aptemplates_aptemplate_id.md`
(lines 5-28, 617-619) names the SDK module path explicitly as
`mistapi.api.v1.orgs.ap_templates.getOrgAptemplate()` and confirms the two
required path parameters with no body, no query params, no pagination.
Adjacent menu code in `MistHelper.py` already uses the same `apisession,
org_id, ...` call convention for related template endpoints
(`listOrgApTemplates`, `listOrgNetworkTemplates`), so the new method drops in
without any new SDK glue. The 200 response body is documented as an `object`
with a required `ap_matching` property (line 593-595 of the reference doc), so
the SDK return type is a dict, not a list -- the flatten step must wrap it in
a one-element list before calling `DataExporter`.

**Alternatives Considered**:
- *Raw `requests` HTTP call*: Rejected. Constitution and project conventions
  mandate `mistapi` as the sole interface to the Mist Cloud; bypassing it
  loses rate-limit handling, session pooling, and `.env`-driven auth.
- *Calling `listOrgApTemplates` and filtering client-side*: Rejected. That
  costs one extra network round trip and risks pagination edge cases on orgs
  with many templates. The dedicated detail endpoint exists for exactly this
  use case.
- *Async / batched fetch over a list of template IDs*: Rejected as out of
  scope. The spec is for a single template detail GET; bulk fetch belongs in
  a separate spec if requested later.

## Research Task 2: Primary Key Strategy

**Decision**: Use **`natural_pk`** with `primary_key=['id']` and indexes on
`['org_id', 'site_id', 'for_site']`. Registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` under the operationId key `getOrgAptemplate`.

**Rationale**: The 200 response body documents `id` as a `string` with
`contentEncoding: uuid` and `readOnly: true`
(`documentation/api/orgs/GET_orgs_org_id_aptemplates_aptemplate_id.md` lines
513-521), and the Mist API guarantees that AP template UUIDs are stable across
GET / PUT / DELETE cycles. No timestamp component is needed for uniqueness,
so a composite key would be wasteful; the row is not an aggregated rollup, so
an auto-increment surrogate is not appropriate. Indexing `org_id` supports
"show all templates for org X" queries from the SQLite backend; indexing
`site_id` supports the site-bound subset (when `for_site=true`); indexing
`for_site` lets analysts filter org-level vs site-bound templates quickly.

**Alternatives Considered**:
- *`composite_pk` on `['id', 'org_id']`*: Rejected. `id` is already globally
  unique within Mist; adding `org_id` to the PK gains no upsert correctness
  and complicates joins from the ArangoDB graph backend.
- *`auto_increment_with_unique`*: Rejected. The endpoint exposes a stable
  UUID; using an internal surrogate would create duplicate rows on every
  re-run when SQLite rolls a new auto-increment value, defeating the entire
  purpose of the strategy table.

## Research Task 3: Output filename and SQLite table

**Decision**:
- **Summary CSV / SQLite table**: `org_aptemplates` -- one row per template,
  carrying scalar fields and JSON-encoded blobs for nested `ap_matching` and
  `wifi` objects.
- **Match-rule CSV / SQLite table**: `org_aptemplate_match_rules` -- zero or
  more rows per template, one row per entry in `ap_matching.rules`, with a
  foreign key column `aptemplate_id` back to `org_aptemplates.id`.
- **CSV output filenames** under `data/`:
  `org_aptemplate_summary_<org_id>_<aptemplate_id>.csv` and
  `org_aptemplate_match_rules_<org_id>_<aptemplate_id>.csv` (suffix mirrors
  the existing two-file split used by Menu 95 / async-claim-status).

**Rationale**: The response is a single object with a nested rules array of
unbounded length, so a single flat CSV would either explode column count or
lose the array entirely. The two-table split matches the pattern already in
use for endpoints with one summary plus a variable-length list (e.g. the
license-async-claim-status feature in spec 500). Including both UUIDs in the
filename keeps re-runs against different orgs / templates from colliding on
disk; SQLite tables are global per backend, and the `aptemplate_id` foreign
key plus the `id` primary key keep multi-template runs distinct without any
filename suffix.

**Alternatives Considered**:
- *Single flattened CSV with `rules.0.match_model`, `rules.1.match_model`,
  ...*: Rejected. Column count is unbounded; comparison across templates
  becomes impractical; SQLite has a 2000-column ceiling that real templates
  can approach.
- *JSON-only output (no CSV)*: Rejected. Conflicts with the multi-backend
  contract -- CSV is a first-class backend, not optional.
- *Single table with a TEXT column holding the entire JSON*: Rejected for the
  match-rules table -- analysts cannot SQL-filter on `match_model` without
  re-parsing JSON every query. The summary table keeps `ap_matching_enabled`
  and `wifi_enabled` as first-class boolean columns and stores the rest as
  JSON-text, balancing flexibility against introspection.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Propose menu number **96** in the safe-org-exports / Viewers
band (92-96). Title: `Get Org AP Template Detail (read-only)`. To be
re-verified at `/speckit.tasks` time; if 96 is taken by an in-flight feature,
fall back to the next free integer in the same safe-read band.

**Rationale**: The
`.github/copilot-instructions.md` menu map places template-related operations
in cluster 37-41 (Templates) and viewers in 92-96. The existing
`listOrgApTemplates` operation is documented as Menu 35
(`documentation/api/orgs/GET_orgs_org_id_aptemplates_aptemplate_id.md` line
636), so the natural cluster is the templates band -- but 37-41 has only five
slots and is likely saturated. The next safe-read slot below the
resource-intensive block (97-101) is 96, which sits in the Viewers cluster --
a semantically reasonable home for "view detail of a single AP template."
Menu 96 keeps the new item well inside the default `--test` sweep range and
clear of the destructive 154-194 band that requires explicit human review.

**Alternatives Considered**:
- *Renumber the templates cluster to make room at 42*: Rejected. Renumbering
  is breaking change for users with scripts that call `--menu <n>`; constitution
  Principle IV (Pipeline) discourages disruptive reorganization in unrelated
  PRs.
- *Place in the destructive range (154-194)*: Rejected. The endpoint is HTTP
  GET only; destructive placement would falsely trip the typed-confirmation
  guardrail and violate Principle III intent.
- *Defer numbering to `/speckit.tasks`*: Rejected. The plan must propose an
  explicit number per the prompt's hard requirements; deferring it leaves a
  NEEDS-CLARIFICATION gap.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Two prompts collected via `safe_input()`:
1. **`org_id`** -- default from `.env` (`MIST_ORG_ID`); empty input keeps the
   default; non-empty input overrides for this invocation only. Validated
   against the Mist UUID shape before use. Prompt context string:
   `"org_aptemplate:org_id"`.
2. **`aptemplate_id`** -- no `.env` default. The user must type the full UUID
   (or paste it after running Menu 35 `listOrgApTemplates` to enumerate
   candidates). Empty input or invalid UUID logs a `WARNING` and returns
   early without making an API call. Prompt context string:
   `"org_aptemplate:aptemplate_id"`.

**Rationale**: `MIST_ORG_ID` is already an established `.env` variable used by
adjacent menu items in `MistHelper.py`, so reusing it removes one prompt for
the common single-org operator case while preserving multi-org flexibility.
`aptemplate_id` is per-template and has no sensible global default; storing
one in `.env` would be misleading and would invite cargo-culted test-data UUIDs
into production runs. Both UUIDs are validated client-side to surface obvious
typos as a logged warning rather than as an opaque Mist 400.

**Alternatives Considered**:
- *Hard-code `org_id` from `.env` with no override prompt*: Rejected. Multi-org
  operators (the documented secondary persona) need a way to switch context
  without editing `.env` between runs.
- *Auto-fetch and present an interactive picker over `listOrgApTemplates`*:
  Rejected as scope creep. The spec is a single endpoint; chaining two API
  calls + interactive selection belongs in a follow-up "browse templates"
  feature. The Menu 35 + Menu 96 workflow (list, then detail-by-UUID) already
  serves this need without coupling the two menus.
- *Read `aptemplate_id` from a CSV file*: Rejected. Adds I/O complexity and
  failure modes for a single-record endpoint; bulk fetch is out of scope.
