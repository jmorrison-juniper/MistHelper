# Phase 0 Research: getMspOrgGroup

**Feature**: 585-mist-get-msp-org-group
**Date**: 2026-06-29
**Source endpoint doc**: `documentation/api/msps/GET_msps_msp_id_orggroups_orggroup_id.md`

This document captures the five research decisions required to ground the implementation
plan for the new MistHelper menu item that wraps Mist API operation `getMspOrgGroup`.
Each task is recorded in **Decision / Rationale / Alternatives Considered** form.

---

## Research Task 1: SDK Function Signature & Behavior

### Decision

The implementation calls the `mistapi` SDK at:

```python
mistapi.api.v1.msps.org_groups.getMspOrgGroup(apisession, msp_id, orggroup_id)
```

- Module path: `mistapi.api.v1.msps.org_groups`
- Function name: `getMspOrgGroup`
- Positional arguments: `apisession` (an authenticated `mistapi.APISession`), `msp_id`
  (string UUID), `orggroup_id` (string UUID)
- Keyword arguments: none (the endpoint has no query parameters)
- Return type: `mistapi.APIResponse` -- the JSON object is in `response.data`
- HTTP behavior: single GET request, not paginated, no rate-limit-specific tuning
- Response shape: a single JSON object with the fields `id`, `name`, `msp_id`,
  `org_ids[]`, `created_time`, `modified_time` (all per the OpenAPI schema captured in
  `documentation/api/msps/GET_msps_msp_id_orggroups_orggroup_id.md`)

### Rationale

The enriched per-endpoint doc explicitly lists the SDK call as
`mistapi.api.v1.msps.org_groups.getMspOrgGroup()`. The path tokens map cleanly to the
SDK's module hierarchy convention (`/api/v1/` -> `api.v1.`, `msps` -> `msps`,
`orggroups` -> `org_groups` -- mistapi snake-cases compound resource segments). The
endpoint takes only path parameters, so the SDK signature mirrors them as positional
strings. Because there is no `?detail=` or `?page=` query parameter on this endpoint,
no kwargs handling is required and the call site stays under the 5-Item Rule limits.

### Alternatives Considered

- **Direct `requests.get()` against the URL template** -- Rejected. The constitution
  mandates the `mistapi` SDK as the sole interface to Mist Cloud; bypassing it would
  also lose adaptive delay and retry support.
- **List endpoint `listMspOrgGroups` followed by client-side filter** -- Rejected. The
  endpoint to catalog is specifically `getMspOrgGroup` (single-record lookup); using the
  list endpoint would over-fetch and would not satisfy the spec's FR-001.

---

## Research Task 2: Primary Key Strategy

### Decision

Use **`natural_pk`** for the summary record:

```python
'getMspOrgGroup': {
    'type': 'natural_pk',
    'primary_key': ['id'],
    'indexes': ['msp_id', 'name'],
    'related_tables': {
        'msp_org_group_members': {
            'type': 'composite_pk',
            'primary_key': ['orggroup_id', 'org_id'],
            'indexes': ['orggroup_id'],
        }
    },
}
```

The response object carries a stable UUID `id` field. The member-org join table
(`msp_org_group_members`) uses **`composite_pk`** on `(orggroup_id, org_id)` because the
join row's identity is exactly that pair.

### Rationale

- The `id` field is documented as the "Unique ID of the object instance in the Mist
  Organization" and is marked `readOnly` with a UUID content encoding -- a textbook
  natural primary key.
- Indexes on `msp_id` and `name` accelerate the common "all org groups for an MSP" and
  "lookup by display name" queries that downstream reporting will ask.
- The `org_ids` array is normalized into a child table to keep the schema 1NF and to
  enable graph edges in the ArangoDB backend (each `(orggroup, org)` becomes an edge).
- Composite PK on the child table guarantees idempotent re-runs: re-importing the same
  org group does not double-write membership rows.

### Alternatives Considered

- **`composite_pk` on `(msp_id, id)`** -- Rejected. The `id` field is already globally
  unique across the Mist tenant; adding `msp_id` to the PK provides no uniqueness
  benefit and complicates upsert SQL.
- **`auto_increment_with_unique`** -- Rejected. That strategy exists for endpoints
  without stable identifiers (aggregates, summaries); this endpoint clearly has one.
- **Denormalize `org_ids` as a comma-joined string in the summary row** -- Rejected.
  Violates 1NF, breaks the ArangoDB graph backend, and prevents JOIN-based reporting.

---

## Research Task 3: Output Filename and SQLite Table

### Decision

- **CSV filenames**: `data/msp_org_group_<msp_id>_<orggroup_id>.csv` for the summary
  row, and `data/msp_org_group_members_<orggroup_id>.csv` for the member-edge rows
- **SQLite tables**:
  - `msp_org_groups` (one row per org group)
  - `msp_org_group_members` (one row per `(orggroup_id, org_id)` membership edge)
- **ArangoDB collections** (when active): `msp_org_groups` (document) and
  `msp_org_group_members` (edge collection between `msp_org_groups` and `orgs`)
- **Redis keys**: `msp_org_group:<orggroup_id>` with TTL governed by existing cache
  policy

### Rationale

