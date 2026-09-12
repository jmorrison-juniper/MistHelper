# Phase 0 Research: countOrgNacClients

This document grounds the implementation in concrete decisions before any code is
written. Each task uses the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature & behavior

**Decision**: Use `mistapi.api.v1.orgs.nac_clients.count.countOrgNacClients(apisession,
org_id, distinct=None, last_nacrule_id=None, nacrule_matched=None, auth_type=None,
last_vlan_id=None, last_nas_vendor=None, idp_id=None, last_ssid=None,
last_username=None, timestamp=None, site_id=None, last_ap=None, mac=None,
last_status=None, type=None, mdm_compliance_status=None, mdm_provider=None,
start=None, end=None, duration="1d", limit=100)`. The call returns a
`mistapi.APIResponse` object whose `.data` attribute is a JSON object with the keys
`distinct`, `start`, `end`, `limit`, `total`, and `results` (a list of objects each
carrying a required `count` integer plus dynamic string-valued attributes for the
grouped fields).

**Rationale**: Sourced directly from
`documentation/api/orgs/GET_orgs_org_id_nac_clients_count.md` (the enriched per-endpoint
doc): 21 query parameters, all optional except the path param `org_id`; default
`duration=1d`, default `limit=100`; response schema documents `results` as a unique
array of `count_result` objects with `additionalProperties: string`. The mistapi SDK
module path is documented in the spec.md header as
`mistapi.api.v1.orgs.nac_clients.count`. Use of the typed `APIResponse` (rather than
parsing raw HTTP) keeps the rate-limit + retry behavior consistent with adjacent menu
items in `MistHelper.py`.

**Alternatives Considered**:

- Direct HTTP via `requests` -- rejected: bypasses the `mistapi` SDK abstraction
  (Constitution Technology & Compatibility Constraints), loses the built-in pagination
  helpers and auth handling, and would duplicate the rate-limit code that already lives
  inside `mistapi.APISession`.
