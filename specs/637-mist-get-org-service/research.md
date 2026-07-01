# Phase 0 Research: getOrgService

**Feature**: 637-mist-get-org-service
**Date**: 2026-06-30
**Source docs**: `documentation/api/orgs/GET_orgs_org_id_services_service_id.md`

## Research Task 1 -- SDK Function Signature and Behavior

- **Decision**: Invoke `mistapi.api.v1.orgs.services.getOrgService(apisession, org_id,
  service_id)`. The call returns an `APIResponse` whose `.data` attribute is a single JSON object
  (not a list) matching the `service` schema documented in the enriched per-endpoint file. No
  query parameters. No pagination. Standard `Authorization: Token {api_token}` header applied by
  the shared `apisession` singleton.
- **Rationale**: The enriched doc file `GET_orgs_org_id_services_service_id.md` explicitly lists
  path parameters `org_id` and `service_id` (both required strings), zero query parameters, a
  200-response schema with the `id`/`org_id`/`name`/`type`/`traffic_type` fields plus optional
  arrays (`addresses`, `apps`, `urls`, `specs`), and states "Not paginated" under the Pagination
  section. The doc also confirms the exact SDK dotted path `mistapi.api.v1.orgs.services.getOrgService()`.
  The plural sibling `listOrgServices` already exists in MistHelper.py at line 6371 using the
  identical `apisession, org_id` calling convention, so the singular sibling only adds one
  positional `service_id` argument.
- **Alternatives Considered**:
  1. Wrap the raw REST endpoint via `requests` -- rejected because it bypasses the shared
     apisession token, retry, and rate-limit hooks in mistapi 0.59+.
  2. Fetch the whole list via `listOrgServices` and filter client-side -- rejected because it
     wastes API budget and duplicates data already correctly stored in `org_services`, and it
     cannot answer the "retrieve one specific service" user story that motivated this spec.

## Research Task 2 -- Primary Key Strategy

- **Decision**: `natural_pk` with `primary_key=["id"]` and `indexes=["org_id", "name", "type"]`,
  matching the existing `listOrgServices` entry at MistHelper.py line 4768.
- **Rationale**: The 200-response schema declares `id` as a `uuid`-encoded string that is
  `readOnly` and marked as the "Unique ID of the object instance in the Mist Organization." The
  `org_id`, `name`, and `type` fields are the standard lookup dimensions for services (org
  scoping, human search, filter by service type). Because the endpoint returns exactly the same
  object shape that `listOrgServices` returns per-element, reusing the same PK strategy
  guarantees `INSERT OR REPLACE` upserts across both endpoints land in one table with no
  duplicate rows.
- **Alternatives Considered**:
  1. `composite_pk=["id","org_id"]` -- rejected because `id` alone is globally unique across the
     org and adding `org_id` provides no additional disambiguation.
  2. `auto_increment_with_unique` on `id` -- rejected because the API already supplies a stable
     UUID; an artificial surrogate key would drift from the source of truth.

## Research Task 3 -- Output Filename and SQLite Table

- **Decision**: Filename base `org_services_detail`, SQLite table `org_services` (shared with the
  list endpoint). Full output path resolves to `data/org_services_detail.csv` (CSV backend) and
  the corresponding `data/mist_data.db` table `org_services` (SQLite backend). CSV name diverges
  from the list endpoint (`org_services.csv`) so that operators can distinguish "single-service
  point read" audit trails from bulk exports, while the underlying SQLite row lands in the same
  authoritative table.
- **Rationale**: `DataExporter.write_with_format_selection(data, filename,
  api_function_name="getOrgService")` uses the `api_function_name` argument to look up the PK
  strategy and target table. Sharing the `org_services` table across list and detail endpoints
  matches the codebase pattern for `list*` / `get*` sibling pairs elsewhere (e.g., sites and site
  detail) and prevents schema divergence.
- **Alternatives Considered**:
  1. Distinct table `org_service_detail` -- rejected because the response schema is identical to
     one element of `listOrgServices`; a second table would either duplicate rows or drift.
  2. Same CSV filename `org_services.csv` -- rejected because it would overwrite the bulk export
     when a user runs only the point read.

## Research Task 4 -- Menu Category Placement and Next Available Menu Number

- **Decision**: Menu number **195**, placed in the "Interactive Safe / Single-Object Viewers"
  category (peer of items 92-96 pattern), described in the README menu table as
  `195 | Get single Org Service by ID | safe read | requires org_id (env), service_id (prompt)`.
- **Rationale**: The reference project layout (agents.md, .github/copilot-instructions.md) shows
  destructive operations run from 154-194 with 194 as the current cap ("Clone device config to
  gateway template"). Placing this safe read at 195 keeps it outside the destructive block, opens
  a new safe-read contiguous range (195+) for future single-object detail endpoints, and avoids
  reshuffling any existing menu number. Categorising as a viewer matches the read-only,
  interactive prompt-driven UX of items 92-96.
- **Alternatives Considered**:
  1. Insert into the 60-96 interactive-safe range by shifting numbers -- rejected because it
     breaks the automation contract that already relies on stable menu numbers (users script
     `--menu N`).
  2. Group next to `listOrgServices` (currently menu 4 per the enriched doc "MistHelper Notes"
     line) -- rejected for the same stability reason.

## Research Task 5 -- Required User Prompts

- **Decision**: Prompt once via `safe_input("Enter service_id UUID: ", context="get_org_service")`
  for the `service_id` path parameter. Load `org_id` from the standard `.env` variable
  `MIST_ORG_ID` via the existing `GlobalImportManager` / `.env` loader, with an optional override
  prompt `safe_input("Override org_id (blank = use MIST_ORG_ID): ",
  context="get_org_service_org_id")` that accepts empty input to keep the env default.
- **Rationale**: `org_id` is a long-lived, per-tenant identifier already resolved from `.env` in
  every existing services-reading menu (consistent with `listOrgServices` at line 6371 which does
  not re-prompt for `org_id`). `service_id` is a per-request selection that must come from the
  user because there is no reasonable default. The override prompt preserves the multi-org
  workflow used elsewhere without penalising the common single-org case.
- **Alternatives Considered**:
  1. Prompt for both org_id and service_id every run -- rejected because it slows the common case
     and diverges from the pattern used by peer menus.
  2. Require operator to also pass service_type / name -- rejected because the endpoint does not
     accept those parameters; only the two path IDs matter.
