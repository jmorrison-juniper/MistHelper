# Phase 0 Research: countSiteSkyatpEvents

**Feature**: 559-mist-count-site-skyatp-events
**Endpoint**: `GET /api/v1/sites/{site_id}/skyatp/events/count`
**Source doc**: `documentation/api/sites/GET_sites_site_id_skyatp_events_count.md`

## Research Task 1: SDK Function Signature & Behaviour

- **Decision**: Call
  `mistapi.api.v1.sites.skyatp.events.count.countSiteSkyatpEvents(apisession, site_id, distinct=None, type=None, mac=None, device_mac=None, threat_level=None, ip=None, start=None, end=None, duration="1d", limit=100)`
  and return `response.data` (a dict with keys `distinct`, `start`, `end`, `limit`,
  `total`, `results`). The `results` field is an array of bucket objects; each bucket
  has a required integer `count` plus arbitrary additional string properties that name
  the distinct attribute value (e.g. `{"count": 17, "type": "mw"}`).
- **Rationale**: The enriched per-endpoint doc
  (`documentation/api/sites/GET_sites_site_id_skyatp_events_count.md`) lists `site_id`
  as the sole required path parameter and ten optional query parameters. The OpenAPI
  schema (200 response) lists six required top-level keys: `distinct`, `end`, `limit`,
  `results`, `start`, `total`. `results[]` is `uniqueItems: true` and each item has
  `additionalProperties` of `type: string` plus the required `count` integer. The
  mistapi SDK follows the standard pattern of `apisession + path params + kwargs for
  query params`, identical to the sibling `searchSiteSkyatpEvents` already used in the
  codebase (see `ENDPOINT_PRIMARY_KEY_STRATEGIES` line ~3353 of `MistHelper.py`).
- **Alternatives Considered**:
  1. Use the raw `mistapi.APISession.mist_get()` with a hand-built URL -- rejected
     because the constitution mandates `mistapi` as the sole SDK and bypassing the
     typed wrapper loses parameter validation.
  2. Loop over every legal `distinct` value to build a one-shot multi-aggregation
     report -- rejected as scope creep; out of scope for FR-001 (single endpoint).

## Research Task 2: Primary Key Strategy

- **Decision**: `auto_increment_with_unique`. Primary key:
  `misthelper_internal_id`. Unique constraint:
  `(site_id, distinct, bucket_value, start_epoch, end_epoch)`. Indexes:
  `site_id`, `distinct`, `start_epoch`.
- **Rationale**: The endpoint is a *count aggregation*, not a feed of stable
  domain entities. Buckets have no API-issued UUID. The composite identity of a row
  is the tuple (site + distinct dimension + bucket value + time window). The same
  bucket re-counted at a later time MUST update in place when the user re-runs with
  the same window, so a pure auto-increment without a unique constraint would
  duplicate rows; conversely a pure composite_pk would be brittle if the API ever
  emits a row with a NULL `bucket_value`. The hybrid pattern is the documented
  fallback in the constitution and matches `getOrgLicensesSummary` in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- **Alternatives Considered**:
  1. `composite_pk` on `(site_id, distinct, bucket_value, start_epoch, end_epoch)` --
     rejected because `bucket_value` is derived from `additionalProperties` at
     runtime and may legally be missing for malformed responses; SQLite would refuse
     the insert.
  2. `natural_pk` on a synthetic hash of the bucket -- rejected because the hash
     would need to be computed by MistHelper, not the API, which violates the
     "natural business keys from the Mist API, not artificial IDs" guideline.

## Research Task 3: Output Filename and SQLite Table

- **Decision**:
  - CSV filename: `data/site_skyatp_events_count_<site_id>_<timestamp>.csv`.
  - SQLite table: `site_skyatp_events_count`.
  - ArangoDB collection: `site_skyatp_events_count` (vertex collection); a single
    edge per row links to the parent `site` vertex (`site -> skyatp_count_bucket`).
