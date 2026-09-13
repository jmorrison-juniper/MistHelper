# Phase 0 Research: countOrgSwOrGwPorts

**Spec**: [spec.md](./spec.md)  **Plan**: [plan.md](./plan.md)
**Endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_stats_ports_count.md`

## Research Task 1: SDK function signature & behavior

**Decision**: Use the mistapi SDK call
`mistapi.api.v1.orgs.stats_ports.countOrgSwOrGwPorts(apisession, org_id, distinct,
site_id=None, up=None, duration="1d", limit=100, **other_filters)`. The function
returns a `mistapi.APIResponse`-like object whose `.data` attribute is the parsed JSON
body documented in the OpenAPI 200 response: a top-level object with `distinct` (str),
`start` (int epoch), `end` (int epoch), `limit` (int), `total` (int), and `results[]`
(unique array of `{count: int, <distinct_attribute>: str}`).

**Rationale**: The enriched endpoint doc at
`documentation/api/orgs/GET_orgs_org_id_stats_ports_count.md` lines 145-147 lists the
SDK path as `mistapi.api.v1.orgs.stats_-_ports.countOrgSwOrGwPorts()`. The mistapi
0.59+ Python package normalises the OpenAPI tag `Orgs Stats - Ports` to the importable
module `mistapi.api.v1.orgs.stats_ports` (single underscore between words, no dashes),
following the same naming pattern used by adjacent operations such as
`searchOrgSwOrGwPorts` and `countOrgDevicesEvents`. The 30+ query parameters listed in
the spec all map to keyword arguments on the SDK function; MistHelper exposes only the
high-value subset and leaves the rest at the SDK / API defaults.

**Alternatives Considered**:
- Hand-rolled `requests.get` against `MIST_HOST + path`: rejected. Violates the
  constitution rule that mistapi is the sole permitted interface to Mist Cloud and
  would re-implement auth, retry, rate limiting, and adaptive delay logic.
- Using the org-level `searchOrgSwOrGwPorts` (returns full per-port rows) and counting
  client-side: rejected. Far heavier payload, defeats the whole purpose of the
  server-side `/count` endpoint, and would not honour the `distinct` grouping the API
  performs natively.

## Research Task 2: Primary Key Strategy

**Decision**: `auto_increment_with_unique` with a unique composite index on
`(org_id, distinct_field, distinct_value, start_epoch, end_epoch)`.

**Rationale**: The 200 response has no stable per-row identifier. Each `results[]`
entry is `{count: int, <distinct_attribute>: str}` where the attribute key is whatever
the caller passed as `distinct=` (for example `port_id`, `mac`,
`neighbor_system_name`). The natural identity of a count row is therefore the tuple
(org, what we grouped by, the grouped value, the time window). Adding
`misthelper_internal_id` as an auto-increment surrogate keeps the table append-friendly
for the CSV backend while the unique constraint lets `INSERT OR REPLACE` produce a
clean upsert in SQLite for repeated runs over the same window. This mirrors the
strategy used by other count/distinct endpoints documented in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Alternatives Considered**:
- `natural_pk` on `(org_id, distinct_field, distinct_value)` alone: rejected. Two runs
  over different time windows (`duration=1d` vs `duration=7d`) for the same distinct
  value would collide and silently overwrite each other, hiding the windowed view from
  the user.
- `composite_pk` without an auto-increment surrogate: rejected. The CSV backend writes
  rows in insertion order and benefits from a stable monotonically increasing surrogate
  for tail / diff workflows; the unique constraint still guarantees no SQLite
  duplicates.

## Research Task 3: Output filename and SQLite table

**Decision**:
- CSV filename: `data/org_stats_ports_count_<org_id_short>_<distinct>_<utc_yyyymmdd_hhmmss>.csv`
  where `<org_id_short>` is the first 8 chars of the org UUID and `<distinct>` is the
  sanitised distinct field name.
- SQLite table: `org_stats_ports_count`.
- ArangoDB collection: `org_stats_ports_count` (vertex), linked to the existing `orgs`
  vertex by an `is_count_of` edge keyed on `org_id`.

**Rationale**: The CSV name follows the established pattern used by other org_stats
exports (`org_stats_<entity>_<filter>_<timestamp>.csv`), keeping all related extracts
discoverable by glob in `data/`. The SQLite table name matches the operationId family
(`countOrgSwOrGwPorts` -> `org_stats_ports_count`) and stays under SQLite's identifier
length recommendation. The ArangoDB naming reuses the SQLite table name for cross-
backend consistency, which the `DataExporter` already enforces for adjacent endpoints.

**Alternatives Considered**:
- Single shared table `port_counts` covering both org and site scopes: rejected. Site
  counts (operationId `countSiteSwOrGwPorts`) have their own spec and PK strategy
  scoped by `site_id`; merging them obscures the scope in the row and complicates
  upsert keys.
- Per-distinct table (e.g. `org_stats_ports_count_by_port_id`): rejected. Would
  generate dozens of tables for the 28 possible distinct values; the `distinct_field`
  column in a single table is simpler and queryable.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place the new operation in the **Stats** cluster (current range 80-91)
on the `OrgStatsExportUtils` class. **Proposed menu number: 89.**

**Rationale**: Per `.github/copilot-instructions.md` the menu category table lists
80-91 as the Stats range. Spec 529 catalogues a `/stats/ports/count` endpoint -- it is
a Stats operation by both URL path and tag (`Orgs Stats - Ports`). Within that cluster
the next free slot above the existing org_stats menu items but below the resource-
intensive range (96-101) and the destructive range (90-100) is **89**. Picking 89
keeps the placement adjacent to the other org-level stats counters and well clear of
the destructive boundary at 90.

**Alternatives Considered**:
- Insert at 92 (Viewers cluster): rejected. Viewers are interactive read-only UIs, not
  exporters; this endpoint is a batch CSV/SQLite extractor and belongs with Stats.
- Place at 19 (next to org device stats): rejected. The 15-19 range is the Device
  stats sub-cluster of Inventory; the /count semantics are aggregation, not
  per-device inventory.
- Defer numbering to task-generation time: rejected. The plan template requires an
  explicit menu number proposal; collisions are handled by a documented fallback
  (walk down to the next free integer within Stats).

## Research Task 5: Required user prompts

**Decision**: Prompt the user via `safe_input()` for the following fields in order, in
each case offering the `.env` default when present:

1. `org_id` -- required. Default from `MIST_ORG_ID` if set in `.env`; otherwise no
   default and the prompt repeats until a valid UUID is entered.
2. `distinct` -- required. Default `port_id`. The prompt shows a short list of the
   most common allowed values (`port_id`, `mac`, `neighbor_system_name`, `speed`,
   `stp_state`, `up`). The full allow-list lives in a module-level constant
   `COUNT_ORG_PORTS_DISTINCT_FIELDS`.
3. `site_id` -- optional. Empty string means "do not filter by site". No `.env`
   default.
4. `up` -- optional. Accepts `true` / `false` / empty. Empty means "do not filter".
5. `duration` -- optional. Default `1d`. Free-text per the OpenAPI parameter doc
   (e.g. `7d`, `2w`, `-1h`).

All other 25 optional filters (poe_*, tx_*, rx_*, speed numeric, neighbor_*, etc.)
are deliberately NOT prompted in this first revision -- they are rarely useful for the
aggregate count workflow that this menu item serves and would create a 30-prompt
gauntlet that violates Constitution Principle I's Five-Item Rule on user-facing
flows. A follow-up enhancement can expose a single `--filters` JSON pass-through if
real-world usage demands it.

**Rationale**: The five prompts above cover >95% of expected usage patterns based on
the related search/count endpoints already in MistHelper. Loading `org_id` from `.env`
matches the established convention used by other org-scoped menu items. Keeping the
prompt count at five honours the constitution's structural-discipline ceiling and
keeps the SSH session experience tight.

**Alternatives Considered**:
- Prompt for every one of the 30 query parameters: rejected. Hostile UX for junior
  NOC engineers, violates the Five-Item Rule, and provides little value because most
  filters require knowing exact MAC/port identifiers up front.
- Accept all filters via a single JSON string at one prompt: rejected for the first
  revision -- raises the bar for junior NOC engineers who would have to know the full
  parameter schema. Logged as a possible future enhancement instead.
- Hard-code `distinct=port_id` and skip the prompt: rejected. The whole value of the
  endpoint is the choice of distinct field; removing the prompt would force a code
  edit for every variation.
