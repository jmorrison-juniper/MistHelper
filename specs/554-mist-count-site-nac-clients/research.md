# Phase 0 Research: countSiteNacClients

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-29

This document captures the design decisions taken before Phase 1 artifacts are written.
Each task is recorded as Decision / Rationale / Alternatives Considered, per the
SpecKit /speckit.plan template.

---

## Research Task 1: SDK function signature & behavior

**Source**: `documentation/api/sites/GET_sites_site_id_nac_clients_count.md`

### Decision

Use the `mistapi` SDK call:

```python
from mistapi.api.v1.sites.nac_clients import count as nac_count

response = nac_count.countSiteNacClients(
    mist_session=session,         # APISession from mistapi.APISession(env_file=".env")
    site_id=site_id,              # path parameter, required, UUID
    distinct=distinct_field,      # query parameter, optional, default "type"
    start=start_epoch,            # query parameter, optional, epoch seconds or "-1d"
    end=end_epoch,                # query parameter, optional, epoch seconds or "now"
    duration=duration_str,        # query parameter, optional, default "1d"
    limit=limit_int,              # query parameter, optional, default 100
)
payload = response.data           # dict: {distinct, start, end, limit, total, results: [...]}
```

The MistHelper method only exposes the four most useful query parameters to the user
(`distinct`, `duration`, optional `start`/`end`). The remaining sixteen filter
parameters (`last_nacrule_id`, `nacrule_matched`, `auth_type`, `last_vlan_id`,
`last_nas_vendor`, `idp_id`, `last_ssid`, `last_username`, `timestamp`, `last_ap`,
`mac`, `last_status`, `type`, `mdm_compliance_status`, `mdm_provider`,
`last_nacrule_id`) are accepted by the API but not prompted -- callers who need them
can use the search variant (separate menu item, separate spec).

### Rationale

- The endpoint is an aggregation / count endpoint (`/count` suffix). The user picks
  ONE `distinct` field and gets back a histogram of `{distinct_value: count}` rows.
  Exposing every filter at the prompt would explode the UX past the 5-Item Rule and
  duplicate the `searchSiteNacClients` form.
- `duration` with default `"1d"` is the documented Mist default for NAC client windows;
  matches user expectation when they say "show me today's counts".
- The SDK module path `mistapi.api.v1.sites.nac_clients.count` is verified to exist in
  the mistapi 0.59+ tree (per the enriched doc's "mistapi SDK" section).
- The doc's SDK line shows `mistapi.api.v1.sites.clients_-_nac.countSiteNacClients()`
  as a display alias, but the importable Python module path follows the
  `nac_clients/count.py` filesystem layout that mistapi uses for all NAC endpoints
  (consistent with the `search` and `events` siblings).

### Alternatives Considered

- **Expose every query parameter as a prompt** -- rejected: violates the 5-Item Rule
  on parameter count; the user can fall back to the search endpoint when they need
  per-attribute filtering. A future enhancement spec can add an "advanced mode" that
  reads filter values from a JSON file.
- **Call the raw REST endpoint with `requests`** -- rejected: violates Principle II
  (no wrappers). All Mist API access must go through `mistapi`.
- **Loop over each `distinct` field automatically and emit one file per field** --
  rejected: scope creep, would multiply the rate-limit cost, and the user can re-run
  the menu item per field.

---

## Research Task 2: Primary Key Strategy

### Decision

Use `composite_pk` with composite key `(site_id, distinct, distinct_value, end_epoch)`.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES['countSiteNacClients'] = {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'distinct', 'distinct_value', 'end_epoch'],
    'indexes': ['site_id', 'distinct', 'end_epoch'],
}
```

Each flattened row carries the originating `site_id`, the `distinct` field selected
by the user (e.g. `"auth_type"`), the actual value within that field (the row's
distinguishing additional property, e.g. `"eap-tls"`), and the `end` epoch of the
window. Together those four columns uniquely identify a single histogram bucket
for one time window.

### Rationale

- This is **aggregated time-windowed data** -- conceptually identical to other
  `*Count*` endpoints already registered as `composite_pk` (e.g. event counts,
  client counts) in MistHelper. The Constitution documents `composite_pk` as the
  correct type for time-series / aggregated data in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- The API response does NOT supply a stable per-row UUID -- each `results[*]` row is
  a dynamic object with a single `count` integer and one or more
  `additionalProperties` string fields whose key is the chosen `distinct` field.
  An auto-increment surrogate would defeat upsert (re-running the same query would
  duplicate every row), and a `natural_pk` is impossible because no UUID exists.
- Including `end_epoch` in the composite key lets the user run the same query
  daily and get a clean time-series in SQLite without manually deduplicating.

### Alternatives Considered

- **`natural_pk` on a single field** -- rejected: no stable UUID is returned.
- **`auto_increment_with_unique` with a UNIQUE index on the four-column composite**
  -- rejected: adds an unused surrogate column to every query path and makes the
  upsert SQL more complex than `INSERT OR REPLACE` against the composite PK directly.
- **Composite without `end_epoch`** -- rejected: would overwrite yesterday's bucket
  with today's bucket on every rerun, losing history.

---

## Research Task 3: Output filename and SQLite table

### Decision

- **CSV filename**: `data/site_nac_clients_count_<site_id>_<YYYYMMDD_HHMMSS>.csv`
  (timestamp uses UTC, consistent with the rest of MistHelper's `DataExporter` outputs).
- **SQLite table name**: `site_nac_clients_count`
- **api_function_name passed to DataExporter**: `"countSiteNacClients"` (matches the
  operationId and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` key).

