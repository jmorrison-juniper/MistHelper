# Phase 0 Research: countMspsMarvisActions

**Feature**: 506-mist-count-msps-marvis-actions
**Date**: 2026-06-28
**Source doc**: `documentation/api/msps/GET_msps_msp_id_suggestion_count.md`

## Research Task 1: SDK function signature & behavior

### Decision

Invoke the endpoint through the `mistapi` SDK path
`mistapi.api.v1.msps.suggestion.count.countMspsMarvisActions(mist_session,
msp_id, distinct=None, limit=100)`. The SDK call returns a `mistapi.APIResponse`
whose `.data` attribute is the parsed JSON object:

```python
{
  "distinct": "status",         # echoes the requested distinct attribute
  "limit": 100,                 # echoes the effective limit
  "total": 3,                   # total distinct buckets
  "results": [                  # one row per distinct value
    {"count": 24, "status": "002e176a-..."},
    {"count": 12, "status": "2d3f176a-..."},
    {"count": 15, "status": "08b2176a-..."}
  ]
}
```

Each `results[]` row always contains an integer `count` plus one dynamic
attribute keyed by the `distinct` value chosen. The Mist API doc cites typical
distinct values such as `status`, `category`, `priority`, and `type`.

### Rationale

The OpenAPI path `/api/v1/msps/{msp_id}/suggestion/count` maps to the SDK
module `mistapi.api.v1.msps.suggestion.count` per the spec input. The enriched
doc lists the operationId as `countMspsMarvisActions`. The function signature
mirrors other Mist count endpoints (e.g. `countOrgClients`) which the
codebase already uses as templates.

### Alternatives Considered

- **Raw `requests.get(...)` call**: rejected. Constitution mandates that
  `mistapi` is the sole permitted interface to the Mist Cloud. Custom HTTP
  also loses the SDK's built-in retry/pagination semantics.
- **Use the also-documented alias `mistapi.api.v1.msps.marvis.countMspsMarvisActions()`**:
  rejected as the OpenAPI URL path is the authoritative one and the alias is
  a convenience re-export that may move; the path-aligned module is stable.

## Research Task 2: Primary Key Strategy

### Decision

Register the operation in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as
**`auto_increment_with_unique`** with a logical unique constraint of
`(msp_id, distinct_attribute, distinct_value, snapshot_timestamp)`:

```python
'countMspsMarvisActions': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique': ['msp_id', 'distinct_attribute', 'distinct_value', 'snapshot_timestamp'],
    'indexes': ['msp_id', 'distinct_attribute', 'snapshot_timestamp'],
}
```

A second sibling table `msp_marvis_actions_count_summary` carries the single
`{distinct, limit, total}` envelope and uses the same strategy keyed on
`(msp_id, distinct_attribute, snapshot_timestamp)`.

### Rationale

The Mist API returns *aggregated* counts, not stable per-row UUIDs. There is
no natural primary key inside any `results[]` row. The dynamic attribute name
(governed by the `distinct` query parameter) precludes a fixed natural-PK
schema. `auto_increment_with_unique` is the documented strategy for
aggregated/summary data, with the unique tuple preventing duplicate inserts
when the same query is re-run within the same minute.

### Alternatives Considered

- **`natural_pk` on the dynamic attribute value**: rejected. The attribute key
  changes with each `distinct=` value, so the table schema cannot pin a single
  natural column.
- **`composite_pk` on `(msp_id, distinct_attribute, distinct_value)`**: rejected
  because rerunning the same query at a later time would overwrite the prior
  snapshot, destroying historical trend data. Including
  `snapshot_timestamp` in a true composite PK is fragile across SQLite
  timestamp precision, so it is enforced as a uniqueness constraint instead.

## Research Task 3: Output filename and SQLite table

### Decision

- **CSV files** (written under `data/`):
  - `msp_marvis_actions_count_summary.csv` -- one row per invocation,
    columns: `msp_id, distinct_attribute, limit, total, snapshot_timestamp`.
  - `msp_marvis_actions_count_results.csv` -- one row per distinct bucket,
    columns: `msp_id, distinct_attribute, distinct_value, count,
    snapshot_timestamp`.