- Exposing every one of the 21 query parameters at the prompt -- rejected: violates
  the Five-Item Rule (Principle I) for prompt count and overwhelms the junior NOC
  engineer audience. The menu prompts only for `org_id`, `distinct`, and an optional
  `duration`; the remaining filters are reachable via a future advanced-prompt mode if
  demand emerges.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` -- the natural unique identity of a returned row is the
tuple `(distinct_field, distinct_value, query_timestamp_epoch)`. Each call returns a
*snapshot* of aggregate counts at the call's effective `start`/`end` window, so the
same `distinct=auth_type, value=eap-tls` row recurs across re-runs and MUST upsert by
window-aware key.

**Rationale**: The endpoint returns aggregated, ephemeral counts -- there is no
server-side stable UUID on each row. Treating the row as `auto_increment_with_unique`
would let identical re-queries duplicate rows in SQLite; treating it as `natural_pk`
on a non-existent ID would fail. The composite key `(distinct_field, distinct_value,
query_timestamp_epoch)` lets the same query window upsert cleanly while preserving
historical comparisons across windows. `distinct_field` is captured because the user
can re-run the menu against the same org with different `distinct` selections (e.g.
first `auth_type`, then `mdm_provider`) -- both result sets must coexist in the same
table.

**Alternatives Considered**:

- `auto_increment_with_unique` keyed on `(misthelper_internal_id)` with `UNIQUE
  (distinct_field, distinct_value)` -- rejected: prevents historical retention across
  time windows; the second run would clobber the first instead of recording a new
  snapshot.
- `natural_pk` on `(count,)` -- rejected: counts are not identities, they are values
  and collide constantly.
- Storing the full request URL as the PK -- rejected: opaque, fragile to SDK changes,
  and not human-debuggable in SQLite.

## Research Task 3: Output filename and SQLite table

**Decision**: CSV filename `org_nac_clients_count_{org_id}_{distinct}_{utc_ts}.csv`
(e.g. `org_nac_clients_count_a1b2c3d4_auth_type_20260629T1542Z.csv`) written under
`data/`. SQLite table name `org_nac_clients_count`. Both are produced by
`DataExporter.write_with_format_selection(rows, filename,
api_function_name="countOrgNacClients")`; the exporter routes to CSV, SQLite, or
ArangoDB+Redis based on the active backend in `.env`.

**Rationale**: The filename pattern matches the existing convention used by other
count / search endpoints in `MistHelper.py` (org scope first, then operation, then
discriminator, then UTC timestamp). Including `distinct` in the filename keeps
multiple distinct-axis snapshots from the same org from overwriting one another in
CSV mode. SQLite naturally upserts via the composite PK chosen in Task 2, so a single
table name (`org_nac_clients_count`) is sufficient regardless of how many distinct
axes the user runs. The `api_function_name="countOrgNacClients"` argument lets
`DataExporter` look up the primary-key strategy from
`ENDPOINT_PRIMARY_KEY_STRATEGIES` and emit `INSERT OR REPLACE` statements correctly.

**Alternatives Considered**:

- One SQLite table per `distinct` axis (e.g. `org_nac_clients_count_auth_type`) --
  rejected: explodes the schema, breaks the convention of one operation = one table,
  and complicates downstream Dash / web-UI queries.
- Reuse the existing `org_nac_clients` search table -- rejected: schema mismatch
  (search rows are individual clients, count rows are aggregates) and would corrupt
  search-side queries.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **58**, placed in the Misc Safe Org Exports cluster (56-59).
The full menu list is re-verified at task generation time; if 58 is taken by an
in-flight feature branch (specs 500-525 are being authored concurrently), the next
free integer in the same cluster (then 56-59 fallback to 88-91 in the Stats cluster)
is used.

**Rationale**: The constitution categorizes operations by destructive risk and
operational intent. `countOrgNacClients` is read-only, org-scoped, and produces
aggregate data -- the perfect fit for the Misc Safe Org Exports cluster (per the
"Menu Categories" table in `.github/copilot-instructions.md`). Slot 58 sits adjacent
to the existing NAC-related safe exports and keeps NAC operations geographically
clustered in the menu listing, which is friendlier to the junior NOC engineer audience
who navigates by section header.

**Alternatives Considered**:

- Place in the Insights cluster (73-79) -- rejected: those slots are reserved for SLE
  and AI-driven endpoints; aggregate counts are not insights.
- Place in the Resource Intensive cluster (97-101, 153) -- rejected: this endpoint
  returns a single aggregated payload and is not long-running; placing it there would
  exclude it from the default test sweep and obscure it from NOC users browsing the
  Safe Exports section.
- Append to the tail of the menu (next free integer above 194) -- rejected: breaks
  the topical clustering convention.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: The menu collects three prompts via `safe_input()`:

1. `org_id` -- from prompt, validated against the Mist UUID shape
   (`^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`). If the user
   has set `DEFAULT_ORG_ID` in `.env`, it is offered as the default and a bare ENTER
   accepts it.
2. `distinct` -- from prompt, validated against a whitelist drawn from the documented
   query-parameter enum domain: `auth_type`, `last_vlan_id`, `last_ssid`,
   `last_nacrule_id`, `last_nas_vendor`, `last_ap`, `last_status`, `type`,
   `mdm_compliance_status`, `mdm_provider`, `idp_id`, `mac`, `site_id`. Default is
   `auth_type` if the user presses ENTER. Invalid values trigger a warning and a
   re-prompt (max 3 attempts, then exit 0).
3. `duration` -- optional, free-text (e.g. `1d`, `7d`, `2w`). Default `1d` matches
   the API default. The prompt is skipped entirely when `--non-interactive` is set
   via `--menu 58`.

`MIST_HOST` and `MIST_API_TOKEN` come from `.env` via the existing
`mistapi.APISession` -- never prompted, never logged.

**Rationale**: Three prompts keep the user experience inside the Five-Item Rule
(Principle I) ceiling on cognitive load. UUID-shape and enum whitelist validation
catch the two most common operator errors (typo'd org ID, misspelled `distinct`
field) before a wasted API call. Reading the API token from `.env` keeps secrets
out of process arguments and shell history (Constitution Principle III, Safety-First,
and the documented security expectations in `agents.md`).

**Alternatives Considered**:

- Auto-iterate over every allowed `distinct` value in one invocation -- rejected:
  multiplies API calls by 13x and pollutes the SQLite table without explicit user
  intent. A future "all distinct axes" menu item can be added separately if demand
  emerges.
- Prompt for every one of the 18 optional filter parameters -- rejected: violates
  Principle I and overwhelms the NOC user. Advanced filtering is deferred to a future
  advanced-prompt mode.
- Read `org_id` from a positional CLI argument only -- rejected: breaks the
  interactive menu-driven UX expected by the junior NOC engineer audience.
