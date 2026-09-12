# Phase 0 Research: countSiteAlarms

This document records the Phase 0 research decisions for adding a new MistHelper menu
item that invokes `GET /api/v1/sites/{site_id}/alarms/count` (operationId
`countSiteAlarms`). All findings are grounded in
`documentation/api/sites/GET_sites_site_id_alarms_count.md` (the enriched per-endpoint
doc), the existing `mistapi` 0.59+ Python SDK layout, and the patterns established by
adjacent menu items in `MistHelper.py`.

## Research Task 1: SDK function signature and behavior

- **Decision**: Use
  `mistapi.api.v1.sites.alarms.count.countSiteAlarms(mist_session, site_id, distinct=None,
  ack_admin_name=None, acked=None, type=None, severity=None, group=None, start=None,
  end=None, duration="1d", limit=100)`. The MistHelper menu method will accept the
  user-provided `site_id` as a required arg and pass the seven optional filters as
  keyword arguments; defaults remain on the SDK side unless the user opts to override
  them. The SDK returns a `requests.Response`-like object whose `.data` attribute is the
  decoded JSON payload documented in the contracts file.
- **Rationale**: The per-endpoint enriched doc lists the operation under the SDK module
  `mistapi.api.v1.sites.alarms.countSiteAlarms()`. mistapi 0.59 follows the convention
  that every operationId corresponds to a same-named module-level function; the function
  accepts the active `APISession` as its first positional arg, then path parameters,
  then query parameters as kwargs. The endpoint documentation lists only `distinct`,
  `ack_admin_name`, `acked`, `type`, `severity`, `group`, `start`, `end`, `duration`,
  and `limit` as query parameters, so the menu method binds exactly that set.
- **Alternatives considered**:
  1. Building the URL by hand with `requests`. Rejected because the project constitution
     mandates `mistapi` as the sole permitted interface to Mist Cloud.
  2. Wrapping the call in a try/except that swallows all exceptions. Rejected because
     Principle V requires `logging.exception` on unexpected exceptions so that
     diagnostics survive to the SQLite/CSV logs.
  3. Accepting all ten query params as menu prompts. Rejected because doing so violates
     the safety-first NOC-friendly UX (too many prompts); instead the menu accepts a
     core trio (distinct + duration + severity) and exposes the rest as optional
     advanced inputs.

## Research Task 2: Primary Key Strategy

- **Decision**: Use **two cooperating strategies** for the two flattened tables:
  1. `site_alarms_count_summary` -> `composite_pk` on `[site_id, distinct, start, end]`.
     One summary row per call; repeated runs with the same scope/time-window upsert.
  2. `site_alarms_count_buckets` -> `composite_pk` on
     `[site_id, distinct, distinct_value, start, end]`. One row per bucket returned in
     the `results` array; the bucket key is the value of the `distinct` field for that
     row (e.g. `severity=critical`, `type=rogue_client`).
- **Rationale**: The response does not include a stable UUID for each bucket -- buckets
  are derived (count, distinct_value) pairs over a time window. A pure `natural_pk`
  is therefore impossible. A pure `auto_increment_with_unique` would create duplicates
  on every rerun, which the spec explicitly forbids (Acceptance Scenario 3). The
  composite key approach matches how other count endpoints (e.g. `searchOrgDeviceEvents`)
  are registered and produces a clean `INSERT OR REPLACE` upsert on rerun.
- **Alternatives considered**:
  1. `natural_pk` using a synthetic hash of all bucket fields. Rejected because the hash
     is not API-provided and the Constitution prefers natural business keys; the
     composite of `(site_id, distinct, distinct_value, start, end)` already uniquely
     identifies a bucket.
  2. `auto_increment_with_unique` with a `UNIQUE` index covering the same columns.
     Rejected because the SQLite layer already supports `composite_pk` upserts via
     `INSERT OR REPLACE`; adding an auto-increment column is dead weight.
  3. Single flat table mixing summary + buckets. Rejected because the column shapes
     differ enough that mixing them produces sparse NULLs and confuses downstream CSV
     consumers.

## Research Task 3: Output filename and SQLite table

- **Decision**: Two flattened outputs feed one `DataExporter.write_with_format_selection`
  call pair:
  1. Summary CSV: `data/site_alarms_count_summary.csv` (and SQLite table
     `site_alarms_count_summary`).
  2. Bucket CSV: `data/site_alarms_count_buckets.csv` (and SQLite table
     `site_alarms_count_buckets`).
  Both tables carry `site_id` for foreign-key style joins back to `org_sites` and to
  any future `site_alarms_search` table.
