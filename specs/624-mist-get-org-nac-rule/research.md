# Phase 0 Research: getOrgNacRule

**Feature**: 624-mist-get-org-nac-rule
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Source of truth**: `documentation/api/orgs/GET_orgs_org_id_nacrules_nacrule_id.md`

This document captures the five Phase 0 research tasks required before Phase 1
design. Each task uses the Decision / Rationale / Alternatives Considered
format mandated by the constitution.

---

## Research Task 1: SDK function signature & behavior

### Decision

Invoke the endpoint through the `mistapi` SDK using:

```python
resp = mistapi.api.v1.orgs.nac_rules.getOrgNacRule(
    apisession,       # mistapi.APISession instance already created at process start
    org_id,           # UUID string from .env MIST_ORG_ID or user prompt
    nacrule_id,       # UUID string prompted from the user via safe_input()
)
payload = resp.data   # single JSON object (nac_rule schema)
```

Key behavioral facts (from `documentation/api/orgs/GET_orgs_org_id_nacrules_nacrule_id.md`):

- HTTP: `GET /api/v1/orgs/{org_id}/nacrules/{nacrule_id}`
- Path params: `org_id` (required, UUID), `nacrule_id` (required, UUID)
- Query params: none
- Request body: none
- Response 200: a single `nac_rule` object with fields `action`, `apply_tags`,
  `created_time`, `enabled`, `guest_auth_state`, `id`, `matching` (nested),
  `modified_time`, `name`, `not_matching` (nested), `order`, `org_id`.
- Pagination: not paginated (single object, not a list).
- Errors: 400 (bad syntax), 401 (unauthorized), 403 (permission denied),
  404 (rule not found), 429 (rate limit -- adaptive delay handles).
- SDK module path in the doc: `mistapi.api.v1.orgs.nac_rules.getOrgNacRule`
  (note: `nac_rules` with an underscore, matching the mistapi 0.59+ module
  layout for camelCase operationIds against the `nacrules` URL segment).

### Rationale

The enriched doc file was auto-generated from the Mist OpenAPI spec plus SDK
introspection, so the module path is authoritative. Using the SDK (not raw
`requests`) is mandatory per the project's dependency rules -- `mistapi` is
the sole permitted Mist Cloud interface. `resp.data` yields the parsed JSON
directly, which matches every other MistHelper menu method.

### Alternatives Considered

- **Raw `requests` HTTP call**: Rejected. Violates the "mistapi SDK is the
  sole interface" project rule and would bypass the SDK's built-in retry,
  header, and rate-limit handling.
- **Using `listOrgNacRules` + client-side filter by id**: Rejected. Wastes
  quota (5000 calls/hour) and defeats the point of a single-object GET.

---

## Research Task 2: Primary Key Strategy

### Decision

Use **`natural_pk`** with `primary_key = ['id']` and secondary indexes on
`org_id` and `name`. Registered as:

```python
'getOrgNacRule': {
    'type': 'natural_pk',
    'primary_key': ['id'],
    'indexes': ['org_id', 'name', 'action', 'enabled'],
}
```

### Rationale

