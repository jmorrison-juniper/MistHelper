# Phase 0 Research: countOrgWirelessClientsSessions

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-29

Source of truth for the SDK and HTTP details:
`documentation/api/orgs/GET_orgs_org_id_clients_sessions_count.md`.

## Research Task 1: SDK Function Signature & Behaviour

**Decision**: Invoke the endpoint via
`mistapi.api.v1.orgs.clients.sessions.count.countOrgWirelessClientsSessions(
apisession, org_id, distinct=None, ap=None, band=None, client_family=None,
client_manufacture=None, client_model=None, client_os=None, ssid=None,
wlan_id=None, start=None, end=None, duration="1d", limit=100)`. The function
returns a `mistapi.APIResponse` object whose `.data` attribute is the JSON body
documented in section "Response 200" of the enriched doc -- an object with
required keys `distinct`, `end`, `limit`, `results`, `start`, `total`. The
`results` field is an array of `count_result` objects: each object contains
the required field `count` (integer) plus `additionalProperties` of type
string (the value of the chosen `distinct` attribute for that bucket, e.g.
`{"count": 42, "ssid": "Corp-Guest"}`).

**Rationale**: The enriched doc explicitly lists path param `org_id` as
required and 13 query params as optional, all string-typed except `limit`
(integer, default 100). `duration` defaults to `1d`. The `mistapi` SDK
follows the standard `apisession + positional path params + keyword query
params` pattern shared by every other `count*` operation already wired in the
codebase (e.g. `countOrgWirelessClients`, `countOrgWiredClients`,
`countOrgWirelessClientEvents` at MistHelper.py lines 4561-4581). Reusing
that calling convention guarantees the new method composes cleanly with
existing rate-limit, retry, and logging infrastructure.

**Alternatives Considered**:

- Raw `requests.get()` to
  `/api/v1/orgs/{org_id}/clients/sessions/count` -- rejected; bypasses the
  `mistapi.APISession` token + adaptive throttle, violates Constitution rule
  "mistapi is the sole permitted Mist API interface".
- Using `searchOrgWirelessClientSessions` and counting client-side -- rejected;
  forces a paginated pull of full session records when the user only asked
  for counts. Server-side aggregation via the `/count` endpoint is orders of
  magnitude cheaper.

## Research Task 2: Primary Key Strategy