- **Rationale**: Splitting the summary from the bucket array keeps each CSV
  rectangular, satisfies the 5-Item Rule at the row-shape level, and matches the
  precedent set by spec 500 (`org_claim_status_summary` + `org_claim_status_details`)
  and by `searchOrgDeviceEvents` (`org_device_events_summary` + `org_device_events`).
  Naming uses the operationId stem (`site_alarms_count`) plus a `_summary` /
  `_buckets` suffix so files self-document.
- **Alternatives considered**:
  1. Single CSV with summary fields repeated on every bucket row. Rejected because it
     duplicates `start`, `end`, `total`, and `limit` on every row and prevents clean
     SQLite normalization.
  2. Filename `count_site_alarms.csv` to mirror the operationId verbatim. Rejected
     because existing exports follow the entity-first naming convention
     (`org_alarms_search.csv`, `site_devices.csv`); the table prefix `site_alarms_*`
     keeps related files alphabetically adjacent in `data/`.

## Research Task 4: Menu category placement and next available menu number

- **Decision**: Propose **menu number 97**. The number is reverified at
  `/speckit.tasks` time against the in-flight 5xx feature branches (specs
  500-540 are also proposing safe-export menu numbers in the same range).
- **Rationale**: The README operation map groups menu items as 1-59 (Safe Org
  Exports), 60-96 (Interactive Safe -- site devices, insights, stats, viewers),
  97-101 + 153 (Resource Intensive), 102-150 (interactive WebSocket/tools), 154-194
  (Destructive). `countSiteAlarms` is a site-scoped read that may cover up to 1 day
  of alarm aggregation, so it sits cleanly at the bottom of the Resource Intensive
  cluster (97) immediately after the Viewers (92-96) block. Adjacent menu 56 already
  hosts `searchOrgAlarms` at org scope, so 97 is the natural site-scoped sibling.
- **Alternatives considered**:
  1. Slot inside the 1-59 Safe Org Exports range. Rejected because that range is
     reserved for org-scoped operations and this endpoint is site-scoped.
  2. Slot in 60-91 (site devices/insights/stats). Rejected because alarms are not
     stats and the existing sub-clusters in 60-91 are already alphabetized by
     entity; inserting in the middle would force renumbering.
  3. A high number (e.g. 195+) beyond the destructive block. Rejected because that
     space is reserved for newly added destructive operations; a safe read in the
     destructive range is misleading to junior NOC engineers.

## Research Task 5: Required user prompts

- **Decision**: The menu method asks for, in order:
  1. `site_id` -- required, validated against the Mist UUID regex. Loaded via
     `safe_input("Site ID: ", context="site_alarms_count:site_id")`. No `.env`
     fallback because most users operate against many sites.
  2. `distinct` -- optional, single-token grouping field. Defaults to `type`.
     Accepted values are the documented distinct buckets (`type`, `severity`,
     `group`, `ack_admin_name`, `acked`). Loaded via `safe_input("Distinct field
     [type]: ", context="site_alarms_count:distinct")`.
  3. `duration` -- optional time window. Defaults to `1d`. Loaded via
     `safe_input("Duration [1d]: ", context="site_alarms_count:duration")`.
  4. `severity`, `group`, `type`, `acked`, `ack_admin_name`, `start`, `end`, `limit`
     -- all skipped at the basic prompt level; available as command-line overrides
     in advanced mode (`--filter severity=critical`). This keeps the interactive
     prompt count at three so junior NOC engineers can finish in five seconds.
  The Mist `org_id` is **not** prompted because the SDK derives it from the active
  `APISession` plus the supplied `site_id`; the API token is loaded from `.env`
  (`MIST_API_TOKEN`) and `MIST_HOST` selects the cloud region.
- **Rationale**: The constitution Safety-First principle calls for a minimal prompt
  count (every prompt is a chance for a junior NOC engineer to enter a wrong value).
  Three core prompts (site, group-by, window) cover 90% of usage; advanced filters
  are reachable but not in the default path.
- **Alternatives considered**:
  1. Prompt for every documented query param. Rejected because it overwhelms the
     interactive user and increases EOF-handling complexity in SSH sessions.
  2. Read `site_id` from `.env`. Rejected because users routinely target multiple
     sites and a hard-coded site ID would surprise them.
  3. Hard-code `distinct=type` with no prompt. Rejected because grouping flexibility
     is the primary reason this endpoint exists -- forcing one value would block
     legitimate use cases (group by severity, by acked, etc.).