The response schema exposes an `id` field described as "Unique ID of the
object instance in the Mist Organization" (contentEncoding: uuid, readOnly:
true). NAC rules are stable configuration objects -- unlike time-series
events or per-request stats, the same rule keeps the same UUID across every
GET. `INSERT OR REPLACE` on `id` therefore gives clean upsert semantics on
repeated runs. Secondary indexes on `org_id`, `name`, `action`, and
`enabled` accelerate the most common NOC queries ("show all block rules
for org X", "find rule named 'guest-vlan'").

### Alternatives Considered

- **`composite_pk` on `(id, org_id)`**: Rejected. The `id` alone is already
  guaranteed unique inside an org, and the same NAC rule id cannot span
  multiple orgs, so the composite adds no uniqueness value.
- **`composite_pk` on `(id, modified_time)`**: Rejected. Would keep every
  historical version of a rule, which is a nice-to-have but not the goal of
  this endpoint -- the endpoint returns "current state", not "history".
  Historical retention can be a future feature.
- **`auto_increment_with_unique`**: Rejected. NAC rules have a stable UUID,
  so introducing a synthetic `misthelper_internal_id` would just add a
  useless column.

---

## Research Task 3: Output filename and SQLite table

### Decision

- **CSV filename**: `data/org_nac_rule.csv`
- **SQLite table**: `org_nac_rule`
- **ArangoDB collection**: `org_nac_rule` (with graph edge `org --contains--> nac_rule` per the existing polyglot pattern)
- **Redis key prefix**: `mist:org_nac_rule:<nacrule_id>`

Filenames use snake_case singular form because the endpoint returns exactly
one rule per call, not a collection. This distinguishes it from the plural
`org_nacrules.csv` that `listOrgNacRules` writes.

### Rationale

Follows the established MistHelper convention: CSV file basename == SQLite
table name == ArangoDB collection name, all snake_case, singular for
single-object GETs and plural for list endpoints. This lets the
`DataExporter.write_with_format_selection(data, filename,
api_function_name='getOrgNacRule')` call resolve the right storage target
by name lookup against `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

### Alternatives Considered

- **`org_nacrule_detail.csv`**: Rejected. "detail" is used elsewhere in the
  codebase for the `detail=true` query-parameter variants (e.g. license
  claim status). This endpoint has no such parameter, so "detail" would
  mislead.
- **Merge with `org_nacrules.csv`**: Rejected. The list endpoint may return
  a subset of fields (Mist API commonly trims sub-objects in list
  responses); merging risks column drift.

---

## Research Task 4: Menu category placement and next available menu number

### Decision

- **Category**: Safe Org Exports > Config / Admin sub-cluster (menu range
  42-59 per the copilot-instructions.md menu map).
- **Proposed menu number**: **59**.
- **Adjacent placement**: Immediately after `listOrgNacRules` (menu 43 per
  the MistHelper Notes section of the enriched doc). If the codebase has a
  free slot at 44-58 that groups the two operations tighter, the task
  phase picks that instead; otherwise 59 is used.

### Rationale

The endpoint is strictly read-only, so it belongs in the Safe Org Exports
band (1-59), never in the destructive range (154-194). Within Safe Org
Exports, NAC-rules operations naturally live in the Config / Admin
sub-cluster (42-50 per the copilot-instructions.md map extended to 59 for
overflow). Placing "get single NAC rule" adjacent to "list NAC rules"
matches the pattern used elsewhere in the codebase (e.g. sites 1 / site 2,
inventory list / inventory detail). Choosing 59 -- the highest free integer
in the sub-cluster -- avoids shuffling existing numbers and keeps the
change to a pure additive edit. If a concurrent feature branch has already
claimed 59, the task phase picks the next free integer in the same band.

### Alternatives Considered

- **Menu 44 (immediately after listOrgNacRules)**: Preferred if free at
  task time. Rejected here as the default because 44 may already be taken
  by an unrelated Config/Admin operation, and reshuffling menu numbers
  breaks existing user muscle memory and any external automation calling
  `--menu 44`.
- **Menu 200+ (new tier for single-object GETs)**: Rejected. Creating a new
  menu tier for one endpoint is over-engineering. The Safe Org Exports
  band already covers this use case.

---

## Research Task 5: Required user prompts

### Decision

Two prompts, both wrapped in `safe_input()`:

1. **`org_id`** -- default value pre-filled from `MIST_ORG_ID` in `.env`
   (loaded via `python-dotenv` at process start). Prompt:
   `"Org ID [<default>]: "`. Empty input keeps the default; any other
   input is validated against the Mist UUID regex before proceeding.
   Context string: `"org_nac_rule:org_id"`.
2. **`nacrule_id`** -- no default. Prompt: `"NAC Rule ID: "`. The user is
   expected to obtain this from a prior run of `listOrgNacRules` (menu 43)
   or from the Mist Cloud UI. Validated against the Mist UUID regex before
   proceeding. Context string: `"org_nac_rule:nacrule_id"`.

No secrets are prompted at runtime -- the API token comes from `.env` only
(loaded once by the existing `mistapi.APISession` setup).

### Rationale

The Mist API path template requires both UUIDs, so both must reach the
method. `MIST_ORG_ID` is the standard MistHelper `.env` variable for the
default org (every other menu method uses the same default), so
pre-filling it saves keystrokes and matches user expectation. NAC rule
UUIDs are not stable per user and cannot come from `.env`; they must be
prompted every run. Wrapping both in `safe_input()` with distinct
`context=` strings ensures graceful EOF handling in SSH and container
sessions per Principle III.

### Alternatives Considered

- **Accept a comma-separated list of `nacrule_id` values to fetch in one
  run**: Rejected for this spec (out of scope per FR-001 which specifies
  the single-object endpoint). A future batch-mode spec can layer this
  on top by calling the single-object method in a loop.
- **Read `nacrule_id` from a file**: Rejected. Adds a file-path prompt and
  a code path for parsing a list, both of which are premature for a
  single-object read.
- **Silently default `nacrule_id` from the last row of
  `data/org_nacrules.csv`**: Rejected. Non-obvious behavior; violates the
  "junior NOC engineer clarity" audience rule.
