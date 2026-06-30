# Phase 0 Research: getMspSle

**Feature**: `587-mist-get-msp-sle`
**Date**: 2026-06-29
**Source doc**: `documentation/api/msps/GET_msps_msp_id_insights_metric.md`

This document captures the five Phase 0 research decisions required by the SpecKit
`/speckit.plan` workflow. Each task uses the Decision / Rationale / Alternatives
Considered format.

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke the endpoint via
`mistapi.api.v1.msps.sles.getMspSle(apisession, msp_id, metric, sle=None,
duration="1d", interval=None, start=None, end=None)`. The call returns a
`mistapi.APIResponse` whose `.data` attribute is a single JSON object with five
documented properties: `start` (int epoch, required), `end` (int epoch, required),
`interval` (int seconds, required), `limit` (int, optional), and `results` (array of
heterogeneous items -- each item is either a number or an object depending on the
chosen `metric`). The endpoint is **not paginated**. The enriched doc lists the SDK
module path as `mistapi.api.v1.msps.sles`; the spec.md mentions
`mistapi.api.v1.msps.insights` as a likely alternate import path. The implementer
must resolve the actual import path at task generation time by inspecting `mistapi`
0.59+ installed in the venv -- whichever module exposes `getMspSle` is the canonical
import.

**Rationale**: The enriched per-endpoint doc at
`documentation/api/msps/GET_msps_msp_id_insights_metric.md` declares HTTP
`GET /api/v1/msps/{msp_id}/insights/{metric}`, lists both `msp_id` and `metric` as
required path parameters, defines five optional query parameters (`sle`, `duration`,
`interval`, `start`, `end`), and shows a flat aggregate response schema with a
required `start`/`end`/`interval` trio and a heterogeneous `results` array. No
pagination cursor is present. The mistapi 0.59+ SDK convention is one Python function
per OpenAPI operationId, with `apisession` as the first parameter, path parameters
following in OpenAPI order as positional args, and query parameters as keyword args
with their documented defaults (e.g. `duration="1d"`); this matches every other GET
method in the codebase (`listOrgSites`, `getOrgLicensesSummary`,
`getOrgLicenseAsyncClaimStatus`, etc.).

**Alternatives Considered**:

- Direct `requests.get()` call -- rejected. Bypasses the project's sole-SDK rule,
  breaks `mistapi.APISession` rate-limit handling, and forfeits the adaptive delay
  metrics that every other menu item benefits from.
- Pre-resolve the SDK module at plan time -- rejected as inappropriate for the
  research phase. The enriched doc and the spec.md disagree on the exact module path
  (`mistapi.api.v1.msps.sles` vs `mistapi.api.v1.msps.insights`), and the only
  authoritative source is the installed SDK. The implementer is instructed to run a
  one-line `python -c "import ...; print(dir(...))"` probe at the start of task
  execution and use the path that actually exposes the function.
- Pre-flight call `listInsightMetrics` to validate the `metric` string before
  invoking the SLE endpoint -- rejected for this spec. That is a separate operationId
  with its own future spec; layering it on now would chain two API calls per menu
  invocation and inflate scope. The cheap shape-and-length check in
  `MspSLEExporter.export_msp_sle()` is sufficient first-line validation; a 400 from
  Mist on an unknown metric is logged and returned cleanly.

## Research Task 2: Primary Key Strategy

**Decision**: Use `composite_pk` keyed on
`(msp_id, metric, start, end, interval)`. `msp_id` and `metric` come from the URL
path. `start`, `end`, and `interval` are echoed in the response body itself (the
schema marks them required), so the row is fully self-describing and no MistHelper
injection is needed for those three. The DataExporter row must still inject `msp_id`
and `metric` from the path parameters because the response body does not echo them.
The heterogeneous `results` array is serialized to a single `results_json` TEXT
column so the variable shape (numbers OR objects per metric) is persisted without a
per-metric schema migration.

**Rationale**: Each combination of `(msp_id, metric, start, end, interval)` produces
exactly one aggregate row. Re-running the menu item against the same MSP, the same
metric, and the same time window with the same interval is a true semantic overwrite
-- the upstream aggregation is deterministic for a finalized window. This satisfies
the constitution's "natural business keys" rule and enables clean
`INSERT OR REPLACE` upserts in SQLite. Including `interval` in the key prevents a
1-hour-rollup row from clobbering a 1-day-rollup row for the same window.

**Alternatives Considered**:

- `composite_pk` on `(msp_id, metric)` only -- rejected. Any two distinct query
  windows for the same metric would collide, so a user comparing yesterday's and
  today's `wifi-connectivity` aggregates would lose the older snapshot.
- `auto_increment_with_unique` on
  `(msp_id, metric, start, end, interval, retrieved_at)` -- rejected. The documented
  fallback for unstable aggregates; here `start`/`end`/`interval` are explicitly
  stable and echoed in the response, so the cheaper composite_pk path is correct.
- Explode the `results` array into one row per result item with index column --
  rejected for this spec. The result item shape varies per metric (sometimes a bare
  number, sometimes a nested object); exploding would force per-metric column
  divergence or a thick polymorphic schema. A single `results_json` column keeps
  every metric round-trippable today and leaves room for a future per-metric
  exploder when the metric set stabilizes.

## Research Task 3: Output filename and SQLite table

**Decision**: Output base name `msp_sle`. CSV path `data/msp_sle.csv`. SQLite table
`msp_sle` in `data/mist_data.db`.

