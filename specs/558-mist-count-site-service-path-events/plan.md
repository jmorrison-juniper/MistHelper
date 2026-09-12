# Implementation Plan: countSiteServicePathEvents Menu Item

**Branch**: `558-mist-count-site-service-path-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/558-mist-count-site-service-path-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/services/events/count` (operationId
`countSiteServicePathEvents`) to retrieve grouped counts of Service Path Events
(for example `GW_SERVICE_PATH_DOWN`, `GW_SERVICE_PATH_UP`) for a site, aggregated
by a caller-chosen `distinct` attribute (e.g. `type`, `vpn_name`, `vpn_path`,
`policy`, `mac`, `model`, `version`, `port_id`). The menu item prompts the user
for `site_id` and the `distinct` field via `safe_input()`, accepts optional
time-window filters (`start` / `end` / `duration`), invokes the `mistapi` SDK,
flattens the `results` array into one row per distinct bucket (with the bucket
value, the count, and the query envelope), and persists the result via
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs of the same query window
upsert cleanly. The new operation is proposed as menu number **96**, the next
available slot in the Interactive Safe / Site Stats cluster, adjacent to the
existing site-events search and insight viewers.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and
optional `MIST_SITE_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known site from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- new item 96 sits at the upper edge of the
Interactive Safe block and is inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
time windows (the endpoint returns pre-aggregated counts -- the `results` array
is bounded by the cardinality of the `distinct` field, not by raw event volume).
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue
to govern back-off; this endpoint is light enough that no special tuning is
required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteEventsExportUtils` class (the same class that owns the related site-events
search exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
SQLite table (`site_service_path_events_count`), one menu registration entry,
one README operation-count bump, one CHANGELOG line. No new dependencies, no
new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_service_path_events_count()` stays under 25 lines, takes <=5
  parameters (`self`, `site_id`, `distinct_field`, `start`, `end`), and contains
  <=5 logical blocks (prompts -> API call -> flatten results -> DataExporter
  call -> return). Hierarchy is unchanged: one new method on an existing class.
  No new packages, modules, or top-level constants are introduced. The flatten
  step is inlined as a single list comprehension; if it grows past 5 lines
  during implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SiteEventsExportUtils` class (the same class that owns the related
  `searchSiteServicePathEvents` and other site-events exports). No standalone
  wrapper function is introduced. The menu dispatch in the main loop references
  the class method directly. Variable names use full words (`distinct_field`,
  `result_bucket`, `query_window_start`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"site_service_path_events_count:site_id"`,
  `"site_service_path_events_count:distinct"`,
  `"site_service_path_events_count:start"`,
  `"site_service_path_events_count:end"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. `site_id` is validated
  against the Mist UUID shape before the API call; the `distinct` value is
  validated against the documented enum (`type`, `vpn_name`, `vpn_path`,
  `policy`, `port_id`, `model`, `version`, `mac`) before the API call. On
  validation failure the method logs a warning and returns early. API token
  comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 countSiteServicePathEvents` -> `git
  push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting service path events for site
  %s distinct=%s window=%s..%s"); `DEBUG` after the call with summary counts
  ("Count response: total=%d buckets=%d"); `WARNING` on 404 / empty payload;
  `ERROR` on unexpected exception with full traceback via `logging.exception`.
  No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing site-events export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, the SDK call, the flatten step, and
  the DataExporter call; `logging.debug(...)` after each with a result count
  or summary. The DataExporter call already emits its own per-backend log
  lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/558-mist-count-site-service-path-events/
|-- plan.md                                   # This file
|-- research.md                               # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md                             # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md                             # Phase 1 - local run + .env + quality gates
|-- contracts/
|   |-- count_site_service_path_events.md     # Phase 1 - HTTP + SDK contract
|-- tasks.md                                  # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteEventsExportUtils class + PK strategy + menu 96
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `SiteEventsExportUtils` class in
`MistHelper.py` (the same class that owns the other site-events exports). If
that class does not yet exist as a discrete owner, the closest existing class
(`SiteExportUtils` or the umbrella `SiteEventsManager`) absorbs the method
instead -- never as a standalone wrapper function. The menu number proposal is
**96**, chosen because operations 60-96 are the Interactive Safe cluster (Site
Devices 60-72, Insights 73-79, Stats 80-91, Viewers 92-96) and 96 is the next
available slot below the Resource Intensive block at 97-101. The full menu list
will be re-verified at task generation time; if 96 collides with an in-flight
feature branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry is a single insert
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SiteEventsExportUtils`. No wrappers introduced. A private flatten helper
  `_flatten_count_buckets` is added on the same class if needed.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation and `distinct` enum validation happen
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompts, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