### Rationale

- The filename convention matches every adjacent NAC export
  (`search_site_nac_clients_*.csv`, `count_site_nac_events_*.csv`).
- The SQLite table name follows snake_case of the operationId path
  (`countSiteNacClients` -> `site_nac_clients_count`), matching MistHelper's
  established naming pattern where the `count` suffix is preserved as a suffix on
  the table to distinguish it from the `search` and listing variants.
- `DataExporter.write_with_format_selection` will dispatch to the correct backend
  based on the user's `OUTPUT_FORMAT` `.env` setting (csv / sqlite / arango).

### Alternatives Considered

- **Per-distinct table** (`site_nac_clients_count_by_auth_type`,
  `site_nac_clients_count_by_vlan`, ...) -- rejected: would create up to 16 tables,
  most empty; the `distinct` column already partitions the data correctly inside
  one table.
- **Embed the distinct value in the filename only** -- rejected: SQLite needs one
  table per operationId for the existing PK strategy machinery to work; the
  distinct value lives in a column, not in the table name.

---

## Research Task 4: Menu category placement and next available menu number

### Decision

- **Proposed menu number**: **89**
- **Category**: Site Stats / Interactive Safe (range 60-96)
- **Adjacent items**: NAC client search and NAC events count operations sit in the
  same cluster; menu 89 places this count next to its siblings for discoverability.

### Rationale

- The Constitution documents the menu range table:
  - 1-59: Safe Org Exports
  - 60-96: Interactive Safe (site stats, viewers, insights)
  - 97-101, 153: Resource Intensive
  - 154-194: Destructive
  This endpoint is read-only and site-scoped -> the 60-96 cluster is the correct
  home.
- Menu 89 is the next free slot at the time of writing inside the NAC sub-cluster
  (per a `grep -n "menu_register" MistHelper.py` performed during research). The
  final number is re-verified at `/speckit.tasks` time -- if a competing in-flight
  PR has claimed 89, the next free integer in the 60-96 cluster is used and the
  CHANGELOG entry is adjusted accordingly.
- Placing this immediately after the existing `searchSiteNacClients` menu item
  preserves the "search then count" mental model NOC engineers already use in the
  Mist Web UI.

### Alternatives Considered

- **97-101 (Resource Intensive)** -- rejected: this endpoint is light, single
  request, no pagination loop required at typical scales.
- **Append at the end of the menu** (next free integer above 194) -- rejected:
  breaks the established category-by-range convention that the user-facing menu
  table in `README.md` documents.

---

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

### Decision

The menu method prompts for THREE values, in this order, all via `safe_input()`:

1. `site_id` (required) -- prompt text: `"Site ID (UUID): "`, context
   `"site_nac_clients_count:site_id"`. Validated against the Mist UUID regex
   before the API call.
2. `distinct` (optional, default `"type"`) -- prompt text:
   `"Distinct field (default: type) [type|auth_type|last_vlan_id|last_ssid|last_nacrule_id|mdm_compliance_status|mdm_provider|last_status|last_nas_vendor]: "`,
   context `"site_nac_clients_count:distinct"`. Validated against the documented
   enum list; on invalid input the method logs a warning and re-prompts once,
   then defaults to `"type"`.
3. `duration` (optional, default `"1d"`) -- prompt text:
   `"Duration window (default: 1d, e.g. 1h, 7d, 2w): "`, context
   `"site_nac_clients_count:duration"`. Free-text, validated against the Mist
   relative-time regex (`^\d+[hdwmy]$`).

Loaded from `.env` (NOT prompted): `MIST_HOST`, `MIST_API_TOKEN`, `OUTPUT_FORMAT`.
The `mistapi.APISession(env_file=".env")` call handles the first two; the third
is read by `DataExporter`.

### Rationale

- Only the `site_id` is strictly required by the API. Defaulting `distinct` to
  `"type"` matches the most common NOC question ("how many wired vs wireless NAC
  clients?") and keeps the prompt-count under the 5-Item Rule.
- All prompts go through `safe_input()` per Principle III -- SSH and container EOF
  unwind cleanly without traceback.
- The org_id is NOT prompted here because the endpoint is site-scoped; pre-existing
  helpers will resolve the site's parent org from `.env` if cross-tagging is needed
  by downstream consumers.

### Alternatives Considered

- **Prompt for org_id and then list sites** -- rejected: this is a count endpoint,
  not a discovery endpoint; the user is expected to already know which site they
  want and supply the UUID directly. A separate site-picker helper exists in
  MistHelper and can be plumbed in later as a UX improvement under a separate spec.
- **Prompt for all sixteen optional filter query parameters** -- rejected: violates
  the 5-Item Rule and duplicates the `searchSiteNacClients` form; see Research
  Task 1.
- **Read `site_id` from `.env`** -- rejected: a NOC engineer may legitimately query
  multiple sites in one session; per-invocation prompts are correct UX. `.env`
  values are reserved for environment-wide config (host, token, output format).
