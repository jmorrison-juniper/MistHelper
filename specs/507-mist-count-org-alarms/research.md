# Phase 0 Research: countOrgAlarms

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_alarms_count.md`

## Research Task 1: SDK function signature & behavior

**Decision**: Call `mistapi.api.v1.orgs.alarms.count.countOrgAlarms(apisession,
org_id, distinct=None, start=None, end=None, duration="1d", limit=100)` exactly
once per menu invocation. The endpoint returns a single JSON envelope (not a
paginated list), so the standard `mistapi.get_all()` helper is **not** used --
a single SDK call is sufficient.

**Rationale**: The enriched per-endpoint doc
(`documentation/api/orgs/GET_orgs_org_id_alarms_count.md`) confirms:

- HTTP method/path: `GET /api/v1/orgs/{org_id}/alarms/count`.
- One required path parameter: `org_id` (string UUID).
- Five optional query parameters: `distinct`, `start`, `end`, `duration`
  (default `1d`), `limit` (integer, default 100).
- Response 200: single object with required keys `distinct`, `end`, `limit`,
  `results`, `start`, `total`. `results` is an array of `count_result` objects
  each with a required `count` integer plus arbitrary additional string
  properties keyed by the distinct attribute value.
- mistapi SDK module: `mistapi.api.v1.orgs.alarms.count`, function
  `countOrgAlarms`.
- Pagination clause in the doc mentions `limit`/`page`, but the response shape
  is a single envelope (count buckets, not raw alarm rows), so multi-page
  fetches are not required for a meaningful answer; the user-supplied `limit`
  caps the bucket count.

**Alternatives Considered**:

1. *Use `mistapi.get_all()` helper to auto-paginate*: rejected because the
   response is a single envelope, not a list. Auto-pagination would either
   merge envelopes incorrectly or no-op silently. The dedicated single call
   matches the endpoint's semantics exactly.
2. *Loop over multiple `distinct` values in one menu run*: rejected on the
   5-Item-Rule grounds (would add a nested loop and grow the method past the
   25-line limit). The user can re-run the menu item for each grouping field
   they need; the SQLite UPSERT keys handle the multi-grouping case cleanly.

## Research Task 2: Primary Key Strategy

**Decision**: Register a **composite_pk** strategy for `countOrgAlarms`. The
output is split across two SQLite tables:

- `org_alarms_count_summary` -- one row per (org_id, distinct, start, end,
  duration, limit) invocation envelope. Primary key
  `(org_id, distinct, start, end)`.
- `org_alarms_count_buckets` -- one row per bucket value in `results`.
  Primary key `(org_id, distinct, start, end, bucket_value)`.

**Rationale**: There is no API-supplied stable UUID on a count envelope or on
its bucket rows, so a `natural_pk` strategy is not applicable. An
`auto_increment_with_unique` strategy would silently insert a new row every
time a junior NOC engineer re-ran the menu against the same window, violating
the "no duplicate primary keys on re-run" acceptance scenario from spec.md.
A `composite_pk` keyed on the parameters that define the count window plus the
grouping attribute lets `INSERT OR REPLACE` upsert cleanly across reruns, which
is exactly the behavior the spec requires.

**Alternatives Considered**:

1. *natural_pk on `total`*: rejected -- `total` is not a unique identifier and
   would collide trivially across different orgs and windows.
2. *auto_increment_with_unique on `(org_id, distinct, start, end)`*: rejected
   -- functionally identical to composite_pk for this read-only endpoint but
   adds an artificial `misthelper_internal_id` column the user never queries,
   which contradicts the project rule "no artificial IDs when a natural key
   exists in the parameter set".
3. *Single flat table mixing envelope and buckets*: rejected -- forces the
   envelope-only columns (`limit`, `total`) to be repeated on every bucket
   row, wasting storage and making aggregate queries harder. The two-table
   split matches the JSON shape (envelope + array).

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV summary file: `data/org_alarms_count_summary_<YYYYMMDD_HHMMSS>.csv`.
- CSV buckets file: `data/org_alarms_count_buckets_<YYYYMMDD_HHMMSS>.csv`.
- SQLite tables: `org_alarms_count_summary` and `org_alarms_count_buckets`
  inside `data/mist_data.db`.
- ArangoDB collections (when the polyglot backend is active): same names as
  the SQLite tables, document IDs derived from the composite PK tuple.
- Redis cache keys: `mist:org:<org_id>:alarms:count:<distinct>:<start>:<end>`
  (existing prefix convention -- matches adjacent alarm/event exports).

**Rationale**: Names match the project's existing pluralized snake_case
convention (compare `org_devices`, `org_inventory`, `org_alarms_search`). The
suffix `_summary` / `_buckets` mirrors the existing two-table split used for
endpoints that return envelope-plus-array payloads (the reference
`getOrgLicenseAsyncClaimStatus` plan uses the same `_summary` / `_details`
split). The timestamp suffix on CSV files is what the existing `DataExporter`
already emits, so no behavior change is needed.

**Alternatives Considered**:

1. *Single CSV with a `row_type` column*: rejected -- mixes schemas in one
   file, breaks `pandas.read_csv` defaults, and fails the "rows upsert by
   primary key" acceptance scenario because envelope rows and bucket rows have
   different key columns.
2. *Use the API name `count_result` for the buckets table*: rejected -- the
   project convention is to name tables after the user-facing concept, not the
   internal JSON `title`. `org_alarms_count_buckets` is more discoverable in
   `sqlite_master` listings than `count_result`.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Propose **menu number 58** in the Safe Org Exports cluster
(operations 1-59). Final selection re-verified at task generation time -- if 58
collides with an in-flight feature branch, take the next free integer in the
same cluster.

**Rationale**: Per the project's menu category map (.github/copilot-
instructions.md "Menu System & Operations"):

- 1-59 = Safe Org Exports. This endpoint is read-only, org-scoped, and ships at
  P1 with no destructive guardrails -- a textbook safe-org-export.
- 8-14 = Inventory, 15-19 = Device stats, 20-26 = Events, 27-30 = Clients,
  31-36 = Gateways, 37-41 = Templates, 42-50 = Config/Admin, 51-55 = SLE,
  56-59 = Misc.
- The endpoint doc's MistHelper Notes section confirms `searchOrgAlarms`
  currently lives at Menu 1. The Misc sub-range 56-59 is the right home for
  `countOrgAlarms` because count operations are cross-cutting helpers rather
  than a primary export. 58 is the next free integer below the 59 boundary
  that does not collide with the existing 56 / 57 / 59 slots observed in the
  current `MistHelper.py`.

**Alternatives Considered**:

1. *Menu 2 (adjacent to searchOrgAlarms)*: rejected -- the 1-7 sub-range is
   the Sites cluster per the category map, and inserting a count operation
   there would push existing site exports down and renumber the whole menu.
   Renumbering would break user muscle memory and external automation.
2. *Menu 80-91 (org stats cluster)*: rejected -- 80-91 is "Stats" in the
   Interactive Safe range, which is reserved for stats endpoints, not count
   endpoints. Mixing categories would erode the menu map's predictability.
3. *Menu 153 (Resource Intensive)*: rejected -- the endpoint is a single
   lightweight GET; it does not belong in the resource-intensive cluster.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Prompt the user for four values; load one from `.env`.

| Value      | Source             | Prompt context string             | Default              |
|------------|--------------------|-----------------------------------|----------------------|
| `api_token`| `.env` (`MIST_API_TOKEN`) | -- (no prompt)             | -- (required)        |
| `mist_host`| `.env` (`MIST_HOST`)      | -- (no prompt)             | `api.mist.com`       |
| `org_id`   | `safe_input()`     | `"org_alarms_count:org_id"`       | -- (required)        |
| `distinct` | `safe_input()`     | `"org_alarms_count:distinct"`     | empty (no grouping)  |
| `duration` | `safe_input()`     | `"org_alarms_count:duration"`     | `"1d"` (doc default) |
| `limit`    | `safe_input()`     | `"org_alarms_count:limit"`        | `100` (doc default)  |

`start` and `end` are intentionally not collected interactively in the v1
implementation -- the `duration` shorthand (e.g. `1d`, `7d`, `1w`) covers the
common NOC-engineer workflow and matches the doc's documented default. A future
enhancement (separate spec) can add explicit epoch prompts if a use case
appears.

**Rationale**:

- `api_token` and `mist_host` come from `.env` per the constitution's Security
  & Secrets principle -- never prompted, never logged.
- `org_id` is the only required path parameter and must come from the user.
  Defaulting it to a `.env` value would mask multi-org installations.
- `distinct` is the entire reason the user picks the count menu over the
  existing search menu; prompting for it is the natural UX. Empty input is
  accepted because the endpoint tolerates a missing `distinct` and returns
  a single bucket equal to `total`.
- `duration` defaults to the doc-documented `1d` so the user can press Enter
  for the common case.
- `limit` defaults to the doc-documented `100`; values above the Mist-side
  cap will be silently truncated by the API (no client-side validation
  required beyond `int()` coercion).

**Alternatives Considered**:

1. *Auto-detect org_id from `.env`*: rejected -- breaks multi-org users and
   contradicts adjacent menu items that all prompt explicitly.
2. *Prompt for `start` and `end` epoch timestamps*: rejected for v1 -- adds
   two more prompts that the typical NOC user does not need (the `duration`
   shorthand covers the common windows). Documented as a possible v2 add-on
   in this research file.
3. *Hard-code `limit=100`*: rejected -- the user must be able to retrieve a
   smaller bucket set when sanity-checking, and the prompt with default
   imposes zero friction.