- **Rationale**: Matches the existing convention used by `searchSiteSkyatpEvents`
  (`site_skyatp_events` table) and the broader pattern of
  `<scope>_<resource>_<verb>` for count endpoints (see
  `org_clients_count`, `org_devices_count` if present). The timestamp suffix on the
  CSV is added by `DataExporter` automatically. The site UUID is included in the CSV
  filename so multi-site exports do not overwrite each other. ASCII-only; lowercase
  with underscores per the codebase's existing table naming convention.
- **Alternatives Considered**:
  1. `site_atp_count` -- rejected: ATP is a Juniper marketing abbreviation; the API
     uses `skyatp`, so the table follows the API.
  2. Per-distinct-value tables (e.g. `site_skyatp_count_by_type`) -- rejected: would
     fragment the data and complicate cross-distinct queries.

## Research Task 4: Menu Category Placement and Next Available Number

- **Decision**: Menu number **195**, registered under the safe-read Site Security /
  Anomaly cluster, dispatched to `SiteAnomalyExporter.export_site_skyatp_events_count`.
- **Rationale**: The current catalogue ends at operation 194 per
  `.github/copilot-instructions.md`. The destructive range (154-194) is preceded by
  the safe interactive range (60-152) which already hosts site-scoped read operations.
  Sky ATP event counting is a strictly read-only site-scoped aggregation, so it
  belongs in the next free safe slot above the current ceiling: **195**. The
  `SiteAnomalyExporter` class is the natural home -- it already owns adjacent
  site-level threat / anomaly read methods. Final number is reconciled with any
  in-flight branch at task generation time; if 195 collides, the next free integer
  is used and `README.md` is updated in the same PR.
- **Alternatives Considered**:
  1. Reuse a number inside 96-101 (resource-intensive) -- rejected: the count call
     is light (single GET, small response), so the resource-intensive label is
     misleading and would discourage routine use by NOC engineers.
  2. Place in the destructive 154-194 range -- rejected: zero side effect, no
     destructive confirmation required.

## Research Task 5: Required User Prompts

- **Decision**: Three `safe_input()` prompts, all with explicit `context=` strings:
  1. `site_id` -- mandatory. Default from `.env` `MIST_SITE_ID` if set; otherwise
     blocking prompt. Validated against the Mist UUID shape via `ValidationUtils`.
     Context: `"site_skyatp_count:site_id"`.
  2. `distinct` -- optional. Default `type`. Accepted values surfaced in the prompt
     text: `type`, `threat_level`, `mac`, `device_mac`, `ip`. Empty input keeps the
     default. Context: `"site_skyatp_count:distinct"`.
  3. `duration` (or explicit `start` / `end`) -- optional. Default `1d`. Accepts the
     Mist relative-time strings (`1d`, `7d`, `2w`, `-1h`, `-1w`) documented in the
     enriched per-endpoint doc. Context: `"site_skyatp_count:window"`.
- **Rationale**: `site_id` is the only required path parameter; everything else is
  optional. Surfacing `distinct`, `type`, `mac`, `device_mac`, `threat_level`, `ip`,
  `start`, `end`, `duration`, and `limit` as ten separate prompts would violate the
  5-Item Rule and overwhelm the junior NOC engineer audience. The three-prompt model
  covers the 90% case: "what dimension do I want to slice by, and over what window?"
  Power users can pass the full kwarg set programmatically via the `--menu 195` CLI
  if needed (a future enhancement, not in scope here). API host and token are loaded
  from `.env` (`MIST_HOST`, `MIST_API_TOKEN`) by the existing `mistapi.APISession`
  bootstrap and are never prompted for.
- **Alternatives Considered**:
  1. Single prompt with a free-form key=value string -- rejected: error-prone and
     hard to log safely.
  2. Ten separate prompts for full parameter coverage -- rejected: violates 5-Item
     Rule and the NOC-engineer-clarity directive.
  3. No prompts (read all from `.env`) -- rejected: bypasses the interactive menu
     paradigm and makes the operation inflexible for ad hoc investigation.