**Decision**: `auto_increment_with_unique`. The entry already exists in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` at MistHelper.py line ~4582 and is reused
verbatim:

```python
"countOrgWirelessClientsSessions": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["org_id", "distinct"],
    "unique_constraints": [],
    "description": "Wireless client session count aggregates",
},
```

**Rationale**: The response is an aggregation, not a stable entity. It has no
API-issued UUID, and the natural keys (`distinct` attribute name + bucket
value) repeat across time windows and across orgs. Treating each invocation
as a new row keyed by an auto-increment `misthelper_internal_id` matches the
established pattern for every other sibling `count*` operation in the
catalog (`countOrgWirelessClients`, `countOrgWiredClients`,
`countOrgWirelessClientEvents`). Indexing on `org_id` and `distinct`
supports the most common analytical lookups without forcing uniqueness.

**Alternatives Considered**:

- Composite PK `(org_id, distinct, start, end, bucket_value)` -- rejected;
  three of those columns are nullable in the response, breaking SQLite
  uniqueness semantics and forcing brittle string coercion for nulls. Also
  defeats the user's likely "snapshot per run" mental model.
- Natural PK on `id` -- rejected; the response has no `id` field.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV / primary export filename:
  `data/count_org_wireless_clients_sessions_results.csv` (one row per bucket
  in the `results` array).
- Companion summary filename:
  `data/count_org_wireless_clients_sessions_summary.csv` (one row per
  invocation capturing the top-level `distinct`, `start`, `end`, `limit`,
  `total`).
- SQLite tables (created automatically by `DataExporter` on first write):
  `count_org_wireless_clients_sessions_results` and
  `count_org_wireless_clients_sessions_summary`, both within
  `data/mist_data.db`.

**Rationale**: The naming pattern mirrors the existing
`count_org_wireless_clients_*` cluster created by sibling exporters
(`countOrgWirelessClients`, `countOrgWiredClients`). Splitting the
single nested JSON object into a flat summary row plus a per-bucket detail
row is the same shape used in the reference plan (spec 500). It keeps each
table truly flat (no JSON-serialised columns), which is the only shape that
upserts cleanly through `DataExporter.write_with_format_selection()` across
all three backends.

**Alternatives Considered**:

- Single CSV with `summary_*` columns repeated on every bucket row -- rejected;
  wastes storage and violates first normal form, making downstream joins
  awkward.
- JSON-serialised `results` column on the summary row -- rejected; SQLite
  loses index-ability and CSV consumers cannot parse it without ad-hoc
  scripts.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Menu number **195**, category "Safe Org Exports - Clients
(wireless)". The new entry is registered immediately above the existing
destructive block (operations 154-194) so the entire safe read-only range
remains contiguous and easy to grep.

**Rationale**: Per the project menu map (copilot-instructions.md), the
current range is 1-194 with 27-30 covering client exports and 154-194
covering destructive operations. There is no free slot inside the 27-30
client cluster, so the next monotonic integer above the existing top -- 195
-- is the cleanest placement. The README operation count is bumped from
194 to 195 in the same PR. If a parallel SpecKit branch lands first and
also claims 195, the implementer selects the next free integer
(196, 197, ...) at task generation time.

**Alternatives Considered**:

- Insert at 31 (next to the existing wireless client menu items) -- rejected;
  forces a renumbering of every operation from 31 through 194, which would
  invalidate user documentation, automation scripts, and the test sweep skip
  list (14, 18, 63-65, 90-100).
- Skip a number to leave room for future siblings -- rejected; monotonic
  numbering is the documented convention.

## Research Task 5: Required User Prompts (Inputs vs .env)

**Decision**: Three prompts via `safe_input()`, all with sensible defaults
pulled from `.env` where applicable:

1. **org_id** -- `safe_input("Org ID [default: %s]: " % env_org_id,
   context="count_wireless_sessions:org_id")`. Default to
   `os.getenv("MIST_ORG_ID")` if set. UUID-validated before the API call.
2. **distinct** -- `safe_input("Distinct attribute (ssid|ap|band|client_family|
   client_manufacture|client_model|client_os|wlan_id) [ssid]: ",
   context="count_wireless_sessions:distinct")`. Default `ssid`. Validated
   against the documented enum; on invalid input the method logs a warning
   and falls back to the default.
3. **duration** -- `safe_input("Duration window (e.g. 1d, 7d, 2w) [1d]: ",
   context="count_wireless_sessions:duration")`. Default `1d`, matching the
   API default. `start` and `end` are deliberately not prompted in this
   release; `duration` covers the dominant operator workflow and avoids
   epoch-conversion errors at the prompt.

**Rationale**: Three prompts is the right number to keep the menu item
usable for junior NOC engineers (the project's stated audience) while still
exposing the two query parameters that materially change the output shape
(`distinct` controls the bucket key; `duration` controls the time window).
Other optional filters (`ap`, `band`, `ssid` as a filter rather than a
distinct field, `wlan_id`, etc.) are accepted in the future via a single
"additional filters as `key=value,key=value`" prompt if user demand
materialises; deferring them now keeps this method under the 5-Item Rule
ceiling.

**Alternatives Considered**:

- Prompt for every documented query parameter (13 prompts) -- rejected;
  violates the junior-NOC-engineer audience and the 5-Item Rule complexity
  budget.
- Take no prompts and rely entirely on `.env` -- rejected; loses the
  interactive analytical workflow the menu system exists to provide.
- Prompt for `start`/`end` epoch values -- rejected for v1; epoch entry is
  error-prone in interactive shells. `duration` is the documented
  API-default-friendly alternative.
