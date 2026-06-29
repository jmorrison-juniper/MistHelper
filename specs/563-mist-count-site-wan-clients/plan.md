# Implementation Plan: countSiteWanClients Menu Item

**Branch**: `563-mist-count-site-wan-clients` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/563-mist-count-site-wan-clients/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/wan_clients/count` (operationId `countSiteWanClients`) to
return aggregated counts of WAN clients (devices behind the site gateway) grouped by a
caller-chosen `distinct` attribute over a time window. The menu method prompts the user
through `safe_input()` for `site_id` and optional faceting / window parameters
(`distinct`, `start`, `end`, `duration`, `limit`), calls the `mistapi` SDK function
`mistapi.api.v1.sites.wan_clients.count.countSiteWanClients()`, flattens the multi-array
response into one summary row plus N bucket rows, and persists results through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot in the
Interactive-Safe Site-Stats cluster (60-96), adjacent to existing site-client viewers
and below the resource-intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. New tables `site_wan_clients_count_summary`
and `site_wan_clients_count_buckets` are created lazily by the exporter on first run.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known site from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65, 90-100) excludes 96 from
the default sweep, so an explicit `--menu 96` invocation with a `MIST_TEST_SITE_ID`
env var is used for smoke testing.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical site
counts (the endpoint returns one JSON object with a small bucket array bounded by the
`limit` query parameter, default 100). Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` govern back-off; this endpoint is light enough that no special
tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); 5-Item Rule on every new function.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteClientExportUtils` class (the same class that owns adjacent site-client exports),
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new SQLite tables, one menu
registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new top-level directories. If no
`SiteClientExportUtils` class exists at implementation time, the method is added to the
nearest existing site-clients class (e.g. `WirelessClientExportUtils` or
`SiteStatsExportUtils`) and the choice is justified in the implementation PR.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_wan_clients_count()` stays under
  25 lines, takes <=4 parameters (`self`, `site_id`, `distinct`, `time_window`) where
  `time_window` is a small dict of `start/end/duration/limit` to keep the parameter
  count under five, and contains <=5 logical blocks (prompt -> validate -> API call ->
  flatten -> DataExporter). Hierarchy is unchanged: one new method on an existing
  class. No new packages, modules, or top-level constants are introduced. The bucket
  flattener is a single comprehension; if it grows past 5 lines during implementation
  it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing site-clients
  export class (preferred: `SiteClientExportUtils`; fallback documented in Technical
  Context). No standalone wrapper function is introduced. The menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`bucket_row`, `distinct_attribute`, `count_summary`); no single-letter iterators
  except indexed loop counters where idiomatic.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings
  (`"site_wan_clients_count:site_id"`,
  `"site_wan_clients_count:distinct"`,
  `"site_wan_clients_count:window"`)
  so SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is required.
  `site_id` is validated against the Mist UUID shape before the API call; on validation
  failure the method logs a warning and returns early. API token comes from `.env` via
  the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with `version
  YY.MM.DD.HH.MM - add menu 96 countSiteWanClients` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs validation + build -> `gh run watch
  <run-id>` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container with the documented `-p 2200:2200 -p 8055:8055
  -v data:/app/data:rw -v .env:/app/.env:ro` flags -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting WAN clients for site %s distinct=%s
  duration=%s"); `DEBUG` after the call with summary counts ("WAN client count
  response: total=%d buckets=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets, tokens,
  or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  will carry an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  site-clients export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write, `logging.debug(...)` after write. The
  `DataExporter` call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/563-mist-count-site-wan-clients/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_wan_clients.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteClientExportUtils class (or nearest
                         # existing site-clients class), new ENDPOINT_PRIMARY_KEY_STRATEGIES
                         # entry for operationId 'countSiteWanClients', and menu 96
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New 'version YY.MM.DD.HH.MM' entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir). DataExporter creates the
                         # two new SQLite tables on first run.
documentation/api/sites/GET_sites_site_id_wan_clients_count.md
                         # Authoritative endpoint contract -- referenced, not modified.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `SiteClientExportUtils` class in `MistHelper.py` (the class that
owns adjacent site-clients exports). The menu number proposal is **96**, chosen because
operations 60-96 are the Interactive-Safe Site-Stats cluster and 96 is the next
available slot below the resource-intensive block at 97-101. The full menu list will be
re-verified at task generation time; if 96 collides with an in-flight feature branch,
the next free integer in the same cluster is used and the spec / plan is updated in the
same PR.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_site_wan_clients.md`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters with the window grouped into a
  single dict, and <=5 logical blocks. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry is a
  single dictionary insertion with no nesting beyond the existing schema.
- **Principle II (Class-Based)**: PASS -- All work lives on `SiteClientExportUtils` (or
  documented fallback). No wrappers introduced. The bucket flattener, if extracted,
  becomes a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. Optional query parameters default
  cleanly when the user accepts the prompt's default value.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token. Bucket count, distinct value,
  and time window are logged at DEBUG.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before / after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
