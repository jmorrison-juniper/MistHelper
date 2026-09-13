# Phase 0 Research: countOrgDevices

All research tasks resolved before Phase 1. No NEEDS CLARIFICATION markers remain.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Use `mistapi.api.v1.orgs.devices.countOrgDevices(apisession, org_id, distinct=None, hostname=None, site_id=None, model=None, managed=None, mac=None, version=None, ip=None, mxtunnel_status=None, mxedge_id=None, lldp_system_name=None, lldp_system_desc=None, lldp_port_id=None, lldp_mgmt_addr=None, type=None, start=None, end=None, duration="1d", limit=100, page=1)` as the sole transport into the Mist Cloud. The function returns a `mistapi.APIResponse` whose `.data` is a JSON object matching the OpenAPI response envelope (`distinct`, `start`, `end`, `limit`, `total`, `results[]`).

**Rationale**: The enriched documentation file
`documentation/api/orgs/GET_orgs_org_id_devices_count.md` confirms the SDK symbol
`mistapi.api.v1.orgs.devices.countOrgDevices()` and enumerates every query parameter
plus the response shape. Routing all Mist HTTP calls through `mistapi` matches the
project standard (`agents.md` "Primary Dependencies: mistapi 0.59+") and inherits
adaptive back-off, pagination helpers, and credential handling from the existing
`mistapi.APISession`.

**Alternatives Considered**:
- Direct `requests.get()` against the Mist host with manual auth header construction --
  rejected because it bypasses the constitution's "mistapi is the sole permitted
  interface" rule and duplicates retry / rate-limit logic already provided by the SDK.
- A custom thin wrapper class around `requests` -- rejected for the same reason and
  because it would violate Principle II (No Wrappers).

## Research Task 2: Primary Key Strategy

**Decision**: Register the operation as `composite_pk` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
Two tables are created: `org_devices_count_summary` (one row per invocation, keyed by
`org_id` + `distinct` + `start` + `end`) and `org_devices_count_results` (one row per
`results[]` entry, keyed by `org_id` + `distinct` + `start` + `distinct_value`).
A monotonically increasing `run_id` is added to both tables so historical snapshots are
preserved across re-runs without overwriting the latest values.

**Rationale**: The response envelope is a time-windowed aggregate. The same `org_id` and
`distinct` combination produces different totals at different times, so a pure natural
key on `org_id` alone would cause every run to overwrite the previous one and destroy
trend data. A composite key including `start` + `end` lets `INSERT OR REPLACE` upsert
within the same time window (idempotent re-runs) while preserving distinct windows
side-by-side. This mirrors the policy other counting endpoints follow
(`searchOrgDeviceEvents`, etc., per `agents.md` Database Strategy section).

**Alternatives Considered**:
- `natural_pk` on `org_id` alone -- rejected because every run would overwrite the
  previous count snapshot and history would be lost.
- `auto_increment_with_unique` -- rejected because it forces a synthetic id and prevents
  the `INSERT OR REPLACE` idempotency that re-runs in the same time window depend on.
- A single denormalized table -- rejected because the envelope-level metadata
  (`total`, `limit`, `start`, `end`) would be duplicated across every result row,
  inflating storage and complicating downstream queries.

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- CSV summary file: `data/org_devices_count_summary.csv`
- CSV results file: `data/org_devices_count_results.csv`
- SQLite tables (in `data/mist_data.db`): `org_devices_count_summary` and
  `org_devices_count_results`
- ArangoDB collections (via DataExporter): `org_devices_count_summary` and
  `org_devices_count_results`

**Rationale**: The naming convention follows the existing pattern (snake_case derived
from the operationId minus the verb -- `countOrgDevices` -> `org_devices_count`).
Splitting summary and results into two artifacts keeps each row schema flat and avoids
the JSON-blob anti-pattern in CSV. The filenames are stable across runs so downstream
NOC dashboards can ingest them without renaming logic. `DataExporter.write_with_format_selection(data, filename, api_function_name="countOrgDevices")`
handles the CSV / SQLite / ArangoDB fan-out using the registered PK strategy.