**Rationale**: The existing MistHelper naming convention is
`<scope>_<resource>[_<sub_resource>]` lowercase with underscores -- matching
`org_sites`, `org_license_summary`, `site_devices`, and the sibling
`msp_saml_metadata` from spec 586. `msp_sle` is short, greppable, and obviously
distinct from any future `org_sle` (the org-level cousin under a different path) and
from the existing `OrgSLEExporter` outputs. Adding the metric to the file name was
considered (`msp_sle_<metric>.csv`) and rejected because the metric is already a
column in the row, so per-metric file splits would produce a sparse `data/` listing
and complicate cross-metric SQL joins.

**Alternatives Considered**:

- `msp_insights` -- rejected. Less specific; the OpenAPI tag is `MSPs SLEs` (plural)
  and the response is specifically SLE aggregates, not generic insights. A future
  non-SLE MSP insights endpoint would collide.
- `getMspSle.csv` (operationId verbatim) -- rejected. Mixed case breaks the
  established lowercase-snake convention and is uglier on Linux containers.
- `msp_sle_<metric>.csv` (one file per metric) -- rejected for the reasons above
  (sparse listing, harder cross-metric analysis, no benefit since `metric` is a
  column).

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place under the **Misc** cluster (operations 56-59). Propose menu
number **59**. If 59 collides with an in-flight feature branch at task generation
time, use the next free integer in the same cluster, or the next contiguous free
integer above 50 within the Safe Org Exports / Misc band.

**Rationale**: The MistHelper menu taxonomy documented in `agents.md` and
`.github/copilot-instructions.md` reserves:

- 1-59 for Safe Org Exports (Sites, Inventory, Device stats, Events, Clients,
  Gateways, Templates, Config/Admin, SLE 51-55, Misc 56-59)
- 60-96 for Interactive Safe operations
- 97-101 / 153 for Resource Intensive
- 102-194 for WebSocket, Interactive, Continuous, and Destructive

The endpoint documentation explicitly notes that menu items 57-62 already cover
org-level SLE exports (`OrgSLEExporter` and related). MSP SLE is the cross-org
companion: read-only, no destructive effect, no fan-out beyond a single API call,
and no interactive prompt beyond two required IDs and a few optional window
selectors. Placing it at **59** lands it inside the Misc band immediately adjacent
to the org-level SLE exporters at 57-62, keeping all SLE-related operations
discoverable in one contiguous range when a user scrolls the menu.

**Alternatives Considered**:

- 51-55 SLE cluster -- rejected. That band is already documented as full per the
  agents.md menu map; inserting an MSP-scope item there would force a renumber of
  adjacent items.
- 60-96 Interactive Safe band -- rejected. The endpoint requires only a couple of
  prompts and has no long-running or interactive watch behavior, so it does not meet
  the "Interactive" cluster criteria and would be misplaced.
- A new MSP-only cluster (e.g., 195+) -- rejected. Premature; spec 586 (MSP SAML
  metadata) and spec 583/584/585 (other MSP reads) are all going into the existing
  Safe Org / Misc bands. Splitting out a dedicated band creates a sparse cluster.
  Revisit when 5+ MSP endpoints have been cataloged and the band is naturally
  contiguous.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Prompt the user for **two required** values via `safe_input()`:
`msp_id` and `metric` (the SLE metric name). Prompt for **four optional** query
selectors via `safe_input()` with documented defaults: `sle` (no default, blank
omits the param), `duration` (default `"1d"`), `interval` (no default, blank omits
the param), `start` (no default, blank omits), `end` (no default, blank omits). None
of these values are read from `.env` for normal interactive runs. The Mist API
session credentials (`MIST_HOST`, `MIST_API_TOKEN`) continue to come from `.env` via
the existing `mistapi.APISession` initialization that all other menu items share. In
`--test` mode, fall back to optional env vars `MIST_TEST_MSP_ID` (UUID),
`MIST_TEST_SLE_METRIC` (default `"wifi-connectivity"` if unset), and
`MIST_TEST_SLE_DURATION` (default `"1d"` if unset) so the non-interactive sweep can
exercise the menu item without prompts.

**Rationale**: The codebase convention is: tenant credentials (token, host, org
default) in `.env`; per-call selectors (specific UUIDs or query windows the user
wants right now) from prompts. `msp_id` and `metric` are per-call selectors -- a
user managing multiple MSPs and exploring multiple metrics will pick a different
combination per invocation, so caching either in `.env` would mislead. The optional
window selectors mirror the upstream API defaults (`duration="1d"`, no `interval`)
and the prompt path with blank-to-omit semantics keeps the common-case interactive
flow short (press Enter four times to accept defaults). The `--test` env vars mirror
the existing `MIST_TEST_ORG_ID` / `MIST_TEST_SITE_ID` pattern already used by
adjacent menu items.

**Alternatives Considered**:

- Pull `msp_id` from `.env` always (one MSP per user) -- rejected. Some users
  legitimately manage multiple MSPs; hard-coding one defeats the menu purpose.
- Skip the optional window prompts and always send the upstream defaults --
  rejected. A NOC engineer comparing this morning's SLE to last week's needs to
  pass an explicit `start`/`end`, and forcing them to edit code or env vars for
  that is a poor experience. The blank-to-omit prompt path keeps the no-window
  case zero-friction while making the windowed case one prompt away.
- Auto-list all MSPs first and let the user pick by index -- rejected for this
  spec. That would require chaining `listMsps` (a separate operationId) which is
  not in scope. A future enhancement spec can layer that on top of this base
  operation. The same argument applies to auto-listing valid metrics via
  `listInsightMetrics`.