- **SQLite tables** (inside `data/mist_data.db`): identical names,
  `msp_marvis_actions_count_summary` and `msp_marvis_actions_count_results`.
- **ArangoDB collections** (when polyglot backend is active): same names; the
  results collection is linked to the summary collection by
  `(msp_id, distinct_attribute, snapshot_timestamp)`.

### Rationale

The endpoint returns a `{summary, results[]}` shape. Flattening into two
tables is the documented MistHelper pattern (see the reference plan's
`org_claim_status_summary` / `org_claim_status_details` pair). Snake_case
names match the existing convention. The `msp_marvis_` prefix groups this
table with any future MSP-scope Marvis exports.

### Alternatives Considered

- **Single denormalized table with NULLs for envelope fields on detail rows**:
  rejected. Mixing two record shapes in one table is brittle and makes the
  CSV unfriendly to spreadsheet consumers.
- **JSON blob column**: rejected. Spreadsheets and ArangoDB graph traversal
  both prefer atomic columns.

## Research Task 4: Menu category placement and next available menu number

### Decision

Place the new operation at menu number **96**, in the Interactive Safe
category (60-96 range per `agents.md` Menu Categories table). Label:
`MSP -- Marvis Actions Count (by distinct attribute)`.

### Rationale

- Interactive Safe (60-96) is the correct category: the endpoint is GET-only,
  requires user-supplied `msp_id`, and may prompt for optional `distinct` and
  `limit` values.
- 96 is the highest free slot in the Interactive Safe band, immediately
  before the Resource Intensive cluster at 97-101.
- The MSP/Marvis pair has no incumbent in this band, so the new entry will
  not crowd a related group.
- If menu 96 is consumed by an in-flight feature branch at task-generation
  time, the next free integer (95 if returned, then 89/88 working down inside
  the same band, never inside the destructive 154-194 range) is used.

### Alternatives Considered

- **Safe Org Exports (1-59)**: rejected. The endpoint is MSP-scoped, not
  org-scoped; placing it in the org cluster would mislead operators.
- **Resource Intensive (97-101)**: rejected. The endpoint returns one small
  document; no long-running behavior justifies that slot.
- **Destructive (154-194)**: rejected. The endpoint is strictly read-only.

## Research Task 5: Required user prompts

### Decision

The menu method prompts the user via `safe_input()` for three values, in
order:

1. **`msp_id`** (required) -- context
   `"msp_marvis_actions_count:msp_id"`. The prompt defaults to
   `os.getenv("MIST_MSP_ID")` if set so power users can press Enter to accept
   the `.env` default. Validation: must match the Mist UUID regex
   `^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`.
   On failure, the method logs a WARNING and returns 0.
2. **`distinct`** (optional) -- context
   `"msp_marvis_actions_count:distinct"`. Empty input leaves the parameter
   unset and lets the Mist API choose its default distinct attribute.
   Suggested non-binding hints printed in the prompt: `status`, `category`,
   `priority`, `type`.
3. **`limit`** (optional) -- context
   `"msp_marvis_actions_count:limit"`. Empty input falls back to the SDK
   default 100. A non-empty value is coerced via `int()` and clamped to
   `[1, 1000]`; parse failure logs a WARNING and uses 100.

The Mist API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) continue to be
loaded from `.env` by the existing `mistapi.APISession` and are never prompted
or printed.

### Rationale

`safe_input()` is the documented Constitution III pattern for SSH /
container EOF resilience. Surfacing both query parameters as prompts (rather
than burying them in code) gives NOC engineers the same flexibility they
have through the Mist UI without forcing them to know the API.

### Alternatives Considered

- **Hard-code `distinct="status"`**: rejected. The endpoint's value comes
  from letting operators slice by category or priority; hard-coding wastes
  the API's expressiveness.
- **Read both query params from `.env`**: rejected. They are per-invocation
  decisions, not deployment-wide secrets.
- **Skip validation and rely on the API to 400-back**: rejected. Pre-validating
  is cheaper, gives a clearer NOC-friendly error message, and respects the
  Safety-First principle.
