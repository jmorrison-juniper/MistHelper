# Phase 0 Research: countOrgSystemEvents

Source: `documentation/api/orgs/GET_orgs_org_id_events_system_count.md`
Spec: [spec.md](./spec.md)

## Research Task 1: SDK function signature & behavior

**Decision**: Call
`mistapi.api.v1.orgs.events.countOrgSystemEvents(mist_session, org_id, distinct=None, limit=100, start=None, end=None, duration="1d", page=1)`
exactly once per menu invocation. Pass the cached
`mistapi.APISession` instance held by MistHelper. The SDK returns a
`mistapi.APIResponse` whose `.data` is a dict shaped like the OpenAPI
200 response: `{distinct, end, limit, results: [{count, ...}], start,
total}`.

**Rationale**: The enriched per-endpoint doc lists the same five query
parameters (`distinct`, `limit`, `start`, `end`, `duration`) and a
single path parameter (`org_id`). The mistapi SDK convention for
`/api/v1/orgs/{org_id}/events/system/count` is the
`mistapi.api.v1.orgs.events` submodule with the `countOrgSystemEvents`
camelCase function -- consistent with other count endpoints already
wrapped by MistHelper (for example `countOrgDeviceEvents`,
`countOrgAlarms`). Pagination via `page` is supported by the API but
rarely needed because the response is an aggregation; we still pass
`page=1` explicitly so the call site is unambiguous.

**Alternatives Considered**:
1. Iterate pages with `mistapi.get_all(...)`. Rejected -- the count
   payload aggregates already; per-page iteration would create
   misleading duplicate rows.
2. Bypass the SDK and use `requests` directly. Rejected -- violates
   the project's hard dependency on the mistapi SDK for token handling,
   retry policy, and rate-limit telemetry.
3. Fold the call into `searchOrgSystemEvents` and compute the count
   client-side. Rejected -- doubles bandwidth and bypasses the
   purpose-built count endpoint.

## Research Task 2: Primary Key Strategy

**Decision**: `auto_increment_with_unique` with a UNIQUE constraint on
`(org_id, distinct, start_epoch, end_epoch)`.

```python
"countOrgSystemEvents": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_constraint": ["org_id", "distinct", "start_epoch", "end_epoch"],
    "indexes": ["org_id", "captured_at"],
}
```

**Rationale**: The 200 response is an aggregation document with no
server-assigned stable ID. The natural deduplication key is the tuple
(org, distinct-field, time-window) -- two runs with the same parameters
should upsert in place rather than producing duplicate count rows.
`auto_increment_with_unique` is the documented strategy in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for exactly this case (aggregated /
summary data without stable keys, per copilot-instructions.md). The
`INSERT OR REPLACE` semantics MistHelper applies on top of the unique
constraint give idempotent re-runs.

**Alternatives Considered**:
1. `natural_pk` on `(org_id, distinct)`. Rejected -- ignores the time
   window; two snapshots taken hours apart would collide and the older
   one would be silently lost.
2. `composite_pk` on `(org_id, distinct, start_epoch, end_epoch)`.
   Rejected -- composite_pk is reserved for time-series rows that
   genuinely vary by `timestamp`; the count aggregation is not a
   time-series row.
3. Pure `auto_increment` (no unique constraint). Rejected -- every
   re-run would create a fresh duplicate row, defeating the idempotency
   acceptance criterion in spec FR-005.

## Research Task 3: Output filename and SQLite table

**Decision**:
- CSV / file backend filename: `data/count_org_system_events.csv`
- SQLite table name: `count_org_system_events`
- ArangoDB collection name: `count_org_system_events` (snake_case to
  match adjacent collections)

**Rationale**: The existing `DataExporter` derives the filename from
the `api_function_name` argument by converting camelCase to snake_case;
`countOrgSystemEvents -> count_org_system_events`. This keeps the
filename stable across all three backends and mirrors the convention
already used by `count_org_device_events`, `count_org_alarms`, and
similar entries.

**Alternatives Considered**:
1. `system_events_count.csv`. Rejected -- inconsistent with adjacent
   `count_*` files; the leading verb groups all count exports together
   in directory listings, which junior NOC engineers rely on.
2. `org_system_events_count.csv`. Rejected -- the org_ prefix is
   redundant; every org-scoped export already drops the prefix.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place at menu number **195** under the existing **Safe
Org Exports** category, alongside spec 530's sibling counter endpoints
that are being catalogued in the same wave.

**Rationale**: Per `.github/copilot-instructions.md` the menu ranges
are: 1-59 Safe Org Exports (filled), 60-96 Interactive Safe (filled),
97-101 + 153 Resource Intensive, 102-123 WebSocket, 124-150
Interactive, 151-152 Continuous, 154-194 Destructive. The destructive
range ends at 194, so 195 is the next sequential number above the
existing catalogue and is the standard slot for new safe org exports.
The endpoint is a read-only GET with no user-confirmation requirement
and falls naturally under "org events" exports. If a later wave merges
that lowers 195, the menu registry assignment is the single line that
needs updating.

**Alternatives Considered**:
1. Insert into the 20-26 Org Events sub-range. Rejected -- those slots
   are already assigned to existing menu items and renumbering would
   break automation invoking `--menu N`.
2. Defer numbering until merge time. Rejected -- the PR conformance
   checklist requires a concrete menu number before review.
3. Reuse spec number 530 as the menu number. Rejected -- spec IDs and
   menu IDs are independent namespaces; conflating them would create
   menu 530 with no operations 196-529.

## Research Task 5: Required user prompts

**Decision**: Prompt the user for four optional refinements after
loading `org_id` from `.env`:

| Prompt | Source | Default | Notes |
|--------|--------|---------|-------|
| `org_id` | `.env` `MIST_ORG_ID` | required | Skipped if env value is present; otherwise `safe_input("Org ID: ", context="count_org_system_events")` |
| `distinct` | user | blank (None) | `safe_input("Distinct field (blank for none): ", context="count_org_system_events")` |
| `duration` | user | `1d` | `safe_input("Duration (e.g. 1d, 7d, 2w) [1d]: ", context="count_org_system_events")` |
| `start` / `end` | user | blank | Only prompted if user types `custom` at the duration prompt; otherwise duration wins |
| `limit` | user | `100` | `safe_input("Per-page limit [100]: ", context="count_org_system_events")` -- coerced to int with a guarded `try/except ValueError` |

**Rationale**:
- `.env` is the canonical source for credentials and the default org
  per `coding-standards.instructions.md` and FR-002. Prompting only
  when missing keeps repeat-runs fast and SSH/container-friendly.
- The Mist API treats `start`/`end` and `duration` as mutually
  exclusive; collapsing the prompt flow to "duration unless custom"
  prevents inconsistent input and keeps the function under the
  25-line / 5-block limit.
- Coercing `limit` defensively avoids passing a non-integer to the
  SDK, which would surface as a TypeError instead of a logged warning.

**Alternatives Considered**:
1. Prompt for every parameter unconditionally. Rejected -- adds three
   prompt cycles to every invocation and inflates the function past
   the 5-block limit.
2. Read all five parameters from `.env`. Rejected -- time-window
   parameters should be ad hoc; baking them into `.env` defeats the
   menu's flexibility.
3. Accept JSON config via stdin. Rejected -- inconsistent with the
   established menu UX; junior NOC engineers expect plain prompts.