**Alternatives Considered**:
- Single combined file with nested JSON in a column -- rejected for the reasons in
  Task 2.
- Filename keyed by `org_id` (`data/org_<id>_devices_count.csv`) -- rejected because it
  prevents merging multi-org runs into a single SQLite table and bloats the `data/`
  directory for users managing many orgs.
- `.json` output -- rejected; DataExporter is the documented multi-backend path and
  already supports CSV + SQLite + polyglot DB from a single call.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place the new operation at **menu number 58** in the "Misc" Safe Org
Exports cluster (56-59).

**Rationale**: Per `agents.md` Menu Categories table, range 1-59 is "Safe Org Exports"
with sub-clusters: Sites (1-7), Inventory (8-14), Device stats (15-19), Events (20-26),
Clients (27-30), Gateways (31-36), Templates (37-41), Config/Admin (42-50),
SLE (51-55), Misc (56-59). The endpoint is a read-only org-level aggregate that does not
neatly fit Inventory (which is item-level) or Device stats (which are device-level),
but does fit Misc as an org-wide count summary. Menu number 58 is the next available
slot below the Interactive Safe cluster that begins at 60. The number is re-verified at
task generation time -- if 58 collides with an in-flight feature branch, the next free
integer in the same cluster (57 or 59) is selected and the plan + research are updated
in the same PR.

**Alternatives Considered**:
- Item 14 (Inventory cluster) -- rejected because 14 is already on the "heavy" skip
  list and represents the full inventory listing, not a count aggregate.
- Item 19 (Device stats cluster) -- rejected because 19 is also on the skip list and the
  cluster is reserved for per-device statistics, not org-aggregate counts.
- A brand-new number above 100 -- rejected because the endpoint is safe, fast, and
  belongs in the test sweep; numbers above 100 are interactive / continuous /
  destructive territory.

## Research Task 5: Required User Prompts

**Decision**: Two required prompts, three optional prompts, all via `safe_input()`:

1. **Required**: `org_id` -- prompted with default to `os.environ.get("MIST_ORG_ID")`
   so `--test` mode and `.env`-driven runs do not need keyboard input. Context string
   `"org_devices_count:org_id"`.
2. **Required**: `distinct` field -- prompted with a numbered menu listing the
   supported grouping values per the OpenAPI doc: `model`, `type`, `version`,
   `hostname`, `mac`, `site_id`, `mxedge_id`, `lldp_system_name`. Default is `model`.
   Context string `"org_devices_count:distinct"`.
3. **Optional**: `site_id` filter -- defaults to None (org-wide). Context string
   `"org_devices_count:site_id"`.
4. **Optional**: time window -- single prompt for a `duration` shorthand
   (e.g. `1d`, `7d`, `2w`) with default `1d`. Context string
   `"org_devices_count:duration"`. The SDK derives `start` / `end` from `duration` when
   the explicit bounds are omitted.
5. **Optional**: `limit` -- defaults to 100 (matching the OpenAPI default). Context
   string `"org_devices_count:limit"`.

API credentials (`MIST_HOST`, `MIST_API_TOKEN`) are loaded from `.env` by the existing
`mistapi.APISession` and are never prompted for. The org id can also come from `.env`
(`MIST_ORG_ID`) so `--test` mode skips the interactive prompt entirely.

**Rationale**: This prompt set covers the documented common case (group by model /
type / version for an org-wide view) while keeping the interactive flow short. Operators
who need the niche filters (`mxtunnel_status`, `lldp_*`, `managed`, etc.) get them via
the `--direct` invocation pattern that already exists for other menu items, where the
full kwargs dict is built from CLI arguments.

**Alternatives Considered**:
- Prompt for every query parameter -- rejected; 18 prompts would violate the spirit of
  Principle I (5-Item Rule) at the user-experience level and slow down operators using
  the menu interactively.
- Skip the `distinct` prompt and default to `model` silently -- rejected because the
  whole point of the endpoint is the aggregation field, so the user must consciously
  choose it.
- Pull `org_id` exclusively from `.env` with no prompt -- rejected because MSP-style
  operators frequently switch orgs within a session and an interactive override
  is required.
