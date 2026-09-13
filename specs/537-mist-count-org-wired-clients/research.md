# Phase 0 Research: countOrgWiredClients

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/orgs/{org_id}/wired_clients/count`
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_wired_clients_count.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call
`mistapi.api.v1.orgs.wired_clients.count.countOrgWiredClients(mist_session, org_id,
distinct=None, start=None, end=None, duration="1d", limit=100)`.

**Rationale**: The enriched per-endpoint doc
(`documentation/api/orgs/GET_orgs_org_id_wired_clients_count.md`) records:

- HTTP: `GET /api/v1/orgs/{org_id}/wired_clients/count`
- Path params: `org_id` (string, required)
- Query params: `distinct` (string, optional), `start` (string -- epoch seconds or
  relative `-1d` / `-1w`, optional), `end` (string -- epoch seconds or relative
  `-2h` / `now`, optional), `duration` (string, default `1d`), `limit` (integer,
  default 100)
- Request body: none
- 200 response: object with required keys `distinct`, `end`, `limit`, `results`,
  `start`, `total`. `results` is a unique-items array of `count_result` objects;
  each result requires a `count` integer and accepts additional string properties
  (one per distinct value).
- Errors: 400 Bad Syntax, 401 Unauthorized, 403 Permission Denied, 404 Not Found,
  429 Too Many Requests.
- SDK module: `mistapi.api.v1.orgs.clients_-_wired.countOrgWiredClients()` (the
  doc's hyphen-in-segment naming is a doc artifact; on disk the mistapi package
  resolves under `mistapi.api.v1.orgs.wired_clients.count` -- the import path is
  verified at task generation by inspecting the installed mistapi 0.59+ wheel).

The SDK returns a `mistapi.APIResponse` whose `.data` attribute is the parsed
JSON envelope. The method consumes `.data` directly; no pagination loop is
required for a single page because `limit` already bounds the result array.

**Alternatives Considered**:

- Calling the raw REST endpoint via `requests` -- rejected; Constitution
  mandates `mistapi` as the sole interface to the Mist Cloud.
- Auto-paginating across `results` using a `page` parameter -- rejected; the
  endpoint is documented as a single-shot count and `limit` is the only
  pagination knob exposed by the doc's response schema.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` keyed on
`("org_id", "distinct", "distinct_value", "start", "end")`.

**Rationale**: The response is an aggregate over a time window. A single API
call expands into 1 + N rows: one envelope row (the summary metadata) and N
result rows (one per distinct value). To make repeated runs upsert cleanly
across overlapping windows we need a key that:

1. Includes `org_id` because the same distinct/time can repeat across orgs.
2. Includes `distinct` (the grouping field, e.g. `mac`, `vlan`, `port_id`)
   because the same time window can be re-queried with different groupings.
3. Includes `distinct_value` (the actual attribute value flattened from
   `results[i].<distinct>`) so each result row is unique within the group.
4. Includes `start` and `end` epoch integers so historical snapshots are
   preserved instead of overwritten when the user re-runs over a different
   window.

The envelope row stores `distinct_value = "__summary__"` (a sentinel) so it
shares the same composite key shape and never collides with a real distinct
value (Mist distinct values are MAC addresses, port IDs, VLANs, etc., never the
literal string `__summary__`).

**Alternatives Considered**:

- `natural_pk` on a single API-provided UUID -- rejected; the endpoint returns
  no UUIDs.
- `auto_increment_with_unique` on a `misthelper_internal_id` surrogate --
  rejected; that strategy is reserved for endpoints with no stable natural
  keys at all. Here the (org_id, distinct, value, start, end) tuple is fully
  stable across runs and gives free deduplication without a surrogate column.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV filename: `data/org_wired_clients_count_<org_id>_<distinct>_<duration>.csv`
- SQLite table: `org_wired_clients_count`
- ArangoDB collection (when polyglot backend is active): `org_wired_clients_count`
  with graph edges to the existing `orgs` vertex collection per spec 188.

**Rationale**: The filename matches the existing pattern used by adjacent
wired-client menu items (`searchOrgWiredClients` already writes
`org_wired_clients_search_<org_id>.csv` per the codebase convention). Including
`<distinct>` and `<duration>` in the filename keeps multiple snapshots from
overwriting each other when the user explores different groupings. The SQLite
table name drops the per-run suffix because `DataExporter` resolves CSV file
names per write but maps all writes for the same `api_function_name` into a
single SQLite table, where the composite PK distinguishes runs.