- The two-letter prefix `msp_` aligns with how MistHelper already names tables for
  MSP-scoped data (existing `msp_*` prefixed tables in `MistHelper.py`).
- Including the two IDs in the CSV filename prevents single-record exports from
  clobbering one another when an operator runs the menu several times against different
  org groups.
- Splitting members into a sibling file/table preserves 1NF and matches the PK
  strategy above.
- The SQLite table names are plural, snake_case, and consistent with the codebase's
  existing `flatten_dict()` plus `DataExporter` naming conventions.

### Alternatives Considered

- **Single file `data/msp_org_group.csv` with `org_ids` as a JSON string column** --
  Rejected. Breaks SQLite filtering and joining; also breaks the polyglot ArangoDB graph
  edges.
- **Per-org-group SQLite database file** -- Rejected. MistHelper centralizes all data
  in `data/mist_data.db`; per-resource databases would require new connection plumbing
  that the constitution's Class-Based Architecture rule discourages.

---

## Research Task 4: Menu Category Placement and Next Available Number

### Decision

The new menu item is proposed at **menu number 96**, labeled `Get MSP Org Group
Details` in the menu table. Category: **Interactive Safe** (ranges 60-96).

### Rationale

- The endpoint requires two interactive inputs (`msp_id`, `orggroup_id`) -- it is not a
  pure org-wide bulk export, so the Safe Org Exports cluster (1-59) is the wrong fit.
- The endpoint is read-only and lightweight (single GET, ~1 KB response), so it does
  not belong in the Resource Intensive cluster (97-101, 153).
- It is not destructive, so the 154-194 range is wrong.
- The Interactive Safe cluster (60-96) already houses other single-record viewers
  (operations 92-96 are "Viewers" per the menu category table in
  `.github/copilot-instructions.md`), making 96 the natural placement.
- 96 is the last slot in the Interactive Safe cluster; if a parallel feature branch
  claims 96 first, `/speckit.tasks` re-checks and uses the next free integer in the
  same cluster (e.g., backfilling a freed slot in 60-95) or escalates to the operator
  for a number assignment.

### Alternatives Considered

- **Place inside Safe Org Exports (1-59)** -- Rejected. That cluster is reserved for
  endpoints that need no interactive input beyond `org_id` (loaded from `.env`).
- **Place inside Resource Intensive (97-101)** -- Rejected. The endpoint is not
  resource-intensive by any measure.
- **Create a new MSP-only menu cluster** -- Rejected at this single-endpoint scope.
  When MSP endpoints reach a critical mass (>=5 menu items), a dedicated cluster will be
  proposed in a separate spec; doing it for one endpoint would violate YAGNI and add
  menu churn.

---

## Research Task 5: Required User Prompts

### Decision

The menu method prompts for exactly two inputs, both via `safe_input()`:

| Prompt | Source | Context String |
|--------|--------|----------------|
| `msp_id` | Interactive (with `.env` fallback `MSP_ID`) | `"msp_org_group:msp_id"` |
| `orggroup_id` | Interactive (with `.env` fallback `MSP_ORG_GROUP_ID`) | `"msp_org_group:orggroup_id"` |

The existing `MIST_HOST` and `MIST_API_TOKEN` are loaded from `.env` by the existing
`mistapi.APISession` bootstrap -- no new env vars beyond `MSP_ID` and
`MSP_ORG_GROUP_ID` (both optional; only required when running `--test` non-interactively
or when the operator prefers a pre-canned ID).

### Rationale

- The endpoint's OpenAPI definition lists `msp_id` and `orggroup_id` as the only
  required path parameters; no query parameters exist.
- `safe_input()` is the project standard for SSH / container EOF safety (Constitution
  Principle III); both prompts use it without exception.
- Allowing `.env` overrides preserves the `python MistHelper.py --test` non-interactive
  contract while keeping the default UX interactive.
- Each prompt is validated against the Mist UUID shape (`r'^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$'`)
  before the SDK call; failure logs a warning and returns early without raising.

### Alternatives Considered

- **Auto-list MSPs and let the user pick by index** -- Rejected at this scope. That
  flow requires also wiring `listMsps`, which is a different endpoint and a separate
  spec. The current spec explicitly catalogs `getMspOrgGroup` only.
- **Read `msp_id` from `MIST_ORG_ID` (the existing org var)** -- Rejected. `MIST_ORG_ID`
  is an Organization UUID; this endpoint needs an MSP UUID, a different entity type.
  Conflating them would be a correctness bug.
- **Hardcode test IDs in `MistHelper.py`** -- Rejected. Violates the secrets-in-`.env`
  rule and breaks the multi-tenant principle.

---

## Summary

All five research tasks resolved without `NEEDS CLARIFICATION` markers. The decisions
above feed directly into the Phase 1 artifacts:

- Task 1 -> `contracts/get_msp_org_group.md` (HTTP + SDK call)
- Task 2 -> `data-model.md` (PK strategy, indexes)
- Task 3 -> `data-model.md` (DDL), `quickstart.md` (expected files)
- Task 4 -> `plan.md` (Structure Decision), `quickstart.md` (invocation)
- Task 5 -> `quickstart.md` (env vars and prompts), `plan.md` (Principle III check)
