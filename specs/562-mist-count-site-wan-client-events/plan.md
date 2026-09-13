# Implementation Plan: countSiteWanClientEvents Menu Item

**Branch**: `562-mist-count-site-wan-client-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/562-mist-count-site-wan-client-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/wan_client/events/count` (operationId
`countSiteWanClientEvents`) to return a count-by-distinct-attribute aggregation of
WAN client events at a single site. The menu item prompts the user for a `site_id`
via `safe_input()`, optionally accepts a `distinct` grouping field, a Mist event
`type` filter, an absolute `start`/`end` window or relative `duration` string, and
a result `limit`. It invokes the `mistapi` SDK once, flattens the response (one
summary row plus N grouped-count rows) and persists output through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent data. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated polls upsert cleanly. The new
operation is proposed as menu number **91** -- the next available slot in the
site-stats cluster (operations 80-91), adjacent to the existing `searchSiteWanClientEvents`
and `countSiteWanClients` exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transitive transport);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, and an optional
`MIST_SITE_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land under `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend when active.
**Testing**: `python MistHelper.py --test` exercises the new menu item in
non-interactive mode using the `.env` site default. Local quality gates are
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, and
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected; menu 91 sits inside the default sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
`ghcr.io/jmorrison-juniper/misthelper:latest` for production / SSH-on-2200. Both
must work without code change.
**Project Type**: CLI tool, single-file monolith `MistHelper.py` (~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI tier.
**Performance Goals**: A single GET to the count endpoint returns in <=5 seconds
for a one-day window on a typical site. The endpoint is non-paginated in the
classic sense but accepts `limit` as a server-side cap on distinct groups; default
`limit=100` is preserved. Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs; all output under `data/`; Windows-safe path joining via `os.path.join`
or `pathlib.Path`. Mist API rate limit (5000 calls/hour) handled by existing
adaptive layer.
**Scale/Scope**: One new public menu method (~22 lines) on a site-stats class
in `MistHelper.py`, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
SQLite table (`site_wan_client_events_count`), one menu registration entry, one
README operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_wan_client_events_count()` stays under 25 executable lines, takes
  <=5 parameters (`self`, `site_id`, `distinct`, `time_filter`, `limit`), and
  contains <=5 logical blocks (prompt collection -> validate -> SDK call ->
  flatten -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are
  introduced. If the flatten block grows past 5 lines during implementation it
  is extracted as a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  site-stats / WAN-client export class (the same class that owns the related
  `searchSiteWanClientEvents` and `countSiteWanClients` exports). No standalone
  wrapper function is introduced. The menu dispatch references the class method
  directly. Variable names use full words (`distinct_field`, `count_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected via `safe_input()` with
  explicit `context=` strings
  (`"site_wan_client_events_count:site_id"`,
  `"site_wan_client_events_count:distinct"`,
  `"site_wan_client_events_count:type"`,
  `"site_wan_client_events_count:duration"`,
  `"site_wan_client_events_count:limit"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. The `site_id` is
  validated against the Mist UUID shape before the API call; on validation
  failure the method logs a warning and returns early. The API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 91 countSiteWanClientEvents`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting.
  `INFO` is emitted before the API call
  (`"Counting WAN client events at site %s distinct=%s"`); `DEBUG` after the
  call with summary counts
  (`"WAN client event count: distinct=%s total=%d results=%d"`); `WARNING` on
  404 or empty payload; `ERROR` on unexpected exception via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will
  carry an inline comment explaining *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing site-WAN export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result count, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/562-mist-count-site-wan-client-events/
|-- plan.md              # This file
|-- spec.md              # Feature specification (already authored)
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_wan_client_events.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the site-WAN export class + PK strategy
                         # + menu 91 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91 addition
data/                    # Runtime output target (existing dir). DataExporter creates
                         # the new SQLite table on first write; no manual migration.
documentation/api/sites/ # Source-of-truth doc:
                         # GET_sites_site_id_wan_client_events_count.md
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing site-WAN export class in `MistHelper.py` (the
class that owns `searchSiteWanClientEvents` and `countSiteWanClients`). If
grep-of-source at task time finds no obvious home class, the method is added to
the broader `SiteStatsExportUtils` / equivalent class -- in no case is a new
top-level wrapper function created (Principle II). The proposed menu number
**91** is the next available slot in the 80-91 site-stats cluster, immediately
adjacent to the related WAN endpoints. The full menu list will be re-verified
at task generation; if 91 collides with an in-flight feature branch, the next
free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is a single dictionary entry
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  site-WAN export class. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path for all five inputs. UUID validation happens before
  the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline. The container build workflow trigger matches the file pattern
  already in place.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, full URL,
  or any prompt values that could leak secrets.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action (prompt,
  API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