`DataExporter.write_with_format_selection(data, filename,
api_function_name="countOrgWiredClients")` handles the backend dispatch; the
`api_function_name` is the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`,
so registering that exact string is mandatory.

**Alternatives Considered**:

- One row per response (the full envelope as a single JSON cell) -- rejected;
  CSV consumers would have to re-parse and SQLite would lose its ability to
  aggregate across runs.
- Separate tables for summary vs results -- rejected; the sentinel
  `distinct_value="__summary__"` pattern keeps the schema flat, matches the
  reference plan 500's pattern for envelope-plus-detail responses, and avoids
  a second `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry.

## Research Task 4: Menu Category Placement and Next Available Number

**Decision**: Place at menu number **88** in the Stats cluster (operations
80-91). Subject to a live-registry collision check at `/speckit.tasks` time;
if 88 is taken by an in-flight feature branch, fall back to the next free
integer in the 80-91 range.

**Rationale**: Per the agent instructions, the menu ranges are documented as:

- 1-59: Safe Org Exports
- 60-96: Interactive Safe
- 80-91: Stats sub-cluster within Interactive Safe
- 90-100: Resource Intensive / partly destructive (skipped by `--test`)
- 154-194: Destructive

`countOrgWiredClients` is a read-only stats / distinct-count endpoint with no
side effects, so the Stats sub-cluster (80-91) is the correct home. 88 sits
two below the resource-intensive boundary at 90 and is consistent with the
pattern of other count / distinct endpoints sitting in the high-80s. The
reference plan 500 picked 95 (org-license cluster); this spec picks 88 to
avoid that cluster and to live with its semantic peers.

**Alternatives Considered**:

- Placing it in the safe-org-exports clients cluster (27-30) -- rejected;
  that cluster is full and is reserved for direct client list exports rather
  than aggregate count endpoints.
- Placing it adjacent to `searchOrgWiredClients` -- rejected only because the
  Stats cluster is the published home for distinct-count operations; if at
  task time it turns out `searchOrgWiredClients` lives at an adjacent
  unallocated integer, that slot is preferred and 88 is dropped.

## Research Task 5: Required User Prompts

**Decision**: The new method prompts for, in order:

1. `org_id` -- defaults to `MIST_ORG_ID` from `.env` (echoed back as
   `[default: <uuid>]`); accepted as-is on empty input. Validated against the
   Mist UUID shape before the API call. Collected via
   `safe_input("Org ID [...]: ", context="wired_clients_count:org_id")`.
2. `distinct` -- free-text field name to group by (e.g. `mac`, `port_id`,
   `vlan`, `device_mac`, `ssid`). Empty input means "do not pass `distinct`"
   and lets the Mist API apply its server-side default. Collected via
   `safe_input("Distinct attribute (blank for API default): ",
   context="wired_clients_count:distinct")`.
3. `duration` -- defaults to `1d`. Accepts relative strings (`1h`, `7d`,
   `2w`) or empty for default. Collected via
   `safe_input("Duration [1d]: ", context="wired_clients_count:duration")`.
   If the user prefers absolute `start`/`end`, they enter them in this
   prompt's follow-up via a comma-separated form `start,end` documented in
   the prompt help text. The implementation parses the comma form; the
   simpler `duration`-only path is the documented default.
4. `limit` -- defaults to `100`. Collected via
   `safe_input("Limit [100]: ", context="wired_clients_count:limit")` and
   coerced to `int` with a try/except that logs a warning and reverts to 100
   on parse failure.

`.env` supplies `MIST_HOST`, `MIST_API_TOKEN`, and `MIST_ORG_ID` (the last is
used only as a prompt default). No prompt asks the user for credentials.

**Rationale**: This prompt set covers all five query parameters from the doc
(`distinct`, `start`, `end`, `duration`, `limit`) while keeping the keystroke
count low in the common case (press Enter four times to accept defaults).
Defaulting `org_id` from `.env` matches the pattern in every other
org-scoped menu item in MistHelper. Defaulting `duration` to `1d` matches the
Mist API documented default so the result is identical to a no-parameter
call. The four prompts give the user full control of the time window without
forcing them to learn the absolute-epoch form.

**Alternatives Considered**:

- Five separate prompts (one for each query param) -- rejected; the
  `start`/`end`/`duration` triad is mutually exclusive in normal usage, and
  collapsing them into a single duration prompt with an optional
  comma-separated escape hatch keeps the UX tight.
- Hard-coding `distinct=mac` -- rejected; the value of the endpoint is the
  ability to pivot on any distinct field. Hard-coding would force a code
  edit for every new pivot.
